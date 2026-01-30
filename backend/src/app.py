from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database import mongo

from src.routes.mcp_server import mcp_server
from src.routes.mcp_client import mcp_client
from src.routes.lnauth import lnauth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo.connect_db()
    yield
    await mongo.close_db()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(mcp_server, prefix="/api")
app.include_router(mcp_client, prefix="/ws")
app.include_router(lnauth, prefix="/lnurl-auth")

@app.get("/health")
async def health():
    return { "status": "Healthy" }