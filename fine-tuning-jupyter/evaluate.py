"""Main evaluation script: run all audio clips through all STT providers."""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from providers import PROVIDERS, get_provider
from metrics import compute_all

DATA_DIR = Path(__file__).parent / "data" / "raw"
TRANSCRIPTS_FILE = Path(__file__).parent / "transcripts" / "ground_truth.json"
RESULTS_DIR = Path(__file__).parent / "results"


def load_ground_truth() -> dict[str, str]:
    """Load ground truth from JSON file, falling back to filenames as labels.

    JSON format: {"filename.wav": "expected text", ...}
    Filename fallback: "hello how are you.wav" -> "hello how are you"
    """
    if TRANSCRIPTS_FILE.exists():
        with open(TRANSCRIPTS_FILE) as f:
            gt = json.load(f)
        if gt:
            return gt

    # Fallback: derive ground truth from filenames
    gt = {}
    for wav in sorted(DATA_DIR.glob("*.wav")):
        gt[wav.name] = wav.stem.replace("_", " ").replace("-", " ")
    return gt


def run_provider(name: str, transcribe_fn, audio_files: list[Path],
                 on_progress=None) -> dict:
    """Run a single provider on all audio files. Returns results dict."""
    results = {}
    for audio_path in audio_files:
        key = audio_path.name
        msg = f"  {key}..."
        print(msg, end=" ", flush=True)
        if on_progress:
            on_progress(f"  {name}: {key}...")
        t0 = time.time()
        try:
            text = transcribe_fn(str(audio_path))
            elapsed = time.time() - t0
            results[key] = {"transcript": text, "time_s": round(elapsed, 2)}
            print(f"OK ({elapsed:.1f}s)")
            if on_progress:
                on_progress(f"  {name}: {key} OK ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            results[key] = {
                "transcript": "",
                "error": str(e),
                "time_s": round(elapsed, 2),
            }
            print(f"ERROR: {e}")
            if on_progress:
                on_progress(f"  {name}: {key} ERROR: {e}")
    return results


def run_evaluation(provider_names, audio_files, ground_truth, results_dir,
                   on_progress=None):
    """Run evaluation for selected providers and return combined results dict.

    Args:
        provider_names: list of provider name strings
        audio_files: list of Path objects to WAV files
        ground_truth: dict mapping filename -> expected text
        results_dir: Path to save result JSON files
        on_progress: optional callback(message: str) for progress updates

    Returns:
        dict with per-provider transcripts and metrics
    """
    results_dir = Path(results_dir)
    results_dir.mkdir(exist_ok=True)

    all_results = {}

    for provider_name in provider_names:
        if on_progress:
            on_progress(f"[{provider_name}] Starting...")
        print(f"[{provider_name}]")

        try:
            transcribe_fn = get_provider(provider_name)
        except (KeyError, ImportError) as e:
            msg = f"[{provider_name}] Failed to load: {e}"
            print(msg)
            if on_progress:
                on_progress(msg)
            continue

        results = run_provider(provider_name, transcribe_fn, audio_files,
                               on_progress=on_progress)

        # Save raw results
        out_path = results_dir / f"{provider_name}_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  -> Saved to {out_path}\n")
        if on_progress:
            on_progress(f"[{provider_name}] Saved results.")

        # Compute metrics
        provider_metrics = {}
        for fname, data in results.items():
            ref = ground_truth.get(fname, "")
            hyp = data.get("transcript", "")
            provider_metrics[fname] = compute_all(ref, hyp)

        all_results[provider_name] = {
            "transcripts": results,
            "metrics": provider_metrics,
        }

    # Save combined results
    combined_path = results_dir / "combined_results.json"
    with open(combined_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Combined results saved to {combined_path}")
    if on_progress:
        on_progress(f"Combined results saved to {combined_path}")

    return all_results


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    ground_truth = load_ground_truth()
    if not ground_truth:
        print("No ground truth found. Add WAV files to data/raw/ or fill transcripts/ground_truth.json")
        sys.exit(1)

    audio_files = [DATA_DIR / fname for fname in sorted(ground_truth.keys())]
    missing = [f for f in audio_files if not f.exists()]
    if missing:
        print(f"Warning: {len(missing)} audio files missing:")
        for f in missing[:5]:
            print(f"  {f}")
        audio_files = [f for f in audio_files if f.exists()]

    if not audio_files:
        print("No audio files found. Place WAV files in data/raw/")
        sys.exit(1)

    # Select which providers to run (all by default, or pass names as args)
    selected = sys.argv[1:] if len(sys.argv) > 1 else list(PROVIDERS.keys())

    print(f"Found {len(audio_files)} audio files, {len(selected)} providers\n")

    all_results = run_evaluation(selected, audio_files, ground_truth, RESULTS_DIR)

    # Print summary table
    print("\n" + "=" * 70)
    print(f"{'Provider':<18} {'Avg WER':>10} {'Avg CER':>10} {'Avg Sim':>10}")
    print("=" * 70)
    for pname, pdata in all_results.items():
        m = pdata["metrics"]
        if not m:
            continue
        avg_wer = sum(v["wer"] for v in m.values()) / len(m)
        avg_cer = sum(v["cer"] for v in m.values()) / len(m)
        avg_sim = sum(v["semantic_similarity"] for v in m.values()) / len(m)
        print(f"{pname:<18} {avg_wer:>10.3f} {avg_cer:>10.3f} {avg_sim:>10.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
