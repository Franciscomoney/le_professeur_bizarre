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
except ImportError:
    from behaviors import ReachyBehaviors, Emotion, Dance


# ==================== CONFIGURATION ====================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REACHY_DAEMON_URL = os.getenv("REACHY_DAEMON_URL", "http://localhost:8000")
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

# Le Professeur Bizarre System Prompt
SYSTEM_PROMPT = """You are Le Professeur Bizarre, a friendly robot language teacher. You teach French to English speakers.

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

CRITICAL: Your FIRST message when someone connects should ONLY be a short greeting like:
"Bonjour! I'm Reachy, your French language buddy. What would you like to learn today?"

Then WAIT for the user to respond. Do NOT keep talking without input."""


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
    }
]


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
                            await websocket.send_json({
                                "type": "error",
                                "message": data.get("error", {}).get("message", "Unknown error")
                            })

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
    <title>Le Professeur Bizarre - Real-time Conversation</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --france-blue: #002395;
            --france-red: #ED2939;
            --france-white: #FFFFFF;
            --gold: #D4AF37;
            --cream: #FDF8F0;
            --dark: #1a1a2e;
            --gray: #6b7280;
            --success: #10B981;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--dark) 0%, #252542 100%);
            min-height: 100vh;
            color: white;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1.5rem;
        }

        header {
            text-align: center;
            margin-bottom: 2rem;
        }

        header h1 {
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--france-blue), var(--france-white), var(--france-red));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        header .subtitle {
            color: var(--gold);
            font-size: 1rem;
            margin-top: 0.5rem;
        }

        .main-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        .panel {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .panel h2 {
            font-size: 0.9rem;
            color: var(--gold);
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        /* Robot Visualization */
        .robot-stage {
            background: linear-gradient(180deg, #0a0a15 0%, #1a1a2e 100%);
            border-radius: 16px;
            height: 350px;
            position: relative;
            overflow: hidden;
            perspective: 800px;
        }

        .stage-grid {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 120px;
            background:
                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            transform: rotateX(60deg);
            transform-origin: bottom;
        }

        .robot-container {
            position: absolute;
            top: 45%;
            left: 50%;
            transform: translate(-50%, -50%);
            transform-style: preserve-3d;
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
            background: radial-gradient(circle at 30% 30%, var(--gold) 0%, #b8960a 100%);
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(212,175,55,0.6);
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

        /* Status */
        .status-bar {
            position: absolute;
            bottom: 12px;
            left: 12px;
            right: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: rgba(0,0,0,0.6);
            border-radius: 20px;
            font-size: 0.75rem;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ef4444;
        }

        .status-dot.connected { background: var(--success); animation: pulse 2s infinite; }
        .status-dot.speaking { background: var(--france-red); animation: pulse 0.3s infinite; }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }

        /* Conversation Panel */
        .conversation-panel {
            display: flex;
            flex-direction: column;
            height: 500px;
        }

        .transcript {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            margin-bottom: 1rem;
        }

        .message {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background: var(--france-blue);
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }

        .message.assistant {
            background: linear-gradient(135deg, var(--france-red), #c41e30);
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }

        .message .role {
            font-size: 0.7rem;
            opacity: 0.7;
            margin-bottom: 0.25rem;
        }

        .message .text {
            font-size: 0.95rem;
            line-height: 1.4;
        }

        .tool-call {
            background: rgba(212,175,55,0.2);
            border: 1px solid var(--gold);
            color: var(--gold);
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            font-size: 0.8rem;
            margin: 0.5rem 0;
        }

        /* Controls */
        .controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .talk-btn {
            flex: 1;
            padding: 1.25rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
        }

        .talk-btn.inactive {
            background: linear-gradient(135deg, var(--france-blue), #3355AA);
            color: white;
        }

        .talk-btn.listening {
            background: linear-gradient(135deg, var(--france-red), #c41e30);
            color: white;
            animation: pulse-btn 1s infinite;
        }

        @keyframes pulse-btn {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        .talk-btn:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .talk-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        /* Behavior Buttons */
        .behavior-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .behavior-btn {
            padding: 0.6rem;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .behavior-btn:hover {
            background: rgba(255,255,255,0.15);
            border-color: var(--gold);
        }

        /* Connection Status */
        .connection-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
        }

        .connection-overlay.hidden { display: none; }

        .connection-box {
            text-align: center;
            padding: 3rem;
        }

        .connection-box h2 {
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            margin-bottom: 1rem;
        }

        .connection-box p {
            color: var(--gray);
            margin-bottom: 2rem;
        }

        .connect-btn {
            padding: 1rem 2.5rem;
            background: linear-gradient(135deg, var(--france-blue), var(--france-red));
            border: none;
            border-radius: 30px;
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .connect-btn:hover {
            transform: scale(1.05);
            filter: brightness(1.1);
        }

        @media (max-width: 900px) {
            .main-layout {
                grid-template-columns: 1fr;
            }
            .robot-stage { height: 280px; }
        }
    </style>
</head>
<body>
    <div class="connection-overlay" id="connectionOverlay">
        <div class="connection-box">
            <h2>Bonjour! Ready to chat?</h2>
            <p>Click below to start a real-time conversation with Le Professeur Bizarre.<br>
            Make sure to allow microphone access!</p>
            <button class="connect-btn" onclick="startConversation()">Start Conversation</button>
        </div>
    </div>

    <div class="container">
        <header>
            <h1>Le Professeur Bizarre</h1>
            <p class="subtitle">Real-time French Conversation with Reachy Mini</p>
        </header>

        <div class="main-layout">
            <div class="panel">
                <h2>Reachy Mini - Live</h2>
                <div class="robot-stage">
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
                            <div class="status-dot" id="daemonDot"></div>
                            <span id="daemonStatus">Connecting...</span>
                        </div>
                        <div class="status-indicator">
                            <div class="status-dot" id="aiDot"></div>
                            <span id="aiStatus">Disconnected</span>
                        </div>
                    </div>
                </div>

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

            <div class="panel conversation-panel">
                <h2>Conversation</h2>
                <div class="transcript" id="transcript">
                    <div class="message assistant">
                        <div class="role">Le Professeur</div>
                        <div class="text">Bonjour! Je suis Le Professeur Bizarre. Click the button below and start speaking to me in English - I'll teach you French!</div>
                    </div>
                </div>

                <div class="controls">
                    <button class="talk-btn inactive" id="talkBtn" onclick="toggleTalking()" disabled>
                        <span id="talkIcon">🎤</span>
                        <span id="talkText">Click to Talk</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ==================== STATE ====================
        let ws = null;
        let stateWs = null;
        let audioContext = null;
        let mediaStream = null;
        let mediaRecorder = null;
        let isListening = false;
        let isAISpeaking = false;  // Track when AI is outputting audio
        let audioQueue = [];
        let isPlaying = false;
        let inputPaused = false;  // Pause input while AI speaks

        const robotHead = document.getElementById('robotHead');
        const antennaLeft = document.getElementById('antennaLeft');
        const antennaRight = document.getElementById('antennaRight');
        const daemonDot = document.getElementById('daemonDot');
        const daemonStatus = document.getElementById('daemonStatus');
        const aiDot = document.getElementById('aiDot');
        const aiStatus = document.getElementById('aiStatus');
        const transcript = document.getElementById('transcript');
        const talkBtn = document.getElementById('talkBtn');
        const talkIcon = document.getElementById('talkIcon');
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

            const audioTracks = mediaStream.getAudioTracks();
            if (audioTracks.length === 0) return;

            // Use AudioWorklet or ScriptProcessor for raw PCM
            const source = audioContext.createMediaStreamSource(mediaStream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                // Don't send audio if AI is speaking (prevents feedback loop)
                if (!isListening || !ws || ws.readyState !== WebSocket.OPEN || isAISpeaking) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Convert to 16-bit PCM
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
                }

                // Convert to base64
                const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)));

                ws.send(JSON.stringify({
                    type: 'audio',
                    audio: base64
                }));
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

            // Add to queue
            playbackQueue.push(base64Audio);

            // If not already playing, start processing queue
            if (!currentlyPlaying) {
                processAudioQueue();
            }
        }

        async function processAudioQueue() {
            if (playbackQueue.length === 0) {
                currentlyPlaying = false;
                isAISpeaking = false;
                return;
            }

            currentlyPlaying = true;
            isAISpeaking = true;  // Mute input while playing

            const base64Audio = playbackQueue.shift();

            // Decode base64 to PCM16
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const pcm16 = new Int16Array(bytes.buffer);

            // Convert to float32
            const float32 = new Float32Array(pcm16.length);
            for (let i = 0; i < pcm16.length; i++) {
                float32[i] = pcm16[i] / 32768;
            }

            // Create audio buffer
            const audioBuffer = audioContext.createBuffer(1, float32.length, 24000);
            audioBuffer.getChannelData(0).set(float32);

            // Play
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);

            source.onended = () => {
                // Process next in queue
                processAudioQueue();
            };

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
                    // New response starting - clear any old audio
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
                    // AI finished speaking - wait then allow input again
                    setTimeout(() => {
                        if (playbackQueue.length === 0) {
                            isAISpeaking = false;
                        }
                    }, 300);
                }
            };

            ws.onclose = () => {
                aiDot.classList.remove('connected');
                aiStatus.textContent = 'Disconnected';
                talkBtn.disabled = true;
            };

            ws.onerror = (e) => {
                console.error('WebSocket error:', e);
            };
        }

        // ==================== UI ====================
        let lastAssistantMessage = null;

        function addMessage(role, text) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            div.innerHTML = `
                <div class="role">${role === 'user' ? 'You' : 'Le Professeur'}</div>
                <div class="text">${text}</div>
            `;
            transcript.appendChild(div);
            transcript.scrollTop = transcript.scrollHeight;

            if (role === 'assistant') {
                lastAssistantMessage = div.querySelector('.text');
            }
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
            talkBtn.classList.remove('inactive');
            talkBtn.classList.add('listening');
            talkIcon.textContent = '🔴';
            talkText.textContent = 'Listening...';

            startRecording();
            lastAssistantMessage = null;
        }

        function stopTalking() {
            isListening = false;
            talkBtn.classList.remove('listening');
            talkBtn.classList.add('inactive');
            talkIcon.textContent = '🎤';
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
