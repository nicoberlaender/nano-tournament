from google import genai
from google.genai import types
import base64


def generate_character_image(description: str) -> bytes:
    """
    Generate a character image based on the description.

    Args:
        description: Text description of the character

    Returns:
        bytes: The generated image as binary data
    """
    client = genai.Client(
        vertexai=True,
        project="tum-cdtm25mun-8766",
        location="global",
    )

    si_text1 = """You will receive a description from the user of a character and should respond with an image in cartoon style suitable for a fighting game character."""

    model = "gemini-2.5-flash-image-preview"
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=description)])
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=32768,
        response_modalities=["TEXT", "IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        system_instruction=[types.Part.from_text(text=si_text1)],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    # Extract image data from response
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            # Decode base64 image data
            return base64.b64decode(part.inline_data.data)

    raise ValueError("No image generated in response")


def generate_fight_condition() -> str:
    """
    Generate a fight condition for the battle (MVP version with predefined conditions).

    Returns:
        str: A fight condition for the battle
    """
    import random

    conditions = [
        "Battle in a mystical forest arena",
        "Fight on a floating platform in the clouds",
        "Duel in an ancient temple",
        "Combat in a futuristic cyber arena",
        "Battle in a volcanic crater",
        "Fight in an underwater dome",
        "Duel in a frozen wasteland",
        "Combat in a neon-lit city rooftop",
    ]

    return random.choice(conditions)
