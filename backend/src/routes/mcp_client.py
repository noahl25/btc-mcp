import httpx
from typing import Optional
from contextlib import AsyncExitStack
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from anthropic import Anthropic
from anthropic.types import ToolParam, MessageParam, ToolResultBlockParam, TextBlockParam
from dotenv import load_dotenv

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import os

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


    async def process_query_stream(self, query: str):

        if not self.session:
            return

        self.messages.append(
            MessageParam(
                role="user",
                content=[TextBlockParam(type="text", text=query)]
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
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                            for char in event.delta.text:
                                yield char

            assistant_msg = stream.get_final_message()
            self.messages.append({
                "role": assistant_msg.role,
                "content": assistant_msg.content
            })

            if assistant_msg.stop_reason == "tool_use":
                for block in assistant_msg.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_args = block.input
                        tool_use_id = block.id

                        result = await self.session.call_tool(tool_name, tool_args)

                        text = ""
                        if isinstance(result.content, list):
                            text = "".join(b.text for b in result.content if getattr(b, "type", None) == "text") #type: ignore
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
                ) as followup:
                    for f_event in followup:
                        if f_event.type == "content_block_delta" and f_event.delta.type == "text_delta":
                            yield f_event.delta.text
                    
                    final_msg = followup.get_final_message()

                self.messages.append({
                    "role": final_msg.role,
                    "content": final_msg.content
                })

    
@mcp_client.websocket("/chat/{id}")
async def websocket_chat(id: str, websocket: WebSocket):
    await websocket.accept()
    client = MCPClient()

    try:
        await client.connect_to_streamable_http_server(f"http://localhost:{id}/mcp")

        while True:
            query = await websocket.receive_text()

            await websocket.send_json({"type": "start"})

            async for chunk in client.process_query_stream(query):
                await websocket.send_json({
                    "type": "token",
                    "content": chunk
                })

            await websocket.send_json({"type": "end"})

    except WebSocketDisconnect:
        pass
    finally:
        await client.cleanup()