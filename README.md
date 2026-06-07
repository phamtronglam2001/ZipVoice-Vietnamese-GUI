# ZipVoice Vietnamese TTS — Portable Offline GUI

[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)

Ứng dụng **Gradio desktop** chạy offline cho [ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — mô hình TTS zero-shot tiếng Việt (123M params, flow matching).

**Đây không phải bản copy nguyên xi** Hugging Face Space hay repo [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice). Đây là **lớp GUI + tooling** viết riêng: portable Windows CPU, giọng mẫu, pipeline chuẩn hóa text, sách dài, công cụ ONNX.

**Phiên bản chỉ ONNX (nhẹ hơn, weights có sẵn):** [ZipVoice-Vietnamese-ONNX-GUI](https://github.com/phamtronglam2001/ZipVoice-Vietnamese-ONNX-GUI)

Tiếng Việt | [English](README_EN.md)

---

## Author

| | |
|---|---|
| **Author** | [Pham Trong Lam](https://github.com/phamtronglam2001) (`phamtronglam2001`) |
| **Repository** | https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI |
| **License (repo + giọng mẫu)** | [Non-Commercial](LICENSE) — nghiên cứu / giáo dục / phi lợi nhuận |

---

## Nguồn gốc & giấy phép thành phần

| Thành phần | Nguồn | Giấy phép |
|------------|-------|-----------|
| **Mã GUI + file `.wav` mẫu** | [phamtronglam2001/ZipVoice-Vietnamese-GUI](https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI) — Pham Trong Lam | **[Non-Commercial](LICENSE)** — cấm kiếm tiền |
| **ZipVoice engine** | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | Apache-2.0 (clone vào `vendor/` khi setup) |
| **Checkpoint tiếng Việt** | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | [CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — **chỉ nghiên cứu / phi thương mại** |
| **Vocos vocoder** | Thư viện [gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) · weights [charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) | MIT (thư viện) · theo model card |
| **Chuẩn hóa text (tùy chọn)** | Xem bảng [Trích dẫn](#trích-dẫn-mã-nguồn--thư-viện-bên-thứ-ba) bên dưới | Theo từng repo |

> Audio sinh ra phải được ghi nhận là AI-generated. Tuân thủ điều khoản model card khi dùng checkpoint `hynt/ZipVoice-Vietnamese-2500h`.

---

## Lời cảm ơn (Acknowledgments)

GUI này **không** train lại model TTS. Mọi synthesis dựa trên checkpoint và engine do các tác giả / nhóm sau công bố — xin ghi nguồn khi dùng hoặc chia sẻ kết quả.

### Checkpoint tiếng Việt — Hugging Face

| | |
|---|---|
| **Tác giả / publisher** | [**Nguyen Thien Hy**](https://huggingface.co/hynt) (`hynt`) |
| **Model** | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — fine-tune ZipVoice trên **~2500 giờ** tiếng Việt |
| **Demo Space** | [hynt/ZipVoice-Vietnamese-100h](https://huggingface.co/spaces/hynt/ZipVoice-Vietnamese-100h) |
| **Giấy phép** | [CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — chỉ nghiên cứu / phi thương mại |

Theo model card: dữ liệu huấn luyện gồm **PhoAudioBook**, **ViVoice**, **UEH** (có ghi nhận thêm ~50h dữ liệu gán nhãn từ Teacher Định — Trường Đại học Kinh tế TP.HCM). Tiền xử lý audio dùng [facebookresearch/demucs](https://github.com/facebookresearch/demucs) để tách nhạc nền.

### Kiến trúc ZipVoice gốc — k2-fsa

| | |
|---|---|
| **Dự án** | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) ([k2-fsa](https://github.com/k2-fsa)) |
| **Bài báo** | Zhu, Han et al., *ZipVoice: Fast and High-Quality Zero-Shot Text-to-Speech with Flow Matching*, [arXiv:2506.13053](https://arxiv.org/abs/2506.13053) (2025) |
| **Giấy phép** | Apache-2.0 |

### Vocoder Vocos

| | |
|---|---|
| **Thư viện** | [gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) — Siuzdak, Hubert et al., [arXiv:2306.00814](https://arxiv.org/abs/2306.00814) |
| **Weights** | [charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) |

### Dataset tham chiếu (khi trích dẫn TTS tiếng Việt)

| Dataset | Nguồn | Ghi chú |
|---------|-------|---------|
| **PhoAudiobook** | [thivux/phoaudiobook](https://huggingface.co/datasets/thivux/phoaudiobook) | Vu, Thi et al., *Zero-Shot Text-to-Speech for Vietnamese*, [ACL 2025](https://aclanthology.org/2025.acl-short.81/) |
| **ViVoice** | Ghi trong model card `hynt/ZipVoice-Vietnamese-2500h` | ~1000+ giờ speech VI (theo tài liệu liên quan) |
| **UEH** | Teacher Định — ĐH Kinh tế TP.HCM | ~50h bổ sung (model card) |

> **Repo GUI này** (Pham Trong Lam): lớp Gradio, giọng mẫu, pipeline chuẩn hóa, chunk sách — **không** thay thế hay đại diện cho `hynt`, `k2-fsa`, hay các tác giả checkpoint gốc.

---

## Trích dẫn mã nguồn & thư viện bên thứ ba

Các module/port trong repo **phải ghi nguồn GitHub** khi dùng hoặc phát hành lại. Bảng dưới là danh sách chính thức.

### Inference & tokenizer

| Thành phần | GitHub / nguồn | Dùng ở đâu | Giấy phép |
|------------|----------------|------------|-----------|
| **ZipVoice** | [github.com/k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | `vendor/ZipVoice/`, `infer_engine.py` | Apache-2.0 |
| **Checkpoint VI** | [huggingface.co/hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | `models/zipvoice/` | CC-BY-NC-SA-4.0 |
| **Vocos (thư viện)** | [github.com/gemelo-ai/vocos](https://github.com/gemelo-ai/vocos) | `vocos` package, `infer_engine.py` | MIT |
| **Vocos mel 24 kHz** | [huggingface.co/charactr/vocos-mel-24khz](https://huggingface.co/charactr/vocos-mel-24khz) | `models/vocoder/` | Theo model card |
| **Espeak + piper_phonemize** | [github.com/k2-fsa/icefall](https://github.com/k2-fsa/icefall) (wheel piper_phonemize) · [github.com/espeak-ng/espeak-ng](https://github.com/espeak-ng/espeak-ng) | phonemize trong ZipVoice upstream | Apache-2.0 / GPL (espeak) |

### Pipeline chuẩn hóa text (GUI)

| Backend | GitHub / nguồn | File / cài đặt | Ghi chú |
|---------|----------------|----------------|---------|
| **VieNeu** | [github.com/pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) — `vieneu_utils/core_utils.py` (`_clean_phoneme_noise`) | `vieneu_text.py` (port, built-in) | Chỉ dọn punctuation/noise, **không** gọi engine VieNeu-TTS |
| **Cấu trúc TTS** | Viết trong repo này (Pham Trong Lam) | `period_linebreak.py` (built-in) | Ngoặc→phẩy; mục `một.` / `2.`→xuống dòng |
| **Xuống dòng → câu** | Viết trong repo này | `period_linebreak.py` (`newline_sentence`) | `Chương 1\nNội dung` → `Chương 1.\nNội dung` |
| **Gộp xuống dòng PDF** | Viết trong repo này | `period_linebreak.py` (`join_soft_breaks`) | Gộp dòng ngắn viết thường (OCR/PDF) |
| **vinorm** | [github.com/NoahDrisort/vinorm](https://github.com/NoahDrisort/vinorm) | `pip install vinorm` → `utils.py` | NSW (số, ngày…) — **không có trong ZipVoice** |
| **vietnormalizer** | [github.com/nghimestudio/vietnormalizer](https://github.com/nghimestudio/vietnormalizer) | `pip install vietnormalizer` | Chuẩn hóa tiếng Việt rộng |
| **sea-g2p Normalizer** | [github.com/pnnbao97/sea-g2p](https://github.com/pnnbao97/sea-g2p) | `pip install sea-g2p` | Chỉ `Normalizer`, **không** dùng G2P; GUI gỡ tag `<en>` |

**Chunk sách dài** (`utils.py` — `split_text_for_tts`): lấy cảm hứng từ logic chia đoạn [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS), triển khai riêng cho ZipVoice.

### UI & runtime

| Thành phần | GitHub |
|------------|--------|
| **Gradio** | [github.com/gradio-app/gradio](https://github.com/gradio-app/gradio) |
| **ONNX export tool** | Dựa trên [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) (`onnx_toolkit.py`, `app_onnx.py`) |

> **Cảnh báo:** Dùng công cụ này để **kiếm tiền / thương mại hóa** là vi phạm giấy phép và có thể dẫn đến **hệ luỵ pháp lý** về sau. Xem [LICENSE](LICENSE).

---

## Giọng mẫu có sẵn (đọc ngay sau khi clone)

Repo đã kèm **9 file WAV** trong `assets/ref_audio/` — chọn trực tiếp trên GUI sau `install_cpu.bat` + `run_cpu.bat`, **không cần tải thêm giọng**.

| ID (`ref_info.json`) | Tên hiển thị | File | Transcript (tóm tắt) |
|--------------------|--------------|------|----------------------|
| `yen_nhi` | Yến Nhi | `yen_nhi.wav` | Hội thoại gia đình — “các anh cứ đội chị lên đầu làm nóc nhà…” |
| `my_van` | Mỹ Vân | `my_van.wav` | Giọng hướng dẫn thở — bài tập hơi thở dài, sâu |
| `ai_vy` | Ái Vy | `ai_vy.wav` | Giọng truyền thông — kỷ nguyên vươn mình, trí tuệ đổi mới |
| `an_nhi` | An Nhi | `an_nhi.wav` | Tương tự Ái Vy — đoạn văn kỷ nguyên vươn mình |
| `dieu_linh` | Diệu Linh | `dieu_linh.wav` | Đoạn ngắn — khát vọng, trí tuệ đổi mới, đoàn kết |
| `khanh_toan` | Khánh Toàn | `khanh_toan.wav` | Giọng nam — kỷ nguyên vươn mình (bản rút gọn) |
| `tran_lam` | Trần Lâm | `tran_lam.wav` | Giọng nam — trí tuệ đổi mới, tương lai thịnh vượng |
| `nsnd_ha_phuong` | NSND Hà Phương | `nsnd_ha_phuong.wav` | Giọng kể chuyện — lời cuối của người sáng lập iPhone |
| `nsnd_kim_cuc` | NSND Kim Cúc | `nsnd_kim_cuc.wav` | Giọng kể — cảnh họp, lão kéo ghế lại đám đông |

Cấu hình trong `assets/ref_info.json` — mỗi giọng có `name`, `audio_path`, `text` (transcript **bắt buộc** khớp audio).

**Dùng ngay:**

1. `install_cpu.bat` → `run_cpu.bat`
2. Menu **Chọn giọng có sẵn** → chọn một dòng trong bảng trên
3. Ô 2 tự điền transcript; ô 3 nhập văn bản cần đọc → **Tổng hợp giọng nói**

---

## Chức năng chương trình

### App chính (`app.py` — port 7860)

- **Zero-shot TTS tiếng Việt** từ giọng mẫu 3–15 giây + transcript thủ công
- **Quản lý giọng** qua `assets/ref_info.json` (menu dropdown, không quét file lẻ)
- **Hai ô text tách biệt:** transcript giọng mẫu (bắt buộc) vs văn bản cần đọc
- **Upload `.txt` / `.md`** cho văn bản dài (sách, nhiều chương)
- **Pipeline chuẩn hóa** danh sách tùy chỉnh theo thứ tự (mặc định **trống**, không giới hạn số bước): VieNeu / Gộp PDF / Xuống dòng→câu / Cấu trúc TTS / vinorm / … — preset **Sách/Audiobook** gợi ý VieNeu → Cấu trúc TTS → vinorm
- **Xem trước chuẩn hóa** trước khi TTS (không load model)
- **Chia chunk thông minh** + nghỉ câu / đoạn / chương / mục đánh số (~1s)
- **Xuất** WAV 24kHz hoặc MP3 (32k/128k) vào `output/`
- **CPU-only** một click (`install_cpu.bat` / `run_cpu.bat`)
- **Logging** `logs/app.log`, `logs/crash.log`
- **Preset/profile** (`profiles/*.json`) — accordion **Tải preset** / **Lưu preset** trên GUI

### Preset / profile (`profiles/`)

Preset JSON **schema v1** lưu toàn bộ cấu hình đọc sách: giọng (bundled hoặc upload), pipeline chuẩn hóa, chunk, nghỉ, tham số diffusion (`num_step`, `guidance_scale`, `t_shift`), xuất file.

| File mặc định | Mô tả |
|---------------|--------|
| `profiles/none.json` | Pipeline trống |
| `profiles/sach.json` | VieNeu + Cấu trúc TTS + vinorm, giọng **Ái Vy** |

**GUI:** accordion **Preset** → chọn file → **Tải preset** (áp dụng mọi widget) hoặc **Lưu preset** (tên file → `profiles/<tên>.json`).

Module dùng chung với repo ONNX: `preset_io.py` · CLI: `cli_tts.py` (cùng schema preset).

### Xuất / nhập lại text đã chuẩn hóa (workflow sách dài)

```
book.txt → pipeline → book_normalized.txt → (sửa tay) → TTS (bỏ qua pipeline) → audio
```

**GUI:** **Xem trước** / **Xuất text đã chuẩn hóa (.txt)** → sửa file → upload lại, chọn **Đã chuẩn hóa (bỏ qua pipeline)** → TTS. Ô preview hiển thị text **đầy đủ**.

**CLI (PyTorch):**

```bat
python cli_tts.py synthesize -p sach -f book.txt --normalize-only --output-normalized output/book_normalized.txt
python cli_tts.py synthesize -p sach -f output/book_normalized.txt --skip-normalize -o output/book.wav
```

Preset JSON: `"input_mode": "raw"` hoặc `"prepared"`.

### Công cụ ONNX (`app_onnx.py` — port 7861)

- Kiểm tra môi trường + log `logs/onnx.log`
- Export `text_encoder.onnx`, `fm_decoder.onnx` (+ INT8)
- Test inference: **PyTorch baseline** vs **ONNX** (vocoder vẫn PyTorch)

### Script hỗ trợ

| Script | Mô tả |
|--------|-------|
| `install_cpu.bat` | Cài `.venv`, PyTorch CPU, k2, models, vendor ZipVoice |
| `run_cpu.bat` | Chạy GUI TTS |
| `run_onnx.bat` | Chạy GUI ONNX |
| `setup_ffmpeg.bat` | FFmpeg cho export MP3 |
| `fix_deps.bat` | Sửa k2 / numpy |
| `view_logs.bat` / `view_onnx_logs.bat` | Mở log |

---

## Khác biệt so với code gốc (đã sửa / thêm mới)

Repo này **không** đưa nguyên Space Hugging Face hay CLI `infer_zipvoice.py`. Các phần **tự viết hoặc sửa đáng kể**:

| Phần | Thay đổi |
|------|----------|
| **`app.py`** | Gradio GUI hoàn chỉnh: giọng từ JSON, upload txt, normalizer tùy chọn, chunk slider, export MP3 |
| **`infer_engine.py`** | Wrapper singleton ZipVoice + Vocos, CPU force, không ASR |
| **`utils.py`** | Pipeline normalize (danh sách bước), chunk sách, checkpoint, xuất text chuẩn hóa |
| **`vieneu_text.py`** | Port [VieNeu-TTS `core_utils`](https://github.com/pnnbao97/VieNeu-TTS) |
| **`period_linebreak.py`** | Ngoặc→phẩy; số+chấm→xuống dòng |
| **`config.py`** | Đường dẫn portable, ffmpeg PATH, offline env |
| **`assets_loader.py`** | Load `ref_info.json`, resolve audio path |
| **`export_audio.py`** | Lưu `output/` WAV/MP3 qua ffmpeg |
| **`download_models.py`** | Tải zipvoice + vocoder (đã **bỏ** PhoWhisper ASR) |
| **`runtime_log.py`** | File log + crash hook (+ log riêng ONNX) |
| **`app_onnx.py` + `onnx_toolkit.py`** | GUI export/test ONNX, lazy import, so sánh PyTorch |
| **`setup_cpu.ps1` / `install_cpu.bat`** | PyTorch CPU + k2 CPU wheel, piper_phonemize |
| **`setup_ffmpeg.ps1`** | Bundle ffmpeg |
| **Transcript** | **Bắt buộc thủ công** — không auto transcribe (chính sách anti careless cloning) |
| **`assets/ref_info.json`** | Registry giọng + transcript cố định |

**Không sửa** core model trong `vendor/ZipVoice/` — clone nguyên bản khi setup.

---

## Yêu cầu hệ thống

- Windows 10/11 (script `.bat` / `.ps1`; Linux/macOS cần chỉnh path)
- Python 3.10–3.13 (khuyến nghị 3.10–3.11)
- Git (clone ZipVoice lúc setup)
- ~5 GB đĩa (venv + models; không commit models vào repo)
- CPU đủ RAM 8GB+; GPU tùy chọn

---

## Cài đặt

### 1. Clone repo

```bat
git clone https://github.com/phamtronglam2001/ZipVoice-Vietnamese-GUI.git
cd ZipVoice-Vietnamese-GUI
```

### 2. Setup một lần (cần internet)

```bat
install_cpu.bat
```

Hoặc PowerShell:

```powershell
.\setup_cpu.ps1
```

Script sẽ:

1. Tạo `.venv`
2. Cài PyTorch CPU, k2, dependencies (vinorm, vietnormalizer, sea-g2p, …)
3. Cài `piper_phonemize` (espeak tokenizer)
4. Clone `vendor/ZipVoice`
5. Tải weights vào `models/zipvoice/`, `models/vocoder/`

### 3. FFmpeg (nếu export MP3 lỗi)

```bat
setup_ffmpeg.bat
```

### 4. Chạy

```bat
run_cpu.bat
```

Mở **http://127.0.0.1:7860**

### 5. Portable / offline

Copy cả thư mục (gồm `.venv`, `models`, `vendor`) sang máy khác → chỉ cần `run_cpu.bat`.

---

## Sử dụng nhanh

1. Chọn giọng từ menu **assets/** hoặc upload WAV 3–15s
2. **Ô 2:** transcript đúng với audio giọng mẫu (**bắt buộc**)
3. **Ô 3:** văn bản TTS hoặc upload `.txt`
4. Cấu hình **pipeline chuẩn hóa** (danh sách bước) và **max ký tự/chunk**; **Xem trước** / **Xuất .txt**
5. **Tổng hợp giọng nói** → file trong `output/`

### Thêm giọng mới

```json
{
  "ten_giong": {
    "name": "Tên hiển thị",
    "audio_path": "assets/ref_audio/ten_giong.wav",
    "text": "Transcript chính xác khớp file audio..."
  }
}
```

Đặt WAV vào `assets/ref_audio/`, cập nhật JSON, bấm **Làm mới danh sách** trên GUI.

### Pipeline chuẩn hóa (chuỗi bước tuần tự)

Thêm/xóa/sắp xếp bước trên GUI — **mỗi bước nhận output của bước trước** (`text₀ → bước₁ → text₁ → …`). Không giới hạn số bước; không cho trùng cùng backend.

| Backend | pip? | Vai trò |
|---------|------|---------|
| **VieNeu** | Không | Dọn punctuation/noise — port [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) |
| **Gộp xuống dòng PDF** | Không | `join_soft_breaks` — gộp dòng ngắn viết thường (text OCR/PDF bị ngắt giữa câu) |
| **Xuống dòng → câu** | Không | `newline_sentence` — thêm `.` trước xuống dòng: `Chương 1\nNội dung` → `Chương 1.\nNội dung` |
| **Cấu trúc TTS** | Không | `period_break` — `mẫu (mẹ)`→`mẫu, mẹ`; `một. đoạn`→`một.\nđoạn` (`period_linebreak.py`) |
| **vinorm** | Có | NSW — [NoahDrisort/vinorm](https://github.com/NoahDrisort/vinorm) |
| **vietnormalizer** | Có | [nghimestudio/vietnormalizer](https://github.com/nghimestudio/vietnormalizer) |
| **sea-g2p** | Có | [pnnbao97/sea-g2p](https://github.com/pnnbao97/sea-g2p) — **chỉ Normalizer** |
| **Không** | — | Bỏ qua bước |

**Mặc định GUI:** pipeline **trống** (chỉ dọn dấu câu). Preset **Sách/Audiobook** → VieNeu → Cấu trúc TTS → vinorm.

**Gợi ý sách:** `VieNeu → Cấu trúc TTS → vinorm` (hoặc sea-g2p). PDF/OCR: thử `join_soft_breaks` trước VieNeu; tiêu đề chương: thêm `newline_sentence`.

**Luồng TTS / preview:** chuẩn hóa **toàn bộ** văn bản một lần (`normalize_full_document`) → **chia chunk** (`split_text_for_tts`) → mỗi chunk chỉ dọn dấu câu nhẹ (không chạy lại pipeline). Ô **Xem trước** / **Text đầy đủ sau chuẩn hóa** hiển thị đúng output chuỗi pipeline, **giữ `\n`** và dấu `.` đã thêm.

### Văn bản dài

- Upload `.txt` / `.md`; tiêu đề `Chương 1` trên dòng riêng
- Chia: chương → đoạn → câu → max chars/chunk
- Nghỉ: ~1.2s chương, ~0.65s đoạn, ~0.35s câu, **~1s sau mục `một.` / `2.`**

---

## ONNX tool

```bat
run_onnx.bat
```

**http://127.0.0.1:7861** — Tab Trạng thái → Export → Test PyTorch rồi Test ONNX.

---

## Cấu trúc thư mục

```
ZipVoice-Vietnamese-GUI/
├── app.py, app_onnx.py      # GUI
├── infer_engine.py          # Inference wrapper
├── utils.py, config.py      # Core helpers
├── vieneu_text.py           # VieNeu punctuation cleanup
├── period_linebreak.py      # Ngoặc→phẩy, số+chấm→xuống dòng
├── assets/
│   ├── ref_info.json        # Registry 9 giọng
│   └── ref_audio/*.wav      # Giọng mẫu (committed)
├── data/ref_audio/          # Alias path (tùy chọn)
├── output/                  # Audio xuất
├── models/                  # Tải khi setup (gitignore)
├── vendor/ZipVoice/         # Clone khi setup (gitignore)
├── logs/                    # Runtime logs (gitignore)
└── *.bat, *.ps1             # Launcher Windows
```

---

## Troubleshooting

| Vấn đề | Cách xử lý |
|--------|------------|
| `Models not found` | Chạy `install_cpu.bat` |
| App thoát im lặng | `view_logs.bat` → `logs/app.log` |
| `Chưa cài vinorm` | `pip install vinorm` hoặc bỏ khỏi pipeline; dùng VieNeu / Cấu trúc TTS |
| Thiếu vietnormalizer / sea-g2p | `.venv\Scripts\pip install -r requirements-cpu.txt` |
| Ngoặc đọc liền | Bật **Cấu trúc TTS** (Bước 2) |
| ffmpeg not found | `setup_ffmpeg.bat` |
| k2 lỗi | `fix_deps.bat` |
| ONNX màn hình đen | `view_onnx_logs.bat`; `pip install -r requirements-onnx.txt` |
| Giọng kém | Transcript ô 2 chính xác; audio sạch 5–10s |

---

## Biến môi trường

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `ZIPVOICE_FORCE_CPU` | `1` trong `run_cpu.bat` | Ép CPU |
| `GRADIO_SERVER_PORT` | `7860` / `7861` | Port TTS / ONNX |
| `GRADIO_SHARE` | `0` | `1` = public Gradio link |

---

## License

- **Repo này (mã nguồn + file `.wav` mẫu):** [Non-Commercial License](LICENSE) — Copyright (c) 2026 Pham Trong Lam  
  Chỉ được dùng **nghiên cứu, giáo dục, phi lợi nhuận**. **Cấm** mọi hình thức **kiếm tiền / thương mại**. Vi phạm có thể bị **xử lý pháp lý** (bản quyền, quyền giọng nói, vi phạm NC license, v.v.).
- **Model weights `hynt/ZipVoice-Vietnamese-2500h`:** CC-BY-NC-SA-4.0 — non-commercial research; disclose AI-generated audio
- **ZipVoice upstream:** Apache-2.0 — [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice)
- **Thư viện chuẩn hóa / TTS bên thứ ba:** xem [Trích dẫn mã nguồn](#trích-dẫn-mã-nguồn--thư-viện-bên-thứ-ba)
