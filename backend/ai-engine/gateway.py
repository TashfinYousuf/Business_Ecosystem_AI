"""
backend/ai-engine/gateway.py
Deterministic Multi-Provider AI Gateway for Trade Wolf OS.
Implements automatic failover: Gemini 2.5 Flash -> Groq (oss-gpt-120b/20b) -> Local Ollama.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx

from config import gateway_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AIGateway")


@dataclass
class GatewayResponse:
    content: str
    provider: str
    model_used: str
    latency_ms: float
    token_usage: Dict[str, int]
    is_fallback: bool
    error: Optional[str] = None


class MultiProviderAIGateway:
    def __init__(self):
        self.settings = gateway_settings
        self.http_client = httpx.AsyncClient(timeout=self.settings.request_timeout_seconds)

    async def close(self):
        """Clean up HTTP client sessions."""
        await self.http_client.aclose()

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> GatewayResponse:
        """
        Executes completion with deterministic cascaded failover.
        Order: Gemini 2.5 Flash -> Groq oss-gpt-120b -> Groq oss-gpt-20b -> Ollama.
        """
        temp = temperature if temperature is not None else self.settings.default_temperature

        # --- 1. Primary Attempt: Google Gemini 2.5 Flash ---
        if self.settings.gemini_api_key:
            try:
                start_time = time.perf_counter()
                logger.info("Attempting completion with Primary: Gemini (%s)", self.settings.gemini_model_name)
                result = await self._call_gemini(messages, system_instruction, temp, json_mode)
                latency = (time.perf_counter() - start_time) * 1000
                return GatewayResponse(
                    content=result["content"],
                    provider="gemini",
                    model_used=self.settings.gemini_model_name,
                    latency_ms=round(latency, 2),
                    token_usage=result.get("usage", {}),
                    is_fallback=False,
                )
            except Exception as e:
                logger.warning("Gemini primary provider failed: %s. Initiating secondary failover.", str(e))
        else:
            logger.info("Gemini API key missing, skipping to secondary provider.")

        # --- 2. Secondary Attempt: Groq Cloud (oss-gpt-120b) ---
        if self.settings.groq_api_key:
            for groq_model in [self.settings.groq_primary_model, self.settings.groq_fallback_model]:
                try:
                    start_time = time.perf_counter()
                    logger.info("Attempting completion with Secondary: Groq (%s)", groq_model)
                    result = await self._call_groq(messages, system_instruction, temp, json_mode, groq_model)
                    latency = (time.perf_counter() - start_time) * 1000
                    return GatewayResponse(
                        content=result["content"],
                        provider="groq",
                        model_used=groq_model,
                        latency_ms=round(latency, 2),
                        token_usage=result.get("usage", {}),
                        is_fallback=True,
                    )
                except Exception as e:
                    logger.warning("Groq (%s) execution failed: %s. Trying next tier.", groq_model, str(e))

        # --- 3. Tertiary Attempt: Local Edge / Offline Ollama ---
        try:
            start_time = time.perf_counter()
            logger.info("Attempting offline fallback with Local Ollama (%s)", self.settings.ollama_model_name)
            result = await self._call_ollama(messages, system_instruction, temp, json_mode)
            latency = (time.perf_counter() - start_time) * 1000
            return GatewayResponse(
                content=result["content"],
                provider="ollama_local",
                model_used=self.settings.ollama_model_name,
                latency_ms=round(latency, 2),
                token_usage=result.get("usage", {}),
                is_fallback=True,
            )
        except Exception as e:
            logger.critical("All AI gateway providers exhausted! Last error (Ollama): %s", str(e))
            raise RuntimeError(f"Complete AI Gateway Outage: All providers failed. Last exception: {str(e)}")

    async def _call_gemini(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str],
        temperature: float,
        json_mode: bool,
    ) -> Dict[str, Any]:
        """Calls Google Gemini v1beta endpoint using standard REST API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model_name}:generateContent?key={self.settings.gemini_api_key}"
        
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": self.settings.max_output_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        candidate = data["candidates"][0]
        text = candidate["content"]["parts"][0]["text"]
        usage_meta = data.get("usageMetadata", {})
        
        return {
            "content": text,
            "usage": {
                "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                "total_tokens": usage_meta.get("totalTokenCount", 0),
            },
        }

    async def _call_groq(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str],
        temperature: float,
        json_mode: bool,
        model_name: str,
    ) -> Dict[str, Any]:
        """Calls Groq OpenAI-compatible chat completion endpoint."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": self.settings.max_output_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = await self.http_client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return {
            "content": choice["message"]["content"],
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    async def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str],
        temperature: float,
        json_mode: bool,
    ) -> Dict[str, Any]:
        """Calls local Ollama chat API endpoint."""
        url = f"{self.settings.ollama_base_url}/api/chat"

        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        formatted_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": self.settings.ollama_model_name,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": self.settings.max_output_tokens,
            },
        }

        if json_mode:
            payload["format"] = "json"

        response = await self.http_client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return {
            "content": data["message"]["content"],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
        }