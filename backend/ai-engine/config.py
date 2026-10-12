"""
backend/ai-engine/config.py
Configuration schemas and environment settings for the Multi-Provider AI Gateway.
"""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


class AIGatewaySettings(BaseModel):
    # Primary Provider: Google Gemini
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model_name: str = "gemini-2.5-flash"

    # Secondary Provider: Groq Cloud
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_primary_model: str = "oss-gpt-120b"
    groq_fallback_model: str = "oss-gpt-20b"

    # Local Fallback Provider: Ollama
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model_name: str = "llama3.2:latest"

    # General Gateway Parameters
    request_timeout_seconds: float = 15.0
    max_retries_per_provider: int = 2
    default_temperature: float = 0.1  # Low temperature for strict financial/data consistency
    max_output_tokens: int = 4096


gateway_settings = AIGatewaySettings()