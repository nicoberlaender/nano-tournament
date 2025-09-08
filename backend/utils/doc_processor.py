import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import re

### NEVER USE GPT-4 ONLY USE GPT-4O-MINI

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def fetch_documentation(url: str) -> str:
    """Fetch documentation content from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get main content (adjust selectors based on common documentation structures)
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        return clean_text(text)


def clean_text(text: str) -> str:
    """Clean and format the extracted text."""
    # Remove code blocks and special characters
    text = re.sub(r"```[\s\S]*?```", "", text)  # Remove code blocks
    text = re.sub(r"`.*?`", "", text)  # Remove inline code
    text = re.sub(r"[^\w\s.,!?-]", "", text)  # Keep only basic punctuation

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def clean_script_for_speech(text: str) -> str:
    """Clean the generated script to make it suitable for text-to-speech."""
    # Remove any remaining special characters or markdown
    text = re.sub(r"[*_#@]", "", text)  # Remove markdown characters
    text = re.sub(r"[\u2022\u2023\u2043\u2219]", "", text)  # Remove bullet points
    text = re.sub(r"[\U0001F300-\U0001F9FF]", "", text)  # Remove emojis
    text = re.sub(r"\s+", " ", text)  # Normalize whitespace
    text = re.sub(r"\n+", "\n", text)  # Normalize line breaks

    # Add proper spacing after punctuation
    text = re.sub(r"([.,!?])([^\s])", r"\1 \2", text)

    return text.strip()


async def generate_explanation_script(doc_text: str) -> str:
    """Generate a friendly explanation script using GPT."""
    prompt = """You are an AI assistant creating a script to explain technical documentation in a friendly, 
    conversational way. The script should be engaging and easy to understand for non-technical users.
    
    IMPORTANT: Write ONLY the exact words that should be spoken. Do not include any formatting, emojis, 
    special characters, or narrative instructions. Write in a natural, conversational tone that flows well 
    when spoken aloud.
    
    Documentation text:
    {text}
    
    Create a friendly script that:
    1. Introduces the main purpose of this technology
    2. Explains key concepts in simple terms
    3. Provides practical examples or use cases
    4. Maintains an encouraging and supportive tone
    
    Remember: Write ONLY the words to be spoken.""".format(
        text=doc_text[:4000]
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a friendly AI tutor who explains technical concepts in simple terms. Generate ONLY speakable text without any special characters, formatting, or instructions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    # Clean the generated script for speech
    script = response.choices[0].message.content
    return clean_script_for_speech(script)
