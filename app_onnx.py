"""
Gradio tool: export ZipVoice → ONNX and smoke-test inference.
Port 7861 (main TTS app uses 7860).
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import gradio as gr

from assets_loader import MANUAL_CHOICE, dropdown_choices, get_voice_by_id, scan_ref_voices
from config import ONNX_DIR, OUTPUT_DIR, ROOT, ensure_ffmpeg_on_path, models_ready
from runtime_log import ONNX_LOG_FILE, setup_onnx_logging

ensure_ffmpeg_on_path()
logger = setup_onnx_logging()

_voice_cache: list = []


def _tail_log(max_lines: int = 40) -> str:
    if not ONNX_LOG_FILE.is_file():
        return "(chưa có log — chạy thao tác để ghi logs/onnx.log)"
    lines = ONNX_LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])


def _refresh_env() -> tuple[str, str]:
    from onnx_toolkit import check_environment

    return check_environment(), _tail_log()


def _refresh_voices() -> gr.Dropdown:
    global _voice_cache
    _voice_cache = scan_ref_voices()
    return gr.Dropdown(choices=dropdown_choices(_voice_cache), value=MANUAL_CHOICE)


def _pick_voice(voice_id: str) -> tuple[str | None, str]:
    voice = get_voice_by_id(voice_id, _voice_cache)
    if voice is None:
        return None, ""
    return voice.audio_path, voice.transcript


def do_export(
    quant_mode: str,
    mixed_te: str,
    mixed_fm: str,
    keep_quant_only: bool,
    export_vocos: bool,
    progress=gr.Progress(),
) -> tuple[str, str, str]:
    from onnx_quant import DEFAULT_MIXED_CONFIG
    from onnx_toolkit import export_zipvoice_onnx

    if not models_ready():
        msg = "Thiếu PyTorch models. Chạy install_cpu.bat trước."
        return msg, _refresh_env()[0], _tail_log()

    mixed_config = {
        "text_encoder": mixed_te,
        "fm_decoder": mixed_fm,
    } if quant_mode == "mixed" else None

    try:
        progress(0.05, desc="Kiểm tra onnxruntime...")
        progress(0.15, desc="Load checkpoint PyTorch...")
        progress(0.35, desc="Export text_encoder + fm_decoder...")
        result = export_zipvoice_onnx(
            quant_mode,
            mixed_config=mixed_config,
            keep_quant_only=keep_quant_only and quant_mode != "fp32",
            export_vocos=export_vocos,
        )
        progress(1.0, desc="Xong" if result.ok else "Lỗi")
        log = result.message
        if result.files:
            log += "\n\nFiles:\n" + "\n".join(f"- {f}" for f in result.files)
        env_md, _ = _refresh_env()
        return log, env_md, _tail_log()
    except Exception as exc:
        logger.error(traceback.format_exc())
        return f"Lỗi export: {exc}", *_refresh_env()


def _resolve_test_inputs(
    voice_id: str,
    ref_audio: str | None,
    ref_text: str,
    gen_text: str,
) -> tuple[str | None, str, str]:
    audio = ref_audio
    transcript = ref_text.strip()
    if voice_id and voice_id != MANUAL_CHOICE:
        v = get_voice_by_id(voice_id, _voice_cache)
        if v:
            audio = audio or v.audio_path
            transcript = transcript or v.transcript
    if not gen_text.strip():
        gen_text = "xin chào, đây là bài test zipvoice tiếng việt."
    return audio, transcript, gen_text.strip()


def do_test_onnx(
    voice_id: str,
    ref_audio: str | None,
    ref_text: str,
    gen_text: str,
    quant_mode: str,
    mixed_te: str,
    mixed_fm: str,
    vocoder_mode: str,
    speed: float,
    progress=gr.Progress(),
) -> tuple[str, str | None, str]:
    from onnx_toolkit import test_onnx_inference

    audio, transcript, text = _resolve_test_inputs(voice_id, ref_audio, ref_text, gen_text)
    mixed_config = (
        {"text_encoder": mixed_te, "fm_decoder": mixed_fm}
        if quant_mode == "mixed"
        else None
    )
    progress(0.2, desc="Load ONNX + vocoder...")
    result = test_onnx_inference(
        prompt_wav=audio or "",
        prompt_text=transcript,
        text=text,
        quant_mode=quant_mode,
        mixed_config=mixed_config,
        speed=speed,
        vocoder_mode=vocoder_mode,
    )
    progress(1.0, desc="Xong" if result.ok else "Lỗi")
    return result.message, result.wav_path, _tail_log()


def do_test_pytorch(
    voice_id: str,
    ref_audio: str | None,
    ref_text: str,
    gen_text: str,
    speed: float,
    progress=gr.Progress(),
) -> tuple[str, str | None, str]:
    from onnx_toolkit import test_pytorch_inference

    audio, transcript, text = _resolve_test_inputs(voice_id, ref_audio, ref_text, gen_text)
    progress(0.2, desc="Load PyTorch ZipVoice...")
    result = test_pytorch_inference(
        prompt_wav=audio or "",
        prompt_text=transcript,
        text=text,
        speed=speed,
    )
    progress(1.0, desc="Xong" if result.ok else "Lỗi")
    return result.message, result.wav_path, _tail_log()


def build_ui() -> gr.Blocks:
    global _voice_cache
    _voice_cache = scan_ref_voices()

    from onnx_quant import COMPONENT_QUANT_CHOICES, DEFAULT_MIXED_CONFIG, QUANT_MODE_CHOICES
    from onnx_toolkit import check_environment, onnx_ready

    with gr.Blocks(title="ZipVoice ONNX Export & Test") as demo:
        gr.Markdown(
            """
# ZipVoice ONNX — Export & Test

1. Tab **Trạng thái** — kiểm tra dependency  
2. Tab **Export** — quant variant (`int8` / `int4` / `fp16` / `mixed`) hoặc FP32 baseline  
3. Tab **Test** — so sánh PyTorch vs ONNX inference (chọn cùng quant mode)  

**Đặt tên file:** `text_encoder[_fp16|_int8|_int4].onnx` · manifest `quantization.json`  
**Quant-only (mặc định):** FP32 chỉ dùng tạm khi quant — output không còn `text_encoder.onnx` / `fm_decoder.onnx` trừ mixed có component FP32.
**INT4 CPU:** cần ORT ≥1.20 + CPU hỗ trợ MatMulNBits (x86 AVX2+); thử nghiệm trên diffusion TTS.  
**Log file:** `logs/onnx.log` · **Output audio:** `output/`
            """
        )

        with gr.Tab("0) Trạng thái"):
            env_md = gr.Markdown(check_environment())
            log_box = gr.Textbox(label="Log gần nhất (logs/onnx.log)", lines=14, max_lines=30)
            btn_refresh_env = gr.Button("Làm mới trạng thái + log", variant="secondary")
            btn_refresh_env.click(
                _refresh_env,
                outputs=[env_md, log_box],
            )
            demo.load(_refresh_env, outputs=[env_md, log_box])

        with gr.Tab("1) Export ONNX"):
            quant_mode = gr.Dropdown(
                label="Chế độ quant sau export FP32",
                choices=list(QUANT_MODE_CHOICES),
                value="int8",
                info="fp32 chỉ baseline; int8 khuyến nghị CPU; int4 ~2× nhỏ hơn int8 (thử nghiệm)",
            )
            keep_quant_only = gr.Checkbox(
                label="Chỉ giữ file quant (xóa FP32)",
                value=True,
                info="FP32 export vào temp; models/onnx/ chỉ còn bản quant (+ FP32 component nếu mixed)",
            )
            export_vocos = gr.Checkbox(
                label="Export Vocos ONNX (100 mel → mag/x/y)",
                value=True,
                info="Ghi `models/vocoder/mel_spec_24khz.onnx` — ISTFT librosa lúc inference (khớp ONNX-GUI)",
            )
            with gr.Row():
                mixed_te = gr.Dropdown(
                    label="Mixed: text_encoder",
                    choices=list(COMPONENT_QUANT_CHOICES),
                    value=DEFAULT_MIXED_CONFIG["text_encoder"],
                    visible=False,
                )
                mixed_fm = gr.Dropdown(
                    label="Mixed: fm_decoder",
                    choices=list(COMPONENT_QUANT_CHOICES),
                    value=DEFAULT_MIXED_CONFIG["fm_decoder"],
                    visible=False,
                )

            def _toggle_mixed(mode: str):
                show = mode == "mixed"
                return (
                    gr.update(visible=show),
                    gr.update(visible=show),
                    gr.update(value=mode != "fp32", interactive=mode != "fp32"),
                )

            quant_mode.change(
                _toggle_mixed,
                inputs=[quant_mode],
                outputs=[mixed_te, mixed_fm, keep_quant_only],
            )

            btn_export = gr.Button("Bắt đầu Export ONNX", variant="primary")
            export_log = gr.Textbox(label="Tiến trình export", lines=12)
            export_env = gr.Markdown(check_environment())

            btn_export.click(
                do_export,
                inputs=[quant_mode, mixed_te, mixed_fm, keep_quant_only, export_vocos],
                outputs=[export_log, export_env, log_box],
            )

        with gr.Tab("2) Test inference"):
            from onnx_toolkit import onnx_ready_report

            gr.Markdown(
                f"""
{onnx_ready_report()}
- Sau export, chạy **Test PyTorch** (baseline) rồi **Test ONNX** (cùng quant mode) để so sánh audio.
- **INT4:** copy `models/onnx/` sang ONNX-GUI repo sau khi export, hoặc chạy `quantize_onnx.py --mode int4` ở repo đích.
                """
            )
            voice_dd = gr.Dropdown(
                label="Giọng từ ref_info.json",
                choices=dropdown_choices(_voice_cache),
                value=MANUAL_CHOICE,
            )
            ref_audio = gr.Audio(label="Giọng mẫu (3–15s)", type="filepath")
            ref_text = gr.Textbox(label="Transcript giọng mẫu (bắt buộc)", lines=2)
            gen_text = gr.Textbox(
                label="Văn bản test",
                value="xin chào, đây là bài test onnx zipvoice tiếng việt.",
                lines=2,
            )
            test_quant_mode = gr.Dropdown(
                label="Quant mode cho Test ONNX",
                choices=list(QUANT_MODE_CHOICES),
                value="fp32",
            )
            with gr.Row():
                test_mixed_te = gr.Dropdown(
                    label="Mixed: text_encoder",
                    choices=list(COMPONENT_QUANT_CHOICES),
                    value=DEFAULT_MIXED_CONFIG["text_encoder"],
                    visible=False,
                )
                test_mixed_fm = gr.Dropdown(
                    label="Mixed: fm_decoder",
                    choices=list(COMPONENT_QUANT_CHOICES),
                    value=DEFAULT_MIXED_CONFIG["fm_decoder"],
                    visible=False,
                )
            test_quant_mode.change(
                _toggle_mixed, inputs=[test_quant_mode], outputs=[test_mixed_te, test_mixed_fm]
            )
            test_vocoder = gr.Radio(
                label="Vocoder cho Test ONNX",
                choices=["pytorch", "onnx"],
                value="pytorch",
                info="onnx = mel_spec_24khz.onnx + librosa ISTFT (100 mel)",
            )
            speed = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Tốc độ")

            with gr.Row():
                btn_pt = gr.Button("① Test PyTorch (baseline)", variant="secondary")
                btn_onnx = gr.Button("② Test ONNX", variant="primary")

            test_log = gr.Textbox(label="Kết quả test", lines=8)
            test_audio = gr.Audio(label="Audio vừa tạo", type="filepath")

            voice_dd.change(_pick_voice, inputs=[voice_dd], outputs=[ref_audio, ref_text])
            btn_pt.click(
                do_test_pytorch,
                inputs=[voice_dd, ref_audio, ref_text, gen_text, speed],
                outputs=[test_log, test_audio, log_box],
            )
            btn_onnx.click(
                do_test_onnx,
                inputs=[
                    voice_dd,
                    ref_audio,
                    ref_text,
                    gen_text,
                    test_quant_mode,
                    test_mixed_te,
                    test_mixed_fm,
                    test_vocoder,
                    speed,
                ],
                outputs=[test_log, test_audio, log_box],
            )

    return demo


def main() -> int:
    host = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")
    port = int(os.environ.get("GRADIO_ONNX_PORT", "7861"))

    logger.info("=" * 60)
    logger.info("ONNX tool starting | http://%s:%s", host, port)
    logger.info("Log file: %s", ONNX_LOG_FILE)

    if not models_ready():
        logger.warning("PyTorch models not ready — export/test will fail until install_cpu.bat")

    try:
        demo = build_ui()
        demo.queue(default_concurrency_limit=1).launch(
            server_name=host,
            server_port=port,
            show_error=True,
            inbrowser=True,
            allowed_paths=[str(ROOT), str(ONNX_DIR), str(OUTPUT_DIR)],
            theme=gr.themes.Soft(),
        )
        return 0
    except Exception:
        logger.critical("Failed to launch Gradio:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    code = main()
    if code != 0:
        print("\n[ERROR] ONNX tool failed. Xem logs/onnx.log", file=sys.stderr)
        input("Nhan Enter de dong...")
    sys.exit(code)
