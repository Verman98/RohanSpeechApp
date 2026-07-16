"""Generate comparison report and charts from evaluation results."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "results"


def load_results() -> dict:
    combined_path = RESULTS_DIR / "combined_results.json"
    if not combined_path.exists():
        raise FileNotFoundError("Run evaluate.py first to generate results.")
    with open(combined_path) as f:
        return json.load(f)


def build_dataframe(results: dict) -> pd.DataFrame:
    """Build a DataFrame with per-clip, per-provider metrics."""
    rows = []
    for provider, pdata in results.items():
        for fname, metrics in pdata["metrics"].items():
            transcript = pdata["transcripts"].get(fname, {}).get("transcript", "")
            time_s = pdata["transcripts"].get(fname, {}).get("time_s", 0)
            rows.append({
                "provider": provider,
                "file": fname,
                "wer": metrics["wer"],
                "cer": metrics["cer"],
                "semantic_similarity": metrics["semantic_similarity"],
                "transcript": transcript,
                "time_s": time_s,
            })
    return pd.DataFrame(rows)


def generate_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """Average metrics per provider."""
    summary = df.groupby("provider")[["wer", "cer", "semantic_similarity", "time_s"]].mean()
    summary = summary.sort_values("wer")
    return summary.round(3)


def plot_bar_chart(summary: pd.DataFrame, output_path: Path):
    """Bar chart comparing providers across WER, CER, and semantic similarity."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    summary["wer"].plot.bar(ax=axes[0], color="indianred")
    axes[0].set_title("Word Error Rate (lower is better)")
    axes[0].set_ylabel("WER")
    axes[0].set_ylim(0, max(1.0, summary["wer"].max() * 1.1))

    summary["cer"].plot.bar(ax=axes[1], color="steelblue")
    axes[1].set_title("Character Error Rate (lower is better)")
    axes[1].set_ylabel("CER")
    axes[1].set_ylim(0, max(1.0, summary["cer"].max() * 1.1))

    summary["semantic_similarity"].plot.bar(ax=axes[2], color="seagreen")
    axes[2].set_title("Semantic Similarity (higher is better)")
    axes[2].set_ylabel("Cosine Similarity")
    axes[2].set_ylim(0, 1.0)

    for ax in axes:
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_path}")
    plt.close()


def plot_per_clip(df: pd.DataFrame, output_path: Path):
    """Heatmap-style per-clip WER comparison."""
    pivot = df.pivot(index="file", columns="provider", values="wer")
    fig, ax = plt.subplots(figsize=(12, max(4, len(pivot) * 0.5)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1.5)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title("WER per Clip per Provider (green=good, red=bad)")
    plt.colorbar(im, ax=ax, label="WER")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Per-clip chart saved to {output_path}")
    plt.close()


def write_text_report(summary: pd.DataFrame, df: pd.DataFrame, output_path: Path):
    """Write a markdown report."""
    lines = ["# CP Speech STT Evaluation Report\n"]

    lines.append("## Summary (averaged across all clips)\n")
    lines.append(summary.to_markdown())
    lines.append("\n")

    lines.append("## Per-clip Transcriptions\n")
    for provider in df["provider"].unique():
        lines.append(f"### {provider}\n")
        pdata = df[df["provider"] == provider]
        for _, row in pdata.iterrows():
            lines.append(f"- **{row['file']}** (WER={row['wer']:.3f}): `{row['transcript']}`")
        lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Report saved to {output_path}")


def main():
    results = load_results()
    df = build_dataframe(results)
    summary = generate_summary_table(df)

    print("\n" + summary.to_string() + "\n")

    RESULTS_DIR.mkdir(exist_ok=True)
    plot_bar_chart(summary, RESULTS_DIR / "comparison_chart.png")
    plot_per_clip(df, RESULTS_DIR / "per_clip_wer.png")
    write_text_report(summary, df, RESULTS_DIR / "report.md")


if __name__ == "__main__":
    main()
