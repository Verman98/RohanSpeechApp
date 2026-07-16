"""AssemblyAI speech-to-text."""

import os
import assemblyai as aai


def transcribe(audio_path: str) -> str:
    aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
    config = aai.TranscriptionConfig(language_code="en")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path, config=config)
    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"AssemblyAI error: {transcript.error}")
    return transcript.text or ""
