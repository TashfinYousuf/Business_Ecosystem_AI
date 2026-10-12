"""
backend/ai-engine/audio_voice_parser.py
Voice order processor: transcribes audio and extracts transactional intent using AI Gateway.
"""

from __future__ import annotations

import json
import logging
from typing import Optional
import httpx

from config import gateway_settings
from gateway import MultiProviderAIGateway
from ingestion_schemas import ExtractedTransactionPayload

logger = logging.getLogger("AudioVoiceParser")

VOICE_EXTRACTION_PROMPT = """
You are Trade Wolf OS Voice Parser. Extract commercial transaction intent from bilingual Bengali/Banglish speech.
Input speech transcript will be provided.
Convert it into this strict JSON structure:
{
  "transaction_type": "SALE" | "PURCHASE" | "DEBT_COLLECTION",
  "customer_or_vendor_name": string | null,
  "phone_number": string | null,
  "items": [
    {"item_name": string, "quantity": number, "unit": string, "unit_price": number, "total_price": number}
  ],
  "subtotal": number,
  "discount": number,
  "grand_total": number,
  "paid_amount": number,
  "due_amount": number,
  "confidence_score": number
}
Ensure accurate arithmetic: due_amount = grand_total - paid_amount.
Return ONLY valid JSON.
"""


class AudioVoiceParser:
    def __init__(self, ai_gateway: Optional[MultiProviderAIGateway] = None):
        self.settings = gateway_settings
        self.gateway = ai_gateway or MultiProviderAIGateway()

    async def transcribe_audio_groq(self, audio_bytes: bytes, filename: str = "voice_note.m4a") -> str:
        """
        Transcribes speech using Groq's high-speed Whisper Large v3 endpoint.
        """
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
        files = {"file": (filename, audio_bytes, "audio/m4a")}
        data = {
            "model": "whisper-large-v3",
            "response_format": "json",
            "temperature": "0.0",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            result = response.json()
            return result.get("text", "")

    async def parse_voice_order(
        self,
        audio_bytes: bytes,
        filename: str = "voice.m4a"
    ) -> ExtractedTransactionPayload:
        """
        End-to-end processing: Audio -> Whisper Transcript -> AI Gateway Structured JSON.
        """
        transcript = await self.transcribe_audio_groq(audio_bytes, filename)
        logger.info("Transcribed audio successfully: %s", transcript)

        messages = [
            {"role": "user", "content": f"Audio Transcript: '{transcript}'"}
        ]

        response = await self.gateway.generate_completion(
            messages=messages,
            system_instruction=VOICE_EXTRACTION_PROMPT,
            temperature=0.0,
            json_mode=True
        )

        parsed_data = json.loads(response.content)
        parsed_data["raw_transcription_or_ocr"] = transcript

        return ExtractedTransactionPayload(**parsed_data)