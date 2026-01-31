import httpx
from typing import Optional
from contextlib import AsyncExitStack
from src.database.mongo import get_db
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from anthropic import Anthropic
from anthropic.types import ToolParam, MessageParam, ImageBlockParam, TextBlockParam, DocumentBlockParam
from dotenv import load_dotenv

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, Depends
import os
import base64
from docx import Document
import io
import tiktoken

from src.l402.l402 import create_response

from src.middleware.middleware import user_session

load_dotenv()

mcp_client = APIRouter()

class ToolError(Exception):
    pass

class OutOfCredits(Exception):
    pass

enc = tiktoken.get_encoding("cl100k_base")

class MCPClient:

    def __init__(self, balance, user_id, creator_id, cost_per_token, max_tokens):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC"))
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
            return self.specified_max_tokens
        return min(self.remaining_tokens() - 20, 1000)
    
    async def update_user_balance(self, new_balance: int):
        users = get_db()["users"]
        await users.update_one({"id": self.user_id}, {"$set": {"balance": new_balance}})

    async def update_creator_credit(self, new_balance: int):
        users = get_db()["creators"]
        await users.update_one({"pubkey": self.creator_id }, {"$set": {"credits": new_balance}})

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
        
        remaining = self.remaining_tokens()
        if remaining <= 20:
            raise OutOfCredits()

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

        with self.anthropic.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=self.max_tokens(),
            messages=self.messages,
            tools=available_tools,
            system=system
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    tokens = len(enc.encode(event.delta.text))
                    self.estimated_output_tokens += tokens

                    if self.estimated_output_tokens >= self.remaining_tokens() - 20:
                        stream.close()
                        raise OutOfCredits()

                    yield event.delta.text

            assistant_msg = stream.get_final_message()
            self.messages.append({
                "role": assistant_msg.role,
                "content": assistant_msg.content
            })
            actual_tokens = assistant_msg.usage.output_tokens
            self.balance -= actual_tokens * self.cost_per_token
            await self.update_user_balance(self.balance)

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
                except:
                    raise ToolError("An error occurred when calling a tool.")

                self.messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result.content,
                        }
                    ],
                })
            remaining = self.remaining_tokens()
            if remaining <= 20:
                raise OutOfCredits()
            with self.anthropic.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=self.max_tokens(),
                messages=self.messages,
                tools=available_tools,
                system=system
            ) as followup:
                for event in followup:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        tokens = len(enc.encode(event.delta.text))
                        self.estimated_output_tokens += tokens
                        if self.estimated_output_tokens >= self.remaining_tokens() - 20:
                            followup.close()
                            raise OutOfCredits()
                        yield event.delta.text

                assistant_msg = followup.get_final_message()
                self.messages.append({
                    "role": assistant_msg.role,
                    "content": assistant_msg.content
                })
                actual_tokens = assistant_msg.usage.output_tokens
                self.balance -= actual_tokens * self.cost_per_token
                await self.update_user_balance(self.balance)

    
@mcp_client.websocket("/chat/{id}")
async def websocket_chat(id: str, websocket: WebSocket, max_tokens: str = Query(None), user = Depends(user_session)):

    await websocket.accept()

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

    try:
        await client.connect_to_streamable_http_server(f"http://localhost:{port}/mcp")

        while True:
            ws = await websocket.receive_text()
            
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
                    await websocket.send_json({
                        "type": "token",
                        "content": chunk
                    })
            except OutOfCredits:
                await websocket.send_json({"type": "402", "message": create_response(user["id"])})
            except ToolError as e:
                await websocket.send_json({"type": "error", "message": str(e)})
            except:
                await websocket.send_json({"type": "error", "message": "An internal server error occurred."})

            await websocket.send_json({"type": "end"})

    except WebSocketDisconnect:
        pass
    finally:
        await client.cleanup()