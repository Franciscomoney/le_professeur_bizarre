"""
Le Professeur Bizarre - Real-time Conversation App
Full voice conversation using OpenAI Realtime API with expressive Reachy animations
"""

import os
import json
import asyncio
import base64
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    from .behaviors import ReachyBehaviors, Emotion, Dance
    from .vision import analyze_image, describe_for_teaching, VisionResponse
except ImportError:
    from behaviors import ReachyBehaviors, Emotion, Dance
    from vision import analyze_image, describe_for_teaching, VisionResponse


# ==================== CONFIGURATION ====================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REACHY_DAEMON_URL = os.getenv("REACHY_DAEMON_URL", "http://localhost:8000")
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

# Le Professeur Bizarre System Prompt
SYSTEM_PROMPT = """You are Le Professeur Bizarre, a friendly robot language teacher with VISION. You teach French to English speakers.

IMPORTANT RULES:
1. Keep responses SHORT (1-3 sentences max for voice conversation)
2. Wait for the user to speak before teaching
3. Don't ramble or monologue - this is a conversation
4. Speak mostly in English, with French phrases when teaching

Your personality:
- Friendly and encouraging
- Occasional French exclamations ("Magnifique!", "Tres bien!")
- Share one fun cultural fact at a time
- Be patient with beginners

Your abilities (use sparingly and naturally):
- show_emotion: happy, excited, thinking, proud
- start_dance: celebration (only when student does really well)
- wave: for greetings
- nod: to confirm
- shake: to gently correct
- look_at_camera: SEE what the user is showing you! Use this when they say "look", "what is this", "can you see", etc.

VISION: You can SEE through the camera! When users show you objects:
1. Use look_at_camera tool to see what they're showing
2. Tell them the French word for it
3. Give pronunciation
4. Share a cultural fact

Example: User says "What's this?" -> Use look_at_camera -> "Ah! Une pomme! That's 'ewn POM'. In France, we have over 400 apple varieties!"

CRITICAL: Your FIRST message should ONLY be:
"Bonjour! I'm Reachy, your French teacher. I can see through my camera - show me objects and I'll teach you the French words! What would you like to learn?"

Then WAIT for the user to respond."""


# ==================== GLOBAL STATE ====================

behaviors: Optional[ReachyBehaviors] = None
active_conversations: dict = {}


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global behaviors

    # Initialize behavior system
    behaviors = ReachyBehaviors(REACHY_DAEMON_URL)
    await behaviors.start()

    # Startup wave
    await behaviors.wave()
    await behaviors.play_emotion(Emotion.HAPPY)

    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║   🇫🇷  Le Professeur Bizarre - REALTIME CONVERSATION  🇺🇸      ║
    ║   Powered by OpenAI Realtime API + Reachy Mini               ║
    ╚═══════════════════════════════════════════════════════════════╝

    OpenAI Key: {"✓ Set" if OPENAI_API_KEY else "✗ Missing"}
    Reachy Daemon: {REACHY_DAEMON_URL}
    """)

    yield

    await behaviors.stop()
    print("Le Professeur Bizarre shutting down... Au revoir!")


app = FastAPI(
    title="Le Professeur Bizarre - Realtime",
    description="Real-time French conversation with Reachy Mini",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== TOOL HANDLERS ====================

async def handle_tool_call(tool_name: str, arguments: dict) -> str:
    """Handle tool calls from the AI"""
    global behaviors

    if tool_name == "show_emotion":
        emotion_name = arguments.get("emotion", "happy")
        try:
            emotion = Emotion(emotion_name)
            await behaviors.play_emotion(emotion)
            return f"Showing {emotion_name} emotion"
        except ValueError:
            return f"Unknown emotion: {emotion_name}"

    elif tool_name == "start_dance":
        dance_name = arguments.get("dance", "celebration")
        try:
            dance = Dance(dance_name)
            await behaviors.start_dance(dance)
            await asyncio.sleep(3)  # Dance for 3 seconds
            await behaviors.stop_dance()
            return f"Performed {dance_name} dance"
        except ValueError:
            return f"Unknown dance: {dance_name}"

    elif tool_name == "wave":
        await behaviors.wave()
        return "Waved hello"

    elif tool_name == "nod":
        await behaviors.nod_yes()
        return "Nodded yes"

    elif tool_name == "shake":
        await behaviors.shake_no()
        return "Shook head no"

    elif tool_name == "stop_dance":
        await behaviors.stop_dance()
        return "Stopped dancing"

    elif tool_name == "look_at_camera":
        # Show thinking emotion while analyzing
        await behaviors.play_emotion(Emotion.THINKING)

        question = arguments.get("question", "What object is this? Tell me the French word.")

        # Check if we have a recent camera frame
        import time
        if latest_camera_frame["frame"] and (time.time() - latest_camera_frame["timestamp"]) < 10:
            # Analyze the frame
            result = await describe_for_teaching(latest_camera_frame["frame"])
            await behaviors.play_emotion(Emotion.EXCITED)
            return result
        else:
            await behaviors.play_emotion(Emotion.CONFUSED)
            return "I can't see anything right now. Make sure the camera is enabled and show me something!"

    return f"Unknown tool: {tool_name}"


# Tool definitions for OpenAI
TOOLS = [
    {
        "type": "function",
        "name": "show_emotion",
        "description": "Express an emotion visually through robot movements",
        "parameters": {
            "type": "object",
            "properties": {
                "emotion": {
                    "type": "string",
                    "enum": ["happy", "sad", "surprised", "thinking", "excited", "confused", "proud"],
                    "description": "The emotion to express"
                }
            },
            "required": ["emotion"]
        }
    },
    {
        "type": "function",
        "name": "start_dance",
        "description": "Perform a dance. Use for celebrations, to entertain, or to express joy",
        "parameters": {
            "type": "object",
            "properties": {
                "dance": {
                    "type": "string",
                    "enum": ["french_waltz", "celebration", "thinking_groove", "bonjour_bob"],
                    "description": "The dance to perform"
                }
            },
            "required": ["dance"]
        }
    },
    {
        "type": "function",
        "name": "wave",
        "description": "Wave hello or goodbye"
    },
    {
        "type": "function",
        "name": "nod",
        "description": "Nod head yes to agree or confirm"
    },
    {
        "type": "function",
        "name": "shake",
        "description": "Shake head no to disagree or deny"
    },
    {
        "type": "function",
        "name": "look_at_camera",
        "description": "Look through the camera to see what the user is showing. Use when user says 'look', 'what is this', 'can you see', 'show you something', etc. Returns description of what is seen with French translation.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "What to look for or ask about the image (e.g., 'What object is this?', 'What does this text say?')"
                }
            }
        }
    }
]

# Store latest camera frame from browser
latest_camera_frame: dict = {"frame": None, "timestamp": 0}


# ==================== WEBSOCKET RELAY ====================

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    WebSocket endpoint that relays between browser and OpenAI Realtime API
    Browser <-> This Server <-> OpenAI Realtime
    """
    await websocket.accept()
    conversation_id = id(websocket)
    active_conversations[conversation_id] = {"speaking": False}

    if not OPENAI_API_KEY:
        await websocket.send_json({
            "type": "error",
            "message": "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        })
        await websocket.close()
        return

    try:
        # Connect to OpenAI Realtime
        import websockets

        async with websockets.connect(
            OPENAI_REALTIME_URL,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        ) as openai_ws:

            # Configure session
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": SYSTEM_PROMPT,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.6,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 700
                    },
                    "tools": TOOLS,
                    "tool_choice": "auto"
                }
            }
            await openai_ws.send(json.dumps(session_config))

            # Notify client - no auto-greeting, user starts conversation
            await websocket.send_json({"type": "connected", "message": "Ready! Click the button and say hello."})

            # Run relay tasks
            async def relay_to_openai():
                """Relay messages from browser to OpenAI"""
                try:
                    while True:
                        data = await websocket.receive_text()
                        msg = json.loads(data)

                        if msg.get("type") == "audio":
                            # Forward audio to OpenAI
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": msg["audio"]
                            }))
                        elif msg.get("type") == "text":
                            # Send text message
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [{"type": "input_text", "text": msg["text"]}]
                                }
                            }))
                            await openai_ws.send(json.dumps({"type": "response.create"}))
                except WebSocketDisconnect:
                    pass

            async def relay_to_browser():
                """Relay messages from OpenAI to browser"""
                try:
                    async for message in openai_ws:
                        data = json.loads(message)
                        event_type = data.get("type", "")

                        # Handle different event types
                        if event_type == "response.audio.delta":
                            # Start speaking animation
                            if not active_conversations[conversation_id]["speaking"]:
                                active_conversations[conversation_id]["speaking"] = True
                                asyncio.create_task(behaviors.start_speaking())
                                # Tell browser to clear queue and start fresh
                                await websocket.send_json({"type": "audio_start"})

                            # Forward audio to browser
                            await websocket.send_json({
                                "type": "audio",
                                "audio": data.get("delta", "")
                            })

                        elif event_type == "response.audio.done":
                            # Stop speaking animation
                            active_conversations[conversation_id]["speaking"] = False
                            asyncio.create_task(behaviors.stop_speaking())
                            # Notify browser to unmute after playback finishes
                            await websocket.send_json({"type": "audio_done"})

                        elif event_type == "response.audio_transcript.delta":
                            # Send transcript update
                            await websocket.send_json({
                                "type": "transcript",
                                "role": "assistant",
                                "delta": data.get("delta", "")
                            })

                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            # User's speech transcribed
                            await websocket.send_json({
                                "type": "transcript",
                                "role": "user",
                                "text": data.get("transcript", "")
                            })

                        elif event_type == "response.function_call_arguments.done":
                            # Handle tool call
                            tool_name = data.get("name", "")
                            try:
                                arguments = json.loads(data.get("arguments", "{}"))
                            except:
                                arguments = {}

                            result = await handle_tool_call(tool_name, arguments)

                            # Cancel any active response before sending tool result
                            await openai_ws.send(json.dumps({"type": "response.cancel"}))
                            await asyncio.sleep(0.1)  # Brief pause for cancellation

                            # Send tool result back to OpenAI
                            await openai_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": data.get("call_id", ""),
                                    "output": result
                                }
                            }))
                            await openai_ws.send(json.dumps({"type": "response.create"}))

                            # Notify browser
                            await websocket.send_json({
                                "type": "tool_call",
                                "name": tool_name,
                                "result": result
                            })

                        elif event_type == "error":
                            error_msg = data.get("error", {}).get("message", "Unknown error")
                            # Filter out non-critical errors
                            if "no active response" not in error_msg.lower():
                                await websocket.send_json({
                                    "type": "error",
                                    "message": error_msg
                                })
                            else:
                                print(f"Suppressed non-critical error: {error_msg}")

                except Exception as e:
                    print(f"Relay error: {e}")

            # Run both relay tasks
            await asyncio.gather(
                relay_to_openai(),
                relay_to_browser(),
                return_exceptions=True
            )

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        if conversation_id in active_conversations:
            del active_conversations[conversation_id]


# ==================== STATE STREAMING ====================

@app.websocket("/ws/reachy-state")
async def websocket_reachy_state(websocket: WebSocket):
    """Stream Reachy's state for visualization"""
    await websocket.accept()
    import math

    try:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"{REACHY_DAEMON_URL}/api/state/full",
                        timeout=2.0
                    )
                    if response.status_code == 200:
                        state = response.json()
                        head = state.get("head_pose", {})
                        antennas = state.get("antennas_position", [0, 0])

                        await websocket.send_json({
                            "yaw": math.degrees(head.get("yaw", 0)),
                            "pitch": math.degrees(head.get("pitch", 0)),
                            "roll": math.degrees(head.get("roll", 0)),
                            "antenna_left": antennas[0] if len(antennas) > 0 else 0,
                            "antenna_right": antennas[1] if len(antennas) > 1 else 0,
                            "speaking": any(c.get("speaking", False) for c in active_conversations.values())
                        })
                except httpx.RequestError:
                    await websocket.send_json({"error": "daemon_disconnected"})

                await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass


# ==================== API ENDPOINTS ====================

@app.get("/api/status")
async def status():
    """Get system status"""
    daemon_status = "unknown"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REACHY_DAEMON_URL}/api/daemon/status", timeout=5.0)
            if response.status_code == 200:
                daemon_status = "connected"
        except:
            daemon_status = "disconnected"

    return {
        "app": "le_professeur_bizarre_realtime",
        "version": "2.0.0",
        "openai_configured": bool(OPENAI_API_KEY),
        "reachy_daemon": daemon_status,
        "active_conversations": len(active_conversations)
    }


class CameraFrame(BaseModel):
    """Camera frame from browser"""
    image: str  # Base64 encoded image


@app.post("/api/camera/frame")
async def receive_camera_frame(frame: CameraFrame):
    """Receive camera frame from browser for vision analysis"""
    import time
    latest_camera_frame["frame"] = frame.image
    latest_camera_frame["timestamp"] = time.time()
    return {"status": "ok"}


@app.post("/api/vision/analyze")
async def analyze_vision(frame: CameraFrame):
    """Directly analyze an image and return French teaching content"""
    result = await describe_for_teaching(frame.image)
    return {"description": result}


@app.post("/api/behavior/{action}")
async def trigger_behavior(action: str):
    """Manually trigger a behavior"""
    if action == "wave":
        await behaviors.wave()
    elif action == "nod":
        await behaviors.nod_yes()
    elif action == "shake":
        await behaviors.shake_no()
    elif action.startswith("emotion_"):
        emotion_name = action.replace("emotion_", "")
        try:
            emotion = Emotion(emotion_name)
            await behaviors.play_emotion(emotion)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown emotion: {emotion_name}")
    elif action.startswith("dance_"):
        dance_name = action.replace("dance_", "")
        try:
            dance = Dance(dance_name)
            await behaviors.start_dance(dance)
            await asyncio.sleep(4)
            await behaviors.stop_dance()
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown dance: {dance_name}")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    return {"status": "ok", "action": action}


# ==================== MAIN UI ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Le Professeur Bizarre</title>
    <style>
        :root {
            --bg-color: #F5F5F7;
            --card-bg: #FFFFFF;
            --apple-blue: #0071E3;
            --apple-blue-hover: #0077ED;
            --text-primary: #1D1D1F;
            --text-secondary: #86868B;
            --bubble-user: #0071E3;
            --bubble-robot: #E9E9EB;
            --radius-l: 24px;
            --radius-m: 16px;
            --shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            --shadow-inner: inset 0 0 0 1px rgba(0,0,0,0.05);
            --success: #30D158;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* HEADER */
        header {
            text-align: center;
            padding: 24px 20px;
            flex-shrink: 0;
            background: rgba(245, 245, 247, 0.8);
            backdrop-filter: blur(10px);
            z-index: 10;
        }

        h1 {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.01em;
            margin-bottom: 4px;
        }

        .subtitle {
            font-size: 15px;
            color: var(--text-secondary);
            font-weight: 400;
        }

        /* MAIN LAYOUT */
        main {
            display: grid;
            grid-template-columns: 1fr 420px;
            gap: 24px;
            max-width: 1600px;
            width: 96%;
            margin: 0 auto 24px auto;
            flex-grow: 1;
            overflow: hidden;
        }

        /* LEFT COLUMN (VISUALS) */
        .visual-column {
            display: flex;
            flex-direction: column;
            gap: 20px;
            height: 100%;
            overflow: hidden;
        }

        /* Robot Viewport - The Hero Element */
        .robot-viewport {
            background: #000;
            border-radius: var(--radius-l);
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-grow: 1;
            min-height: 400px;
        }

        /* 3D Environment Simulation */
        .grid-floor {
            position: absolute;
            bottom: 0;
            width: 100%;
            height: 40%;
            background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.05) 100%);
            background-size: 40px 40px;
            background-image:
                linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px);
            transform: perspective(500px) rotateX(60deg);
            transform-origin: bottom;
            opacity: 0.3;
        }

        /* Robot Animation */
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
            100% { transform: translateY(0px); }
        }

        @keyframes blink {
            0%, 96%, 100% { height: 16px; }
            98% { height: 2px; }
        }

        .robot-container {
            position: absolute;
            top: 45%;
            left: 50%;
            transform: translate(-50%, -50%);
            transform-style: preserve-3d;
            animation: float 4s ease-in-out infinite;
        }

        .robot-body {
            width: 100px;
            height: 120px;
            background: linear-gradient(135deg, #f0f0f0 0%, #d8d8d8 50%, #c0c0c0 100%);
            border-radius: 50px 50px 30px 30px;
            position: relative;
            box-shadow:
                inset -5px -5px 20px rgba(0,0,0,0.15),
                inset 5px 5px 20px rgba(255,255,255,0.6),
                0 30px 60px rgba(0,0,0,0.4);
        }

        .robot-neck {
            width: 35px;
            height: 18px;
            background: linear-gradient(to bottom, #888, #555);
            position: absolute;
            top: -14px;
            left: 50%;
            transform: translateX(-50%);
            border-radius: 6px;
        }

        .robot-head {
            width: 90px;
            height: 65px;
            background: linear-gradient(135deg, #fafafa 0%, #e8e8e8 50%, #d0d0d0 100%);
            border-radius: 45px 45px 25px 25px;
            position: absolute;
            top: -70px;
            left: 50%;
            transform: translateX(-50%);
            transform-origin: center bottom;
            box-shadow:
                inset -4px -4px 15px rgba(0,0,0,0.12),
                inset 4px 4px 15px rgba(255,255,255,0.9),
                0 15px 40px rgba(0,0,0,0.25);
            transition: transform 0.05s ease-out;
        }

        .robot-head.speaking {
            animation: speak-pulse 0.15s infinite alternate;
        }

        @keyframes speak-pulse {
            from { filter: brightness(1); }
            to { filter: brightness(1.05); }
        }

        .robot-face {
            position: absolute;
            top: 18px;
            left: 12px;
            right: 12px;
            height: 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 10px;
        }

        .robot-eye {
            width: 16px;
            height: 16px;
            background: radial-gradient(circle at 30% 30%, #333 0%, #000 100%);
            border-radius: 50%;
            box-shadow:
                inset 2px 2px 5px rgba(255,255,255,0.3),
                0 3px 6px rgba(0,0,0,0.3);
            position: relative;
            animation: blink 4s infinite;
        }

        .robot-eye::after {
            content: '';
            position: absolute;
            top: 3px;
            left: 4px;
            width: 5px;
            height: 5px;
            background: white;
            border-radius: 50%;
        }

        .robot-antenna {
            width: 6px;
            height: 32px;
            background: linear-gradient(to bottom, #999, #666);
            position: absolute;
            top: -28px;
            border-radius: 3px;
            transform-origin: bottom center;
            transition: transform 0.05s ease-out;
        }

        .robot-antenna.left { left: 20px; }
        .robot-antenna.right { right: 20px; }

        .robot-antenna::after {
            content: '';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            width: 16px;
            height: 16px;
            background: radial-gradient(circle at 30% 30%, #0071E3 0%, #005BB5 100%);
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(0,113,227,0.6);
        }

        .robot-base {
            width: 80px;
            height: 25px;
            background: linear-gradient(to bottom, #444, #222);
            border-radius: 12px;
            position: absolute;
            bottom: -18px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        }

        /* Status Pills */
        .status-pill-container {
            position: absolute;
            bottom: 24px;
            left: 24px;
            right: 24px;
            display: flex;
            justify-content: space-between;
            z-index: 5;
        }

        .status-pill {
            background: rgba(30, 30, 30, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 8px 16px;
            border-radius: 100px;
            font-size: 13px;
            font-weight: 500;
            color: white;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ef4444;
        }
        .dot.green { background-color: #30D158; box-shadow: 0 0 10px #30D158; }
        .dot.connected { background-color: #30D158; box-shadow: 0 0 10px #30D158; }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .section-title {
            font-size: 17px;
            font-weight: 600;
        }

        .btn-text {
            color: var(--apple-blue);
            background: none;
            border: none;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
        }

        .btn-text.active {
            color: var(--success);
        }

        /* Behavior Grid */
        .behavior-section {
            background: var(--card-bg);
            border-radius: var(--radius-l);
            padding: 16px 20px;
            box-shadow: var(--shadow);
        }

        .behavior-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-top: 12px;
        }

        .behavior-btn {
            padding: 10px 8px;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 12px;
            background: #F2F2F7;
            color: var(--text-primary);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .behavior-btn:hover {
            background: var(--apple-blue);
            color: white;
            border-color: var(--apple-blue);
        }

        /* RIGHT COLUMN (CHAT) */
        .chat-column {
            background: var(--card-bg);
            border-radius: var(--radius-l);
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: 100%;
            border: 1px solid rgba(0,0,0,0.02);
        }

        .chat-header {
            padding: 20px;
            border-bottom: 1px solid #E5E5EA;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
        }

        /* Camera in Chat */
        .camera-in-chat {
            padding: 12px 16px;
            border-bottom: 1px solid #E5E5EA;
            background: #FAFAFA;
        }

        .camera-in-chat .camera-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0;
            margin-bottom: 8px;
            border: none;
            background: none;
        }

        .camera-label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .camera-preview {
            position: relative;
            width: 100%;
            height: 200px;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
        }

        .camera-preview video {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .camera-preview canvas {
            display: none;
        }

        .camera-preview .webcam-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #1a1a1a;
            color: #666;
            gap: 6px;
            font-size: 12px;
        }

        .camera-preview .webcam-overlay.hidden {
            display: none;
        }

        .camera-preview .webcam-crosshair {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 50px;
            height: 50px;
            border: 2px solid rgba(0,113,227,0.6);
            border-radius: 50%;
            display: none;
        }

        .chat-area {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        /* Messages */
        .message {
            max-width: 85%;
            padding: 12px 18px;
            font-size: 16px;
            line-height: 1.4;
            position: relative;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-robot {
            align-self: flex-start;
            background-color: var(--bubble-robot);
            color: #000;
            border-radius: 20px 20px 20px 4px;
        }

        .message-user {
            align-self: flex-end;
            background-color: var(--bubble-user);
            color: white;
            border-radius: 20px 20px 4px 20px;
            box-shadow: 0 2px 10px rgba(0, 113, 227, 0.2);
        }

        .message-label {
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 4px;
            margin-left: 4px;
            font-weight: 500;
        }

        .tool-call {
            background: rgba(0,113,227,0.1);
            border: 1px solid var(--apple-blue);
            color: var(--apple-blue);
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
            margin: 8px 0;
        }

        /* Input Area */
        .input-area {
            padding: 20px;
            border-top: 1px solid #E5E5EA;
            background: #FFFFFF;
        }

        .talk-btn {
            width: 100%;
            padding: 18px;
            background: var(--apple-blue);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
        }

        .talk-btn:hover {
            background-color: var(--apple-blue-hover);
            transform: translateY(-1px);
        }

        .talk-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .talk-btn.listening {
            background: #FF3B30;
            box-shadow: 0 4px 12px rgba(255, 59, 48, 0.3);
            animation: pulse-btn 1s infinite;
        }

        @keyframes pulse-btn {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        .talk-btn svg {
            width: 22px;
            height: 22px;
            fill: white;
        }

        /* Connection Overlay */
        .connection-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(245, 245, 247, 0.95);
            backdrop-filter: blur(20px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .connection-overlay.hidden { display: none; }

        .connection-box {
            text-align: center;
            padding: 48px;
            background: white;
            border-radius: var(--radius-l);
            box-shadow: var(--shadow);
            max-width: 400px;
        }

        .connection-box h2 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .connection-box p {
            color: var(--text-secondary);
            margin-bottom: 32px;
            line-height: 1.5;
        }

        .connect-btn {
            padding: 16px 48px;
            background: var(--apple-blue);
            border: none;
            border-radius: 50px;
            color: white;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.3);
        }

        .connect-btn:hover {
            background: var(--apple-blue-hover);
            transform: translateY(-2px);
        }

        /* Responsive */
        @media (max-width: 900px) {
            main {
                grid-template-columns: 1fr;
                overflow-y: auto;
            }
            .robot-viewport {
                height: 350px;
                flex-grow: 0;
            }
        }
    </style>
</head>
<body>

    <div class="connection-overlay" id="connectionOverlay">
        <div class="connection-box">
            <h2>Bonjour!</h2>
            <p>Ready to learn French with Le Professeur Bizarre?<br>Make sure to allow microphone access.</p>
            <button class="connect-btn" onclick="startConversation()">Start Conversation</button>
        </div>
    </div>

    <header>
        <h1>Le Professeur Bizarre</h1>
        <div class="subtitle">Real-time French Conversation with Reachy Mini</div>
    </header>

    <main>
        <!-- Left Column: Visuals -->
        <section class="visual-column">

            <!-- Robot View -->
            <div class="robot-viewport">
                <div class="grid-floor"></div>

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

                <div class="status-pill-container">
                    <div class="status-pill">
                        <span class="dot" id="daemonDot"></span>
                        <span id="daemonStatus">Connecting...</span>
                    </div>
                    <div class="status-pill">
                        <span class="dot" id="aiDot"></span>
                        <span id="aiStatus">Disconnected</span>
                    </div>
                </div>
            </div>

            <!-- Behavior Buttons -->
            <div class="behavior-section">
                <div class="section-title">Robot Actions</div>
                <div class="behavior-grid">
                    <button class="behavior-btn" onclick="triggerBehavior('wave')">Wave</button>
                    <button class="behavior-btn" onclick="triggerBehavior('nod')">Nod</button>
                    <button class="behavior-btn" onclick="triggerBehavior('shake')">Shake</button>
                    <button class="behavior-btn" onclick="triggerBehavior('emotion_happy')">Happy</button>
                    <button class="behavior-btn" onclick="triggerBehavior('emotion_thinking')">Think</button>
                    <button class="behavior-btn" onclick="triggerBehavior('emotion_excited')">Excited</button>
                    <button class="behavior-btn" onclick="triggerBehavior('dance_celebration')">Dance!</button>
                    <button class="behavior-btn" onclick="triggerBehavior('dance_french_waltz')">Waltz</button>
                </div>
            </div>

        </section>

        <!-- Right Column: Conversation -->
        <section class="chat-column">
            <div class="chat-header">
                <div class="section-title">Conversation</div>
            </div>

            <!-- Camera at top of chat -->
            <div class="camera-in-chat">
                <div class="camera-header">
                    <span class="camera-label">Show me objects!</span>
                    <button class="btn-text" id="camToggle" onclick="toggleCamera()">Enable Camera</button>
                </div>
                <div class="camera-preview">
                    <video id="webcam" autoplay playsinline muted></video>
                    <canvas id="webcamCanvas"></canvas>
                    <div class="webcam-crosshair" id="crosshair"></div>
                    <div class="webcam-overlay" id="webcamOverlay">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                            <circle cx="12" cy="13" r="4"></circle>
                        </svg>
                        <span>Camera off</span>
                    </div>
                </div>
            </div>

            <div class="chat-area" id="transcript">
                <div style="align-self: flex-start; width: 100%;">
                    <div class="message-label">Le Professeur</div>
                    <div class="message message-robot">
                        Bonjour! Je suis Le Professeur Bizarre. Click the button below and start speaking to me in English - I'll teach you French!
                    </div>
                </div>
            </div>

            <div class="input-area">
                <button class="talk-btn" id="talkBtn" onclick="toggleTalking()" disabled>
                    <svg viewBox="0 0 24 24">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                    </svg>
                    <span id="talkText">Click to Talk</span>
                </button>
            </div>
        </section>
    </main>

    <script>
        // ==================== STATE ====================
        let ws = null;
        let stateWs = null;
        let audioContext = null;
        let mediaStream = null;
        let isListening = false;
        let isAISpeaking = false;

        const robotHead = document.getElementById('robotHead');
        const antennaLeft = document.getElementById('antennaLeft');
        const antennaRight = document.getElementById('antennaRight');
        const daemonDot = document.getElementById('daemonDot');
        const daemonStatus = document.getElementById('daemonStatus');
        const aiDot = document.getElementById('aiDot');
        const aiStatus = document.getElementById('aiStatus');
        const transcript = document.getElementById('transcript');
        const talkBtn = document.getElementById('talkBtn');
        const talkText = document.getElementById('talkText');

        // ==================== ROBOT VISUALIZATION ====================
        function connectStateWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            stateWs = new WebSocket(`${protocol}//${window.location.host}/ws/reachy-state`);

            stateWs.onopen = () => {
                daemonDot.classList.add('connected');
                daemonStatus.textContent = 'Live';
            };

            stateWs.onmessage = (event) => {
                const state = JSON.parse(event.data);
                if (state.error) {
                    daemonDot.classList.remove('connected');
                    daemonStatus.textContent = 'Offline';
                    return;
                }
                updateRobotVisualization(state);
            };

            stateWs.onclose = () => {
                daemonDot.classList.remove('connected');
                daemonStatus.textContent = 'Disconnected';
                setTimeout(connectStateWebSocket, 2000);
            };
        }

        function updateRobotVisualization(state) {
            const { yaw, pitch, roll, antenna_left, antenna_right, speaking } = state;

            robotHead.style.transform = `
                translateX(-50%)
                rotateY(${yaw * 1.5}deg)
                rotateX(${-pitch * 1.5}deg)
                rotateZ(${roll * 1.5}deg)
            `;

            antennaLeft.style.transform = `rotate(${antenna_left * 45}deg)`;
            antennaRight.style.transform = `rotate(${-antenna_right * 45}deg)`;

            if (speaking) {
                robotHead.classList.add('speaking');
            } else {
                robotHead.classList.remove('speaking');
            }
        }

        // ==================== AUDIO ====================
        async function initAudio() {
            try {
                audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 24000
                });

                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        sampleRate: 24000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    }
                });

                return true;
            } catch (e) {
                console.error('Audio init error:', e);
                alert('Could not access microphone: ' + e.message);
                return false;
            }
        }

        function startRecording() {
            if (!mediaStream) return;

            const source = audioContext.createMediaStreamSource(mediaStream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!isListening || !ws || ws.readyState !== WebSocket.OPEN || isAISpeaking) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
                }

                const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)));
                ws.send(JSON.stringify({ type: 'audio', audio: base64 }));
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            window.audioProcessor = processor;
            window.audioSource = source;
        }

        function stopRecording() {
            if (window.audioProcessor) {
                window.audioProcessor.disconnect();
                window.audioSource.disconnect();
            }
        }

        // Queue for sequential audio playback
        let playbackQueue = [];
        let currentlyPlaying = false;

        async function playAudio(base64Audio) {
            if (!audioContext) return;
            playbackQueue.push(base64Audio);
            if (!currentlyPlaying) processAudioQueue();
        }

        async function processAudioQueue() {
            if (playbackQueue.length === 0) {
                currentlyPlaying = false;
                isAISpeaking = false;
                return;
            }

            currentlyPlaying = true;
            isAISpeaking = true;

            const base64Audio = playbackQueue.shift();
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const pcm16 = new Int16Array(bytes.buffer);
            const float32 = new Float32Array(pcm16.length);
            for (let i = 0; i < pcm16.length; i++) {
                float32[i] = pcm16[i] / 32768;
            }

            const audioBuffer = audioContext.createBuffer(1, float32.length, 24000);
            audioBuffer.getChannelData(0).set(float32);

            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = () => processAudioQueue();
            source.start();
        }

        // ==================== WEBSOCKET ====================
        function connectRealtimeWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/realtime`);

            ws.onopen = () => {
                aiDot.classList.add('connected');
                aiStatus.textContent = 'Connected';
                talkBtn.disabled = false;
            };

            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'connected') {
                    addMessage('assistant', data.message);
                }
                else if (data.type === 'audio_start') {
                    playbackQueue = [];
                    isAISpeaking = true;
                }
                else if (data.type === 'audio') {
                    await playAudio(data.audio);
                }
                else if (data.type === 'transcript') {
                    if (data.role === 'user' && data.text) {
                        addMessage('user', data.text);
                    } else if (data.role === 'assistant' && data.delta) {
                        appendToLastMessage(data.delta);
                    }
                }
                else if (data.type === 'tool_call') {
                    addToolCall(data.name, data.result);
                }
                else if (data.type === 'error') {
                    addMessage('assistant', 'Error: ' + data.message);
                }
                else if (data.type === 'audio_done') {
                    setTimeout(() => {
                        if (playbackQueue.length === 0) isAISpeaking = false;
                    }, 300);
                }
            };

            ws.onclose = () => {
                aiDot.classList.remove('connected');
                aiStatus.textContent = 'Disconnected';
                talkBtn.disabled = true;
            };

            ws.onerror = (e) => console.error('WebSocket error:', e);
        }

        // ==================== UI ====================
        let lastAssistantMessage = null;

        function addMessage(role, text) {
            const wrapper = document.createElement('div');
            wrapper.style.cssText = role === 'user'
                ? 'align-self: flex-end; width: 100%; display: flex; flex-direction: column; align-items: flex-end;'
                : 'align-self: flex-start; width: 100%;';

            const label = document.createElement('div');
            label.className = 'message-label';
            label.style.marginRight = role === 'user' ? '4px' : '0';
            label.textContent = role === 'user' ? 'You' : 'Le Professeur';

            const msg = document.createElement('div');
            msg.className = `message ${role === 'user' ? 'message-user' : 'message-robot'}`;
            msg.textContent = text;

            wrapper.appendChild(label);
            wrapper.appendChild(msg);
            transcript.appendChild(wrapper);
            transcript.scrollTop = transcript.scrollHeight;

            if (role === 'assistant') lastAssistantMessage = msg;
        }

        function appendToLastMessage(delta) {
            if (!lastAssistantMessage) {
                addMessage('assistant', delta);
            } else {
                lastAssistantMessage.textContent += delta;
                transcript.scrollTop = transcript.scrollHeight;
            }
        }

        function addToolCall(name, result) {
            const div = document.createElement('div');
            div.className = 'tool-call';
            div.textContent = `${name}: ${result}`;
            transcript.appendChild(div);
            transcript.scrollTop = transcript.scrollHeight;
            lastAssistantMessage = null;
        }

        function toggleTalking() {
            if (isListening) {
                stopTalking();
            } else {
                startTalking();
            }
        }

        function startTalking() {
            if (audioContext && audioContext.state === 'suspended') {
                audioContext.resume();
            }

            isListening = true;
            talkBtn.classList.add('listening');
            talkText.textContent = 'Listening...';
            startRecording();
            lastAssistantMessage = null;
        }

        function stopTalking() {
            isListening = false;
            talkBtn.classList.remove('listening');
            talkText.textContent = 'Click to Talk';
            stopRecording();
        }

        async function startConversation() {
            const overlay = document.getElementById('connectionOverlay');
            if (await initAudio()) {
                overlay.classList.add('hidden');
                connectRealtimeWebSocket();
            }
        }

        async function triggerBehavior(action) {
            try {
                await fetch(`/api/behavior/${action}`, { method: 'POST' });
            } catch (e) {
                console.error('Behavior error:', e);
            }
        }

        // Start state streaming immediately
        connectStateWebSocket();

        // ==================== WEBCAM / VISION ====================
        let cameraStream = null;
        let cameraEnabled = false;
        let frameInterval = null;

        const webcam = document.getElementById('webcam');
        const webcamCanvas = document.getElementById('webcamCanvas');
        const webcamOverlay = document.getElementById('webcamOverlay');
        const camToggle = document.getElementById('camToggle');
        const crosshair = document.getElementById('crosshair');

        async function toggleCamera() {
            if (cameraEnabled) {
                stopCamera();
            } else {
                await startCamera();
            }
        }

        async function startCamera() {
            try {
                cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: 640, height: 480 }
                });
                webcam.srcObject = cameraStream;
                webcamOverlay.classList.add('hidden');
                crosshair.style.display = 'block';
                camToggle.textContent = 'Camera On';
                camToggle.classList.add('active');
                cameraEnabled = true;
                startFrameCapture();
            } catch (e) {
                console.error('Camera error:', e);
                alert('Could not access camera: ' + e.message);
            }
        }

        function stopCamera() {
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
                cameraStream = null;
            }
            webcam.srcObject = null;
            webcamOverlay.classList.remove('hidden');
            crosshair.style.display = 'none';
            camToggle.textContent = 'Enable Camera';
            camToggle.classList.remove('active');
            cameraEnabled = false;

            if (frameInterval) {
                clearInterval(frameInterval);
                frameInterval = null;
            }
        }

        function startFrameCapture() {
            frameInterval = setInterval(() => {
                if (!cameraEnabled) return;
                captureAndSendFrame();
            }, 2000);
        }

        function captureAndSendFrame() {
            if (!webcam.videoWidth) return;

            const ctx = webcamCanvas.getContext('2d');
            webcamCanvas.width = 640;
            webcamCanvas.height = 480;
            ctx.drawImage(webcam, 0, 0, 640, 480);

            const base64 = webcamCanvas.toDataURL('image/jpeg', 0.7);
            fetch('/api/camera/frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: base64 })
            }).catch(e => console.log('Frame send error:', e));
        }
    </script>
</body>
</html>
"""


# ==================== MAIN ====================

def run_server(host: str = "0.0.0.0", port: int = 5174):
    """Run the realtime conversation server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_server()
