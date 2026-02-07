from src.database.embed import embed_query
from src.database.mongo import get_db
from fastapi import APIRouter
from typing import Literal

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
            "$project": {
                "_id": 0,
                "port": 0,
                "embedding": 0
            }
        }
        # {
        #     "$addFields": {
        #         "score": { "$meta": "vectorSearchScore" }
        #     }
        # }
    ]
    
    cursor = await get_db()["agents"].aggregate(pipeline)
    return await cursor.to_list(length=limit)

@agents.get("/agents")
async def get(query: str | None = None, sort_by: Literal["date", "staked"] = "date", skip: int = 0, exact_search: bool = False):
    if query and query != "":
        if exact_search:
            pipeline = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {}
                ]
            }
            cursor = get_db()["agents"].find(pipeline, {"_id": 0, "port": 0, "embeddings": 0}).sort(sort_by, -1 if sort_by == "staked" else 1).skip(skip).limit(50)
            return await cursor.to_list(length=50)
        else:
            res = await vector_search(query.strip())
            return res
    else:
        cursor = get_db()["agents"].find({}, {"_id": 0, "port": 0, "embeddings": 0}).sort(sort_by, -1 if sort_by == "staked" else 1).skip(skip).limit(50)
        return await cursor.to_list(length=50)
    
@agents.get("/agents/{id}")
async def get_by_id(id: str):
    return await get_db()["agents"].find_one({ "id": id }, { "_id": 0, "port": 0, "embeddings": 0 })