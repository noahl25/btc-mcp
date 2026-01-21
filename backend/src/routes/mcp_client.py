import httpx
from typing import Optional, cast, List
from contextlib import AsyncExitStack
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from anthropic import Anthropic
from anthropic.types import MessageParam, ToolUnionParam, TextBlockParam
from dotenv import load_dotenv

load_dotenv()

class MCPClient:

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

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


async def process_query(self, query: str) -> str:

    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    response = await self.session.list_tools()
    available_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in response.tools]

    response = self.anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )
    final_text = []

    assistant_message_content = []
    for content in response.content:
        if content.type == 'text':
            final_text.append(content.text)
            assistant_message_content.append(content)
        elif content.type == 'tool_use':
            tool_name = content.name
            tool_args = content.input

            result = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            assistant_message_content.append(content)

            messages.append({
                "role": "assistant",
                "content": json.dumps(assistant_message_content, default=str)
            })

            messages.append({
                "role": "user",
                "content": json.dumps([
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ], default=str)
            })

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            final_text.append(response.content[0].text)

    return "\n".join(final_text)
