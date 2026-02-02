# Le Professeur Bizarre 🇫🇷🤖🇺🇸

> Real-time French conversation with an expressive robot teacher that can SEE!

**Le Professeur Bizarre** transforms your Reachy Mini into an eccentric French language teacher with real-time voice conversation, computer vision, expressive animations, and rich behaviors.

## Live Demo

**Try it now:** [https://professeur.experiment.franciscocordobaotalora.com](https://professeur.experiment.franciscocordobaotalora.com)

## Features

### 🎙️ Real-time Voice Conversation
- **OpenAI Realtime API** for natural back-and-forth voice chat
- **Live transcription** displayed as iMessage-style chat bubbles
- **Echo cancellation** - mutes input while AI speaks
- Speak English, learn French naturally!

### 👁️ Computer Vision
- **NVIDIA Nemotron VL** for object recognition
- **Camera preview in chat** - Show objects and see the camera feed right above the conversation
- **Real-time webcam feed** with targeting crosshair
- Just say "What is this?" or "Look at this" while holding an object

### 🤖 Expressive Robot Behaviors
- **Floating animation** - Subtle idle movement with blinking eyes
- **Speech animation** - Visual feedback while talking
- **Emotions** - Happy, sad, surprised, thinking, excited, confused, proud
- **Dances** - French waltz, celebration, thinking groove, bonjour bob
- **Gestures** - Wave, nod yes, shake no

### 🎯 AI-Triggered Actions
The AI naturally triggers robot behaviors during conversation:
- Waves when greeting
- Shows excitement when you learn something
- Does a celebration dance when you nail a phrase
- Shows "thinking" emotion while analyzing images
- Expresses confusion at American customs

### 🎨 Modern Apple-Style UI
- Clean, minimal design with light theme
- 3D robot visualization with metallic shading
- iMessage-style chat bubbles (blue for user, gray for robot)
- Camera integrated at top of chat panel
- Responsive layout for all screen sizes

## Quick Start

### 1. Start Reachy Daemon
```bash
# Headless simulation (no hardware needed)
reachy-mini-daemon --mockup-sim

# Or with MuJoCo visualization
reachy-mini-daemon --sim

# Or with real hardware
reachy-mini-daemon
```

### 2. Set Environment Variables
```bash
export OPENAI_API_KEY="sk-your-openai-key"
export OPENROUTER_API_KEY="sk-or-your-openrouter-key"  # For vision
export REACHY_DAEMON_URL="http://localhost:8000"  # optional
```

### 3. Run Le Professeur
```bash
cd le_professeur_bizarre
python3 realtime_app.py
```

### 4. Open Browser
Go to **http://localhost:5174**

1. Click "Start Conversation"
2. Allow microphone access
3. Click "Click to Talk" and say hello!

## Example Interactions

Try saying:
- "Hello, can you teach me some French?"
- "How do I say 'I love cheese' in French?"
- "What's a fun cultural fact about France?"
- "Do a little dance for me!"
- "How do French people greet each other?"

### Vision Examples
Enable the camera and try:
- Hold up an apple: "What is this?"
- Show your coffee mug: "Look at this!"
- Point to any object: "Can you see what I'm holding?"

## API Endpoints

### Behaviors
```
POST /api/behavior/wave
POST /api/behavior/nod
POST /api/behavior/shake
POST /api/behavior/emotion_happy
POST /api/behavior/emotion_excited
POST /api/behavior/emotion_thinking
POST /api/behavior/dance_celebration
POST /api/behavior/dance_french_waltz
```

### Status
```
GET /api/status
```

### Vision
```
POST /api/camera/frame    - Receive camera frame from browser
POST /api/vision/analyze  - Analyze image and get French teaching
```

### WebSockets
```
WS /ws/realtime      - Voice conversation relay
WS /ws/reachy-state  - Robot state streaming (20 FPS)
```

## Architecture

```
                              OpenAI Realtime API
                                     ^
                                     | WebSocket (voice)
                                     |
Browser <--WebSocket--> FastAPI Server --HTTP--> OpenRouter (Nemotron VL)
   |                          |                        (vision)
   | Camera frames            v
   +--------------------> Reachy Daemon
                              |
                              v
                      Reachy Mini Robot
```

### Layered Motion System
1. **Breathing** (base) - Always running, subtle idle animation
2. **Face tracking** (optional) - Follows detected faces
3. **Primary motion** - Emotions, dances, goto poses
4. **Speech wobble** (top) - Reactive movement while speaking

## Project Structure

```
le_professeur_bizarre/
├── realtime_app.py      # Main server with OpenAI Realtime + Vision
├── vision.py            # NVIDIA Nemotron VL vision module
├── behaviors.py         # Robot animation system
├── integrated_server.py # Legacy translation-only mode
├── lessons.py           # Structured French lessons
├── llm.py              # OpenRouter/Nemotron integration
└── main.py             # ReachyMiniApp base class
```

## Tech Stack

- **Robot**: [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) by Pollen Robotics
- **Voice AI**: [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- **Vision AI**: [NVIDIA Nemotron VL](https://openrouter.ai/nvidia/nemotron-nano-12b-v2-vl) via OpenRouter
- **Backend**: FastAPI + WebSockets
- **Frontend**: Vanilla JS + Web Audio API + WebRTC (camera)
- **Simulation**: MuJoCo physics (via reachy-mini-daemon)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key for Realtime voice |
| `OPENROUTER_API_KEY` | required | OpenRouter key for vision (Nemotron VL) |
| `REACHY_DAEMON_URL` | `http://localhost:8000` | Reachy daemon address |

## Legacy Mode

The original translation-only mode is still available:
```bash
python3 integrated_server.py  # Runs on port 5173
```

This provides:
- Text/voice input → French translation
- Structured French lessons
- Cultural facts from NVIDIA Nemotron

## Contest Entry

Created for the **Reachy Mini App Contest 2025** by Pollen Robotics and Hugging Face.

## License

MIT License - Feel free to remix and share!

---

*Built with ❤️ and a slight obsession with French cheese*
