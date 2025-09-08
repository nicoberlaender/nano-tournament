from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.utils.error_handler import handle_error
from backend.models.database import DocumentationScript, get_db
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

### NEVER USE GPT-4 ONLY USE GPT-4O-MINI

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter(prefix="/api/chat", tags=["chat"])


class Message(BaseModel):
    role: str  # 'user' or 'assistant' or 'system'
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    doc_url: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        if not request.doc_url:
            raise HTTPException(status_code=400, detail="Documentation URL is required")

        # Get the root URL and find the corresponding documentation script
        root_url = DocumentationScript.get_root_url(request.doc_url)
        query = select(DocumentationScript).where(
            DocumentationScript.root_url == root_url
        )
        result = await db.execute(query)
        doc_script = result.scalar_one_or_none()

        if not doc_script:
            raise HTTPException(
                status_code=404,
                detail=f"No documentation found for {root_url}. Please process the documentation first.",
            )

        # Convert 'ai' role to 'assistant' for OpenAI API compatibility
        openai_messages = []

        # Add system message first
        openai_messages.append(
            {
                "role": "system",
                "content": f"""You are a helpful AI assistant explaining documentation. 
            Use this documentation context to answer questions: {doc_script.script_content}
            
            Keep responses conversational and easy to understand. Focus on the documentation content. Keep answers concise and to the point.""",
            }
        )

        # Add user messages, converting 'ai' to 'assistant' if present
        for msg in request.messages:
            role = "assistant" if msg.role == "ai" else msg.role
            openai_messages.append({"role": role, "content": msg.content})

        # Generate response using OpenAI
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
            temperature=0.7,
            max_tokens=500,
        )

        return ChatResponse(
            response=response.choices[0].message.content,
            audio_url=None,  # We'll implement audio generation later
        )

    except Exception as e:
        raise handle_error(e)
