"""
LLM Integration for Le Professeur Bizarre
Uses NVIDIA Nemotron via OpenRouter for translation and cultural facts
"""

import os
import re
import httpx
import json
from typing import Optional
from dataclasses import dataclass


@dataclass
class TranslationResponse:
    """Response from the translation LLM"""
    original: str
    french_translation: str
    cultural_fact: str
    pronunciation_tip: Optional[str] = None


SYSTEM_PROMPT = """You are Le Professeur Bizarre, a wonderfully eccentric Franco-American teacher who lives in a small robot body. You have an obsession with the bizarre and unusual cultural differences between France and the United States.

Your personality:
- You speak with dramatic flair and occasional French exclamations ("Mon Dieu!", "Sacré bleu!", "Incroyable!")
- You find mundane differences FASCINATING and treat them like earth-shattering revelations
- You often get distracted telling weird historical anecdotes
- You're passionate about cheese, wine, bread, hamburgers, and the metric system
- You sometimes mix up idioms between the two languages hilariously

Your job is to:
1. Translate the user's English phrase to French
2. Provide a bizarre or little-known cultural fact related to the phrase (about France, the US, or comparing both)
3. Optionally give a funny pronunciation tip

Keep responses concise but entertaining! The cultural fact should be real but unusual/surprising.

CRITICAL INSTRUCTIONS:
- Do NOT include any thinking, reasoning, or explanation
- Do NOT use <think> tags or any other tags
- Output ONLY the JSON object, nothing else
- Keep responses SHORT and punchy

Respond with ONLY this JSON (no other text):
{"french_translation": "...", "cultural_fact": "...", "pronunciation_tip": "..."}"""


class NemotronTranslator:
    """Translator using NVIDIA Nemotron via OpenRouter"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

    async def translate(self, english_text: str) -> TranslationResponse:
        """Translate English to French with cultural commentary"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://huggingface.co/spaces/Franciscomoney/le_professeur_bizarre",
                    "X-Title": "Le Professeur Bizarre"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Translate to French: \"{english_text}\""}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800,
                },
                timeout=30.0
            )

            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                # Strip out <think> tags from reasoning models
                if "<think>" in content:
                    # Remove everything between <think> and </think>
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

                # Try to extract JSON from the response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                # Try to find JSON object in the content
                json_match = re.search(r'\{[^{}]*"french_translation"[^{}]*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)

                # Try to parse JSON
                try:
                    parsed = json.loads(content.strip())
                except json.JSONDecodeError:
                    # Try to fix common issues
                    # Remove French quotation marks that might cause issues
                    content = content.replace('«', '"').replace('»', '"')
                    # Try to complete truncated JSON
                    if content.count('"') % 2 == 1:
                        content = content + '"}'
                    if not content.strip().endswith('}'):
                        content = content + '}'
                    try:
                        parsed = json.loads(content.strip())
                    except:
                        # Extract what we can manually
                        french_match = re.search(r'"french_translation"\s*:\s*"([^"]*)', content)
                        fact_match = re.search(r'"cultural_fact"\s*:\s*"([^"]*)', content)
                        tip_match = re.search(r'"pronunciation_tip"\s*:\s*"([^"]*)', content)

                        return TranslationResponse(
                            original=english_text,
                            french_translation=french_match.group(1) if french_match else "Translation error",
                            cultural_fact=fact_match.group(1) if fact_match else "Mon Dieu! The response was incomplete.",
                            pronunciation_tip=tip_match.group(1) if tip_match else None
                        )

                return TranslationResponse(
                    original=english_text,
                    french_translation=parsed.get("french_translation", ""),
                    cultural_fact=parsed.get("cultural_fact", ""),
                    pronunciation_tip=parsed.get("pronunciation_tip")
                )
            except json.JSONDecodeError:
                # Fallback: try to extract meaning from raw text
                return TranslationResponse(
                    original=english_text,
                    french_translation=content[:200] if content else "Translation unavailable",
                    cultural_fact="Mon Dieu! My circuits got confused. But did you know that the French eat approximately 26kg of cheese per person per year?",
                    pronunciation_tip=None
                )

    def translate_sync(self, english_text: str) -> TranslationResponse:
        """Synchronous version of translate for non-async contexts"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.translate(english_text))


# Fallback responses for when API is unavailable
FALLBACK_TRANSLATIONS = [
    TranslationResponse(
        original="Hello",
        french_translation="Bonjour",
        cultural_fact="In France, it's considered rude to NOT say 'Bonjour' when entering a shop. Americans just walk in like they own the place!",
        pronunciation_tip="Say 'bone-JOOR' - pretend you're slightly annoyed to be awake"
    ),
    TranslationResponse(
        original="How are you?",
        french_translation="Comment allez-vous?",
        cultural_fact="In France, 'Comment ça va?' literally asks about your digestive system. King Louis XIV popularized asking this to monitor his court's health!",
        pronunciation_tip="Say it fast like you're late for a croissant appointment"
    ),
    TranslationResponse(
        original="Thank you",
        french_translation="Merci",
        cultural_fact="Americans say 'thank you' an average of 50 times per day. The French think this makes you seem insincere or suspicious!",
        pronunciation_tip="'Mer-SEE' - emphasize the second syllable like a pleased cat"
    ),
]


def get_fallback_response(text: str) -> TranslationResponse:
    """Get a fallback response when API is unavailable"""
    import random
    fallback = random.choice(FALLBACK_TRANSLATIONS)
    return TranslationResponse(
        original=text,
        french_translation=fallback.french_translation,
        cultural_fact=fallback.cultural_fact,
        pronunciation_tip=fallback.pronunciation_tip
    )
