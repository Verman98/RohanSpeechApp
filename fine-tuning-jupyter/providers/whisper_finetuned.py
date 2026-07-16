"""Fine-tuned Whisper inference using the model produced by finetune_whisper.ipynb."""

import os
from transformers import pipeline

MODEL_PATH = "models/whisper_finetuned"

_pipe = None


def _get_pipe():
    global _pipe
    if _pipe is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Fine-tuned model not found at '{MODEL_PATH}'.\n"
                "Run finetune_whisper.ipynb first to train and save the model."
            )
        _pipe = pipeline(
            "automatic-speech-recognition",
            model=MODEL_PATH,
        )
    return _pipe


def transcribe(audio_path: str) -> str:
    return _get_pipe()(audio_path)["text"].strip()
