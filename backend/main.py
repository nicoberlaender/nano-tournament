from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import session, generate, users, websocket
from models.database import init_db
from dotenv import load_dotenv
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Nano Tournament API",
    description="Backend API for mobile fighting game with AI-generated characters",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(session.router)
app.include_router(generate.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {"message": "Welcome to AI Documentation Journey API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
