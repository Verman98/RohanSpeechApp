"""OpenAI Whisper API (whisper-1 / large-v3)."""

import os
from openai import OpenAI


def transcribe(audio_path: str) -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="en",
        )
    return resp.text
