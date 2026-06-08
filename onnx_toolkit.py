"""
Export ZipVoice Vietnamese checkpoint to ONNX and run smoke-test inference.
Vocos: optional ONNX export (mag/x/y + librosa ISTFT) or PyTorch decode at test time.
Heavy imports are lazy so the Gradio GUI can start even before onnxruntime is installed.
"""
from __future__ import annotations

import json
import logging
import shutil
import tempfile
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
from onnx_quant import (
    DEFAULT_MIXED_CONFIG,
    QUANT_MODE_CHOICES,
    QuantComponent,
    QuantMode,
    export_quant_variants,
    format_sizes,
    needed_fp32_baselines,
    normalize_quant_mode,
    onnx_filenames,
    onnx_ready_for_mode,
    read_quant_manifest,
    write_quant_manifest,
)

ensure_vendor_on_path()
set_offline_env()

logger = logging.getLogger("zipvoice_onnx")

SAMPLING_RATE = 24000
FEAT_SCALE = 0.1
TARGET_RMS = 0.1


def vocos_onnx_path() -> Path:
    from vocos_export import VOCOS_ONNX_NAME

    return VOCODER_DIR / VOCOS_ONNX_NAME


def vocos_onnx_ready() -> bool:
    return vocos_onnx_path().is_file()


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


def _onnx_files(
    quant_mode: QuantMode | str = "fp32",
    *,
    use_int8: bool | None = None,
    mixed_config: dict[str, QuantComponent] | None = None,
) -> list[str]:
    te, fm = onnx_filenames(normalize_quant_mode(quant_mode, use_int8=use_int8), mixed_config)
    return [te, fm]


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

    artifact_names = [
        "text_encoder.onnx",
        "fm_decoder.onnx",
        "text_encoder_fp16.onnx",
        "fm_decoder_fp16.onnx",
        "text_encoder_int8.onnx",
        "fm_decoder_int8.onnx",
        "text_encoder_int4.onnx",
        "fm_decoder_int4.onnx",
        "model.json",
        "tokens.txt",
        "quantization.json",
    ]
    voc_path = vocos_onnx_path()
    if voc_path.is_file():
        mb = voc_path.stat().st_size / (1024 * 1024)
        lines.append(f"- `{voc_path.name}` (vocoder, 100 mel) — {mb:.1f} MB")
    else:
        lines.append(f"- `{voc_path.name}` (vocoder) — *missing*")

    for name in artifact_names:
        p = ONNX_DIR / name
        if p.is_file():
            mb = p.stat().st_size / (1024 * 1024)
            lines.append(f"- `{name}` — {mb:.1f} MB")
        elif name.endswith(".onnx"):
            lines.append(f"- `{name}` — *missing*")

    manifest = read_quant_manifest(ONNX_DIR)
    if manifest:
        lines.append("")
        lines.append(f"**quantization.json:** mode=`{manifest.get('mode', '?')}`")

    lines.append("")
    lines.append(
        "**Vocoder ONNX:** `models/vocoder/mel_spec_24khz.onnx` "
        "(100 mel → mag/x/y; ISTFT librosa lúc inference)"
    )
    return "\n".join(lines)


def onnx_ready(
    quant_mode: QuantMode | str = "fp32",
    *,
    use_int8: bool | None = None,
    mixed_config: dict[str, QuantComponent] | None = None,
) -> bool:
    mode = normalize_quant_mode(quant_mode, use_int8=use_int8)
    mixed = mixed_config if mode == "mixed" else None
    return onnx_ready_for_mode(ONNX_DIR, mode, mixed)


def onnx_ready_report() -> str:
    """Markdown summary of quant variant readiness for GUI."""
    from onnx_quant import missing_onnx_files, quant_readiness_hint

    lines = ["**Quant readiness:**"]
    for mode in QUANT_MODE_CHOICES:
        mixed = DEFAULT_MIXED_CONFIG if mode == "mixed" else None
        missing = missing_onnx_files(ONNX_DIR, mode, mixed)
        ready = not missing
        lines.append(f"- ONNX **{mode}** ready: **{ready}**")
        if not ready:
            hint = quant_readiness_hint(mode, missing)
            if hint:
                lines.append(f"  - {hint}")
            if missing:
                lines.append(f"  - Missing: `{', '.join(missing)}`")
    return "\n".join(lines)


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


def export_zipvoice_onnx(
    quant_mode: QuantMode | str = "int8",
    *,
    export_int8: bool | None = None,
    mixed_config: dict[str, QuantComponent] | None = None,
    keep_quant_only: bool = True,
    export_vocos: bool = True,
) -> ExportResult:
    """Export text_encoder + fm_decoder ONNX from local Vietnamese checkpoint."""
    ok, dep_msg = _check_onnxruntime()
    if not ok:
        return ExportResult(False, dep_msg, [])

    mode = normalize_quant_mode(quant_mode, use_int8=export_int8)
    mixed = mixed_config or DEFAULT_MIXED_CONFIG

    log_lines: list[str] = []

    def step(msg: str) -> None:
        logger.info(msg)
        log_lines.append(msg)

    try:
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

        use_temp_fp32 = mode != "fp32" and keep_quant_only
        fp32_dir = ONNX_DIR
        temp_ctx = None
        if use_temp_fp32:
            temp_ctx = tempfile.TemporaryDirectory(prefix="zipvoice_onnx_fp32_")
            fp32_dir = Path(temp_ctx.name)
            step("[3/6] Export text_encoder (FP32 → temp, không ghi ra models/onnx/) ...")
        else:
            step("[3/6] Export text_encoder.onnx ...")

        text_encoder_file = fp32_dir / "text_encoder.onnx"
        fm_decoder_file = fp32_dir / "fm_decoder.onnx"

        zv["export_text_encoder"](zv["OnnxTextModel"](model=model), str(text_encoder_file))

        if not use_temp_fp32:
            step("[4/6] Export fm_decoder.onnx ...")
        else:
            step("[4/6] Export fm_decoder (FP32 → temp) ...")
        zv["export_fm_decoder"](
            zv["OnnxFlowMatchingModel"](model=model, distill=False),
            str(fm_decoder_file),
        )

        mixed_cfg = mixed if mode == "mixed" else None

        if mode == "fp32":
            created = [text_encoder_file.name, fm_decoder_file.name]
            step("[5/6] Chỉ FP32 — không tạo bản quant.")
            write_quant_manifest(ONNX_DIR, "fp32", created=created)
        else:
            step(f"[5/6] Quantize mode={mode} ...")
            if mode == "mixed":
                step(
                    f"  mixed: text_encoder={mixed['text_encoder']}, "
                    f"fm_decoder={mixed['fm_decoder']}"
                )
            keep_fp32 = not keep_quant_only
            quant_created = export_quant_variants(
                ONNX_DIR,
                mode,
                mixed_config=mixed_cfg,
                fp32_source_dir=fp32_dir if use_temp_fp32 else None,
                keep_fp32_baseline=keep_fp32,
            )
            if keep_quant_only:
                created = quant_created
                needed = needed_fp32_baselines(mode, mixed_cfg)
                if needed:
                    step(
                        f"✓ FP32 intermediate removed; shipped quant + "
                        f"{', '.join(sorted(needed))}"
                    )
                else:
                    step(f"✓ FP32 intermediate removed; shipped **{mode}** only.")
            elif mode in ("int8", "int4", "fp16"):
                created = ["text_encoder.onnx", "fm_decoder.onnx"] + quant_created
            else:
                created = quant_created

        if temp_ctx is not None:
            temp_ctx.cleanup()

        te_name, fm_name = onnx_filenames(mode, mixed_cfg)
        step("[6/7] ZipVoice ONNX hoàn tất.")
        if export_vocos:
            step("[7/7] Export Vocos vocoder ONNX (100 mel → mag/x/y)...")
            from vocos_export import export_vocos_onnx

            voc_result = export_vocos_onnx(VOCODER_DIR)
            if voc_result.ok and voc_result.path:
                created.append(Path(voc_result.path).name)
                step(voc_result.message.split("\n")[0])
            else:
                step(f"Vocos export thất bại: {voc_result.message}")
        else:
            step("[7/7] Bỏ qua export Vocos (chỉ PyTorch).")

        size_note = format_sizes(ONNX_DIR, (te_name, fm_name))
        voc_note = ""
        if export_vocos and vocos_onnx_ready():
            voc_note = f"\nVocoder ONNX: `{vocos_onnx_path().name}` trong `models/vocoder/`."
        elif export_vocos:
            voc_note = "\nVocoder ONNX: export thất bại — test vẫn dùng PyTorch vocoder."
        else:
            voc_note = "\nVocoder: PyTorch only (`models/vocoder/`)."
        msg = "\n".join(log_lines) + (
            f"\n\nExport xong {len(created)} file vào `{ONNX_DIR}` (+ vocoder nếu có).\n"
            f"Mode: **{mode}** · Inference files: {size_note}{voc_note}\n"
            "Copy `models/onnx/` và `models/vocoder/mel_spec_24khz.onnx` sang ONNX-GUI repo."
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
    quant_mode: QuantMode | str = "fp32",
    *,
    use_int8: bool | None = None,
    mixed_config: dict[str, QuantComponent] | None = None,
    speed: float = 1.0,
    out_path: Path | None = None,
    vocoder_mode: str = "pytorch",
) -> TestResult:
    ok, dep_msg = _check_onnxruntime()
    if not ok:
        return TestResult(False, dep_msg, None, None, None)

    mode = normalize_quant_mode(quant_mode, use_int8=use_int8)
    mixed = mixed_config if mode == "mixed" else None
    if not onnx_ready(mode, mixed_config=mixed):
        te, fm = onnx_filenames(mode, mixed)
        return TestResult(
            False,
            f"Chưa có ONNX cho mode={mode} (`{te}`, `{fm}`).\n"
            "Tab Export → chọn mode tương ứng → Export ONNX.",
            None,
            None,
            None,
        )
    if not prompt_wav or not Path(prompt_wav).is_file():
        return TestResult(False, "Thiếu file giọng mẫu.", None, None, None)
    if not prompt_text.strip() or not text.strip():
        return TestResult(False, "Thiếu transcript giọng mẫu hoặc văn bản test.", None, None, None)

    use_onnx_vocoder = str(vocoder_mode).strip().lower() == "onnx"
    if use_onnx_vocoder and not vocos_onnx_ready():
        return TestResult(
            False,
            "Chọn vocoder ONNX nhưng thiếu `models/vocoder/mel_spec_24khz.onnx`.\n"
            "Tab Export → bật export Vocos → Export ONNX.",
            None,
            None,
            None,
        )

    try:
        logger.info(
            "ONNX test start | mode=%s | vocoder=%s | text_len=%d",
            mode,
            vocoder_mode,
            len(text),
        )
        zv = _import_zipvoice_onnx_stack()
        torch = zv["torch"]
        torchaudio = zv["torchaudio"]

        te_name, fm_name = _onnx_files(mode, mixed_config=mixed)
        size_note = format_sizes(ONNX_DIR, (te_name, fm_name))
        model = zv["OnnxModel"](
            str(ONNX_DIR / te_name),
            str(ONNX_DIR / fm_name),
            num_thread=1,
        )
        tokenizer = zv["EspeakTokenizer"](
            token_file=str(ONNX_DIR / "tokens.txt"), lang="vi"
        )
        feature_extractor = zv["VocosFbank"]()
        vocoder = None
        vocoder_sess = None
        if use_onnx_vocoder:
            import onnxruntime as ort

            vocoder_sess = ort.InferenceSession(
                str(vocos_onnx_path()),
                providers=["CPUExecutionProvider"],
            )
        else:
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
        if use_onnx_vocoder:
            from vocos_export import decode_mag_xy_with_librosa

            mag, x, y = vocoder_sess.run(
                None,
                {"mels": pred.cpu().numpy().astype("float32")},
            )
            wav_np = decode_mag_xy_with_librosa(mag, x, y)
            wav = torch.from_numpy(wav_np).unsqueeze(0)
            vocoder_label = "ONNX mag/x/y + librosa ISTFT"
        else:
            wav = vocoder.decode(pred).squeeze(1).clamp(-1, 1)
            vocoder_label = "PyTorch Vocos"
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
            f"- Mode: {mode} · Models: {size_note}\n"
            f"- Audio: {dur:.2f}s · RTF {rtf:.3f}\n"
            f"- File: `{out}`\n"
            f"- Vocoder: {vocoder_label}",
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

