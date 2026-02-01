# Le Professeur Bizarre 🇫🇷🤖🇺🇸

> Real-time French conversation with an expressive robot teacher

**Le Professeur Bizarre** transforms your Reachy Mini into an eccentric French language teacher with real-time voice conversation, expressive animations, and rich behaviors.

## Features

### 🎙️ Real-time Voice Conversation
- **OpenAI Realtime API** for natural back-and-forth voice chat
- **Live transcription** of both user and AI speech
- **Echo cancellation** - mutes input while AI speaks
- Speak English, learn French naturally!

### 🤖 Expressive Robot Behaviors
- **Breathing animation** - Subtle idle movement when not speaking
- **Speech wobble** - Head and antenna movements while talking
- **Emotions** - Happy, sad, surprised, thinking, excited, confused, proud
- **Dances** - French waltz, celebration, thinking groove, bonjour bob
- **Gestures** - Wave, nod yes, shake no

### 🎯 AI-Triggered Actions
The AI naturally triggers robot behaviors during conversation:
- Waves when greeting
- Shows excitement when you learn something
- Does a celebration dance when you nail a phrase
- Expresses confusion at American customs

### 📺 Live Visualization
- Real-time 3D robot view in browser
- WebSocket streaming at 20 FPS
- See every head tilt and antenna wiggle

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

### WebSockets
```
WS /ws/realtime      - Voice conversation relay
WS /ws/reachy-state  - Robot state streaming (20 FPS)
```

## Architecture

```
Browser <--WebSocket--> FastAPI Server <--WebSocket--> OpenAI Realtime API
                              |
                              v
                        Reachy Daemon
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
├── realtime_app.py      # Main server with OpenAI Realtime
├── behaviors.py         # Robot animation system
├── integrated_server.py # Legacy translation-only mode
├── lessons.py           # Structured French lessons
├── llm.py              # OpenRouter/Nemotron integration
└── main.py             # ReachyMiniApp base class
```

## Tech Stack

- **Robot**: [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) by Pollen Robotics
- **Voice AI**: [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- **Backend**: FastAPI + WebSockets
- **Frontend**: Vanilla JS + Web Audio API
- **Simulation**: MuJoCo physics (via reachy-mini-daemon)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key for Realtime |
| `REACHY_DAEMON_URL` | `http://localhost:8000` | Reachy daemon address |
| `OPENROUTER_API_KEY` | optional | For legacy translation mode |

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
