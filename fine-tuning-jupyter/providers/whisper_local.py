"""Local Whisper large-v3 inference via faster-whisper."""

from faster_whisper import WhisperModel

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = WhisperModel("large-v3", device="auto", compute_type="auto")
    return _model


def transcribe(audio_path: str) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio_path, language="en")
    return " ".join(seg.text.strip() for seg in segments)
