"""
Reachy Mini Behaviors for Le Professeur Bizarre
Rich animations: breathing, emotions, dances, speech reactions
"""

import asyncio
import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Awaitable

import httpx


class Emotion(Enum):
    HAPPY = "happy"
    SAD = "sad"
    SURPRISED = "surprised"
    THINKING = "thinking"
    EXCITED = "excited"
    CONFUSED = "confused"
    PROUD = "proud"
    DISAPPOINTED = "disappointed"


class Dance(Enum):
    FRENCH_WALTZ = "french_waltz"
    CELEBRATION = "celebration"
    THINKING_GROOVE = "thinking_groove"
    BONJOUR_BOB = "bonjour_bob"


@dataclass
class MotionState:
    """Current state of the motion system"""
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    antenna_left: float = 0.0
    antenna_right: float = 0.0
    breathing_active: bool = True
    speaking: bool = False
    tracking_face: bool = False
    current_emotion: Optional[Emotion] = None
    current_dance: Optional[Dance] = None


class ReachyBehaviors:
    """
    Layered motion system for Reachy Mini

    Layers (from bottom to top):
    1. Breathing - subtle idle animation
    2. Face tracking - follows detected face
    3. Primary motion - emotions, dances, goto poses
    4. Speech wobble - reactive movement while speaking
    """

    def __init__(self, daemon_url: str = "http://localhost:8000"):
        self.daemon_url = daemon_url
        self.state = MotionState()
        self._breathing_task: Optional[asyncio.Task] = None
        self._speech_wobble_task: Optional[asyncio.Task] = None
        self._dance_task: Optional[asyncio.Task] = None
        self._emotion_task: Optional[asyncio.Task] = None
        self._tracking_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the behavior system"""
        self._running = True
        self.state.breathing_active = True
        self._breathing_task = asyncio.create_task(self._breathing_loop())
        print("Behavior system started")

    async def stop(self):
        """Stop all behaviors"""
        self._running = False
        self.state.breathing_active = False

        for task in [self._breathing_task, self._speech_wobble_task,
                     self._dance_task, self._emotion_task, self._tracking_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        print("Behavior system stopped")

    async def _move_head(self, yaw: float, pitch: float, roll: float, duration: float = 0.3):
        """Move head to position"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.daemon_url}/api/move/goto",
                    json={
                        "head_pose": {
                            "yaw": math.radians(yaw),
                            "pitch": math.radians(pitch),
                            "roll": math.radians(roll),
                            "x": 0, "y": 0, "z": 0
                        },
                        "duration": duration,
                        "interpolation_mode": "minjerk"
                    },
                    timeout=5.0
                )
                self.state.yaw = yaw
                self.state.pitch = pitch
                self.state.roll = roll
            except Exception as e:
                pass  # Silent fail for smooth animation

    async def _move_antennas(self, left: float, right: float, duration: float = 0.2):
        """Move antennas"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.daemon_url}/api/move/goto",
                    json={
                        "antennas": [left, right],
                        "duration": duration,
                        "interpolation_mode": "minjerk"
                    },
                    timeout=5.0
                )
                self.state.antenna_left = left
                self.state.antenna_right = right
            except Exception:
                pass

    # ==================== BREATHING ====================

    async def _breathing_loop(self):
        """Subtle breathing animation - always running when idle"""
        t = 0
        while self._running and self.state.breathing_active:
            if not self.state.speaking and not self.state.current_dance:
                # Gentle sine wave breathing
                breath = math.sin(t * 0.5) * 3  # ±3 degrees
                antenna_breath = math.sin(t * 0.7) * 0.1  # Subtle antenna movement

                base_pitch = self.state.pitch if self.state.tracking_face else 0
                base_yaw = self.state.yaw if self.state.tracking_face else 0

                await self._move_head(
                    yaw=base_yaw + math.sin(t * 0.3) * 2,
                    pitch=base_pitch + breath,
                    roll=math.sin(t * 0.4) * 1.5,
                    duration=0.3
                )
                await self._move_antennas(
                    antenna_breath,
                    -antenna_breath,
                    duration=0.2
                )

            t += 0.3
            await asyncio.sleep(0.3)

    # ==================== SPEECH REACTIONS ====================

    async def start_speaking(self):
        """Called when Reachy starts speaking"""
        self.state.speaking = True
        self._speech_wobble_task = asyncio.create_task(self._speech_wobble_loop())

    async def stop_speaking(self):
        """Called when Reachy stops speaking"""
        self.state.speaking = False
        if self._speech_wobble_task:
            self._speech_wobble_task.cancel()
            try:
                await self._speech_wobble_task
            except asyncio.CancelledError:
                pass
        # Return to neutral
        await self._move_head(0, 0, 0, duration=0.4)
        await self._move_antennas(0, 0, duration=0.3)

    async def _speech_wobble_loop(self):
        """Expressive movement while speaking"""
        t = 0
        while self.state.speaking:
            # More energetic movement while talking
            wobble_yaw = math.sin(t * 2.5) * 12 + random.uniform(-3, 3)
            wobble_pitch = math.sin(t * 1.8) * 8 + random.uniform(-2, 2)
            wobble_roll = math.sin(t * 2.1) * 6

            # Expressive antenna gestures
            ant_left = math.sin(t * 3) * 0.5 + random.uniform(-0.1, 0.1)
            ant_right = math.sin(t * 3 + 1) * 0.5 + random.uniform(-0.1, 0.1)

            await self._move_head(wobble_yaw, wobble_pitch, wobble_roll, duration=0.15)
            await self._move_antennas(ant_left, ant_right, duration=0.1)

            t += 0.15
            await asyncio.sleep(0.12)

    # ==================== EMOTIONS ====================

    async def play_emotion(self, emotion: Emotion, duration: float = 2.0):
        """Play an emotional expression"""
        self.state.current_emotion = emotion

        if self._emotion_task:
            self._emotion_task.cancel()

        self._emotion_task = asyncio.create_task(
            self._emotion_animation(emotion, duration)
        )

    async def _emotion_animation(self, emotion: Emotion, duration: float):
        """Animate an emotion"""
        try:
            if emotion == Emotion.HAPPY:
                await self._happy_animation()
            elif emotion == Emotion.SAD:
                await self._sad_animation()
            elif emotion == Emotion.SURPRISED:
                await self._surprised_animation()
            elif emotion == Emotion.THINKING:
                await self._thinking_animation()
            elif emotion == Emotion.EXCITED:
                await self._excited_animation()
            elif emotion == Emotion.CONFUSED:
                await self._confused_animation()
            elif emotion == Emotion.PROUD:
                await self._proud_animation()

            await asyncio.sleep(duration)
        finally:
            self.state.current_emotion = None
            await self._move_head(0, 0, 0, duration=0.3)
            await self._move_antennas(0, 0, duration=0.2)

    async def _happy_animation(self):
        """Happy/joyful expression"""
        for _ in range(3):
            await self._move_head(0, -15, 0, duration=0.15)
            await self._move_antennas(0.7, 0.7, duration=0.1)
            await asyncio.sleep(0.1)
            await self._move_head(0, 5, 0, duration=0.15)
            await self._move_antennas(0.3, 0.3, duration=0.1)
            await asyncio.sleep(0.1)

    async def _sad_animation(self):
        """Sad/disappointed expression"""
        await self._move_head(0, 20, 0, duration=0.5)
        await self._move_antennas(-0.5, -0.5, duration=0.4)
        await asyncio.sleep(0.5)
        # Slight droop
        await self._move_head(5, 25, -3, duration=0.3)

    async def _surprised_animation(self):
        """Surprised expression"""
        # Quick jerk back
        await self._move_head(0, -20, 0, duration=0.1)
        await self._move_antennas(0.8, 0.8, duration=0.08)
        await asyncio.sleep(0.2)
        # Hold surprised pose
        await self._move_head(0, -10, 0, duration=0.2)

    async def _thinking_animation(self):
        """Thinking/pondering expression"""
        await self._move_head(20, 15, 8, duration=0.4)
        await self._move_antennas(0.4, -0.2, duration=0.3)
        await asyncio.sleep(0.3)
        # Slight head tilt variations
        for _ in range(3):
            await self._move_head(15 + random.uniform(-5, 5), 12, 10, duration=0.3)
            await asyncio.sleep(0.4)

    async def _excited_animation(self):
        """Excited/enthusiastic expression"""
        for _ in range(4):
            await self._move_head(random.uniform(-15, 15), -12, random.uniform(-8, 8), duration=0.12)
            await self._move_antennas(0.8, 0.8, duration=0.08)
            await asyncio.sleep(0.08)
            await self._move_antennas(-0.3, -0.3, duration=0.08)
            await asyncio.sleep(0.08)

    async def _confused_animation(self):
        """Confused expression"""
        await self._move_head(-15, 5, -12, duration=0.3)
        await self._move_antennas(0.5, -0.3, duration=0.25)
        await asyncio.sleep(0.3)
        await self._move_head(15, 8, 12, duration=0.3)
        await self._move_antennas(-0.3, 0.5, duration=0.25)

    async def _proud_animation(self):
        """Proud/satisfied expression"""
        await self._move_head(0, -8, 0, duration=0.3)
        await self._move_antennas(0.5, 0.5, duration=0.25)
        await asyncio.sleep(0.2)
        # Slight confident head movement
        await self._move_head(8, -5, 3, duration=0.25)

    # ==================== DANCES ====================

    async def start_dance(self, dance: Dance):
        """Start a dance sequence"""
        if self._dance_task:
            await self.stop_dance()

        self.state.current_dance = dance
        self._dance_task = asyncio.create_task(self._dance_loop(dance))

    async def stop_dance(self):
        """Stop current dance"""
        self.state.current_dance = None
        if self._dance_task:
            self._dance_task.cancel()
            try:
                await self._dance_task
            except asyncio.CancelledError:
                pass
        await self._move_head(0, 0, 0, duration=0.3)
        await self._move_antennas(0, 0, duration=0.2)

    async def _dance_loop(self, dance: Dance):
        """Execute a dance sequence"""
        try:
            while self.state.current_dance == dance:
                if dance == Dance.FRENCH_WALTZ:
                    await self._french_waltz_step()
                elif dance == Dance.CELEBRATION:
                    await self._celebration_step()
                elif dance == Dance.THINKING_GROOVE:
                    await self._thinking_groove_step()
                elif dance == Dance.BONJOUR_BOB:
                    await self._bonjour_bob_step()
        except asyncio.CancelledError:
            pass

    async def _french_waltz_step(self):
        """Elegant French waltz movement"""
        # 1-2-3, 1-2-3 waltz pattern
        moves = [
            (15, -5, 10),
            (0, 0, 5),
            (-15, 5, -5),
            (0, 5, -10),
            (10, -8, 8),
            (-10, 0, -8),
        ]
        for yaw, pitch, roll in moves:
            await self._move_head(yaw, pitch, roll, duration=0.35)
            await self._move_antennas(
                0.3 if yaw > 0 else -0.3,
                -0.3 if yaw > 0 else 0.3,
                duration=0.25
            )
            await asyncio.sleep(0.3)

    async def _celebration_step(self):
        """Energetic celebration dance"""
        for _ in range(2):
            # Jump up
            await self._move_head(0, -20, 0, duration=0.1)
            await self._move_antennas(0.8, 0.8, duration=0.08)
            await asyncio.sleep(0.1)
            # Down
            await self._move_head(0, 10, 0, duration=0.1)
            await self._move_antennas(-0.3, -0.3, duration=0.08)
            await asyncio.sleep(0.1)
        # Side to side
        await self._move_head(25, -5, 15, duration=0.15)
        await self._move_antennas(0.6, -0.4, duration=0.1)
        await asyncio.sleep(0.15)
        await self._move_head(-25, -5, -15, duration=0.15)
        await self._move_antennas(-0.4, 0.6, duration=0.1)
        await asyncio.sleep(0.15)

    async def _thinking_groove_step(self):
        """Subtle thinking groove"""
        t = random.uniform(0, 6.28)
        for _ in range(4):
            await self._move_head(
                math.sin(t) * 10,
                10 + math.sin(t * 0.5) * 5,
                math.cos(t) * 8,
                duration=0.4
            )
            await self._move_antennas(
                math.sin(t) * 0.3,
                math.cos(t) * 0.3,
                duration=0.3
            )
            t += 0.8
            await asyncio.sleep(0.35)

    async def _bonjour_bob_step(self):
        """Friendly bonjour bobbing"""
        # Nod forward
        await self._move_head(0, 15, 0, duration=0.2)
        await self._move_antennas(0.4, 0.4, duration=0.15)
        await asyncio.sleep(0.15)
        # Back up
        await self._move_head(0, -5, 0, duration=0.2)
        await self._move_antennas(0.1, 0.1, duration=0.15)
        await asyncio.sleep(0.15)
        # Slight side tilt
        await self._move_head(10, 5, 8, duration=0.25)
        await self._move_antennas(0.3, -0.2, duration=0.2)
        await asyncio.sleep(0.2)
        await self._move_head(-10, 5, -8, duration=0.25)
        await self._move_antennas(-0.2, 0.3, duration=0.2)
        await asyncio.sleep(0.2)

    # ==================== FACE TRACKING ====================

    async def enable_face_tracking(self, get_face_position: Callable[[], Awaitable[Optional[tuple]]]):
        """
        Enable face tracking
        get_face_position should return (x, y) normalized -1 to 1, or None if no face
        """
        self.state.tracking_face = True
        self._tracking_task = asyncio.create_task(
            self._face_tracking_loop(get_face_position)
        )

    async def disable_face_tracking(self):
        """Disable face tracking"""
        self.state.tracking_face = False
        if self._tracking_task:
            self._tracking_task.cancel()
            try:
                await self._tracking_task
            except asyncio.CancelledError:
                pass

    async def _face_tracking_loop(self, get_face_position):
        """Follow face position"""
        while self.state.tracking_face:
            try:
                pos = await get_face_position()
                if pos and not self.state.speaking and not self.state.current_dance:
                    x, y = pos
                    # Map face position to head angles
                    target_yaw = x * 30  # ±30 degrees
                    target_pitch = y * 20  # ±20 degrees

                    # Smooth tracking
                    self.state.yaw = self.state.yaw * 0.7 + target_yaw * 0.3
                    self.state.pitch = self.state.pitch * 0.7 + target_pitch * 0.3

                    await self._move_head(
                        self.state.yaw,
                        self.state.pitch,
                        0,
                        duration=0.15
                    )
            except Exception:
                pass

            await asyncio.sleep(0.1)

    # ==================== UTILITY ====================

    async def look_at(self, yaw: float, pitch: float, duration: float = 0.4):
        """Look at a specific position"""
        await self._move_head(yaw, pitch, 0, duration=duration)

    async def wave(self):
        """Friendly wave gesture"""
        await self._move_head(20, 0, 10, duration=0.3)
        for _ in range(3):
            await self._move_antennas(0.7, -0.3, duration=0.15)
            await asyncio.sleep(0.12)
            await self._move_antennas(-0.3, 0.7, duration=0.15)
            await asyncio.sleep(0.12)
        await self._move_head(0, 0, 0, duration=0.3)
        await self._move_antennas(0, 0, duration=0.2)

    async def nod_yes(self):
        """Nod yes"""
        for _ in range(3):
            await self._move_head(0, 15, 0, duration=0.15)
            await asyncio.sleep(0.1)
            await self._move_head(0, -5, 0, duration=0.15)
            await asyncio.sleep(0.1)
        await self._move_head(0, 0, 0, duration=0.2)

    async def shake_no(self):
        """Shake head no"""
        for _ in range(3):
            await self._move_head(20, 0, 0, duration=0.12)
            await asyncio.sleep(0.08)
            await self._move_head(-20, 0, 0, duration=0.12)
            await asyncio.sleep(0.08)
        await self._move_head(0, 0, 0, duration=0.2)
