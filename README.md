# Le Professeur Bizarre 🇫🇷🤖🇺🇸

> A quirky Franco-American cultural teacher for Reachy Mini

**Le Professeur Bizarre** transforms your Reachy Mini into an eccentric language teacher who translates English to French while sharing bizarre cultural facts about France and the United States.

## Features

### 🎭 Free Translation Mode
- **Real-time Translation**: Speak or type English, get French translations
- **Voice Input**: Click the mic button and speak naturally
- **Voice Output**: Reachy speaks the French translation using TTS
- **Bizarre Cultural Facts**: Learn unusual tidbits about Franco-American cultural differences
- **Pronunciation Tips**: Get helpful tips on how to sound more French

### 📚 Structured French Lessons
- **4 Complete Lessons**: Greetings, Restaurant, Essential Phrases, Romance
- **23 Phrases Total**: Each with pronunciation guides and cultural context
- **Progress Tracking**: Visual progress bar as you learn
- **Interactive Teaching**: Reachy animates while teaching each phrase

### 🤖 Live Reachy Visualization
- **Real-time 3D View**: See Reachy's head and antenna movements live
- **WebSocket Streaming**: 20 FPS state updates for smooth animation
- **Expressive Animations**: Head tilts, nods, shakes, waves, and antenna wiggles
- **Interactive Controls**: Make Reachy wave, nod, shake, or dance!

## Demo

### Translation Mode
Say something in English like:
- "Hello, how are you?" → *Bonjour, comment allez-vous?*
- "I love cheese" → *J'adore le fromage*
- "Where is the bathroom?" → *Où sont les toilettes?*

And Le Professeur will not only translate but also share a bizarre fact like:

> "In France, it's considered extremely rude to enter a shop without saying 'Bonjour'. Americans often skip this, causing French shopkeepers to silently judge them."

### Lesson Mode
Learn structured phrases across 4 categories:
- 👋 **Greetings & Basics** - Hello, goodbye, please, thank you
- 🍽️ **At the Restaurant** - Ordering, the check, compliments
- 🆘 **Essential Phrases** - Getting help, directions, emergencies
- ❤️ **Romance & Compliments** - Because it's France, after all!

## Installation

```bash
# Clone the repository
git clone https://github.com/Franciscomoney/le_professeur_bizarre

# Install dependencies
cd le_professeur_bizarre
pip install -e .
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required: OpenRouter API key
export OPENROUTER_API_KEY="your-key-here"

# Optional: Reachy daemon URL (default: http://localhost:8000)
export REACHY_DAEMON_URL="http://localhost:8000"

# Optional: Choose a specific model (default: nvidia/nemotron-3-nano-30b-a3b)
export NEMOTRON_MODEL="nvidia/nemotron-3-nano-30b-a3b"
```

## Running

### Start the Reachy Daemon

```bash
# With real hardware
reachy-mini-daemon

# In simulation (no hardware required)
reachy-mini-daemon --sim

# Headless simulation (no MuJoCo window)
reachy-mini-daemon --mockup-sim
```

### Start Le Professeur Bizarre

```bash
# Run the integrated server
cd le_professeur_bizarre
python integrated_server.py

# Or run as a module
python -m le_professeur_bizarre.integrated_server
```

Open **http://localhost:5173** to see Le Professeur in action!

## API Endpoints

### Translation
- `POST /api/translate` - Translate English to French with cultural facts

### Lessons
- `GET /api/lessons` - List all available lessons
- `GET /api/lessons/{id}` - Get a specific lesson with all phrases
- `GET /api/lessons/{id}/phrase/{index}` - Get a specific phrase
- `POST /api/lessons/{id}/phrase/{index}/teach` - Teach phrase with animation

### Reachy Control
- `POST /api/reachy/wave` - Make Reachy wave
- `POST /api/reachy/nod` - Make Reachy nod yes
- `POST /api/reachy/shake` - Make Reachy shake head no
- `POST /api/reachy/dance` - Make Reachy dance!
- `GET /api/status` - Get app and daemon status

### WebSocket
- `WS /ws/reachy-state` - Real-time Reachy state stream (20 FPS)

## The Personality

Le Professeur Bizarre is:
- Dramatically passionate about minor cultural differences
- Prone to French exclamations ("Mon Dieu!", "Sacré bleu!")
- Obsessed with cheese, wine, and the metric system
- Hilariously confused by American customs

## Tech Stack

- **Robot**: [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) by Pollen Robotics
- **AI**: [NVIDIA Nemotron](https://openrouter.ai/nvidia) via OpenRouter
- **Backend**: FastAPI with WebSocket support
- **Frontend**: Vanilla JS with Web Speech API
- **Simulation**: MuJoCo physics engine (via reachy-mini-daemon)

## Project Structure

```
le_professeur_bizarre/
├── le_professeur_bizarre/
│   ├── __init__.py
│   ├── integrated_server.py  # Main server with UI
│   ├── llm.py                # NVIDIA Nemotron integration
│   ├── lessons.py            # Structured French lessons
│   └── main.py               # ReachyMiniApp integration
├── pyproject.toml
├── README.md
└── .env.example
```

## Contest Entry

This app was created for the **Reachy Mini App Contest 2025** hosted by Pollen Robotics and Hugging Face.

## License

MIT License - Feel free to remix and share!

---

*Built with ❤️ and a slight obsession with French cheese*
