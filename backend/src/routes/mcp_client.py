import httpx
from typing import Optional
from contextlib import AsyncExitStack
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from anthropic import Anthropic
from anthropic.types import ToolParam, MessageParam, ImageBlockParam, TextBlockParam, DocumentBlockParam
from dotenv import load_dotenv

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os
import base64
from docx import Document
import io

load_dotenv()

mcp_client = APIRouter()

class MCPClient:

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC"))
        self.messages = []

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
        
        system = "You are a helpful AI assistant." #TODO: Get system prompt from client.
        
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

        tools_response = await self.session.list_tools()
        available_tools: list[ToolParam] = [
            ToolParam(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema,
            )
            for tool in tools_response.tools
        ]

        with self.anthropic.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=self.messages,
            tools=available_tools,
            system=system
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    for char in event.delta.text:
                        yield char

            assistant_msg = stream.get_final_message()
            self.messages.append({
                "role": assistant_msg.role,
                "content": assistant_msg.content
            })
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

                result = await self.session.call_tool(tool_name, tool_args)

                text = ""
                if isinstance(result.content, list):
                    text = "".join(
                        b.text for b in result.content if getattr(b, "type", None) == "text" #type: ignore
                    )
                else:
                    text = str(result.content)

                self.messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": text,
                        }
                    ],
                })

            with self.anthropic.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=self.messages,
                tools=available_tools,
                system=system
            ) as followup:
                for f_event in followup:
                    if f_event.type == "content_block_delta" and f_event.delta.type == "text_delta":
                        yield f_event.delta.text
                assistant_msg = followup.get_final_message()
                self.messages.append({
                    "role": assistant_msg.role,
                    "content": assistant_msg.content
                })

    
@mcp_client.websocket("/chat/{id}")
async def websocket_chat(id: str, websocket: WebSocket):

    await websocket.accept()
    client = MCPClient()

    try:
        await client.connect_to_streamable_http_server(f"http://localhost:{id}/mcp")

        while True:
            ws = await websocket.receive_text()
            data: list = json.loads(ws)

            await websocket.send_json({"type": "start"})

            async for chunk in client.process_query_stream(data): #TODO: Don't accept queries larger than x bytes.
                await websocket.send_json({
                    "type": "token",
                    "content": chunk
                })

            await websocket.send_json({"type": "end"})

    except WebSocketDisconnect:
        pass
    finally:
        await client.cleanup()