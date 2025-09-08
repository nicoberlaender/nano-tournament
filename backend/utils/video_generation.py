import time
import os
import io
import logging
from typing import Optional
from google import genai
from google.genai.types import GenerateVideosConfig
from google.genai.types import Image

logger = logging.getLogger(__name__)


def generate_battle_video(
    confrontation_image: bytes,
    battle_script: str,
    output_gcs_uri: str = "gs://battle_videos",
) -> str:
    """
    Generate a battle video using a confrontation image and battle script.

    Args:
        confrontation_image: Binary data of the confrontation image showing both characters
        battle_script: The detailed battle script from the LLM judge
        output_gcs_uri: GCS bucket URI for storing the generated video

    Returns:
        str: URL to the generated video

    Raises:
        Exception: If video generation fails
    """
    from google.genai import types

    client = genai.Client()

    # Validate confrontation image data
    if not confrontation_image:
        raise ValueError("Confrontation image data is empty")

    logger.info(
        f"Starting video generation with confrontation image size: {len(confrontation_image)} bytes"
    )
    logger.info(f"Battle script: {battle_script[:100]}...")

    operation = client.models.generate_videos(
        model="veo-3.0-fast-generate-001",
        prompt=battle_script,
        image=Image(
            image_bytes=confrontation_image, mime_type="image/png"
        ),  # Pass the confrontation image as starting frame
        config=GenerateVideosConfig(
            aspect_ratio="9:16",  # Mobile-friendly vertical format
            output_gcs_uri=output_gcs_uri,
            duration_seconds=6,
            generate_audio=True,
        ),
    )

    # Poll for completion
    while not operation.done:
        logger.info("Video generation in progress...")
        time.sleep(15)
        operation = client.operations.get(operation)

    if operation.response:
        gcs_uri = operation.result.generated_videos[0].video.uri
        logger.info(f"Video generation completed with GCS URI: {gcs_uri}")

        # Convert GCS URI to public HTTPS URL
        # Format: gs://bucket/path -> https://storage.googleapis.com/bucket/path
        if gcs_uri.startswith("gs://"):
            bucket_and_path = gcs_uri[5:]  # Remove "gs://" prefix
            public_url = f"https://storage.googleapis.com/{bucket_and_path}"
            logger.info(f"Converted to public URL: {public_url}")
            return public_url
        else:
            # If it's already a public URL, return as is
            return gcs_uri
    else:
        logger.error("Video generation failed - no response")
        raise Exception("Video generation failed - no response")
