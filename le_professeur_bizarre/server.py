"""
Le Professeur Bizarre - FastAPI Server Extension

This module adds a translation endpoint to the Reachy Mini daemon's API.
It can also run standalone for testing the web interface.
"""

import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .llm import NemotronTranslator, TranslationResponse, get_fallback_response


class TranslateRequest(BaseModel):
    """Request model for translation"""
    text: str


class TranslateResponse(BaseModel):
    """Response model for translation"""
    original: str
    french_translation: str
    cultural_fact: str
    pronunciation_tip: str | None = None


# Global translator instance
translator: NemotronTranslator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize translator on startup"""
    global translator
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        translator = NemotronTranslator(api_key)
        print("✓ Nemotron translator initialized")
    else:
        print("⚠ No OPENROUTER_API_KEY - using demo mode")
    yield
    print("Le Professeur Bizarre server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Le Professeur Bizarre",
    description="A quirky Franco-American cultural teacher for Reachy Mini",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/api/apps/le_professeur_bizarre/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    Translate English text to French with cultural commentary.

    This endpoint is designed to be called from the web interface
    and integrates with the Reachy Mini animation system.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        if translator:
            response = await translator.translate(request.text)
        else:
            # Demo mode - use fallback
            await asyncio.sleep(1.5)  # Simulate API delay
            response = get_fallback_response(request.text)

        return TranslateResponse(
            original=response.original,
            french_translation=response.french_translation,
            cultural_fact=response.cultural_fact,
            pronunciation_tip=response.pronunciation_tip
        )

    except Exception as e:
        print(f"Translation error: {e}")
        # Return a fallback response on error
        fallback = get_fallback_response(request.text)
        return TranslateResponse(
            original=request.text,
            french_translation=fallback.french_translation,
            cultural_fact=f"Mon Dieu! Error occurred, but here's a fact: {fallback.cultural_fact}",
            pronunciation_tip=fallback.pronunciation_tip
        )


@app.get("/api/apps/le_professeur_bizarre/status")
async def status():
    """Check if the app is running and translator is available"""
    return {
        "app": "le_professeur_bizarre",
        "version": "1.0.0",
        "translator_available": translator is not None,
        "model": os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
    }


# Mount static files for the web interface
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def root():
        """Serve the web interface"""
        return FileResponse(static_dir / "index.html")


def run_standalone(host: str = "0.0.0.0", port: int = 5173):
    """Run the server standalone for testing"""
    import uvicorn
    print(f"\n🇫🇷 Le Professeur Bizarre server starting...")
    print(f"   Open http://localhost:{port} in your browser")
    print(f"   Press Ctrl+C to stop\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_standalone()
