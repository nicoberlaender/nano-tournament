from google import genai
from google.genai import types
import logging
from typing import Optional
import os
logger = logging.getLogger(__name__)


def call_llm(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    model: str = "gemini-2.0-flash-exp",
) -> str:
    """
    General utility function for making LLM calls with text responses.

    Args:
        prompt: The user prompt/question to send to the LLM
        system_instruction: Optional system instruction to guide the LLM behavior
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum number of tokens in the response
        model: The Gemini model to use

    Returns:
        str: The LLM's text response
    """
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GEMINI_PROJECT_ID"),
        location="global",
    )

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

    config_params = {
        "temperature": temperature,
        "top_p": 0.95,
        "max_output_tokens": max_tokens,
        "response_modalities": ["TEXT"],
        "safety_settings": [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    }

    # Add system instruction if provided
    if system_instruction:
        config_params["system_instruction"] = [
            types.Part.from_text(text=system_instruction)
        ]

    generate_content_config = types.GenerateContentConfig(**config_params)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    # Extract text from response - fail fast if not found
    return response.candidates[0].content.parts[0].text.strip()


def judge_battle(
    player1_character_prompt: str,
    player2_character_prompt: str,
    battle_condition: str,
    player1_id: str = "Player 1",
    player2_id: str = "Player 2",
) -> dict:
    """
    Use LLM to judge who wins a battle between two characters and generate a battle script.

    Args:
        player1_character_prompt: Description of player 1's character
        player2_character_prompt: Description of player 2's character
        battle_condition: The battle environment/condition
        player1_id: ID of player 1 (for response formatting)
        player2_id: ID of player 2 (for response formatting)

    Returns:
        dict: Contains winner_id, battle_script, and battle_summary
    """
    system_instruction = """You are a battle choreographer for a mobile fighting game. Your job is to determine who wins between two AI-generated characters and create a detailed battle script suitable for video generation.

Rules:
1. Consider the character descriptions and how they might perform in the given battle condition
2. Be creative but fair in your judgment
3. Create a detailed battle script with specific actions, movements, and moments
4. The script should be visual and suitable for video generation
5. Your response must be in this exact JSON format:
{
    "winner": "player1" or "player2",
    "battle_script": "Detailed step-by-step script of how the battle unfolds, including specific actions, movements, attacks, and reactions. Write it as a series of visual scenes suitable for video generation. Keep it concise but vivid - aim for 3-5 key scenes.",
    "battle_summary": "Brief one-sentence summary of the battle outcome"
}

Make the battle script visual, dynamic, and exciting. Focus on specific actions that can be animated. Do NOT use markdown formatting - write in plain text only."""

    prompt = f"""Battle Condition: {battle_condition}

Player 1 Character: {player1_character_prompt}
Player 2 Character: {player2_character_prompt}

Who wins this battle and why?"""

    response_text = call_llm(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.8,
        max_tokens=1024,
    )

    # Parse JSON response
    import json

    # Remove markdown code blocks if present
    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()

    result = json.loads(clean_text)

    # Convert winner to actual player ID
    winner_id = player1_id if result["winner"] == "player1" else player2_id

    return {
        "winner_id": winner_id,
        "battle_script": result["battle_script"],
        "battle_summary": result["battle_summary"],
    }
