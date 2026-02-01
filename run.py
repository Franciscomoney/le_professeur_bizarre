#!/usr/bin/env python3
"""
Le Professeur Bizarre - Quick Start Script

Run this script to start the web interface for testing.
For full Reachy Mini integration, use: reachy-mini-daemon --sim
"""

import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🇫🇷  Le Professeur Bizarre  🇺🇸                          ║
    ║                                                           ║
    ║   Your Eccentric Franco-American Cultural Teacher         ║
    ║   Powered by NVIDIA Nemotron                              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print("    ✓ OpenRouter API key found")
        print(f"    ✓ Model: {os.getenv('NEMOTRON_MODEL', 'nvidia/nemotron-3-nano-30b-a3b')}")
    else:
        print("    ⚠ No API key - running in demo mode")
        print("    Set OPENROUTER_API_KEY in .env for full functionality")

    print()
    print("    Starting web server...")
    print("    Open http://localhost:5173 in your browser")
    print("    Press Ctrl+C to stop")
    print()

    from le_professeur_bizarre.server import run_standalone
    run_standalone()


if __name__ == "__main__":
    main()
