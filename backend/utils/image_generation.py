from google import genai
from google.genai import types
import base64
import os
import logging

logger = logging.getLogger(__name__)


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
        location="global",
        project=os.getenv("GEMINI_PROJECT_ID"),
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
            return part.inline_data.data

    raise ValueError("No image generated in response")


def generate_fight_condition() -> str:
    """
    Generate a fight condition for the battle using LLM.

    Returns:
        str: A fight condition for the battle
    """
    from utils.llm_service import call_llm

    system_instruction = "You are a creative writer for a mobile fighting game. Generate a single, exciting battle arena/condition description in one sentence. Make it vivid and suitable for a fighting game."

    prompt = "Create an exciting battle arena or fighting condition for two AI-generated characters to fight in."

    condition = call_llm(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.9,  # High creativity
        max_tokens=100,
    )

    return condition.strip()


def generate_confrontation_image(
    character1_image: bytes, character2_image: bytes, battle_condition: str
) -> bytes:
    """
    Generate a confrontation image using Gemini 2.5 with actual character images as input.

    Args:
        character1_image: Binary data of the first character image
        character2_image: Binary data of the second character image
        battle_condition: The battle environment/condition

    Returns:
        bytes: The generated confrontation image as binary data
    """
    client = genai.Client(
        vertexai=True,
        location="global",
        project=os.getenv("GEMINI_PROJECT_ID"),
    )

    # Create a detailed prompt for the confrontation scene
    confrontation_prompt = f"""Create an epic confrontation scene showing these two fighting game characters facing each other in battle stance, ready to fight.

Take the character from the first image and place them on the left side, and the character from the second image on the right side. They should be facing each other in dynamic fighting poses, with tension and energy between them.

Battle Environment: {battle_condition}

The image should show both characters positioned as if about to engage in combat, with the battle environment visible in the background. Maintain the cartoon/anime style suitable for a mobile fighting game, with vibrant colors and dramatic lighting that emphasizes the confrontation. Keep the visual style and characteristics of both characters consistent with their original appearance."""

    si_text = """You will receive two character images and should generate a single confrontation scene showing both characters facing each other in an epic battle stance. Use the exact visual appearance of the characters from the provided images, maintaining their style and characteristics while creating a dynamic confrontation scene suitable for a mobile fighting game."""

    model = "gemini-2.5-flash-image-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=confrontation_prompt),
                types.Part.from_bytes(data=character1_image, mime_type="image/png"),
                types.Part.from_bytes(data=character2_image, mime_type="image/png"),
            ],
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,  # Lower temperature for more consistent character representation
        top_p=0.95,
        max_output_tokens=32768,
        response_modalities=["IMAGE", "TEXT"],
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
        system_instruction=[types.Part.from_text(text=si_text)],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    # Extract image data from response
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = part.inline_data.data

            # Save locally for verification
            import datetime
            import io
            from PIL import Image

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"confrontation_{timestamp}.png"
            local_path = os.path.join("data", "confrontations", local_filename)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Save the image locally
            img = Image.open(io.BytesIO(image_data))
            img.save(local_path)
            logger.info(
                f"AI-generated confrontation image saved locally at: {local_path}"
            )
            logger.info(
                f"Generated AI confrontation image size: {len(image_data)} bytes"
            )

            return image_data

    raise ValueError("No confrontation image generated in response")
