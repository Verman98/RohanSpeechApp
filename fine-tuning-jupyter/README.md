# CP Speech - STT Evaluation for Dysarthric Speech

Benchmarks 7 speech-to-text services on cerebral palsy / dysarthric speech to find the best foundation for an accessible conversational AI.

## Providers Evaluated

| Provider | Type | Notes |
|---|---|---|
| Whisper local (large-v3) | Local | Baseline via `faster-whisper`, fine-tunable |
| OpenAI Whisper API | Cloud API | whisper-1 endpoint |
| AssemblyAI | Cloud API | Strong general accuracy |
| Deepgram Nova-3 | Cloud API | Fast, medical variant available |
| Google Cloud STT | Cloud API | Backed by Project Euphonia |
| GPT-4o audio | Multimodal LLM | Semantic recovery via language understanding |
| Gemini 2.5 Pro | Multimodal LLM | Google's multimodal with audio input |

## Metrics

- **WER** (Word Error Rate) - standard ASR metric, lower is better
- **CER** (Character Error Rate) - more granular, lower is better
- **Semantic Similarity** - sentence embedding cosine similarity, higher is better

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

## Usage

1. Place WAV files in `data/raw/`
2. Add ground truth to `transcripts/ground_truth.json`:
   ```json
   {"clip1.wav": "hello how are you", "clip2.wav": "I want water"}
   ```
   Or name files as the ground truth: `hello how are you.wav`
3. Run evaluation (all providers or select specific ones):
   ```bash
   python evaluate.py                          # all providers
   python evaluate.py whisper_local openai_whisper  # specific providers
   ```
4. Generate report:
   ```bash
   python report.py
   ```
5. Check `results/` for outputs, charts, and the markdown report.
