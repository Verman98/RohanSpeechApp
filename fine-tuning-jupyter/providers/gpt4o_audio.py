"""GPT-4o audio mode - multimodal LLM approach to transcription."""

import base64
import os
from openai import OpenAI


def transcribe(audio_path: str) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()

    resp = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a speech transcription assistant. The speaker has "
                    "cerebral palsy and dysarthric speech. Listen carefully and "
                    "transcribe exactly what they are saying. Output ONLY the "
                    "transcription, nothing else."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": "wav",
                        },
                    },
                ],
            },
        ],
    )
    return resp.choices[0].message.content.strip()
