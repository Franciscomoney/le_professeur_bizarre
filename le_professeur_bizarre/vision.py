"""
Vision Module for Le Professeur Bizarre
Uses NVIDIA Nemotron VL for image understanding
"""

import os
import base64
import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class VisionResponse:
    """Response from vision analysis"""
    description: str
    french_word: Optional[str] = None
    pronunciation: Optional[str] = None
    cultural_note: Optional[str] = None


# NVIDIA Nemotron Vision-Language Model via OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt for vision analysis - kept very simple for Nemotron VL
VISION_SYSTEM_PROMPT = """You identify objects in images. Name the main object you see in 1-3 words. Be specific and accurate. If unclear, say 'unclear'."""


async def analyze_image(image_base64: str, prompt: str = "What do you see?") -> VisionResponse:
    """
    Analyze an image using NVIDIA Nemotron VL

    Args:
        image_base64: Base64 encoded image (JPEG or PNG)
        prompt: Optional specific question about the image

    Returns:
        VisionResponse with French teaching content
    """
    if not OPENROUTER_API_KEY:
        return VisionResponse(
            description="Vision not available - OPENROUTER_API_KEY not set",
            french_word=None,
            pronunciation=None,
            cultural_note=None
        )

    # Ensure proper base64 format
    if not image_base64.startswith("data:"):
        # Assume JPEG if no prefix
        image_base64 = f"data:image/jpeg;base64,{image_base64}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://huggingface.co/spaces/Franciscomoney/le_professeur_bizarre",
                    "X-Title": "Le Professeur Bizarre Vision"
                },
                json={
                    "model": VISION_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": VISION_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_base64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": 500,  # Increased for reasoning tokens
                    "temperature": 0.3  # Lower for more deterministic responses
                },
                timeout=30.0
            )

            response.raise_for_status()
            data = response.json()

            message = data["choices"][0]["message"]
            content = message.get("content", "").strip()

            # Debug: print raw response
            print(f"Vision API response - content: {repr(content)}")

            # Check if content is empty but reasoning exists
            if not content and message.get("reasoning"):
                reasoning = message.get("reasoning", "")
                print(f"Content empty, checking reasoning: {reasoning[:300]}...")
                # Try to extract the object from reasoning
                # Look for patterns like "it's a", "this is a", "I see a", etc.
                import re
                patterns = [
                    r"it's\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\.|,|$)",
                    r"this\s+is\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\.|,|$)",
                    r"I\s+see\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\.|,|$)",
                    r"shows?\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\.|,|$)",
                ]
                for pattern in patterns:
                    match = re.search(pattern, reasoning, re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        print(f"Extracted from reasoning: {content}")
                        break

            # Clean up the content
            content = content.strip().lower()

            # Check for unclear responses
            if not content or content == "unclear" or "cannot" in content or "can't" in content:
                return VisionResponse(
                    description="unclear",
                    french_word=None,
                    pronunciation=None,
                    cultural_note=None
                )

            # Return the identified object - let main model handle French
            print(f"Vision identified: {content}")
            return VisionResponse(
                description=content,
                french_word=None,  # Main model will provide French
                pronunciation=None,
                cultural_note=None
            )

    except Exception as e:
        print(f"Vision error: {e}")
        return VisionResponse(
            description=f"Could not analyze image: {str(e)}",
            french_word=None,
            pronunciation=None,
            cultural_note=None
        )


async def describe_for_teaching(image_base64: str) -> str:
    """
    Get a teaching-ready description of an image
    Returns a string that the main AI model can use to teach French
    """
    result = await analyze_image(
        image_base64,
        "Name the main object in this image in 1-3 words."
    )

    obj = result.description.lower().strip() if result.description else "unclear"

    # Return structured info for the main AI model to use
    if obj and obj != "unclear" and "cannot" not in obj:
        # Vision model identified the object - tell the main model what we see
        return f"VISION RESULT: I see '{result.description}'. Now teach the user the French word for '{result.description}', the pronunciation, and a fun fact."
    else:
        return "VISION RESULT: The image is unclear or too dark. Ask the user to hold the object closer and make sure there is good lighting."


async def translate_text_in_image(image_base64: str) -> str:
    """
    Detect and translate any text visible in an image
    """
    result = await analyze_image(
        image_base64,
        "Is there any text in this image? If so, tell me what it says and translate it to French."
    )

    return result.description


# Quick test
if __name__ == "__main__":
    import asyncio

    async def test():
        # Test with a simple prompt (no image)
        print("Vision module loaded successfully")
        print(f"Model: {VISION_MODEL}")
        print(f"API Key set: {bool(OPENROUTER_API_KEY)}")

    asyncio.run(test())
