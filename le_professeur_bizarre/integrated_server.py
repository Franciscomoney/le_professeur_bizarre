"""
Le Professeur Bizarre - Integrated Server with Real-time Reachy Visualization

This server:
1. Serves the web UI with real-time Reachy animation
2. Translates text using NVIDIA Nemotron
3. Controls Reachy Mini via the daemon API
4. Streams Reachy's state via WebSocket for live visualization
"""

import os
import asyncio
import math
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

try:
    from .llm import NemotronTranslator, TranslationResponse, get_fallback_response
    from .lessons import get_lesson, get_all_lessons, get_phrase, LESSONS
except ImportError:
    from llm import NemotronTranslator, TranslationResponse, get_fallback_response
    from lessons import get_lesson, get_all_lessons, get_phrase, LESSONS


# Reachy Mini Daemon API
REACHY_DAEMON_URL = os.getenv("REACHY_DAEMON_URL", "http://localhost:8000")
REACHY_DAEMON_WS = REACHY_DAEMON_URL.replace("http://", "ws://").replace("https://", "wss://")


class TranslateRequest(BaseModel):
    text: str


class TranslateResponseModel(BaseModel):
    original: str
    french_translation: str
    cultural_fact: str
    pronunciation_tip: str | None = None


# Global translator
translator: NemotronTranslator | None = None


async def move_reachy_head(yaw: float = 0, pitch: float = 0, roll: float = 0, duration: float = 1.0):
    """Move Reachy's head using the daemon API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REACHY_DAEMON_URL}/api/move/goto",
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
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error moving Reachy: {e}")
            return False


async def move_reachy_antennas(left: float, right: float, duration: float = 0.3):
    """Move Reachy's antennas"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{REACHY_DAEMON_URL}/api/move/goto",
                json={
                    "antennas": [left, right],
                    "duration": duration,
                    "interpolation_mode": "minjerk"
                },
                timeout=10.0
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error moving antennas: {e}")
            return False


async def reachy_speaking_animation():
    """Animate Reachy as if speaking - with expressive antenna movements"""
    movements = [
        {"yaw": 15, "pitch": 8, "roll": 3, "ant_l": 0.6, "ant_r": -0.3},
        {"yaw": -10, "pitch": -5, "roll": -2, "ant_l": -0.4, "ant_r": 0.6},
        {"yaw": 8, "pitch": 10, "roll": 5, "ant_l": 0.5, "ant_r": 0.5},
        {"yaw": -15, "pitch": 0, "roll": -3, "ant_l": -0.6, "ant_r": -0.6},
        {"yaw": 5, "pitch": 5, "roll": 2, "ant_l": 0.7, "ant_r": -0.5},
        {"yaw": -8, "pitch": 8, "roll": -4, "ant_l": -0.3, "ant_r": 0.7},
        {"yaw": 12, "pitch": -5, "roll": 3, "ant_l": 0.4, "ant_r": 0.2},
        {"yaw": 0, "pitch": 0, "roll": 0, "ant_l": 0, "ant_r": 0},
    ]
    for move in movements:
        # Move head
        await move_reachy_head(yaw=move["yaw"], pitch=move["pitch"], roll=move["roll"], duration=0.3)
        # Expressive antenna wiggle
        await move_reachy_antennas(move["ant_l"], move["ant_r"], duration=0.12)
        await asyncio.sleep(0.15)
        # Quick antenna flutter
        await move_reachy_antennas(-move["ant_l"] * 0.5, -move["ant_r"] * 0.5, duration=0.1)
        await asyncio.sleep(0.12)
    # Final settle
    await move_reachy_antennas(0, 0, duration=0.3)


async def reachy_thinking_animation():
    """Animate Reachy thinking"""
    await move_reachy_head(yaw=20, pitch=15, roll=8, duration=0.5)
    await move_reachy_antennas(0.3, 0.3, duration=0.3)


async def reachy_excited_animation():
    """Animate Reachy being excited"""
    for _ in range(3):
        await move_reachy_head(yaw=0, pitch=-12, roll=0, duration=0.15)
        await move_reachy_antennas(0.6, 0.6, duration=0.1)
        await asyncio.sleep(0.1)
        await move_reachy_head(yaw=0, pitch=8, roll=0, duration=0.15)
        await move_reachy_antennas(-0.4, -0.4, duration=0.1)
        await asyncio.sleep(0.1)
    await move_reachy_head(yaw=0, pitch=0, roll=0, duration=0.3)
    await move_reachy_antennas(0, 0, duration=0.2)


async def reachy_teaching_animation():
    """Animate Reachy in teaching mode - professorly gestures with antennas"""
    # Get attention first
    await move_reachy_head(yaw=0, pitch=-8, roll=0, duration=0.2)
    await move_reachy_antennas(0.5, 0.5, duration=0.15)
    await asyncio.sleep(0.2)

    # Teaching gestures - animated antenna "pointing"
    teaching_moves = [
        {"yaw": 12, "pitch": 5, "roll": 5, "ant_l": 0.8, "ant_r": -0.2},   # Point left antenna
        {"yaw": -12, "pitch": 5, "roll": -5, "ant_l": -0.2, "ant_r": 0.8},  # Point right antenna
        {"yaw": 0, "pitch": 10, "roll": 0, "ant_l": 0.6, "ant_r": 0.6},     # Both up - emphasis
        {"yaw": 8, "pitch": -3, "roll": 3, "ant_l": -0.5, "ant_r": 0.5},    # Gesture
        {"yaw": -8, "pitch": 5, "roll": -3, "ant_l": 0.5, "ant_r": -0.5},   # Counter gesture
    ]

    for move in teaching_moves:
        await move_reachy_head(yaw=move["yaw"], pitch=move["pitch"], roll=move["roll"], duration=0.25)
        await move_reachy_antennas(move["ant_l"], move["ant_r"], duration=0.15)
        await asyncio.sleep(0.2)
        # Quick flutter for emphasis
        await move_reachy_antennas(move["ant_l"] * 0.3, move["ant_r"] * 0.3, duration=0.08)
        await asyncio.sleep(0.1)

    # Return to neutral but attentive
    await move_reachy_head(yaw=0, pitch=5, roll=0, duration=0.3)
    await move_reachy_antennas(0.1, 0.1, duration=0.2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    global translator
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        translator = NemotronTranslator(api_key)
        print("✓ Nemotron translator initialized")
    else:
        print("⚠ No OPENROUTER_API_KEY - using demo mode")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REACHY_DAEMON_URL}/api/daemon/status", timeout=5.0)
            if response.status_code == 200:
                print(f"✓ Connected to Reachy daemon at {REACHY_DAEMON_URL}")
                # Startup wave
                await move_reachy_antennas(0.5, -0.5, duration=0.3)
                await asyncio.sleep(0.3)
                await move_reachy_antennas(-0.5, 0.5, duration=0.3)
                await asyncio.sleep(0.3)
                await move_reachy_antennas(0, 0, duration=0.3)
        except Exception as e:
            print(f"⚠ Could not connect to Reachy daemon: {e}")

    yield
    print("Le Professeur Bizarre shutting down...")


app = FastAPI(
    title="Le Professeur Bizarre",
    description="Franco-American cultural teacher with real-time Reachy visualization",
    version="1.0.0",
    lifespan=lifespan
)


@app.websocket("/ws/reachy-state")
async def websocket_reachy_state(websocket: WebSocket):
    """WebSocket endpoint that streams Reachy's state for real-time visualization"""
    await websocket.accept()

    try:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    # Poll the daemon for current state
                    response = await client.get(
                        f"{REACHY_DAEMON_URL}/api/state/full",
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        state = response.json()
                        # Convert to degrees for easier use in frontend
                        head = state.get("head_pose", {})
                        antennas = state.get("antennas_position", [0, 0])

                        await websocket.send_json({
                            "yaw": math.degrees(head.get("yaw", 0)),
                            "pitch": math.degrees(head.get("pitch", 0)),
                            "roll": math.degrees(head.get("roll", 0)),
                            "antenna_left": antennas[0] if len(antennas) > 0 else 0,
                            "antenna_right": antennas[1] if len(antennas) > 1 else 0,
                        })
                except httpx.RequestError:
                    await websocket.send_json({"error": "daemon_disconnected"})

                await asyncio.sleep(0.05)  # 20 FPS update rate

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.post("/api/translate", response_model=TranslateResponseModel)
async def translate(request: TranslateRequest):
    """Translate English to French with Reachy animations"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Start thinking animation
    asyncio.create_task(reachy_thinking_animation())

    try:
        if translator:
            response = await translator.translate(request.text)
        else:
            await asyncio.sleep(1.0)
            response = get_fallback_response(request.text)

        # Speaking animation
        asyncio.create_task(reachy_speaking_animation())

        # Excited animation after a delay
        async def delayed_excitement():
            await asyncio.sleep(2.5)
            await reachy_excited_animation()
        asyncio.create_task(delayed_excitement())

        return TranslateResponseModel(
            original=response.original,
            french_translation=response.french_translation,
            cultural_fact=response.cultural_fact,
            pronunciation_tip=response.pronunciation_tip
        )

    except Exception as e:
        print(f"Translation error: {e}")
        fallback = get_fallback_response(request.text)
        return TranslateResponseModel(
            original=request.text,
            french_translation=fallback.french_translation,
            cultural_fact=f"Mon Dieu! {fallback.cultural_fact}",
            pronunciation_tip=fallback.pronunciation_tip
        )


@app.get("/api/status")
async def status():
    """Get app and daemon status"""
    daemon_status = "unknown"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REACHY_DAEMON_URL}/api/daemon/status", timeout=5.0)
            if response.status_code == 200:
                daemon_status = "connected"
        except:
            daemon_status = "disconnected"

    return {
        "app": "le_professeur_bizarre",
        "version": "1.0.0",
        "translator_available": translator is not None,
        "model": os.getenv("NEMOTRON_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1"),
        "reachy_daemon": daemon_status
    }


@app.post("/api/reachy/wave")
async def wave():
    """Make Reachy wave"""
    await move_reachy_head(yaw=25, pitch=0, roll=12, duration=0.4)
    for _ in range(3):
        await move_reachy_antennas(0.7, -0.3, duration=0.2)
        await asyncio.sleep(0.15)
        await move_reachy_antennas(-0.3, 0.7, duration=0.2)
        await asyncio.sleep(0.15)
    await move_reachy_head(yaw=0, pitch=0, roll=0, duration=0.4)
    await move_reachy_antennas(0, 0, duration=0.3)
    return {"status": "waved"}


@app.post("/api/reachy/nod")
async def nod():
    """Make Reachy nod yes"""
    for _ in range(3):
        await move_reachy_head(yaw=0, pitch=18, roll=0, duration=0.2)
        await asyncio.sleep(0.15)
        await move_reachy_head(yaw=0, pitch=-8, roll=0, duration=0.2)
        await asyncio.sleep(0.15)
    await move_reachy_head(yaw=0, pitch=0, roll=0, duration=0.3)
    return {"status": "nodded"}


@app.post("/api/reachy/shake")
async def shake():
    """Make Reachy shake head no"""
    for _ in range(3):
        await move_reachy_head(yaw=25, pitch=0, roll=0, duration=0.15)
        await asyncio.sleep(0.1)
        await move_reachy_head(yaw=-25, pitch=0, roll=0, duration=0.15)
        await asyncio.sleep(0.1)
    await move_reachy_head(yaw=0, pitch=0, roll=0, duration=0.3)
    return {"status": "shook"}


@app.post("/api/reachy/dance")
async def dance():
    """Make Reachy do a little dance"""
    moves = [
        {"yaw": 20, "pitch": 10, "roll": 15},
        {"yaw": -20, "pitch": -10, "roll": -15},
        {"yaw": 15, "pitch": 15, "roll": -10},
        {"yaw": -15, "pitch": -15, "roll": 10},
        {"yaw": 0, "pitch": 20, "roll": 0},
        {"yaw": 0, "pitch": -10, "roll": 0},
    ]
    for move in moves:
        await move_reachy_head(**move, duration=0.25)
        await move_reachy_antennas(0.5 if move["yaw"] > 0 else -0.5,
                                   -0.5 if move["yaw"] > 0 else 0.5, duration=0.15)
        await asyncio.sleep(0.2)
    await move_reachy_head(yaw=0, pitch=0, roll=0, duration=0.3)
    await move_reachy_antennas(0, 0, duration=0.2)
    return {"status": "danced"}


# ==================== LESSON API ENDPOINTS ====================

@app.get("/api/lessons")
async def list_lessons():
    """Get all available lessons"""
    return get_all_lessons()


@app.get("/api/lessons/{lesson_id}")
async def get_lesson_detail(lesson_id: str):
    """Get a specific lesson with all phrases"""
    lesson = get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")
    return {
        "id": lesson_id,
        **lesson
    }


@app.get("/api/lessons/{lesson_id}/phrase/{phrase_index}")
async def get_lesson_phrase(lesson_id: str, phrase_index: int):
    """Get a specific phrase from a lesson and animate Reachy"""
    phrase = get_phrase(lesson_id, phrase_index)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    # Animate Reachy as if teaching
    asyncio.create_task(reachy_speaking_animation())

    return phrase


@app.post("/api/lessons/{lesson_id}/phrase/{phrase_index}/teach")
async def teach_phrase(lesson_id: str, phrase_index: int):
    """Have Reachy teach a phrase with full animation"""
    phrase = get_phrase(lesson_id, phrase_index)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    # Use the teaching animation with expressive antenna movements
    asyncio.create_task(reachy_teaching_animation())

    return {
        **phrase,
        "animation": "teaching"
    }


# Main HTML page with real-time Reachy visualization
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Le Professeur Bizarre - Reachy Mini Live</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --france-blue: #002395;
            --france-red: #ED2939;
            --gold: #D4AF37;
            --cream: #FDF8F0;
            --dark: #1a1a2e;
            --gray: #6b7280;
            --nvidia-green: #76B900;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--cream) 0%, #fff 50%, var(--cream) 100%);
            min-height: 100vh;
            padding: 1.5rem;
        }
        .container { max-width: 1100px; margin: 0 auto; }

        .header { text-align: center; margin-bottom: 1.5rem; }
        .header h1 {
            font-family: 'Playfair Display', serif;
            font-size: 2.2rem;
            color: var(--dark);
        }
        .header .subtitle { color: var(--gray); font-size: 0.95rem; }
        .header .powered {
            color: var(--nvidia-green);
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }

        /* Mode Tabs */
        .mode-tabs {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .mode-tab {
            padding: 0.75rem 1.5rem;
            border: 2px solid #e5e7eb;
            border-radius: 25px;
            background: white;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .mode-tab:hover {
            border-color: var(--france-blue);
        }
        .mode-tab.active {
            background: var(--france-blue);
            border-color: var(--france-blue);
            color: white;
        }
        .mode-tab.lesson-tab.active {
            background: linear-gradient(135deg, var(--france-red), #c41e30);
            border-color: var(--france-red);
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 1.5rem;
        }

        .panel {
            background: white;
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        .panel h2 {
            font-size: 0.85rem;
            color: var(--gray);
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Hide/Show Modes */
        .mode-content { display: none; }
        .mode-content.active { display: block; }

        /* Reachy 3D-ish Visualization */
        .reachy-stage {
            background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #252540 100%);
            border-radius: 12px;
            height: 320px;
            position: relative;
            overflow: hidden;
            perspective: 800px;
        }

        .stage-grid {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 100px;
            background:
                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 30px 30px;
            transform: rotateX(60deg);
            transform-origin: bottom;
        }

        .robot-container {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            transform-style: preserve-3d;
        }

        .robot-body {
            width: 90px;
            height: 110px;
            background: linear-gradient(135deg, #f0f0f0 0%, #d8d8d8 50%, #c0c0c0 100%);
            border-radius: 45px 45px 25px 25px;
            position: relative;
            box-shadow:
                inset -5px -5px 15px rgba(0,0,0,0.1),
                inset 5px 5px 15px rgba(255,255,255,0.5),
                0 20px 40px rgba(0,0,0,0.3);
        }

        .robot-neck {
            width: 30px;
            height: 15px;
            background: linear-gradient(to bottom, #888, #666);
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            border-radius: 5px;
        }

        .robot-head {
            width: 80px;
            height: 55px;
            background: linear-gradient(135deg, #fafafa 0%, #e8e8e8 50%, #d0d0d0 100%);
            border-radius: 40px 40px 20px 20px;
            position: absolute;
            top: -60px;
            left: 50%;
            transform-origin: center bottom;
            box-shadow:
                inset -3px -3px 10px rgba(0,0,0,0.1),
                inset 3px 3px 10px rgba(255,255,255,0.8),
                0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.05s ease-out;
        }

        .robot-face {
            position: absolute;
            top: 15px;
            left: 10px;
            right: 10px;
            height: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 8px;
        }

        .robot-eye {
            width: 14px;
            height: 14px;
            background: radial-gradient(circle at 30% 30%, #333 0%, #000 100%);
            border-radius: 50%;
            box-shadow:
                inset 2px 2px 4px rgba(255,255,255,0.3),
                0 2px 4px rgba(0,0,0,0.3);
            position: relative;
        }
        .robot-eye::after {
            content: '';
            position: absolute;
            top: 3px;
            left: 3px;
            width: 4px;
            height: 4px;
            background: white;
            border-radius: 50%;
        }

        .robot-antenna {
            width: 5px;
            height: 28px;
            background: linear-gradient(to bottom, #999, #666);
            position: absolute;
            top: -25px;
            border-radius: 2px;
            transform-origin: bottom center;
            transition: transform 0.05s ease-out;
        }
        .robot-antenna.left { left: 18px; }
        .robot-antenna.right { right: 18px; }

        .robot-antenna::after {
            content: '';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 14px;
            height: 14px;
            background: radial-gradient(circle at 30% 30%, var(--gold) 0%, #b8960a 100%);
            border-radius: 50%;
            box-shadow: 0 0 10px rgba(212,175,55,0.5);
        }

        .robot-base {
            width: 70px;
            height: 20px;
            background: linear-gradient(to bottom, #555, #333);
            border-radius: 10px;
            position: absolute;
            bottom: -15px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 5px 15px rgba(0,0,0,0.4);
        }

        .status-bar {
            position: absolute;
            bottom: 10px;
            left: 10px;
            right: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-indicator {
            padding: 0.4rem 0.8rem;
            background: rgba(0,0,0,0.6);
            border-radius: 20px;
            color: white;
            font-size: 0.7rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ef4444;
        }
        .status-dot.connected { background: #10B981; animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .position-display {
            font-family: monospace;
            font-size: 0.65rem;
            color: rgba(255,255,255,0.7);
        }

        .control-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        .ctrl-btn {
            flex: 1;
            min-width: 70px;
            padding: 0.6rem 0.8rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.3rem;
        }
        .ctrl-btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .ctrl-btn:active { transform: translateY(0); }
        .ctrl-btn.wave { background: var(--france-blue); color: white; }
        .ctrl-btn.nod { background: var(--nvidia-green); color: white; }
        .ctrl-btn.shake { background: var(--france-red); color: white; }
        .ctrl-btn.dance { background: linear-gradient(135deg, var(--gold), #c9a227); color: var(--dark); }

        /* Translation Panel */
        .input-section { margin-bottom: 1rem; }
        .input-section label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        .input-with-mic {
            display: flex;
            gap: 0.5rem;
            align-items: stretch;
        }
        .input-section textarea {
            flex: 1;
            padding: 0.8rem;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-family: inherit;
            font-size: 0.95rem;
            resize: none;
            transition: border-color 0.2s;
        }
        .input-section textarea:focus {
            outline: none;
            border-color: var(--france-blue);
        }
        .mic-btn {
            width: 50px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            background: white;
            font-size: 1.4rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .mic-btn:hover {
            border-color: var(--france-red);
            background: #fff5f5;
        }
        .mic-btn.listening {
            border-color: var(--france-red);
            background: var(--france-red);
            animation: pulse-mic 1s infinite;
        }
        @keyframes pulse-mic {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .mic-status {
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 0.4rem;
            text-align: center;
        }

        .translate-btn {
            width: 100%;
            padding: 0.9rem;
            background: linear-gradient(135deg, var(--france-blue), #3355AA);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .translate-btn:hover { opacity: 0.9; }
        .translate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .result { display: none; margin-top: 1rem; }
        .result.show { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .french-box {
            padding: 1rem;
            background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%);
            border-left: 4px solid var(--france-blue);
            border-radius: 8px;
            margin-bottom: 0.75rem;
        }
        .french-box h3 { font-size: 0.75rem; color: var(--gray); margin-bottom: 0.4rem; }
        .french-box p {
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            color: var(--dark);
        }

        .fact-box {
            padding: 1rem;
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
            border-left: 4px solid var(--gold);
            border-radius: 8px;
        }
        .fact-box h3 { font-size: 0.75rem; color: var(--gray); margin-bottom: 0.4rem; }
        .fact-box p { font-size: 0.9rem; line-height: 1.5; }

        .tip-text {
            margin-top: 0.75rem;
            font-style: italic;
            color: var(--gray);
            font-size: 0.85rem;
        }

        .quick-phrases {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.75rem;
        }
        .quick-btn {
            padding: 0.35rem 0.7rem;
            background: var(--cream);
            border: 1px solid #e5e7eb;
            border-radius: 15px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .quick-btn:hover {
            background: white;
            border-color: var(--france-blue);
            color: var(--france-blue);
        }

        /* ==================== LESSON MODE STYLES ==================== */
        .lesson-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }

        .lesson-card {
            padding: 1.25rem;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            background: white;
        }
        .lesson-card:hover {
            border-color: var(--france-blue);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .lesson-card .icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .lesson-card .title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }
        .lesson-card .desc {
            font-size: 0.8rem;
            color: var(--gray);
        }
        .lesson-card .count {
            font-size: 0.75rem;
            color: var(--france-blue);
            margin-top: 0.5rem;
        }

        /* Lesson View */
        .lesson-view { display: none; }
        .lesson-view.active { display: block; }

        .lesson-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e5e7eb;
        }
        .back-btn {
            padding: 0.5rem 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            font-size: 0.9rem;
        }
        .back-btn:hover {
            border-color: var(--france-red);
            color: var(--france-red);
        }
        .lesson-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
        }

        .progress-bar {
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--france-blue), var(--nvidia-green));
            border-radius: 3px;
            transition: width 0.3s;
        }

        .phrase-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .phrase-english {
            font-size: 0.9rem;
            color: var(--gray);
            margin-bottom: 0.75rem;
        }
        .phrase-french {
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            color: var(--dark);
            margin-bottom: 0.5rem;
        }
        .phrase-pronunciation {
            font-size: 1rem;
            color: var(--france-blue);
            font-style: italic;
            margin-bottom: 1rem;
        }

        .phrase-tip {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
        }
        .phrase-tip strong { color: var(--france-blue); }

        .phrase-fact {
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
        }
        .phrase-fact strong { color: #92400e; }

        .lesson-controls {
            display: flex;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }
        .lesson-btn {
            flex: 1;
            padding: 0.9rem;
            border: none;
            border-radius: 10px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .lesson-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        .lesson-btn.prev {
            background: #e5e7eb;
            color: var(--dark);
        }
        .lesson-btn.speak {
            background: linear-gradient(135deg, var(--france-red), #c41e30);
            color: white;
        }
        .lesson-btn.next {
            background: linear-gradient(135deg, var(--france-blue), #3355AA);
            color: white;
        }
        .lesson-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            filter: brightness(1.05);
        }

        .lesson-complete {
            text-align: center;
            padding: 2rem;
        }
        .lesson-complete h3 {
            font-family: 'Playfair Display', serif;
            font-size: 1.8rem;
            margin-bottom: 1rem;
        }
        .lesson-complete p {
            color: var(--gray);
            margin-bottom: 1.5rem;
        }

        @media (max-width: 800px) {
            .main-grid { grid-template-columns: 1fr; }
            .reachy-stage { height: 280px; }
            .lesson-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🇫🇷 Le Professeur Bizarre 🇺🇸</h1>
            <p class="subtitle">Your Eccentric Franco-American Cultural Teacher</p>
            <p class="powered">Powered by NVIDIA Nemotron + Reachy Mini SDK</p>
        </header>

        <!-- Mode Tabs -->
        <div class="mode-tabs">
            <button class="mode-tab active" onclick="switchMode('translate')">🎭 Free Translate</button>
            <button class="mode-tab lesson-tab" onclick="switchMode('lesson')">📚 French Lessons</button>
        </div>

        <div class="main-grid">
            <div class="panel">
                <h2>🤖 Reachy Mini - Live View</h2>
                <div class="reachy-stage">
                    <div class="stage-grid"></div>
                    <div class="robot-container">
                        <div class="robot-body">
                            <div class="robot-neck"></div>
                            <div class="robot-head" id="robotHead">
                                <div class="robot-antenna left" id="antennaLeft"></div>
                                <div class="robot-antenna right" id="antennaRight"></div>
                                <div class="robot-face">
                                    <div class="robot-eye"></div>
                                    <div class="robot-eye"></div>
                                </div>
                            </div>
                            <div class="robot-base"></div>
                        </div>
                    </div>
                    <div class="status-bar">
                        <div class="status-indicator">
                            <div class="status-dot" id="statusDot"></div>
                            <span id="statusText">Connecting...</span>
                        </div>
                        <div class="position-display" id="posDisplay">Y:0° P:0° R:0°</div>
                    </div>
                </div>
                <div class="control-buttons">
                    <button class="ctrl-btn wave" onclick="doAction('wave')">👋 Wave</button>
                    <button class="ctrl-btn nod" onclick="doAction('nod')">✓ Nod</button>
                    <button class="ctrl-btn shake" onclick="doAction('shake')">✗ Shake</button>
                    <button class="ctrl-btn dance" onclick="doAction('dance')">💃 Dance</button>
                </div>
            </div>

            <div class="panel">
                <!-- ===== TRANSLATE MODE ===== -->
                <div id="translateMode" class="mode-content active">
                    <h2>🗣️ Translation</h2>
                    <div class="input-section">
                        <label>Say something in English:</label>
                        <div class="input-with-mic">
                            <textarea id="input" rows="2" placeholder="Hello, how are you?"></textarea>
                            <button class="mic-btn" id="micBtn" onclick="toggleListening()" title="Click to speak">
                                🎤
                            </button>
                        </div>
                        <div class="mic-status" id="micStatus">Click mic to speak</div>
                    </div>
                    <button class="translate-btn" id="translateBtn" onclick="translate()">
                        Translate & Speak! 🎭
                    </button>

                    <div class="result" id="result">
                        <div class="french-box">
                            <h3>🇫🇷 French</h3>
                            <p id="frenchText"></p>
                        </div>
                        <div class="fact-box">
                            <h3>💡 Bizarre Fact</h3>
                            <p id="factText"></p>
                        </div>
                        <p class="tip-text" id="tipText"></p>
                    </div>

                    <div class="quick-phrases">
                        <button class="quick-btn" onclick="setAndTranslate('Hello, how are you?')">Hello!</button>
                        <button class="quick-btn" onclick="setAndTranslate('I love cheese')">Cheese</button>
                        <button class="quick-btn" onclick="setAndTranslate('Where is the wine?')">Wine</button>
                        <button class="quick-btn" onclick="setAndTranslate('The croissant is amazing')">Croissant</button>
                        <button class="quick-btn" onclick="setAndTranslate('I am American')">American</button>
                    </div>
                </div>

                <!-- ===== LESSON MODE ===== -->
                <div id="lessonMode" class="mode-content">
                    <!-- Lesson Selection -->
                    <div id="lessonSelect" class="lesson-view active">
                        <h2>📚 Choose a Lesson</h2>
                        <div class="lesson-grid" id="lessonGrid">
                            <!-- Lessons will be loaded here -->
                        </div>
                    </div>

                    <!-- Lesson Viewer -->
                    <div id="lessonViewer" class="lesson-view">
                        <div class="lesson-header">
                            <button class="back-btn" onclick="backToLessons()">← Back</button>
                            <span class="lesson-title" id="currentLessonTitle">Greetings</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                        </div>

                        <div class="phrase-card" id="phraseCard">
                            <div class="phrase-english" id="phraseEnglish">Hello</div>
                            <div class="phrase-french" id="phraseFrench">Bonjour</div>
                            <div class="phrase-pronunciation" id="phrasePronunciation">bohn-ZHOOR</div>

                            <div class="phrase-tip" id="phraseTip">
                                <strong>💡 Tip:</strong> <span id="phraseTipText">Use this until evening</span>
                            </div>
                            <div class="phrase-fact" id="phraseFact">
                                <strong>🎭 Bizarre Fact:</strong> <span id="phraseFactText">In France, you MUST say Bonjour when entering any shop!</span>
                            </div>
                        </div>

                        <div class="lesson-controls">
                            <button class="lesson-btn prev" id="prevBtn" onclick="prevPhrase()">← Previous</button>
                            <button class="lesson-btn speak" onclick="speakCurrentPhrase()">🔊 Speak</button>
                            <button class="lesson-btn next" id="nextBtn" onclick="nextPhrase()">Next →</button>
                        </div>
                    </div>

                    <!-- Lesson Complete -->
                    <div id="lessonComplete" class="lesson-view">
                        <div class="lesson-complete">
                            <h3>🎉 Magnifique!</h3>
                            <p>You've completed this lesson! Le Professeur is très proud of you.</p>
                            <button class="lesson-btn next" onclick="backToLessons()">Choose Another Lesson</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Elements
        const robotHead = document.getElementById('robotHead');
        const antennaLeft = document.getElementById('antennaLeft');
        const antennaRight = document.getElementById('antennaRight');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const posDisplay = document.getElementById('posDisplay');
        const translateBtn = document.getElementById('translateBtn');
        const input = document.getElementById('input');
        const result = document.getElementById('result');

        // WebSocket for real-time state
        let ws;
        let reconnectAttempts = 0;

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/reachy-state`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                statusDot.classList.add('connected');
                statusText.textContent = 'Live';
                reconnectAttempts = 0;
            };

            ws.onmessage = (event) => {
                const state = JSON.parse(event.data);
                if (state.error) {
                    statusDot.classList.remove('connected');
                    statusText.textContent = 'Daemon offline';
                    return;
                }
                updateRobotVisualization(state);
            };

            ws.onclose = () => {
                statusDot.classList.remove('connected');
                statusText.textContent = 'Disconnected';
                // Reconnect with backoff
                reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
                setTimeout(connectWebSocket, delay);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }

        function updateRobotVisualization(state) {
            const { yaw, pitch, roll, antenna_left, antenna_right } = state;

            // Update head transform (with scaling for visual effect)
            const visualYaw = yaw * 1.5;
            const visualPitch = pitch * 1.5;
            const visualRoll = roll * 1.5;

            robotHead.style.transform = `
                translateX(-50%)
                rotateY(${visualYaw}deg)
                rotateX(${-visualPitch}deg)
                rotateZ(${visualRoll}deg)
            `;

            // Update antennas (convert from radians-ish to degrees for visual)
            const leftAngle = antenna_left * 40; // Scale for visibility
            const rightAngle = antenna_right * 40;
            antennaLeft.style.transform = `rotate(${leftAngle}deg)`;
            antennaRight.style.transform = `rotate(${-rightAngle}deg)`;

            // Update position display
            posDisplay.textContent = `Y:${yaw.toFixed(1)}° P:${pitch.toFixed(1)}° R:${roll.toFixed(1)}°`;
        }

        function setAndTranslate(text) {
            input.value = text;
            translate();
        }

        async function translate() {
            const text = input.value.trim();
            if (!text) return;

            translateBtn.disabled = true;
            translateBtn.textContent = 'Thinking...';

            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                const data = await response.json();

                document.getElementById('frenchText').textContent = data.french_translation;
                document.getElementById('factText').textContent = data.cultural_fact;
                document.getElementById('tipText').textContent = data.pronunciation_tip
                    ? '🎤 ' + data.pronunciation_tip : '';
                result.classList.add('show');
            } catch (e) {
                console.error('Translation error:', e);
                alert('Translation error: ' + e.message);
            } finally {
                translateBtn.disabled = false;
                translateBtn.textContent = 'Translate & Speak! 🎭';
            }
        }

        async function doAction(action) {
            try {
                await fetch(`/api/reachy/${action}`, { method: 'POST' });
            } catch (e) {
                console.error(`Error doing ${action}:`, e);
            }
        }

        // Enter key to translate
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                translate();
            }
        });

        // Start WebSocket connection
        connectWebSocket();

        // ========== SPEECH RECOGNITION (Listen) ==========
        let recognition = null;
        let isListening = false;
        const micBtn = document.getElementById('micBtn');
        const micStatus = document.getElementById('micStatus');

        function initSpeechRecognition() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                micBtn.style.display = 'none';
                console.log('Speech recognition not supported');
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                isListening = true;
                micBtn.classList.add('listening');
                micStatus.textContent = 'Listening...';
            };

            recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                input.value = transcript;

                // If final result, translate
                if (event.results[event.results.length - 1].isFinal) {
                    micStatus.textContent = 'Got it!';
                    setTimeout(() => translate(), 500);
                }
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                micStatus.textContent = 'Error: ' + event.error;
                stopListening();
            };

            recognition.onend = () => {
                stopListening();
            };
        }

        function toggleListening() {
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        function stopListening() {
            isListening = false;
            micBtn.classList.remove('listening');
            micStatus.textContent = 'Click mic to speak';
        }

        // ========== TEXT-TO-SPEECH (Speak French) ==========
        let frenchVoice = null;

        function initTTS() {
            // Wait for voices to load
            function loadVoices() {
                const voices = speechSynthesis.getVoices();
                // Try to find a French voice
                frenchVoice = voices.find(v => v.lang.startsWith('fr')) ||
                              voices.find(v => v.name.toLowerCase().includes('french')) ||
                              voices[0];
                console.log('Using voice:', frenchVoice?.name);
            }

            loadVoices();
            speechSynthesis.onvoiceschanged = loadVoices;
        }

        function speakFrench(text) {
            if (!text) return;

            // Cancel any ongoing speech
            speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.voice = frenchVoice;
            utterance.lang = 'fr-FR';
            utterance.rate = 0.9;
            utterance.pitch = 1.0;

            speechSynthesis.speak(utterance);
        }

        // Modify translate to speak result
        const originalTranslate = translate;
        translate = async function() {
            const text = input.value.trim();
            if (!text) return;

            translateBtn.disabled = true;
            translateBtn.textContent = 'Thinking...';

            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                const data = await response.json();

                document.getElementById('frenchText').textContent = data.french_translation;
                document.getElementById('factText').textContent = data.cultural_fact;
                document.getElementById('tipText').textContent = data.pronunciation_tip
                    ? '🎤 ' + data.pronunciation_tip : '';
                result.classList.add('show');

                // Speak the French translation!
                speakFrench(data.french_translation);

            } catch (e) {
                console.error('Translation error:', e);
                alert('Translation error: ' + e.message);
            } finally {
                translateBtn.disabled = false;
                translateBtn.textContent = 'Translate & Speak! 🎭';
            }
        };

        // Initialize speech features
        initSpeechRecognition();
        initTTS();

        // ========== MODE SWITCHING ==========
        let currentMode = 'translate';

        function switchMode(mode) {
            currentMode = mode;

            // Update tabs
            document.querySelectorAll('.mode-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector(mode === 'translate' ? '.mode-tab:first-child' : '.mode-tab.lesson-tab').classList.add('active');

            // Update content
            document.getElementById('translateMode').classList.toggle('active', mode === 'translate');
            document.getElementById('lessonMode').classList.toggle('active', mode === 'lesson');

            // Load lessons if switching to lesson mode
            if (mode === 'lesson') {
                loadLessons();
                // Wave to greet student
                doAction('wave');
            }
        }

        // ========== LESSON MODE ==========
        let lessons = {};
        let currentLesson = null;
        let currentPhraseIndex = 0;
        let totalPhrases = 0;

        async function loadLessons() {
            try {
                const response = await fetch('/api/lessons');
                lessons = await response.json();

                const grid = document.getElementById('lessonGrid');
                grid.innerHTML = '';

                for (const [id, lesson] of Object.entries(lessons)) {
                    const card = document.createElement('div');
                    card.className = 'lesson-card';
                    card.onclick = () => startLesson(id);
                    card.innerHTML = `
                        <div class="icon">${lesson.icon}</div>
                        <div class="title">${lesson.title}</div>
                        <div class="desc">${lesson.description}</div>
                        <div class="count">${lesson.phrase_count} phrases</div>
                    `;
                    grid.appendChild(card);
                }
            } catch (e) {
                console.error('Error loading lessons:', e);
            }
        }

        async function startLesson(lessonId) {
            try {
                const response = await fetch(`/api/lessons/${lessonId}`);
                const lesson = await response.json();

                currentLesson = lesson;
                currentPhraseIndex = 0;
                totalPhrases = lesson.phrases.length;

                document.getElementById('currentLessonTitle').textContent = `${lesson.icon} ${lesson.title}`;

                // Show lesson viewer
                document.getElementById('lessonSelect').classList.remove('active');
                document.getElementById('lessonViewer').classList.add('active');
                document.getElementById('lessonComplete').classList.remove('active');

                // Load first phrase
                showPhrase(0);

                // Reachy gets excited to teach
                doAction('nod');
            } catch (e) {
                console.error('Error starting lesson:', e);
            }
        }

        function showPhrase(index) {
            if (!currentLesson || index < 0 || index >= totalPhrases) return;

            const phrase = currentLesson.phrases[index];
            currentPhraseIndex = index;

            // Update progress
            const progress = ((index + 1) / totalPhrases) * 100;
            document.getElementById('progressFill').style.width = progress + '%';

            // Update phrase display
            document.getElementById('phraseEnglish').textContent = phrase.english;
            document.getElementById('phraseFrench').textContent = phrase.french;
            document.getElementById('phrasePronunciation').textContent = phrase.pronunciation;
            document.getElementById('phraseTipText').textContent = phrase.tip;
            document.getElementById('phraseFactText').textContent = phrase.cultural_fact;

            // Update button states
            document.getElementById('prevBtn').disabled = index === 0;
            document.getElementById('nextBtn').textContent = index === totalPhrases - 1 ? 'Complete ✓' : 'Next →';

            // Teach the phrase (Reachy animates)
            fetch(`/api/lessons/${currentLesson.id}/phrase/${index}/teach`, { method: 'POST' });
        }

        function nextPhrase() {
            if (currentPhraseIndex >= totalPhrases - 1) {
                // Lesson complete!
                document.getElementById('lessonViewer').classList.remove('active');
                document.getElementById('lessonComplete').classList.add('active');
                doAction('dance');
                return;
            }
            showPhrase(currentPhraseIndex + 1);
        }

        function prevPhrase() {
            if (currentPhraseIndex > 0) {
                showPhrase(currentPhraseIndex - 1);
            }
        }

        function speakCurrentPhrase() {
            if (!currentLesson) return;
            const phrase = currentLesson.phrases[currentPhraseIndex];
            speakFrench(phrase.french);
            // Make Reachy animate while speaking
            doAction('nod');
        }

        function backToLessons() {
            document.getElementById('lessonSelect').classList.add('active');
            document.getElementById('lessonViewer').classList.remove('active');
            document.getElementById('lessonComplete').classList.remove('active');
            currentLesson = null;
        }
    </script>
</body>
</html>
"""


def run_server(host: str = "0.0.0.0", port: int = 5173):
    """Run the integrated server"""
    import uvicorn
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║   🇫🇷  Le Professeur Bizarre  🇺🇸                          ║
    ║   Real-time Reachy Visualization                          ║
    ╚═══════════════════════════════════════════════════════════╝

    Web UI: http://localhost:{port}
    Reachy Daemon: {REACHY_DAEMON_URL}

    Press Ctrl+C to stop
    """)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_server()
