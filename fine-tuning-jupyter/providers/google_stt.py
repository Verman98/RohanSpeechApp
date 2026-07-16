"""Google Cloud Speech-to-Text v1."""

from google.cloud import speech


def transcribe(audio_path: str) -> str:
    client = speech.SpeechClient()

    with open(audio_path, "rb") as f:
        content = f.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
        enable_automatic_punctuation=True,
        # Enhanced model is better for impaired speech
        model="latest_long",
    )

    response = client.recognize(config=config, audio=audio)
    parts = [result.alternatives[0].transcript for result in response.results]
    return " ".join(parts)
