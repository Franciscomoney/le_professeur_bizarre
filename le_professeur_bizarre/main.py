"""
Le Professeur Bizarre - Main Reachy Mini App

A quirky Franco-American cultural teacher that translates English to French
with bizarre cultural facts. Powered by NVIDIA Nemotron via OpenRouter.
"""

import os
import time
import threading
import logging
import asyncio
from pathlib import Path
from typing import Optional
import numpy as np

from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.utils import create_head_pose

from .llm import NemotronTranslator, TranslationResponse, get_fallback_response


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeProfesseurBizarre(ReachyMiniApp):
    """
    Le Professeur Bizarre - A quirky Franco-American cultural teacher

    This Reachy Mini app translates English phrases to French while teaching
    bizarre cultural facts about France and the United States.

    Features:
    - Real-time translation using NVIDIA Nemotron via OpenRouter
    - Animated head movements while speaking
    - Expressive antenna movements for emphasis
    - Web interface for text input
    """

    # URL for the custom web interface
    custom_app_url: str | None = "http://localhost:5173"

    def __init__(self):
        super().__init__()
        self._current_text: Optional[str] = None
        self._response: Optional[TranslationResponse] = None
        self._is_speaking = False
        self._translator: Optional[NemotronTranslator] = None

        # Try to initialize translator
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                self._translator = NemotronTranslator(api_key)
                logger.info("Nemotron translator initialized successfully")
            else:
                logger.warning("No OPENROUTER_API_KEY found - using fallback responses")
        except Exception as e:
            logger.warning(f"Could not initialize translator: {e}")

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        """
        Main app loop - runs in a background thread.

        The robot performs idle animations while waiting for input,
        and animated speaking motions when translating.
        """
        logger.info("Le Professeur Bizarre is ready to teach!")

        t0 = time.time()
        idle_animation_speed = 0.3  # Hz for gentle idle motion

        while not stop_event.is_set():
            t = time.time() - t0

            if self._is_speaking and self._response:
                # Animated speaking mode - more energetic movements
                self._do_speaking_animation(reachy_mini, t)
            else:
                # Idle animation - gentle swaying
                self._do_idle_animation(reachy_mini, t, idle_animation_speed)

            time.sleep(0.02)  # 50Hz update rate

        # Reset to neutral position on stop
        self._reset_to_neutral(reachy_mini)
        logger.info("Le Professeur Bizarre is taking a break. Au revoir!")

    def _do_idle_animation(self, reachy_mini: ReachyMini, t: float, speed: float):
        """Gentle idle animation - curious head movements"""
        # Slow, curious head movements
        yaw = 10 * np.sin(2 * np.pi * speed * t)
        pitch = 5 * np.sin(2 * np.pi * speed * 0.7 * t)
        roll = 3 * np.sin(2 * np.pi * speed * 0.5 * t + 1.0)

        head_pose = create_head_pose(yaw=yaw, pitch=pitch, roll=roll, degrees=True)

        # Gentle antenna wiggle
        antenna_offset = 0.1 * np.sin(2 * np.pi * speed * 2 * t)
        antennas = [antenna_offset, -antenna_offset]

        reachy_mini.set_target(head=head_pose, antennas=antennas)

    def _do_speaking_animation(self, reachy_mini: ReachyMini, t: float):
        """Energetic speaking animation - emphatic movements"""
        # More dynamic head movements while "speaking"
        base_speed = 1.5  # Faster when speaking

        # Main speaking motion - nodding with emphasis
        yaw = 15 * np.sin(2 * np.pi * base_speed * t)
        pitch = 8 * np.sin(2 * np.pi * base_speed * 1.3 * t)
        roll = 5 * np.sin(2 * np.pi * base_speed * 0.8 * t)

        # Add occasional "emphasis" - larger movements
        emphasis = 0.3 * np.sin(2 * np.pi * 0.2 * t)
        if emphasis > 0.2:
            pitch += 10
            yaw *= 1.5

        head_pose = create_head_pose(yaw=yaw, pitch=pitch, roll=roll, degrees=True)

        # Expressive antenna movements - like gesturing
        antenna_speed = 2.0
        left_antenna = 0.4 * np.sin(2 * np.pi * antenna_speed * t)
        right_antenna = 0.4 * np.sin(2 * np.pi * antenna_speed * t + np.pi / 3)
        antennas = [left_antenna, right_antenna]

        reachy_mini.set_target(head=head_pose, antennas=antennas)

    def _reset_to_neutral(self, reachy_mini: ReachyMini):
        """Return to neutral rest position"""
        head_pose = create_head_pose(yaw=0, pitch=0, roll=0, degrees=True)
        reachy_mini.goto_target(head=head_pose, antennas=[0, 0], duration=1.0)

    def translate(self, english_text: str) -> TranslationResponse:
        """
        Translate English text to French with cultural commentary.

        This method can be called from the web interface.
        """
        logger.info(f"Translating: {english_text}")

        self._current_text = english_text
        self._is_speaking = True

        try:
            if self._translator:
                # Use async translator
                self._response = self._translator.translate_sync(english_text)
            else:
                # Use fallback
                self._response = get_fallback_response(english_text)

            logger.info(f"Translation: {self._response.french_translation}")
            logger.info(f"Cultural fact: {self._response.cultural_fact}")

            # Simulate speaking duration based on response length
            speak_duration = max(3.0, len(self._response.french_translation) * 0.05)
            time.sleep(speak_duration)

        except Exception as e:
            logger.error(f"Translation error: {e}")
            self._response = get_fallback_response(english_text)

        finally:
            self._is_speaking = False

        return self._response

    def get_current_response(self) -> Optional[TranslationResponse]:
        """Get the most recent translation response"""
        return self._response

    def is_speaking(self) -> bool:
        """Check if the professor is currently speaking"""
        return self._is_speaking


# Entry point for direct testing
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    # Test the translator directly
    print("Testing Le Professeur Bizarre translator...")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        translator = NemotronTranslator(api_key)
        test_phrases = [
            "Hello, how are you?",
            "I love cheese",
            "Where is the bathroom?",
            "This coffee is delicious"
        ]

        for phrase in test_phrases:
            print(f"\n--- Translating: '{phrase}' ---")
            try:
                response = translator.translate_sync(phrase)
                print(f"French: {response.french_translation}")
                print(f"Fact: {response.cultural_fact}")
                if response.pronunciation_tip:
                    print(f"Tip: {response.pronunciation_tip}")
            except Exception as e:
                print(f"Error: {e}")
    else:
        print("No API key found. Using fallback responses...")
        for _ in range(3):
            response = get_fallback_response("test")
            print(f"\nFrench: {response.french_translation}")
            print(f"Fact: {response.cultural_fact}")
