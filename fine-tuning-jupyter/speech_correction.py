"""Core logic for CP speech pronunciation correction.

Two-phase system:
  Phase 1 (Learning): Analyze WAV + correct text to build discrepancy patterns.
  Phase 2 (Correction): Transcribe new WAV and correct using learned patterns.
"""

import base64
import json
import os
from pathlib import Path

from openai import OpenAI

DATA_DIR = Path(__file__).parent / "data"
DISCREPANCIES_FILE = DATA_DIR / "discrepancies.json"

_EMPTY_DATA = {"patterns": [], "speaker_notes": ""}


def _get_client() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _whisper_transcribe(client: OpenAI, audio_path: str) -> str:
    """Transcribe audio using Whisper API."""
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1", file=f, language="en",
        )
    return resp.text


def _audio_to_b64(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def load_discrepancies() -> dict:
    """Load discrepancy data from JSON. Returns empty structure if not found."""
    if DISCREPANCIES_FILE.exists():
        with open(DISCREPANCIES_FILE) as f:
            return json.load(f)
    return {"patterns": [], "speaker_notes": ""}


def save_discrepancies(data: dict):
    """Merge new patterns (deduplicating), then write JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Deduplicate by (spoken, intended) pair
    seen = set()
    unique = []
    for p in data.get("patterns", []):
        key = (p.get("spoken", "").lower(), p.get("intended", "").lower())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    data["patterns"] = unique

    with open(DISCREPANCIES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def analyze_discrepancies(audio_path: str, correct_text: str) -> dict:
    """Phase 1: Whisper transcribes, GPT-4o extracts pronunciation patterns.

    Returns:
        {
            "raw_transcript": str,
            "patterns": [
                {"spoken": str, "intended": str, "pattern_type": str, "notes": str}
            ]
        }
    """
    client = _get_client()

    # Step 1: Whisper transcription
    raw_transcript = _whisper_transcribe(client, audio_path)

    # Step 2: GPT-4o analyzes audio + raw transcript + correct text
    audio_b64 = _audio_to_b64(audio_path)
    filename = Path(audio_path).name

    resp = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a speech-language pathology assistant analyzing "
                    "dysarthric speech from a speaker with cerebral palsy.\n\n"
                    "You will receive:\n"
                    "1. Audio of the speaker\n"
                    "2. A raw Whisper transcript (may contain errors)\n"
                    "3. The correct/intended text\n\n"
                    "Identify specific pronunciation discrepancies — what the "
                    "speaker's speech sounds like vs. what they intended to say. "
                    "Focus on systematic patterns (e.g., final consonant deletion, "
                    "vowel substitution, consonant cluster reduction).\n\n"
                    "Respond ONLY with valid JSON in this exact format:\n"
                    "{\n"
                    '  "patterns": [\n'
                    '    {"spoken": "baw", "intended": "ball", '
                    '"pattern_type": "final consonant deletion", '
                    '"notes": "description"}\n'
                    "  ]\n"
                    "}\n\n"
                    "If no discrepancies are found, return {\"patterns\": []}."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_b64, "format": "wav"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Raw Whisper transcript: \"{raw_transcript}\"\n"
                            f"Correct text: \"{correct_text}\"\n"
                            f"Source file: {filename}\n\n"
                            "Identify pronunciation discrepancy patterns."
                        ),
                    },
                ],
            },
        ],
    )

    # Parse GPT-4o response
    content = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[: content.rfind("```")]
        content = content.strip()

    try:
        result = json.loads(content)
        patterns = result.get("patterns", [])
    except json.JSONDecodeError:
        patterns = []

    # Tag each pattern with the source file
    for p in patterns:
        p.setdefault("notes", "")
        if filename not in p["notes"]:
            p["notes"] = f"from {filename}" + (
                f"; {p['notes']}" if p["notes"] else ""
            )

    return {"raw_transcript": raw_transcript, "patterns": patterns}


def corrected_transcribe(audio_path: str) -> dict:
    """Phase 2: Whisper transcribes, GPT-4o corrects using discrepancy table.

    Returns:
        {"raw_transcript": str, "corrected_transcript": str}
    """
    client = _get_client()

    # Step 1: Whisper transcription
    raw_transcript = _whisper_transcribe(client, audio_path)

    # Step 2: Load discrepancy table
    data = load_discrepancies()
    patterns = data.get("patterns", [])

    if not patterns:
        # No learned patterns — return raw transcript as-is
        return {
            "raw_transcript": raw_transcript,
            "corrected_transcript": raw_transcript,
        }

    # Step 3: GPT-4o corrects using patterns + audio
    audio_b64 = _audio_to_b64(audio_path)
    patterns_text = json.dumps(patterns, indent=2)

    resp = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a speech-language pathology assistant. The speaker "
                    "has cerebral palsy with dysarthric speech.\n\n"
                    "You will receive:\n"
                    "1. Audio of the speaker\n"
                    "2. A raw Whisper transcript (may contain errors)\n"
                    "3. A table of known pronunciation patterns for this speaker\n\n"
                    "Using the audio and the known patterns, produce a corrected "
                    "transcription of what the speaker intended to say.\n\n"
                    "Output ONLY the corrected transcription text, nothing else."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_b64, "format": "wav"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Raw Whisper transcript: \"{raw_transcript}\"\n\n"
                            f"Known pronunciation patterns:\n{patterns_text}\n\n"
                            "Produce the corrected transcription."
                        ),
                    },
                ],
            },
        ],
    )

    corrected = resp.choices[0].message.content.strip()
    return {
        "raw_transcript": raw_transcript,
        "corrected_transcript": corrected,
    }
