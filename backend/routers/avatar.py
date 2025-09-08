import time
from fastapi import APIRouter, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import aiohttp
import asyncio
import os
import uuid
from datetime import datetime
import aiofiles
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/avatar", tags=["avatar"])

SIMLI_API_KEY = os.getenv("SIMLIAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # Add this to your .env file
if not SIMLI_API_KEY:
    raise ValueError("SIMLIAI_API_KEY environment variable is not set")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable is not set")

# Create videos directory if it doesn't exist
VIDEOS_DIR = os.path.join("backend", "static", "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)


class AvatarRequest(BaseModel):
    text: str
    face_id: Optional[str] = "default"
    voice_id: Optional[str] = "pMsXgVXv3BLzUgSXRplE"  # Default ElevenLabs voice


class AvatarResponse(BaseModel):
    success: bool
    message: str
    video_url: Optional[str] = None
    hls_url: Optional[str] = None


async def download_video(url: str, file_path: str):
    time.sleep(5)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await response.read())
            else:
                raise HTTPException(status_code=500, detail="Failed to download video")


@router.post("/generate", response_model=AvatarResponse)
async def generate_avatar_video(request: AvatarRequest):
    try:
        # Prepare the request payload for Simli API
        payload = {
            "ttsAPIKey": ELEVENLABS_API_KEY,
            "simliAPIKey": SIMLI_API_KEY,
            "faceId": request.face_id,
            "requestBody": {
                "audioProvider": "ElevenLabs",
                "text": request.text,
                "voice": request.voice_id,  # Changed from voiceName to voice
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.1,
                    "similarity_boost": 0.3,
                    "style": 0.2,
                },
            },
        }

        # Make request to Simli API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.simli.ai/textToVideoStream",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Simli API error: {error_text}",
                    )

                result = await response.json()
                if not isinstance(result, dict) or "mp4_url" not in result:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Unexpected API response format: {result}",
                    )

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"avatar_{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
        file_path = os.path.join(VIDEOS_DIR, filename)

        # Download and save the MP4 file
        await download_video(result["mp4_url"], file_path)

        # Return both the local URL for the video and the HLS stream URL
        return AvatarResponse(
            success=True,
            message="Avatar video generated successfully",
            video_url=f"/static/videos/{filename}",
            hls_url=result.get("hls_url"),  # Include HLS URL if available
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating avatar video: {str(e)}"
        )
