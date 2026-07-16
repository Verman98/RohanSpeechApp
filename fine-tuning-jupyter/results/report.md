# CP Speech STT Evaluation Report

## Summary (averaged across all clips)

| provider       |   wer |   cer |   semantic_similarity |   time_s |
|:---------------|------:|------:|----------------------:|---------:|
| gpt4o_audio    | 1.033 | 0.728 |                 0.511 |    2.234 |
| openai_whisper | 1.483 | 0.507 |                 0.604 |    2.048 |


## Per-clip Transcriptions

### openai_whisper

- **Effects of the first world war.wav** (WER=0.667): `effects of the First World War.`
- **For producing the things.wav** (WER=1.250): `all fellow dudes in the tents.`
- **The prices doubled.wav** (WER=4.667): `d up r i z e d d u p f u l d`
- **in England were setup by seventeenthirty.wav** (WER=0.667): `in England was set up by 1730.`
- **that the sour and bitter taste.wav** (WER=0.167): `that the sour and bitter taste.`

### gpt4o_audio

- **Effects of the first world war.wav** (WER=0.833): `The impact of the First World War.`
- **For producing the things.wav** (WER=1.000): `falling balloons in the tent`
- **The prices doubled.wav** (WER=1.667): `Double I said that double.`
- **in England were setup by seventeenthirty.wav** (WER=0.833): `England was set up by 1730.`
- **that the sour and bitter taste.wav** (WER=0.833): `{"time": 0.00, "text": "Dad, the sour and bitter taste"}`
