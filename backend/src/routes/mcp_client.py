import httpx
from typing import Optional
from contextlib import AsyncExitStack
from src.database.mongo import get_db
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from anthropic import AsyncAnthropic
from anthropic.types import ToolParam, MessageParam, ImageBlockParam, TextBlockParam, DocumentBlockParam
from dotenv import load_dotenv
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
import os
import base64
from docx import Document
import io
import tiktoken
from src.l402.l402 import create_response
from src.middleware.middleware import user_session
from src.database.redis import redis
from uuid import uuid4

load_dotenv()

mcp_client = APIRouter()

@mcp_client.get("/balance")
async def get_balance(user_id: str = Query(...)):
    users = get_db()["users"]
    user = await users.find_one({"user_id": user_id})
    if not user:
        return { "status": "failed", "message": "User not found." }
    return {
        "user_id": user_id,
        "balance": user["balance"]
    }

class ToolError(Exception):
    pass

class OutOfCredits(Exception):
    pass

class NotEnoughTokensForInput(Exception):
    pass

enc = tiktoken.get_encoding("cl100k_base")

class MCPClient:
    def __init__(self, balance, user_id, creator_id, cost_per_token, max_tokens):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC"))
        self.messages = []
        self.balance = balance
        self.cost_per_token = cost_per_token
        self.specified_max_tokens = max_tokens
        self.user_id = user_id
        self.creator_id = creator_id

    def remaining_tokens(self) -> int:
        return int(self.balance // self.cost_per_token)
    
    def max_tokens(self) -> int:
        if self.specified_max_tokens:
            return int(self.specified_max_tokens)
        return min(self.remaining_tokens() - 20, 1000)
    
    async def update_user_balance(self, new_balance: int):
        users = get_db()["users"]
        await users.update_one({"user_id": self.user_id}, {"$set": {"balance": max(0, new_balance)}})

    async def update_creator_credit(self, output_tokens: int, input_tokens: int):
        creators = get_db()["creators"]
        credits = (output_tokens * 0.05) + (input_tokens * 0.01)
        await creators.update_one({"pubkey": self.creator_id }, {"$inc": {"credits": credits}})

    async def connect_to_streamable_http_server(self, server_url: str, headers: Optional[dict] = None):
        self._streams_context = streamable_http_client(
            url=server_url,
            http_client=httpx.AsyncClient(headers=headers or {})
        )
        read_stream, write_stream, _ = await self._streams_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session = await self._session_context.__aenter__()

        await self.session.initialize()

    async def cleanup(self):
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


    async def process_query_stream(self, query: list):

        if not self.session:
            return

        system = "You are a helpful AI assistant." #TODO: What should this be?
        
        def docx_to_text(b: bytes) -> str:
            file_like = io.BytesIO(b)
            doc = Document(file_like)
            return "\n".join(p.text for p in doc.paragraphs)
        
        def base64_file_to_text(b64: str, filename: str) -> str:
            data = base64.b64decode(b64)
            ext = filename.rsplit(".", 1)[-1].lower()

            if ext in ["txt", "md", "csv"]:
                return data.decode("utf-8", errors="replace")
            elif ext == "docx":
                return docx_to_text(data)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

        def create_block_param(block):
            if block["type"] == "text":
                return TextBlockParam(type="text", text=block["text"])
            elif block["type"] == "image":
                return ImageBlockParam(type="image", source={
                    "type": "base64",
                    "data": block["data"],
                    "media_type": block["media_type"]
                })
            elif block["type"] == "document":
                return DocumentBlockParam(type="document", source={
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": block["data"]
                })
            elif block["type"] == "misc":
                try:
                    text = base64_file_to_text(block["data"], block["filename"])
                    return TextBlockParam(type="text", text=text)
                except ValueError as e:
                    return TextBlockParam(type="text", text=f"User attempted to add file which was unable to be parsed: {str(e)}")
            return None

        content = []
        for block in query:
            param = create_block_param(block)
            if param != None:
                content.append(param)

        self.messages.append(
            MessageParam(
                role="user",
                content=content
            )
        )

        input_token_cost = await self.anthropic.messages.count_tokens(messages=self.messages, model="claude-haiku-4-5-20251001")
        if self.balance - input_token_cost.input_tokens * self.cost_per_token / 5 < 50:
            self.messages.pop()
            raise NotEnoughTokensForInput()

        remaining = self.remaining_tokens()
        if remaining <= 20:
            self.messages.pop()
            raise OutOfCredits()

        tools_response = await self.session.list_tools()
        available_tools: list[ToolParam] = [
            ToolParam(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema,
            )
            for tool in tools_response.tools
        ]

        self.estimated_output_tokens = 0

        async with self.anthropic.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=self.max_tokens(),
            messages=self.messages,
            tools=available_tools,
            system=system
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    yield {"type": "text", "content": event.delta.text}

            assistant_msg = await stream.get_final_message()
            self.messages.append({
                "role": assistant_msg.role,
                "content": assistant_msg.content
            })
            self.actual_tokens = assistant_msg.usage.output_tokens
            input_tokens = assistant_msg.usage.input_tokens
            self.balance -= self.actual_tokens * self.cost_per_token
            self.balance -= input_tokens * (self.cost_per_token / 5)
            await self.update_user_balance(self.balance)
            await self.update_creator_credit(self.actual_tokens, input_tokens)

        while assistant_msg.stop_reason == "tool_use":
            new_tool_uses = [
                block for block in assistant_msg.content
                if getattr(block, "type", None) == "tool_use"
            ]

            if not new_tool_uses:
                break

            for block in new_tool_uses:
                tool_name = block.name #type: ignore
                tool_args = block.input #type: ignore
                tool_use_id = block.id #type: ignore

                try:
                    result = await self.session.call_tool(tool_name, tool_args)
                except Exception as e:
                    print(f"Tool call error: {e}")
                    raise ToolError(f"An error occurred when calling tool '{tool_name}': {str(e)}")

                tool_result_content = []
                for content_block in result.content:
                    block_type = getattr(content_block, 'type', None)
                    
                    if block_type == 'text':
                        tool_result_content.append({
                            "type": "text",
                            "text": content_block.text  # type: ignore
                        })
                    elif block_type == 'image':
                        tool_result_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_block.mimeType,  # type: ignore
                                "data": content_block.data  # type: ignore
                            }
                        })
                    elif block_type == 'audio':
                        tool_result_content.append({
                            "type": "audio",
                            "data": content_block.data,  # type: ignore
                            "media_type": content_block.mimeType  # type: ignore
                        })
                    elif block_type == 'resource_link':
                        description = getattr(content_block, 'description', '') or ''
                        tool_result_content.append({
                            "type": "text",
                            "text": f"Resource: {content_block.name}\nURI: {content_block.uri}\n{description}".strip()  # type: ignore
                        })
                    elif block_type == 'resource':
                        resource = content_block.resource  # type: ignore
                        if hasattr(resource, 'text'):
                            tool_result_content.append({
                                "type": "text",
                                "text": resource.text  # type: ignore
                            })
                        elif hasattr(resource, 'blob'):
                            mime_type = getattr(resource, 'mimeType', 'application/octet-stream')
                            tool_result_content.append({
                                "type": "blob",
                                "uri": resource.uri,  # type: ignore
                                "media_type": mime_type,
                                "data": resource.blob  # type: ignore
                            })
                        else:
                            tool_result_content.append({
                                "type": "text",
                                "text": f"[Resource: {getattr(resource, 'uri', 'unknown')}]"
                            })
                    else:
                        tool_result_content.append({
                            "type": "text",
                            "text": str(content_block)
                        })

                anthropic_content = []
                for item in tool_result_content:
                    if item["type"] == "text":
                        anthropic_content.append(item)
                    elif item["type"] == "image":
                        yield {"type": "image", "data": item["source"]["data"], "media_type": item["source"]["media_type"]}
                        anthropic_content.append({
                            "type": "text",
                            "text": f"Created image: {item['source']['media_type']}"
                        })
                    elif item["type"] == "audio":
                        yield {"type": "audio", "data": item["data"], "media_type": item["media_type"]}
                        anthropic_content.append({
                            "type": "text",
                            "text": f"Created audio: {item['media_type']}"
                        })
                    elif item["type"] == "blob":
                        yield {"type": "blob", "uri": item["uri"], "data": item["data"], "media_type": item["media_type"]}
                        anthropic_content.append({
                            "type": "text",
                            "text": f"Created blob: {item['media_type']} (uri: {item['uri']})"
                        })
                
                self.messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": anthropic_content,
                        }
                    ],
                })

            remaining = self.remaining_tokens()
            if remaining <= 20:
                raise OutOfCredits()
            async with self.anthropic.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=self.max_tokens(),
                messages=self.messages,
                tools=available_tools,
                system=system
            ) as followup:
                async for event in followup:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield { "type": "text", "content": event.delta.text}

                assistant_msg = await followup.get_final_message()
                self.messages.append({
                    "role": assistant_msg.role,
                    "content": assistant_msg.content
                })
                self.actual_tokens = assistant_msg.usage.output_tokens
                input_tokens = assistant_msg.usage.input_tokens
                self.balance -= self.actual_tokens * self.cost_per_token
                self.balance -= input_tokens * (self.cost_per_token / 5)
                await self.update_user_balance(self.balance)
                await self.update_creator_credit(self.actual_tokens, input_tokens)

    
@mcp_client.websocket("/chat/{id}")
async def websocket_chat(id: str, websocket: WebSocket, max_tokens: str = Query(None)):

    await websocket.accept()

    user = await user_session(websocket)

    agents = get_db()["agents"]
    agent = await agents.find_one({ "id": id })

    if not agent:
        await websocket.send_json({
            "type": "error",
            "message": "Agent not found.",
        })
        await websocket.close(1000)
        return

    port = agent["port"]
    cost_per_token = agent["cost_per_token"]

    if not user:
        await websocket.send_json({
            "type": "error",
            "message": "Authorization not found. Call /user-signin to receive an authorization token.",
        })
        await websocket.close(1000)
        return
        
    client = MCPClient(user["balance"], user["user_id"], agent["creator"], cost_per_token, max_tokens)

    ws_id = str(uuid4())

    try:
        set = await redis.setex(f"ws_active:{user["user_id"]}", 300, ws_id)
        if not set:
            await websocket.close(1000)
            return

        try:
            await client.connect_to_streamable_http_server(f"http://localhost:{port}/mcp")
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to connect to MCP server: {str(e)}",
            })
            await websocket.close(1000)
            return

        while True:
            
            ws = await websocket.receive_text()

            user = await get_db()["users"].find_one({ "user_id": user["user_id"] }) #type: ignore
            client.balance = user["balance"] #type: ignore
            
            if len(ws.encode('utf-8')) > 20000000:
                await websocket.send_json({"type": "error", "message": "Input too large."})
                await websocket.send_json({"type": "end"})
                continue
            try:
                data: list = json.loads(ws)
            except:
                await websocket.send_json({"type": "error", "message": "Unable to parse input"})
                await websocket.send_json({"type": "end"})
                continue

            await websocket.send_json({"type": "start"})

            try:
                async for chunk in client.process_query_stream(data):
                    await websocket.send_json(chunk)
            except OutOfCredits:
                await websocket.send_json({"type": "402", "message": create_response(user["user_id"], "top-up")}) #type: ignore
            except ToolError as e:
                await websocket.send_json({"type": "error", "message": str(e)})
            except NotEnoughTokensForInput as e:
                await websocket.send_json({"type": "error", "message": create_response(user["user_id"], "top-up", "Not enough credits to support input size.")}) #type: ignore
            except Exception as e:
                import traceback
                traceback.print_exc()
                await websocket.send_json({"type": "error", "message": f"An internal server error occurred: {str(e)}"})

            await websocket.send_json({"type": "end"})

    except WebSocketDisconnect:
        pass
    finally:
        owner = await redis.get(f"ws_active:{user["user_id"]}") #type: ignore
        if owner == ws_id:
            await redis.delete(f"ws_active:{user["user_id"]}") #type: ignore
        await client.cleanup()