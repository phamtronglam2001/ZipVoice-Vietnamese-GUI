# ZipVoice Vietnamese TTS — Portable Offline GUI

[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)

Offline **Gradio desktop** application for [ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — Vietnamese zero-shot TTS (123M parameters, flow matching).

This is a **custom GUI and tooling layer**, not a verbatim copy of the Hugging Face Space or [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice). It adds portable Windows CPU setup, voice management, a three-step text pipeline, long-form chunking, and ONNX export tools.

**ONNX-only variant (lighter, bundled weights):** [ZipVoice-Vietnamese-ONNX-GUI](https://github.com/phamtronglam2001/ZipVoice-Vietnamese-ONNX-GUI)

English | [Tiếng Việt](README.md)

---

## Author & license

| | |
|---|---|
| **Author** | [Pham Trong Lam](https://github.com/phamtronglam2001) |
| **Repository** | https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI |
| **License (GUI + sample voices)** | [Non-Commercial](LICENSE) — research / education / non-profit only |

| Component | Source | License |
|-----------|--------|---------|
| GUI code + `.wav` samples | Pham Trong Lam | Non-Commercial |
| ZipVoice engine | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | Apache-2.0 |
| Vietnamese checkpoint | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | CC-BY-NC-SA-4.0 |
| vinorm / vietnormalizer / sea-g2p | PyPI third-party packages | Per-package |

---

## Bundled voices (ready after setup)

Nine WAV files in `assets/ref_audio/` with transcripts in `assets/ref_info.json`. Select from the GUI dropdown — no extra download required.

See the voice table in [README.md](README.md) (Vietnamese).

---

## Main features (`app.py` — port 7860)

- Zero-shot Vietnamese TTS from a 3–15 s reference clip + **manual transcript**
- Voice registry via `assets/ref_info.json`
- `.txt` / `.md` upload for books and long documents
- **Three-step normalization pipeline** (up to 3 backends in order)
- **Preview normalization** before synthesis
- Smart chunking with pauses for sentences, paragraphs, chapters, and numbered list items
- WAV 24 kHz or MP3 export to `output/`
- CPU one-click install (`install_cpu.bat` / `run_cpu.bat`)
- Logging: `logs/app.log`, `logs/crash.log`

### ONNX tool (`app_onnx.py` — port 7861)

Environment check, export `text_encoder.onnx` / `fm_decoder.onnx` (+ INT8), PyTorch vs ONNX test.

---

## Normalization pipeline (Steps 1 → 2 → 3)

| Backend | pip? | Role |
|---------|------|------|
| **VieNeu** | No | Punctuation / noise cleanup (from VieNeu-TTS) |
| **TTS structure** | No | `mẫu (mẹ)` → `mẫu, mẹ`; `một. next` → line break + ~1 s pause |
| **vinorm** | Yes | NSW — **not bundled in ZipVoice** (separate PyPI package) |
| **vietnormalizer** | Yes | Broader Vietnamese normalization |
| **sea-g2p Normalizer** | Yes | Rich NSW (**Normalizer only**, no G2P) |
| **None** | — | Skip step |

**GUI defaults:** Step 1 = VieNeu, Step 2 = TTS structure.

**Suggested for books:** `VieNeu → TTS structure → vinorm` (or sea-g2p).

All steps output plain text. ZipVoice phonemizes via Espeak separately — safe to chain.

### TTS structure details

| Rule | Example |
|------|---------|
| `()`, `[]`, `{}` → comma | `mẫu (mẹ)` → `mẫu, mẹ` |
| Number + period → newline | `một. read next` → `một.` + newline + `read next` |
| Pause after list-only block | ~1.0 s before the next block |

---

## Quick start

```bat
git clone https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI.git
cd ZipVoice-Vietnamese-GUI
install_cpu.bat
run_cpu.bat
```

Open http://127.0.0.1:7860

`install_cpu.bat` creates `.venv`, installs PyTorch CPU, k2, normalizers, clones `vendor/ZipVoice`, downloads models (~2 GB).

---

## Project layout

```
app.py, app_onnx.py       # Gradio GUIs
infer_engine.py           # ZipVoice + Vocos wrapper
utils.py                  # Pipeline + long-text chunking
vieneu_text.py            # VieNeu punctuation cleanup
period_linebreak.py       # Brackets→commas, list line breaks
assets/ref_info.json      # Voice registry
assets/ref_audio/*.wav    # Nine bundled voices
models/                   # Downloaded at setup (gitignored)
vendor/ZipVoice/          # Cloned at setup (gitignored)
output/                   # Exported audio
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Models not found` | Run `install_cpu.bat` |
| `vinorm` not installed | `pip install vinorm`, or remove from pipeline |
| Parentheses read too fast | Enable **TTS structure** (Step 2) |
| Silent exit | `view_logs.bat` → `logs/app.log` |
| ONNX black screen | `view_onnx_logs.bat`; `pip install -r requirements-onnx.txt` |

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ZIPVOICE_FORCE_CPU` | `1` in `run_cpu.bat` | Force CPU |
| `GRADIO_SERVER_PORT` | `7860` / `7861` | TTS / ONNX port |

---

## License summary

- **This repository (code + sample WAV):** Non-Commercial — Pham Trong Lam, 2026
- **Model weights:** CC-BY-NC-SA-4.0 — non-commercial research; disclose AI-generated audio
- **ZipVoice upstream:** Apache-2.0

Commercial use is prohibited under the repo license and model card terms.
