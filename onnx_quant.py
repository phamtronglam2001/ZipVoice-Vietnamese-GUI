"""
ONNX quantization helpers shared between export (PyTorch GUI) and inference (ONNX GUI).

Modes:
  int4   — block weight-only INT4 via ORT MatMulNBits (text_encoder_int4.onnx, ...)
  int8   — dynamic MatMul INT8 (text_encoder_int8.onnx, fm_decoder_int8.onnx)

FP32 baselines (text_encoder.onnx, fm_decoder.onnx) are used only as a temporary export
intermediate; shipped artifacts are int4 or int8 only.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Literal

logger = logging.getLogger("zipvoice_onnx")

QuantMode = Literal["int8", "int4"]

QUANT_MODE_CHOICES: tuple[str, ...] = ("int4", "int8")

QUANT_MANIFEST = "quantization.json"
ONNX_COMPONENTS = ("text_encoder", "fm_decoder")

_SUFFIX: dict[QuantMode, str] = {
    "int8": "_int8",
    "int4": "_int4",
}


def normalize_quant_mode(mode: str | None, *, use_int8: bool | None = None) -> QuantMode:
    """Resolve mode from string or legacy use_int8 flag."""
    if mode is not None:
        m = str(mode).strip().lower()
        if m in QUANT_MODE_CHOICES:
            return m  # type: ignore[return-value]
        if m in ("fp32", "fp16", "mixed"):
            logger.warning("Quant mode %r is no longer supported; using int4", m)
    if use_int8 is True:
        return "int8"
    return "int4"


def component_filename(component: str, mode: QuantMode) -> str:
    return f"{component}{_SUFFIX[mode]}.onnx"


def fp32_baseline_filename(component: str) -> str:
    return f"{component}.onnx"


def onnx_filenames(mode: QuantMode | str) -> tuple[str, str]:
    mode = normalize_quant_mode(str(mode))
    return component_filename("text_encoder", mode), component_filename("fm_decoder", mode)


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024) if path.is_file() else 0.0


def format_sizes(onnx_dir: Path, filenames: tuple[str, str]) -> str:
    parts = []
    for name in filenames:
        p = onnx_dir / name
        if p.is_file():
            parts.append(f"`{name}` {file_size_mb(p):.1f} MB")
        else:
            parts.append(f"`{name}` missing")
    return " · ".join(parts)


def required_onnx_files(mode: QuantMode | str) -> tuple[str, str, str, str]:
    te, fm = onnx_filenames(mode)
    return te, fm, "model.json", "tokens.txt"


def missing_onnx_files(onnx_dir: Path, mode: QuantMode | str) -> list[str]:
    """Return filenames missing for the given quant mode."""
    return [
        name
        for name in required_onnx_files(mode)
        if not (onnx_dir / name).is_file()
    ]


def onnx_ready_for_mode(onnx_dir: Path, mode: QuantMode | str) -> bool:
    return not missing_onnx_files(onnx_dir, mode)


def quant_readiness_hint(mode: QuantMode | str, missing: list[str]) -> str:
    """Short user-facing hint when a quant mode is not ready."""
    mode = normalize_quant_mode(str(mode))
    if not missing:
        return ""

    onnx_missing = [n for n in missing if n.endswith(".onnx")]
    if mode == "int4" and onnx_missing:
        return (
            "Tab Export → chọn **int4** → Export ONNX trong PyTorch GUI, "
            "rồi copy `models/onnx/` sang ONNX-GUI repo."
        )
    if mode == "int8" and onnx_missing:
        return "Tab Export → chọn **int8** → Export ONNX."
    return f"Thiếu: {', '.join(missing)}"


def write_quant_manifest(
    onnx_dir: Path,
    mode: QuantMode,
    *,
    created: list[str] | None = None,
) -> Path:
    payload: dict = {
        "mode": mode,
        "text_encoder": mode,
        "fm_decoder": mode,
        "filenames": dict(zip(ONNX_COMPONENTS, onnx_filenames(mode))),
    }
    if created:
        payload["created"] = created
    path = onnx_dir / QUANT_MANIFEST
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def read_quant_manifest(onnx_dir: Path) -> dict | None:
    path = onnx_dir / QUANT_MANIFEST
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


_FOLDER_SCAN_ORDER: tuple[QuantMode, ...] = ("int4", "int8")


def detect_quant_mode_from_folder(onnx_dir: Path) -> QuantMode | None:
    """Scan models/onnx/ for a ready uniform quant set. Priority: int4 > int8."""
    for mode in _FOLDER_SCAN_ORDER:
        if onnx_ready_for_mode(onnx_dir, mode):
            return mode
    return None


def resolve_default_quant_mode(
    onnx_dir: Path,
    *,
    env_quant: str | None = None,
    legacy_int8_env: str | None = None,
) -> tuple[QuantMode, str]:
    """
    Default inference quant mode when the caller does not pass an explicit mode.

    Priority:
      1. ZIPVOICE_ONNX_QUANT env
      2. quantization.json ``mode``
      3. folder scan (int4 > int8)
      4. legacy ZIPVOICE_ONNX_INT8 when explicitly set
      5. int4 (default)
    """
    if env_quant:
        return normalize_quant_mode(env_quant), "env"

    manifest = read_quant_manifest(onnx_dir)
    if manifest and manifest.get("mode"):
        return normalize_quant_mode(str(manifest["mode"])), "manifest"

    detected = detect_quant_mode_from_folder(onnx_dir)
    if detected:
        return detected, "folder"

    if legacy_int8_env is not None and legacy_int8_env.strip():
        use_int8 = legacy_int8_env.strip().lower() in {"1", "true", "yes"}
        return normalize_quant_mode(None, use_int8=use_int8), "legacy"

    return "int4", "default"


def resolve_inference_mode(onnx_dir: Path, requested: str | None = None) -> QuantMode:
    """Pick quant mode for inference: explicit request > manifest > folder scan > default."""
    if requested:
        return normalize_quant_mode(requested)
    mode, _source = resolve_default_quant_mode(onnx_dir)
    return mode


def _quantize_int8(src: Path, dst: Path) -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(
        model_input=str(src),
        model_output=str(dst),
        op_types_to_quantize=["MatMul"],
        weight_type=QuantType.QInt8,
    )


def _quantize_int4(src: Path, dst: Path) -> None:
    from onnxruntime.quantization import quant_utils
    from onnxruntime.quantization.matmul_nbits_quantizer import (
        DefaultWeightOnlyQuantConfig,
        MatMulNBitsQuantizer,
    )

    quant_config = DefaultWeightOnlyQuantConfig(
        block_size=128,
        is_symmetric=True,
        accuracy_level=4,
        quant_format=quant_utils.QuantFormat.QOperator,
        op_types_to_quantize=("MatMul",),
        bits=4,
    )
    model = quant_utils.load_model_with_shape_infer(src)
    quant = MatMulNBitsQuantizer(model, algo_config=quant_config)
    quant.process()
    quant.model.save_model_to_file(str(dst), use_external_data_format=False)


def needed_fp32_baselines(mode: QuantMode | str) -> frozenset[str]:
    """FP32 baseline filenames required in the output folder for inference (none for int4/int8)."""
    return frozenset()


def remove_unneeded_fp32_files(onnx_dir: Path, mode: QuantMode | str) -> list[str]:
    """Delete FP32 baseline files after quant export."""
    removed: list[str] = []
    for comp in ONNX_COMPONENTS:
        name = fp32_baseline_filename(comp)
        path = onnx_dir / name
        if path.is_file():
            mb = file_size_mb(path)
            path.unlink()
            removed.append(name)
            logger.info("Removed unneeded FP32 baseline: %s (%.1f MB)", name, mb)
    return removed


def quantize_component(src_fp32: Path, dst: Path, mode: QuantMode) -> None:
    """Create quantized variant from FP32 ONNX file."""
    if not src_fp32.is_file():
        raise FileNotFoundError(f"Missing FP32 source: {src_fp32}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_file():
        dst.unlink()

    if mode == "int8":
        _quantize_int8(src_fp32, dst)
    elif mode == "int4":
        _quantize_int4(src_fp32, dst)
    else:
        raise ValueError(f"Unknown quant mode: {mode}")

    logger.info("Quantized %s -> %s (%s, %.1f MB)", src_fp32.name, dst.name, mode, file_size_mb(dst))


def export_quant_variants(
    onnx_dir: Path,
    mode: QuantMode,
    *,
    fp32_source_dir: Path | None = None,
    keep_fp32_baseline: bool = False,
) -> list[str]:
    """
    After FP32 base export, build requested quantized artifacts.

    *fp32_source_dir* — read FP32 baselines here (e.g. temp dir) instead of *onnx_dir*.
    *keep_fp32_baseline* — when True, also copy FP32 files into *onnx_dir* (legacy CLI only).
    """
    mode = normalize_quant_mode(mode)
    src_dir = fp32_source_dir or onnx_dir
    created: list[str] = []
    base = {c: src_dir / fp32_baseline_filename(c) for c in ONNX_COMPONENTS}

    for comp in ONNX_COMPONENTS:
        out = onnx_dir / component_filename(comp, mode)
        quantize_component(base[comp], out, mode)
        created.append(out.name)

    if keep_fp32_baseline:
        for comp in ONNX_COMPONENTS:
            dst = onnx_dir / fp32_baseline_filename(comp)
            shutil.copy2(base[comp], dst)
            if dst.name not in created:
                created.append(dst.name)
    else:
        remove_unneeded_fp32_files(onnx_dir, mode)

    write_quant_manifest(onnx_dir, mode, created=created)
    return created
