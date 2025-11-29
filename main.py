from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="Backend API",
    description="FastAPI backend for webdevhackathon",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class MessageResponse(BaseModel):
    message: str


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Backend API"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now()
    )


@app.get("/api/hello", response_model=MessageResponse)
async def hello():
    """Hello endpoint"""
    return MessageResponse(message="Hello from backend!")


# Import and include the transcript router
from transcript import router as transcript_router
app.include_router(transcript_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
