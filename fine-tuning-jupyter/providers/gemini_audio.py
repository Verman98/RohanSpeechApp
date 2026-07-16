"""Gemini 2.5 Pro - multimodal LLM approach to transcription."""

import os
from google import genai
from google.genai import types


def transcribe(audio_path: str) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    audio_part = types.Part.from_bytes(data=audio_data, mime_type="audio/wav")

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            types.Content(
                parts=[
                    types.Part.from_text(
                        "You are a speech transcription assistant. The speaker has "
                        "cerebral palsy and dysarthric speech. Listen carefully and "
                        "transcribe exactly what they are saying. Output ONLY the "
                        "transcription, nothing else."
                    ),
                    audio_part,
                ]
            )
        ],
    )
    return response.text.strip()
