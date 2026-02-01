"""
Le Professeur Bizarre - A quirky Franco-American cultural teacher for Reachy Mini

This app translates English to French while teaching bizarre cultural facts
about France and the US. Powered by NVIDIA Nemotron via OpenRouter.
"""

from .main import LeProfesseurBizarre
from .llm import NemotronTranslator, TranslationResponse

__version__ = "1.0.0"
__all__ = ["LeProfesseurBizarre", "NemotronTranslator", "TranslationResponse"]
