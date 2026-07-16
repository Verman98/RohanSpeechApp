"""Metrics for evaluating STT output: WER, CER, and semantic similarity."""

import jiwer
from sentence_transformers import SentenceTransformer, util

_sim_model = None


def _get_sim_model():
    global _sim_model
    if _sim_model is None:
        _sim_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sim_model


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate. Returns 1.0 if reference is empty."""
    if not reference.strip():
        return 1.0 if hypothesis.strip() else 0.0
    return jiwer.wer(reference, hypothesis)


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Character Error Rate. Returns 1.0 if reference is empty."""
    if not reference.strip():
        return 1.0 if hypothesis.strip() else 0.0
    return jiwer.cer(reference, hypothesis)


def semantic_similarity(reference: str, hypothesis: str) -> float:
    """Cosine similarity of sentence embeddings (0-1). Higher is better."""
    if not reference.strip() or not hypothesis.strip():
        return 0.0
    model = _get_sim_model()
    emb = model.encode([reference, hypothesis], convert_to_tensor=True)
    score = util.cos_sim(emb[0], emb[1]).item()
    return max(0.0, score)


def compute_all(reference: str, hypothesis: str) -> dict:
    """Compute all metrics for a reference/hypothesis pair."""
    return {
        "wer": word_error_rate(reference, hypothesis),
        "cer": character_error_rate(reference, hypothesis),
        "semantic_similarity": semantic_similarity(reference, hypothesis),
    }
