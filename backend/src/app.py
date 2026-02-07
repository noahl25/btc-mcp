from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database import mongo

from src.routes.mcp_server import mcp_server
from src.routes.mcp_client import mcp_client
from src.routes.creator import creator
from src.routes.user import user
from src.routes.agents import agents
from src.routes.payments import payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo.connect_db()
    yield
    await mongo.close_db()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(mcp_server, prefix="/api")
app.include_router(mcp_client, prefix="/ws")
app.include_router(creator, prefix="/creator")
app.include_router(user, prefix="/user")
app.include_router(agents, prefix="/api")
app.include_router(payments, prefix="/api/payments")

@app.get("/health")
async def health():
    return { "status": "Healthy" }