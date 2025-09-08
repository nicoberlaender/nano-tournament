from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.utils.doc_processor import fetch_documentation, generate_explanation_script
from backend.utils.error_handler import handle_error
from backend.models.database import DocumentationScript, get_db

router = APIRouter(prefix="/api/docs", tags=["documentation"])

### NEVER USE GPT-4 ONLY USE GPT-4O-MINI


class DocumentationRequest(BaseModel):
    url: HttpUrl
    sections: Optional[List[str]] = None


class DocumentationResponse(BaseModel):
    success: bool
    message: str
    script: str
    sections: Optional[List[str]] = None


@router.post("/process", response_model=DocumentationResponse)
async def process_documentation(
    request: DocumentationRequest, db: AsyncSession = Depends(get_db)
):
    try:
        url_str = str(request.url)
        root_url = DocumentationScript.get_root_url(url_str)

        # Check if we already have a script for this root_url
        query = select(DocumentationScript).where(
            DocumentationScript.root_url == root_url
        )
        result = await db.execute(query)
        existing_script = result.scalar_one_or_none()

        if existing_script:
            return DocumentationResponse(
                success=True,
                message="Documentation script retrieved from database",
                script=existing_script.script_content,
                sections=["Introduction", "Key Concepts", "Use Cases"],
            )

        # If not in database, generate new script
        doc_text = await fetch_documentation(url_str)
        script = await generate_explanation_script(doc_text)

        # Save to database
        new_script = DocumentationScript(
            root_url=root_url, original_url=url_str, script_content=script
        )
        db.add(new_script)
        await db.commit()

        return DocumentationResponse(
            success=True,
            message="Documentation processed successfully",
            script=script,
            sections=["Introduction", "Key Concepts", "Use Cases"],
        )
    except Exception as e:
        await db.rollback()
        raise handle_error(e)


@router.get("/scripts")
async def list_scripts(db: AsyncSession = Depends(get_db)):
    """List all processed documentation scripts"""
    try:
        query = select(DocumentationScript)
        result = await db.execute(query)
        scripts = result.scalars().all()
        return {
            "success": True,
            "scripts": [
                {
                    "root_url": script.root_url,
                    "original_url": script.original_url,
                    "created_at": script.created_at,
                }
                for script in scripts
            ],
        }
    except Exception as e:
        raise handle_error(e)
