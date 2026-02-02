from src.database.embed import embed_query
from src.database.mongo import get_db
from fastapi import APIRouter
from typing import Optional

agents = APIRouter()

async def vector_search(query: str, limit=50):
    query_embedding = embed_query(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "agent_vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 100,
                "limit": limit
            }
        },
        {
            "$addFields": {
                "port": 0,
                "embeddings": 0
            }
        }
        # {
        #     "$addFields": {
        #         "score": { "$meta": "vectorSearchScore" }
        #     }
        # }
    ]
    
    return await (await get_db()["agents"].aggregate(pipeline)).to_list()

@agents.get("/agents")
async def get(query: Optional[str] = None, skip: int = 0):
    if query and query != "":
        return await vector_search(query.strip())
    else:
        cursor = get_db()["agents"].find().sort("date", 1).skip(skip).limit(50)
        return await cursor.to_list(length=50) 
    
@agents.get("/agents/{id}")
async def get_by_id(id: int):
    return get_db()["agents"].find_one({ "id": id }, { "port": 0, "embeddings": 0 })