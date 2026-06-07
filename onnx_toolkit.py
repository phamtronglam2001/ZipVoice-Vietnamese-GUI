"""
Export ZipVoice Vietnamese checkpoint to ONNX and run smoke-test inference.
Vocos vocoder stays PyTorch (same as upstream ZipVoice ONNX path).
Heavy imports are lazy so the Gradio GUI can start even before onnxruntime is installed.
"""
from __future__ import annotations

import json
import logging
import shutil
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

from config import (
    ONNX_DIR,
    OUTPUT_DIR,
    VOCODER_DIR,
    ZIPVOICE_CKPT,
    ZIPVOICE_CONFIG,
    ZIPVOICE_TOKENS,
    ensure_vendor_on_path,
    models_ready,
    set_offline_env,
)

ensure_vendor_on_path()
set_offline_env()

logger = logging.getLogger("zipvoice_onnx")

SAMPLING_RATE = 24000
FEAT_SCALE = 0.1
TARGET_RMS = 0.1


@dataclass
class ExportResult:
    ok: bool
    message: str
    files: list[str]


@dataclass
class TestResult:
    ok: bool
    message: str
    wav_path: str | None
    rtf: float | None
    seconds: float | None


def _onnx_files(use_int8: bool = False) -> list[str]:
    if use_int8:
        return ["text_encoder_int8.onnx", "fm_decoder_int8.onnx"]
    return ["text_encoder.onnx", "fm_decoder.onnx"]


def _check_onnxruntime() -> tuple[bool, str]:
    try:
        import onnxruntime as ort  # noqa: F401

        import onnx  # noqa: F401

        return True, ""
    except ImportError as exc:
        return False, (
            f"Thiếu onnxruntime/onnx: {exc}\n"
            "Chạy: .venv\\Scripts\\pip install -r requirements-onnx.txt"
        )


def check_environment() -> str:
    """Markdown trạng thái môi trường — không import zipvoice onnx."""
    lines = ["### Kiểm tra môi trường ONNX", ""]

    ok, msg = _check_onnxruntime()
    lines.append(f"- **onnxruntime + onnx:** {'OK' if ok else 'THIẾU — ' + msg}")

    lines.append(f"- **PyTorch models:** {'OK' if models_ready() else 'THIẾU — chạy install_cpu.bat'}")
    for label, path in [
        ("config", ZIPVOICE_CONFIG),
        ("tokens", ZIPVOICE_TOKENS),
        ("checkpoint", ZIPVOICE_CKPT),
        ("vocoder", VOCODER_DIR),
    ]:
        exists = path.is_file() or (path.is_dir() and label == "vocoder")
        lines.append(f"- `{path.name}`: {'OK' if exists else 'missing'}")

    lines.append("")
    lines.append(onnx_status())
    lines.append("")
    lines.append("**Log:** `logs/onnx.log`")
    return "\n".join(lines)


def onnx_status() -> str:
    lines = ["**ONNX artifacts** (`models/onnx/`):"]
    if not ONNX_DIR.is_dir():
        lines.append("- (chưa export)")
        return "\n".join(lines)

    for name in [
        "text_encoder.onnx",
        "fm_decoder.onnx",
        "text_encoder_int8.onnx",
        "fm_decoder_int8.onnx",
        "model.json",
        "tokens.txt",
    ]:
        p = ONNX_DIR / name
        if p.is_file():
            mb = p.stat().st_size / (1024 * 1024)
            lines.append(f"- `{name}` — {mb:.1f} MB")
        else:
            lines.append(f"- `{name}` — *missing*")

    lines.append("")
    lines.append("**Không export ONNX:** Vocos vocoder (PyTorch)")
    return "\n".join(lines)


def onnx_ready(use_int8: bool = False) -> bool:
    for f in _onnx_files(use_int8):
        if not (ONNX_DIR / f).is_file():
            return False
    return (ONNX_DIR / "model.json").is_file() and (ONNX_DIR / "tokens.txt").is_file()


def _import_zipvoice_onnx_stack():
    import torch
    import torchaudio
    from zipvoice.bin.infer_zipvoice import get_vocoder
    from zipvoice.bin.infer_zipvoice_onnx import OnnxModel, sample
    from zipvoice.bin.onnx_export import (
        OnnxFlowMatchingModel,
        OnnxTextModel,
        export_fm_decoder,
        export_text_encoder,
    )
    from zipvoice.models.zipvoice import ZipVoice
    from zipvoice.tokenizer.tokenizer import EspeakTokenizer
    from zipvoice.utils.checkpoint import load_checkpoint
    from zipvoice.utils.feature import VocosFbank
    from zipvoice.utils.scaling_converter import convert_scaled_to_non_scaled

    return {
        "torch": torch,
        "torchaudio": torchaudio,
        "get_vocoder": get_vocoder,
        "OnnxModel": OnnxModel,
        "sample": sample,
        "OnnxFlowMatchingModel": OnnxFlowMatchingModel,
        "OnnxTextModel": OnnxTextModel,
        "export_fm_decoder": export_fm_decoder,
        "export_text_encoder": export_text_encoder,
        "ZipVoice": ZipVoice,
        "EspeakTokenizer": EspeakTokenizer,
        "load_checkpoint": load_checkpoint,
        "VocosFbank": VocosFbank,
        "convert_scaled_to_non_scaled": convert_scaled_to_non_scaled,
    }


def export_zipvoice_onnx(export_int8: bool = True) -> ExportResult:
    """Export text_encoder + fm_decoder ONNX from local Vietnamese checkpoint."""
    ok, dep_msg = _check_onnxruntime()
    if not ok:
        return ExportResult(False, dep_msg, [])

    log_lines: list[str] = []

    def step(msg: str) -> None:
        logger.info(msg)
        log_lines.append(msg)

    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        zv = _import_zipvoice_onnx_stack()

        for p in (ZIPVOICE_CONFIG, ZIPVOICE_TOKENS, ZIPVOICE_CKPT):
            if not p.is_file():
                return ExportResult(False, f"Thiếu file PyTorch: {p}", [])

        ONNX_DIR.mkdir(parents=True, exist_ok=True)
        step("[1/6] Copy model.json + tokens.txt → models/onnx/")
        shutil.copy2(ZIPVOICE_CONFIG, ONNX_DIR / "model.json")
        shutil.copy2(ZIPVOICE_TOKENS, ONNX_DIR / "tokens.txt")

        with open(ZIPVOICE_CONFIG, encoding="utf-8") as f:
            model_config = json.load(f)

        EspeakTokenizer = zv["EspeakTokenizer"]
        tokenizer = EspeakTokenizer(token_file=str(ZIPVOICE_TOKENS), lang="vi")
        tokenizer_config = {
            "vocab_size": tokenizer.vocab_size,
            "pad_id": tokenizer.pad_id,
        }

        step("[2/6] Load PyTorch ZipVoice checkpoint...")
        ZipVoice = zv["ZipVoice"]
        load_checkpoint = zv["load_checkpoint"]
        convert_scaled_to_non_scaled = zv["convert_scaled_to_non_scaled"]

        model = ZipVoice(**model_config["model"], **tokenizer_config)
        load_checkpoint(filename=str(ZIPVOICE_CKPT), model=model, strict=True)
        model.eval()
        convert_scaled_to_non_scaled(model, inplace=True, is_onnx=True)

        text_encoder_file = ONNX_DIR / "text_encoder.onnx"
        fm_decoder_file = ONNX_DIR / "fm_decoder.onnx"

        step("[3/6] Export text_encoder.onnx ...")
        zv["export_text_encoder"](zv["OnnxTextModel"](model=model), str(text_encoder_file))
        step("[4/6] Export fm_decoder.onnx ...")
        zv["export_fm_decoder"](
            zv["OnnxFlowMatchingModel"](model=model, distill=False),
            str(fm_decoder_file),
        )

        created = [text_encoder_file.name, fm_decoder_file.name]

        if export_int8:
            step("[5/6] Quantize INT8 (MatMul)...")
            te_int8 = ONNX_DIR / "text_encoder_int8.onnx"
            fm_int8 = ONNX_DIR / "fm_decoder_int8.onnx"
            quantize_dynamic(
                model_input=str(text_encoder_file),
                model_output=str(te_int8),
                op_types_to_quantize=["MatMul"],
                weight_type=QuantType.QInt8,
            )
            quantize_dynamic(
                model_input=str(fm_decoder_file),
                model_output=str(fm_int8),
                op_types_to_quantize=["MatMul"],
                weight_type=QuantType.QInt8,
            )
            created.extend([te_int8.name, fm_int8.name])
        else:
            step("[5/6] Bỏ qua INT8.")

        step("[6/6] Export hoàn tất.")
        msg = "\n".join(log_lines) + (
            f"\n\nExport xong {len(created)} file vào `{ONNX_DIR}`.\n"
            "Vocos vocoder vẫn dùng PyTorch (`models/vocoder/`)."
        )
        return ExportResult(True, msg, created)

    except Exception as exc:
        logger.exception("ONNX export failed")
        detail = traceback.format_exc()
        return ExportResult(False, f"Export lỗi: {exc}\n\n{detail}", [])


def _load_vocoder_local():
    zv = _import_zipvoice_onnx_stack()
    vocoder = zv["get_vocoder"](str(VOCODER_DIR))
    return vocoder.eval()


def test_onnx_inference(
    prompt_wav: str,
    prompt_text: str,
    text: str,
    use_int8: bool = False,
    speed: float = 1.0,
    out_path: Path | None = None,
) -> TestResult:
    ok, dep_msg = _check_onnxruntime()
    if not ok:
        return TestResult(False, dep_msg, None, None, None)

    if not onnx_ready(use_int8):
        return TestResult(
            False,
            "Chưa có ONNX — tab Export → bấm Export ONNX trước.",
            None,
            None,
            None,
        )
    if not prompt_wav or not Path(prompt_wav).is_file():
        return TestResult(False, "Thiếu file giọng mẫu.", None, None, None)
    if not prompt_text.strip() or not text.strip():
        return TestResult(False, "Thiếu transcript giọng mẫu hoặc văn bản test.", None, None, None)

    try:
        logger.info("ONNX test start | int8=%s | text_len=%d", use_int8, len(text))
        zv = _import_zipvoice_onnx_stack()
        torch = zv["torch"]
        torchaudio = zv["torchaudio"]

        te_name, fm_name = _onnx_files(use_int8)
        model = zv["OnnxModel"](
            str(ONNX_DIR / te_name),
            str(ONNX_DIR / fm_name),
            num_thread=1,
        )
        tokenizer = zv["EspeakTokenizer"](
            token_file=str(ONNX_DIR / "tokens.txt"), lang="vi"
        )
        feature_extractor = zv["VocosFbank"]()
        vocoder = _load_vocoder_local()

        prompt_audio, sr = torchaudio.load(prompt_wav)
        if sr != SAMPLING_RATE:
            prompt_audio = torchaudio.transforms.Resample(sr, SAMPLING_RATE)(
                prompt_audio
            )
        prompt_rms = torch.sqrt(torch.mean(torch.square(prompt_audio)))
        if prompt_rms < TARGET_RMS:
            prompt_audio = prompt_audio * TARGET_RMS / prompt_rms

        prompt_features = feature_extractor.extract(
            prompt_audio, sampling_rate=SAMPLING_RATE
        ).unsqueeze(0) * FEAT_SCALE

        tokens = tokenizer.texts_to_token_ids([text.lower()])
        prompt_tokens = tokenizer.texts_to_token_ids([prompt_text.lower()])

        t0 = time.perf_counter()
        pred = zv["sample"](
            model=model,
            tokens=tokens,
            prompt_tokens=prompt_tokens,
            prompt_features=prompt_features,
            speed=speed,
            num_step=16,
            guidance_scale=1.0,
        )
        pred = pred.permute(0, 2, 1) / FEAT_SCALE
        wav = vocoder.decode(pred).squeeze(1).clamp(-1, 1)
        if prompt_rms < TARGET_RMS:
            wav = wav * prompt_rms / TARGET_RMS
        elapsed = time.perf_counter() - t0
        dur = wav.shape[-1] / SAMPLING_RATE
        rtf = elapsed / dur if dur > 0 else 0

        out = out_path or (OUTPUT_DIR / "onnx_test_output.wav")
        out.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(out), wav.cpu(), SAMPLING_RATE)

        logger.info("ONNX test OK | %.2fs audio | RTF %.3f", dur, rtf)
        return TestResult(
            True,
            f"ONNX inference OK\n"
            f"- Audio: {dur:.2f}s · RTF {rtf:.3f} · int8={use_int8}\n"
            f"- File: `{out}`\n"
            f"- Vocoder: PyTorch Vocos (như upstream)",
            str(out),
            rtf,
            dur,
        )
    except Exception as exc:
        logger.exception("ONNX test failed")
        return TestResult(
            False,
            f"Test lỗi: {exc}\n\n{traceback.format_exc()}",
            None,
            None,
            None,
        )


def test_pytorch_inference(
    prompt_wav: str,
    prompt_text: str,
    text: str,
    speed: float = 1.0,
) -> TestResult:
    """Baseline PyTorch — so sánh với ONNX sau export."""
    if not models_ready():
        return TestResult(False, "Thiếu PyTorch models.", None, None, None)
    if not prompt_wav or not Path(prompt_wav).is_file():
        return TestResult(False, "Thiếu file giọng mẫu.", None, None, None)
    if not prompt_text.strip() or not text.strip():
        return TestResult(False, "Thiếu transcript hoặc văn bản test.", None, None, None)

    try:
        import torchaudio
        from infer_engine import ZipVoiceEngine

        logger.info("PyTorch baseline test start")
        engine = ZipVoiceEngine.get()
        t0 = time.perf_counter()
        wav_t = engine.generate(
            prompt_text=prompt_text.lower(),
            prompt_wav=prompt_wav,
            text=text.lower(),
            speed=speed,
        ).detach().cpu()
        elapsed = time.perf_counter() - t0
        dur = wav_t.shape[-1] / engine.sampling_rate
        rtf = elapsed / dur if dur > 0 else 0

        out = OUTPUT_DIR / "pytorch_test_output.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(out), wav_t, engine.sampling_rate)

        logger.info("PyTorch test OK | %.2fs | RTF %.3f", dur, rtf)
        return TestResult(
            True,
            f"PyTorch inference OK (baseline)\n"
            f"- Audio: {dur:.2f}s · RTF {rtf:.3f}\n"
            f"- File: `{out}`",
            str(out),
            rtf,
            dur,
        )
    except Exception as exc:
        logger.exception("PyTorch test failed")
        return TestResult(
            False,
            f"PyTorch test lỗi: {exc}\n\n{traceback.format_exc()}",
            None,
            None,
            None,
        )
