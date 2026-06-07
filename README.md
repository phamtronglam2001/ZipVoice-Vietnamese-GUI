# ZipVoice Vietnamese TTS — Portable Offline GUI

[![License: Non-Commercial](https://img.shields.io/badge/License-Non--Commercial-red.svg)](LICENSE)

Ứng dụng **Gradio desktop** chạy offline cho [ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) — mô hình TTS zero-shot tiếng Việt (123M params, flow matching).

**Đây không phải bản copy nguyên xi** Hugging Face Space hay repo [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice). Đây là **lớp GUI + tooling** viết riêng, tối ưu cài đặt portable trên Windows CPU, quản lý giọng mẫu, chuẩn hóa text, văn bản dài và công cụ ONNX.

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
| **Mã GUI + file `.wav` mẫu** | Pham Trong Lam | **[Non-Commercial](LICENSE)** — cấm kiếm tiền |
| **ZipVoice engine** | [k2-fsa/ZipVoice](https://github.com/k2-fsa/ZipVoice) | Apache-2.0 (clone vào `vendor/` khi setup) |
| **Checkpoint tiếng Việt** | [hynt/ZipVoice-Vietnamese-2500h](https://huggingface.co/hynt/ZipVoice-Vietnamese-2500h) | [CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — **chỉ nghiên cứu / phi thương mại** |
| **Vocos vocoder** | [k2-fsa/Vocos](https://huggingface.co/k2-fsa/Vocos) | Theo model card |
| **vinorm / vietnormalizer / sea-g2p** | Thư viện PyPI bên thứ ba | Theo từng gói |

> Audio sinh ra phải được ghi nhận là AI-generated. Tuân thủ điều khoản model card khi dùng checkpoint `hynt/ZipVoice-Vietnamese-2500h`.

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
- **Chuẩn hóa text** (chọn 1): không / vinorm / vietnormalizer / sea-g2p Normalizer
- **Chia chunk thông minh** + khoảng nghỉ theo câu / đoạn / chương
- **Xuất** WAV 24kHz hoặc MP3 (32k/128k) vào `output/`
- **CPU-only** một click (`install_cpu.bat` / `run_cpu.bat`)
- **Logging** `logs/app.log`, `logs/crash.log`

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
| **`utils.py`** | `split_text_for_tts` (đoạn/câu/chương + pause), 4 backend normalize, `read_text_file` |
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
4. Chọn **chuẩn hóa text** và **max ký tự/chunk** nếu cần
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

### Chuẩn hóa text

| Backend | Ghi chú |
|---------|---------|
| Không | Chỉ dọn dấu câu |
| vinorm | Mặc định |
| vietnormalizer | Số, ngày, tiền (pure Python) |
| sea-g2p Normalizer | Ký hiệu khoa học; **chỉ Normalizer**, không G2P |

### Văn bản dài

- Format: đoạn cách `\n\n`, tiêu đề `Chương 1` trên dòng riêng
- Chia: chương → đoạn → câu → max chars/chunk
- Nghỉ: ~1.2s / chương, ~0.65s / đoạn, ~0.35s / câu

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
| Thiếu vietnormalizer / sea-g2p | `.venv\Scripts\pip install -r requirements-cpu.txt` |
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
