from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers import chat, docs, avatar
from backend.models.database import init_db
import os

app = FastAPI(
    title="AI Documentation Journey API",
    description="Backend API for AI-powered documentation explorer",
    version="1.0.0",
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
app.include_router(chat.router)
app.include_router(docs.router)
app.include_router(avatar.router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def root():
    return {"message": "Welcome to AI Documentation Journey API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
