import asyncio
import base64
import httpx
import json
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, field_validator
from langchain_core.tools import tool
import os
import websockets
from lightspark_client import LightsparkClient

CACHE = f"{os.path.expanduser("~")}\\.btc-mcp"
USER_ID: str | None = None
LIGHTSPARK_CLIENT: LightsparkClient | None = None
WS_CONNECTION: websockets.ClientConnection | None = None

def get_new_user_id():
    global USER_ID
    response = httpx.post("http://localhost:8000/user/user-signin")
    response.raise_for_status()
    json = response.json()
    USER_ID = json["id"]
    with open(f"{CACHE}\\cache.txt", "w") as cache:
        cache.write(str(USER_ID))

def sign_in():
    global USER_ID
    if not os.path.exists(f"{CACHE}\\cache.txt"):
        get_new_user_id()
    else:
        with open(f"{CACHE}\\cache.txt", "r") as cache:
            contents = cache.read()
        if not contents:
            get_new_user_id()
        else:
            USER_ID = contents

os.makedirs(CACHE, exist_ok=True)
sign_in()

def init_lightspark_client(lightspark_client_id: str, lightspark_client_secret: str, lightspark_node_id: str, lightspark_node_password: str, max_spend: int | None = None):
    global LIGHTSPARK_CLIENT
    LIGHTSPARK_CLIENT = LightsparkClient(lightspark_client_id, lightspark_client_secret, lightspark_node_id, lightspark_node_password, max_spend)

@tool
def search_agents(query: Optional[str] = None, sort_by: Literal["date", "staked"] = "date", skip: int = 0, exact_search: bool = False) -> list[dict]:
    """
    Search for available AI agents.
    
    Use this tool to discover AI agents that can help with specific tasks.
    You can search by keyword, sort by date or staked amount, and paginate results.
    
    Args:
        query: Optional search query to filter agents by title/description. Leave empty to get all agents.
        sort_by: How to sort results - "date" for newest first or "staked" for most staked (or most "upvoted") first.
        skip: Number of results to skip for pagination.
        exact_search: If True, performs exact text matching. If False, uses semantic search.
    
    Returns:
        A list of agent dictionaries containing agent details like id, title, description, etc.
    """
    params = {
        "sort_by": sort_by,
        "skip": skip,
        "exact_search": exact_search
    }
    if query:
        params["query"] = query
    response = httpx.get("http://localhost:8000/api/agents", params=params)
    response.raise_for_status()
    return response.json()

class TextBlock(BaseModel):
    type: Literal["text"]
    text: str

class ImageBlock(BaseModel):
    type: Literal["image"]
    data: str
    media_type: str
    @field_validator("data")
    def check_base64(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Invalid base64 data for image.")
        return v

class DocumentBlock(BaseModel):
    """ For PDF's specifically """
    type: Literal["document"]
    data: str
    @field_validator("data")
    def check_base64(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Invalid base64 data for document.")
        return v

class MiscBlock(BaseModel):
    type: Literal["misc"]
    data: str
    filename: str
    @field_validator("data")
    def check_base64(cls, v):
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("Invalid base64 data for misc.")
        return v

class Input(BaseModel):
    input: List[Union[TextBlock, ImageBlock, DocumentBlock, MiscBlock]]

class StartChatInput(BaseModel):
    input: List[Union[TextBlock, ImageBlock, DocumentBlock, MiscBlock]]
    agent_id: str
    max_tokens: Optional[int] = None

async def _send_and_receive(ws: websockets.ClientConnection, message: list[dict]) -> list[dict]:
    await ws.send(json.dumps(message))
    chunks: list[dict] = []
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=120)
        except asyncio.TimeoutError:
            chunks.append({"type": "error", "message": "Response timed out after 120 seconds."})
            break
        except websockets.exceptions.ConnectionClosed as e:
            chunks.append({"type": "error", "message": f"Connection closed: {str(e)}"})
            break
        data = json.loads(raw)
        chunks.append(data)
        if data.get("type") in ("end", "error", "402"):
            break
    return chunks

@tool(args_schema=StartChatInput)
async def start_chat(input: List[Union[TextBlock, ImageBlock, DocumentBlock, MiscBlock]], agent_id: str, max_tokens: Optional[int] = None) -> list[dict]:
    """
    Start a new chat session with an AI agent.

    Opens a persistent WebSocket connection to the specified agent and sends
    the initial query. The connection remains open for follow-up messages
    via continue_chat. Call end_chat when the conversation is finished.

    The input is a list of content blocks that can contain text, images
    (base64-encoded with media_type), PDF documents (base64-encoded), or
    miscellaneous files (base64-encoded with filename).

    Args:
        input: A list of content blocks to send as the first message. Each block
            is one of TextBlock, ImageBlock, DocumentBlock (pdf), or MiscBlock.
        agent_id: The unique identifier of the agent to chat with. Use
            search_agents to discover available agent IDs.
        max_tokens: Optional maximum number of output tokens per response.
            If not provided, the server calculates a limit based on your balance.

    Returns:
        A list of response chunks from the agent. Each chunk is a dict with a
        "type" key ("start", "text", "image", "audio", "blob", "error", "402",
        or "end") and associated data.
    """
    global WS_CONNECTION

    if WS_CONNECTION is not None:
        try:
            await WS_CONNECTION.close()
        except Exception:
            pass
        WS_CONNECTION = None

    if not USER_ID:
        return [{"type": "error", "message": "Not signed in. USER_ID is not set."}]

    url = f"ws://localhost:8000/ws/chat/{agent_id}"
    if max_tokens is not None:
        url += f"?max_tokens={max_tokens}"

    headers = {"Authorization": f"Bearer {USER_ID}"}

    try:
        ws = await websockets.connect(url, additional_headers=headers, open_timeout=30, close_timeout=10)
    except Exception as e:
        return [{"type": "error", "message": f"Failed to connect to agent: {str(e)}"}]

    WS_CONNECTION = ws

    message = [block.model_dump() for block in input]
    try:
        return await _send_and_receive(ws, message)
    except Exception as e:
        return [{"type": "error", "message": f"Error during chat: {str(e)}"}]


@tool(args_schema=Input)
async def continue_chat(input: List[Union[TextBlock, ImageBlock, DocumentBlock, MiscBlock]]) -> list[dict]:
    """
    Continue an existing chat session with the current agent.

    Sends a follow-up message over the WebSocket connection that was opened
    by start_chat. The conversation context is preserved server-side.

    The input is a list of content blocks that can contain text, images
    (base64-encoded with media_type), PDF documents (base64-encoded), or
    miscellaneous files (base64-encoded with filename).

    Args:
        input: A list of content blocks to send as a follow-up message. Each
            block is one of TextBlock, ImageBlock, DocumentBlock, or MiscBlock.

    Returns:
        A list of response chunks from the agent. Each chunk is a dict with a
        "type" key ("start", "text", "image", "audio", "blob", "error", "402",
        or "end") and associated data.
    """
    global WS_CONNECTION

    if WS_CONNECTION is None:
        return [{"type": "error", "message": "No active chat session. Call start_chat first."}]

    message = [block.model_dump() for block in input]
    try:
        return await _send_and_receive(WS_CONNECTION, message)
    except Exception as e:
        WS_CONNECTION = None
        return [{"type": "error", "message": f"Error during chat: {str(e)}"}]


@tool
async def top_up(offer_id: str) -> dict:
    """
    Purchase credits by paying a Lightning invoice for the specified offer.

    Requests a Lightning invoice from the server for the given offer and
    automatically pays it using the configured Lightspark client. The user's
    balance is updated server-side upon successful payment.

    Requires a Lightspark client to be initialized via init_lightspark_client
    before calling this tool.

    Args:
        offer_id: The unique identifier of the credit offer to purchase.
            Available offers are returned in 402 payment-required responses
            from the server when credits run out.

    Returns:
        A dict with the payment result. On success: {"status": "success"}.
        On failure: {"status": "failed", "message": "..."}.
    """
    if not LIGHTSPARK_CLIENT:
        return {"status": "failed", "message": "Lightspark client not initialized. Call init_lightspark_client first."}

    if not USER_ID:
        return {"status": "failed", "message": "Not signed in. USER_ID is not set."}

    try:
        response = httpx.post(
            "http://localhost:8000/api/payments/top-up",
            json={"offer_id": offer_id, "authorization_token": USER_ID}
        )
        response.raise_for_status()
        invoice = response.text.strip().strip('"')
    except Exception as e:
        return {"status": "failed", "message": f"Failed to create invoice: {str(e)}"}

    try:
        result = LIGHTSPARK_CLIENT.pay_invoice(invoice)
        return result
    except Exception as e:
        return {"status": "failed", "message": f"Failed to pay invoice: {str(e)}"}


@tool
async def end_chat() -> dict:
    """
    End the current chat session and close the WebSocket connection.

    Cleanly closes the WebSocket connection that was opened by start_chat.
    After calling this, you must call start_chat again to begin a new
    conversation.

    Returns:
        A dict with the status of the operation. On success:
        {"status": "success", "message": "Chat session ended."}.
    """
    global WS_CONNECTION

    if WS_CONNECTION is None:
        return {"status": "success", "message": "No active chat session."}

    try:
        await WS_CONNECTION.close()
    except Exception:
        pass
    finally:
        WS_CONNECTION = None

    return {"status": "success", "message": "Chat session ended."}


@tool
def get_balance() -> dict:
    """
    Retrieve the current credit balance for the authenticated user.

    Queries the server for the user's remaining credit balance. Credits are
    consumed when chatting with agents and can be replenished via top_up.

    Returns:
        A dict containing the user's balance information with keys "user_id"
        and "balance", or a failure message if the user is not found.
    """
    if not USER_ID:
        return {"status": "failed", "message": "Not signed in. USER_ID is not set."}

    try:
        response = httpx.get(
            "http://localhost:8000/ws/balance",
            params={"user_id": USER_ID}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "failed", "message": f"Failed to get balance: {str(e)}"}