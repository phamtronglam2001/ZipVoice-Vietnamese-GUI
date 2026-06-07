# ZipVoice Vietnamese TTS — Portable Offline GUI

[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)

Offline **Gradio desktop** application for [ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — Vietnamese zero-shot TTS (123M parameters, flow matching).

This is a **custom GUI and tooling layer**, not a verbatim copy of the Hugging Face Space or [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice). It adds portable Windows CPU setup, voice management, a configurable normalization pipeline, long-form chunking, and ONNX export tools.

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
| GUI code + `.wav` samples | [phamtronglam2001/ZipVoice-Vietnamese-GUI](https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI) — Pham Trong Lam | Non-Commercial |
| ZipVoice engine | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | Apache-2.0 |
| Vietnamese checkpoint | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | CC-BY-NC-SA-4.0 |
| Vocos vocoder | Library [gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) · weights [charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) | MIT · per model card |
| Text normalizers (optional) | See [Attributions](#third-party-source-attributions) below | Per repository |

---

## Acknowledgments

This GUI **does not** train TTS models. Synthesis relies on checkpoints and engines published by the authors and teams below — please cite them when sharing results.

### Vietnamese checkpoint — Hugging Face

| | |
|---|---|
| **Author / publisher** | [**Nguyen Thien Hy**](https://huggingface.co/hynt) (`hynt`) |
| **Model** | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — ZipVoice fine-tuned on **~2500 hours** of Vietnamese speech |
| **Demo Space** | [hynt/ZipVoice-Vietnamese-100h](https://huggingface.co/spaces/hynt/ZipVoice-Vietnamese-100h) |
| **License** | [CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — non-commercial research only |

Per the model card: training data includes **PhoAudioBook**, **ViVoice**, and **UEH** (with an additional ~50 h labeled set from Teacher Định, University of Economics Ho Chi Minh City). Background music was removed with [facebookresearch/demucs](https://github.com/facebookresearch/demucs).

### Base ZipVoice architecture — k2-fsa

| | |
|---|---|
| **Project** | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) ([k2-fsa](https://github.com/k2-fsa)) |
| **Paper** | Zhu, Han et al., *ZipVoice: Fast and High-Quality Zero-Shot Text-to-Speech with Flow Matching*, [arXiv:2506.13053](https://arxiv.org/abs/2506.13053) (2025) |
| **License** | Apache-2.0 |

### Vocos vocoder

| | |
|---|---|
| **Library** | [gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) — Siuzdak, Hubert et al., [arXiv:2306.00814](https://arxiv.org/abs/2306.00814) |
| **Weights** | [charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) |

### Referenced datasets (Vietnamese TTS)

| Dataset | Source | Notes |
|---------|--------|-------|
| **PhoAudiobook** | [thivux/phoaudiobook](https://huggingface.co/datasets/thivux/phoaudiobook) | Vu, Thi et al., *Zero-Shot Text-to-Speech for Vietnamese*, [ACL 2025](https://aclanthology.org/2025.acl-short.81/) |
| **ViVoice** | Listed on `hynt/ZipVoice-Vietnamese-2500h` model card | Large-scale Vietnamese speech corpus |
| **UEH** | Teacher Định — UEH | ~50 h additional labeled data (model card) |

> **This GUI repository** (Pham Trong Lam): Gradio layer, sample voices, normalization pipeline, long-text chunking — **not** a replacement for or official distribution of `hynt`, `k2-fsa`, or the original checkpoint authors.

---

## Third-party source attributions

Official GitHub sources for ported modules and optional normalizers.

### Inference & tokenizer

| Component | GitHub / source | Used in | License |
|-----------|-----------------|---------|---------|
| **ZipVoice** | [github.com/k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | `vendor/ZipVoice/`, `infer_engine.py` | Apache-2.0 |
| **Vietnamese checkpoint** | [huggingface.co/hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | `models/zipvoice/` | CC-BY-NC-SA-4.0 |
| **Vocos (library)** | [github.com/gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) | `vocos` package | MIT |
| **Vocos mel 24 kHz** | [huggingface.co/charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) | `models/vocoder/` | Per model card |
| **Espeak + piper_phonemize** | [github.com/k2-fsa/icefall](https://github.com/k2-fsa/icefall) · [github.com/espeak-ng/espeak-ng](https://github.com/espeak-ng/espeak-ng) | ZipVoice phonemization | Apache-2.0 / GPL (espeak) |

### Text normalization pipeline (GUI)

| Backend | GitHub / source | File / install | Notes |
|---------|-----------------|----------------|-------|
| **VieNeu** | [github.com/pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) — `vieneu_utils/core_utils.py` | `vieneu_text.py` (ported, built-in) | Punctuation cleanup only — **not** the VieNeu-TTS engine |
| **TTS structure** | Original to this repo (Pham Trong Lam) | `period_linebreak.py` (built-in) | Brackets→commas; list items→line breaks |
| **vinorm** | [github.com/NoahDrisort/vinorm](https://github.com/NoahDrisort/vinorm) | `pip install vinorm` | NSW — **not bundled in ZipVoice** |
| **vietnormalizer** | [github.com/nghimestudio/vietnormalizer](https://github.com/nghimestudio/vietnormalizer) | `pip install vietnormalizer` | Broader Vietnamese normalization |
| **sea-g2p Normalizer** | [github.com/pnnbao97/sea-g2p](https://github.com/pnnbao97/sea-g2p) | `pip install sea-g2p` | **Normalizer only**; GUI strips `<en>` tags |

**Long-text chunking** (`utils.py`): inspired by [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) chunking ideas, reimplemented for ZipVoice.

### UI & tooling

| Component | GitHub |
|-----------|--------|
| **Gradio** | [github.com/gradio-app/gradio](https://github.com/gradio-app/gradio) |
| **ONNX export tool** | Based on [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) (`onnx_toolkit.py`, `app_onnx.py`) |

---

## Bundled voices (ready after setup)

Nine WAV files in `assets/ref_audio/` with transcripts in `assets/ref_info.json`. Select from the GUI dropdown — no extra download required.

See the voice table in [README.md](README.md) (Vietnamese).

---

## Main features (`app.py` — port 7860)

- Zero-shot Vietnamese TTS from a 3–15 s reference clip + **manual transcript**
- Voice registry via `assets/ref_info.json`
- `.txt` / `.md` upload for books and long documents
- **Configurable normalization pipeline** (ordered backends; default empty; audiobook preset)
- **Preview normalization** before synthesis
- Smart chunking with pauses for sentences, paragraphs, chapters, and numbered list items
- WAV 24 kHz or MP3 export to `output/`
- CPU one-click install (`install_cpu.bat` / `run_cpu.bat`)
- Logging: `logs/app.log`, `logs/crash.log`
- **Presets** (`profiles/*.json`) — **Load preset** / **Save preset** in the GUI accordion

### Presets / profiles (`profiles/`)

JSON **schema v1** captures voice (bundled or manual upload), normalization pipeline, chunking, pauses, diffusion params (`num_step`, `guidance_scale`, `t_shift`), and export format.

| Default file | Description |
|--------------|-------------|
| `profiles/none.json` | Empty pipeline |
| `profiles/sach.json` | VieNeu + TTS structure + vinorm, voice **Ái Vy** |

**GUI:** **Preset** accordion → select file → **Load preset** (all widgets) or **Save preset** → `profiles/<name>.json`.

Shared module with the ONNX repo: `preset_io.py`. CLI is ONNX-only: [ZipVoice-Vietnamese-ONNX-GUI](https://github.com/phamtronglam2001/ZipVoice-Vietnamese-ONNX-GUI).

### ONNX tool (`app_onnx.py` — port 7861)

Environment check, export `text_encoder.onnx` / `fm_decoder.onnx` (+ INT8), PyTorch vs ONNX test.

---

## Normalization pipeline (ordered steps)

Add, remove, and reorder steps on the GUI. **Each step receives the previous step's output** (`text₀ → step₁ → text₁ → …`). No step-count limit; duplicate backends are skipped.

| Backend | pip? | Role |
|---------|------|------|
| **VieNeu** | No | Port of [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) `core_utils` |
| **Join PDF line breaks** | No | `join_soft_breaks` — merge short lowercase lines (OCR/PDF mid-sentence wraps) |
| **Newline → sentence** | No | `newline_sentence` — append `.` before line breaks: `Chương 1\nNội dung` → `Chương 1.\nNội dung` |
| **TTS structure** | No | `period_break` — brackets→commas; `một. next` → `một.\nnext` (`period_linebreak.py`) |
| **vinorm** | Yes | [NoahDrisort/vinorm](https://github.com/NoahDrisort/vinorm) |
| **vietnormalizer** | Yes | [nghimestudio/vietnormalizer](https://github.com/nghimestudio/vietnormalizer) |
| **sea-g2p Normalizer** | Yes | [pnnbao97/sea-g2p](https://github.com/pnnbao97/sea-g2p) — Normalizer only |
| **None** | — | Skip step |

**GUI default:** empty pipeline (light punctuation cleanup). **Audiobook preset** → VieNeu → TTS structure → vinorm.

**Suggested for books:** `VieNeu → TTS structure → vinorm` (or sea-g2p). For PDF/OCR text, try `join_soft_breaks` before VieNeu; for chapter headings, add `newline_sentence`.

**TTS / preview flow:** normalize the **full document** once (`normalize_full_document`) → **split** (`split_text_for_tts`) → per-chunk light cleanup only (pipeline not re-run). **Preview normalization** and **full normalized text** show the chained pipeline output with preserved `\n` and added periods.

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
- **ZipVoice upstream:** Apache-2.0 — [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice)
- **Third-party normalizers / TTS libraries:** see [Third-party source attributions](#third-party-source-attributions)

Commercial use is prohibited under the repo license and model card terms.
