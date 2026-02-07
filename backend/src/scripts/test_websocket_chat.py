"""
Test script for the /chat/{id} WebSocket endpoint.

Usage:
    python test-websocket-chat.py --agent-id <agent_id> --token <user_token> [--max-tokens <num>]

Example:
    python test-websocket-chat.py --agent-id abc123 --token my-user-id --max-tokens 500
"""

import asyncio
import argparse
import json
import websockets


async def test_websocket_chat(base_url: str, agent_id: str, token: str, max_tokens: str | None = None):
    url = f"{base_url}/chat/{agent_id}"
    if max_tokens:
        url += f"?max_tokens={max_tokens}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"Connecting to {url}...")

    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("Connected!\n")

            while True:
                # Get user input
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Closing connection...")
                    break

                # Send message as a list with a text block
                message = [
                    {
                        "type": "text",
                        "text": user_input
                    }
                ]
                await ws.send(json.dumps(message))

                # Receive and print response
                assistant_response = ""
                while True:
                    response = await ws.recv()
                    data = json.loads(response)

                    if data["type"] == "start":
                        print("Assistant: ", end="", flush=True)
                    elif data["type"] == "token":
                        print(data["content"], end="", flush=True)
                        assistant_response += data["content"]
                    elif data["type"] == "error":
                        print(f"\n[ERROR] {data['message']}")
                        break
                    elif data["type"] == "402":
                        print(f"\n[OUT OF CREDITS] Payment required.")
                        print(f"Payment info: {json.dumps(data['message'], indent=2)}")
                        break
                    elif data["type"] == "end":
                        print("\n")
                        break

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test the WebSocket chat endpoint")
    parser.add_argument("--base-url", default="ws://localhost:8000/ws", help="Base WebSocket URL (default: ws://localhost:8000/ws)")
    parser.add_argument("--agent-id", required=True, help="The agent ID to chat with")
    parser.add_argument("--token", required=True, help="User authorization token (from /user-signin)")
    parser.add_argument("--max-tokens", default=None, help="Max tokens per response (optional)")

    args = parser.parse_args()

    asyncio.run(test_websocket_chat(
        base_url=args.base_url,
        agent_id=args.agent_id,
        token=args.token,
        max_tokens=args.max_tokens
    ))


if __name__ == "__main__":
    main()
