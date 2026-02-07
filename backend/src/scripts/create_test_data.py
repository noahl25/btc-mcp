# import_agents.py

import json
import asyncio
from datetime import datetime
from src.database.mongo import get_db, connect_db
from src.database.embed import embed

JSON_FILE = "src/scripts/test_data.json"

def load_agents(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        agents = json.load(f)

    for agent in agents:
        if isinstance(agent.get("date"), str):
            agent["date"] = datetime.fromisoformat(agent["date"].replace("Z", "+00:00"))

        agent["embedding"] = embed(agent["title"], agent["description"], json.dumps(agent["tools"]))
    return agents

async def main():
    await connect_db()
    db = get_db()
    collection = db["agents"]

    agents = load_agents(JSON_FILE)
    if agents:
        result = await collection.insert_many(agents)

if __name__ == "__main__":
    asyncio.run(main())
