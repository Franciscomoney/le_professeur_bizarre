#!/usr/bin/env python3
"""
Test script for Le Professeur Bizarre

This script tests the translation functionality without requiring
the Reachy Mini hardware or daemon.
"""

import os
import sys
import asyncio

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from le_professeur_bizarre.llm import NemotronTranslator, get_fallback_response


async def test_translation():
    """Test the translation with real API"""
    print("=" * 60)
    print("Le Professeur Bizarre - Translation Test")
    print("=" * 60)

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("\n⚠️  No OPENROUTER_API_KEY found in environment")
        print("   Testing with fallback responses...\n")

        test_phrases = ["Hello", "I love cheese", "Where is the bathroom?"]
        for phrase in test_phrases:
            response = get_fallback_response(phrase)
            print(f"📝 Input: {phrase}")
            print(f"🇫🇷 French: {response.french_translation}")
            print(f"💡 Fact: {response.cultural_fact}")
            if response.pronunciation_tip:
                print(f"🎤 Tip: {response.pronunciation_tip}")
            print("-" * 40)
        return

    print(f"\n✓ API key found")
    print(f"  Model: {os.getenv('NEMOTRON_MODEL', 'nvidia/nemotron-3-nano-30b-a3b')}")
    print()

    translator = NemotronTranslator(api_key)

    test_phrases = [
        "Hello, how are you?",
        "I love cheese",
        "Where is the bathroom?",
        "This coffee is delicious",
        "Can I have the check please?"
    ]

    for phrase in test_phrases:
        print(f"📝 Translating: \"{phrase}\"")
        try:
            response = await translator.translate(phrase)
            print(f"🇫🇷 French: {response.french_translation}")
            print(f"💡 Fact: {response.cultural_fact}")
            if response.pronunciation_tip:
                print(f"🎤 Tip: {response.pronunciation_tip}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 40)

    print("\n✅ Test complete!")


async def test_server():
    """Test the FastAPI server"""
    import httpx

    print("\n" + "=" * 60)
    print("Testing API Server")
    print("=" * 60)

    base_url = "http://localhost:5173"

    async with httpx.AsyncClient() as client:
        try:
            # Test status endpoint
            response = await client.get(f"{base_url}/api/apps/le_professeur_bizarre/status")
            print(f"\n✓ Status endpoint: {response.json()}")

            # Test translation endpoint
            response = await client.post(
                f"{base_url}/api/apps/le_professeur_bizarre/translate",
                json={"text": "Hello world"}
            )
            print(f"✓ Translation endpoint: {response.json()}")

        except httpx.ConnectError:
            print(f"\n⚠️  Server not running at {base_url}")
            print("   Start it with: python -m le_professeur_bizarre.server")


if __name__ == "__main__":
    print("\n🇫🇷 Le Professeur Bizarre Test Suite 🇺🇸\n")

    # Run translation test
    asyncio.run(test_translation())

    # Optionally test server
    if "--server" in sys.argv:
        asyncio.run(test_server())
