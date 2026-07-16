"""Deepgram Nova-3 speech-to-text."""

import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource


def transcribe(audio_path: str) -> str:
    client = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])

    with open(audio_path, "rb") as f:
        buffer_data = f.read()

    payload: FileSource = {"buffer": buffer_data}
    options = PrerecordedOptions(
        model="nova-3",
        language="en",
        smart_format=False,
    )

    response = client.listen.rest.v("1").transcribe_file(payload, options)
    return response.results.channels[0].alternatives[0].transcript
