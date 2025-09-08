from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./backend/data/ai_documentation.db"
)

# Ensure the data directory exists
os.makedirs(
    os.path.dirname(DATABASE_URL.replace("sqlite+aiosqlite:///", "")), exist_ok=True
)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class DocumentationScript(Base):
    __tablename__ = "documentation_scripts"

    id = Column(Integer, primary_key=True)
    root_url = Column(
        String, unique=True, index=True
    )  # Main domain name (e.g., "langchain")
    original_url = Column(String)  # Full URL that was processed
    script_content = Column(Text)  # Generated explanation script
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_root_url(url: str) -> str:
        """Extract main domain name from URL.
        Example: https://python.langchain.com/docs/introduction/ -> langchain
        """
        parsed = urlparse(url)
        # Split the netloc by dots and get the main domain name
        parts = parsed.netloc.split(".")
        # Handle cases like api.example.com, docs.example.com, etc.
        if len(parts) >= 2:
            # Get the main domain name (usually the second-to-last part)
            return parts[-2]
        return parts[0]  # Fallback to the first part if only one exists


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting async database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
