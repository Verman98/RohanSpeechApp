# CP Speech: Pronunciation Correction Approaches

## Problem

GPT-4o audio and OpenAI Whisper both make transcription errors on CP/dysarthric speech. Words are misheard, consonants are dropped, and vowels are substituted — leading to high WER even from the best STT providers.

## Approach A: Post-Processing Correction Pipeline (Current)

**Idea:** Learn a speaker's pronunciation patterns from labeled examples, then use those patterns to correct future transcriptions at inference time.

### How It Works

**Phase 1 — Learning:**
1. User provides WAV files paired with correct transcriptions
2. Whisper generates a raw transcript for each clip
3. GPT-4o audio analyzes the audio + raw transcript + correct text to extract structured pronunciation patterns (e.g., "speaker says 'baw', means 'ball'")
4. Patterns saved to `data/discrepancies.json`

**Phase 2 — Corrected Transcription:**
1. New WAV file is transcribed by Whisper
2. GPT-4o receives the raw transcript + full pattern table + audio
3. GPT-4o outputs a corrected transcription informed by the speaker's known patterns

### Pros
- No GPU training required
- Works immediately with a handful of labeled clips
- Patterns are human-readable and editable
- Leverages GPT-4o's language understanding for contextual correction

### Cons
- Correction quality depends on GPT-4o's ability to apply patterns
- API costs per transcription (Whisper + GPT-4o)
- Pattern table grows; may need pruning for very large datasets
- No acoustic model adaptation — relies entirely on text-level correction

### Data Requirements
- Minimum: 5-10 labeled clips to establish basic patterns
- Recommended: 20-50 clips covering common vocabulary and phoneme contexts
- Format: WAV audio + correct text (filename stem used as default)

## Approach B: Fine-Tuned Whisper (Future)

**Idea:** Fine-tune the Whisper model on labeled dysarthric speech so it learns to transcribe correctly at the acoustic level.

### How It Would Work
1. Collect 500+ hours of labeled dysarthric speech
2. Fine-tune Whisper (or a distilled variant) on this data
3. Deploy fine-tuned model for direct transcription

### Pros
- End-to-end solution — no post-processing needed
- Potentially higher accuracy for well-represented speech patterns
- Single inference pass (lower latency)

### Cons
- Requires 500+ hours of labeled data (extremely difficult to collect for CP speech)
- GPU training infrastructure needed
- Model is speaker-specific unless trained on diverse speakers
- Long iteration cycles for experimentation

## Roadmap

1. **Now:** Post-processing pipeline (Approach A) with correction GUI
2. **Next:** Evaluate correction accuracy across clips; tune GPT-4o prompts
3. **Later:** Explore speaker-adaptive fine-tuning if sufficient data becomes available
4. **Ongoing:** Grow the discrepancy pattern library across sessions
