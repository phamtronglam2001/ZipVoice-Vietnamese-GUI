"""
ONNX quantization helpers shared between export (PyTorch GUI) and inference (ONNX GUI).

Modes:
  fp32   — baseline export (text_encoder.onnx, fm_decoder.onnx)
  fp16   — float16 weights (text_encoder_fp16.onnx, fm_decoder_fp16.onnx)
  int8   — dynamic MatMul INT8 (text_encoder_int8.onnx, fm_decoder_int8.onnx)
  int4   — block weight-only INT4 via ORT MatMulNBits (text_encoder_int4.onnx, ...)
  mixed  — per-component quant from mixed_config (default: text_encoder=int8, fm_decoder=fp32)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

logger = logging.getLogger("zipvoice_onnx")

QuantComponent = Literal["fp32", "fp16", "int8", "int4"]
QuantMode = Literal["fp32", "fp16", "int8", "int4", "mixed"]

QUANT_MODE_CHOICES: tuple[str, ...] = ("fp32", "fp16", "int8", "int4", "mixed")
COMPONENT_QUANT_CHOICES: tuple[str, ...] = ("fp32", "fp16", "int8", "int4")

DEFAULT_MIXED_CONFIG: dict[str, QuantComponent] = {
    "text_encoder": "int8",
    "fm_decoder": "fp32",
}

QUANT_MANIFEST = "quantization.json"
ONNX_COMPONENTS = ("text_encoder", "fm_decoder")

_SUFFIX: dict[QuantComponent, str] = {
    "fp32": "",
    "fp16": "_fp16",
    "int8": "_int8",
    "int4": "_int4",
}


def normalize_quant_mode(mode: str | None, *, use_int8: bool | None = None) -> QuantMode:
    """Resolve mode from string or legacy use_int8 flag."""
    if mode is not None:
        m = str(mode).strip().lower()
        if m in QUANT_MODE_CHOICES:
            return m  # type: ignore[return-value]
    if use_int8 is True:
        return "int8"
    if use_int8 is False:
        return "fp32"
    return "fp32"


def component_filename(component: str, quant: QuantComponent) -> str:
    suffix = _SUFFIX[quant]
    return f"{component}{suffix}.onnx"


def onnx_filenames(
    mode: QuantMode | str,
    mixed_config: dict[str, QuantComponent] | None = None,
) -> tuple[str, str]:
    mode = normalize_quant_mode(str(mode))
    if mode == "mixed":
        cfg = mixed_config or DEFAULT_MIXED_CONFIG
        te_q = cfg.get("text_encoder", "int8")
        fm_q = cfg.get("fm_decoder", "fp32")
        return component_filename("text_encoder", te_q), component_filename("fm_decoder", fm_q)
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


def onnx_ready_for_mode(
    onnx_dir: Path,
    mode: QuantMode | str,
    mixed_config: dict[str, QuantComponent] | None = None,
) -> bool:
    te, fm = onnx_filenames(mode, mixed_config)
    return all((onnx_dir / name).is_file() for name in (te, fm, "model.json", "tokens.txt"))


def write_quant_manifest(
    onnx_dir: Path,
    mode: QuantMode,
    *,
    mixed_config: dict[str, QuantComponent] | None = None,
    created: list[str] | None = None,
) -> Path:
    payload: dict = {
        "mode": mode,
        "text_encoder": mode if mode != "mixed" else (mixed_config or DEFAULT_MIXED_CONFIG)["text_encoder"],
        "fm_decoder": mode if mode != "mixed" else (mixed_config or DEFAULT_MIXED_CONFIG)["fm_decoder"],
        "filenames": dict(zip(ONNX_COMPONENTS, onnx_filenames(mode, mixed_config))),
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


def resolve_inference_mode(onnx_dir: Path, requested: str | None = None) -> tuple[QuantMode, dict[str, QuantComponent] | None]:
    """Pick quant mode for inference: explicit request > manifest > env legacy."""
    if requested:
        mode = normalize_quant_mode(requested)
        if mode == "mixed":
            manifest = read_quant_manifest(onnx_dir)
            mixed = None
            if manifest and manifest.get("mode") == "mixed":
                mixed = {
                    "text_encoder": manifest.get("text_encoder", "int8"),
                    "fm_decoder": manifest.get("fm_decoder", "fp32"),
                }
            return "mixed", mixed
        return mode, None

    manifest = read_quant_manifest(onnx_dir)
    if manifest and manifest.get("mode") in QUANT_MODE_CHOICES:
        mode = manifest["mode"]
        if mode == "mixed":
            return "mixed", {
                "text_encoder": manifest.get("text_encoder", "int8"),
                "fm_decoder": manifest.get("fm_decoder", "fp32"),
            }
        return mode, None

    return normalize_quant_mode(None), None


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


def _convert_fp16(src: Path, dst: Path) -> None:
    try:
        from onnxconverter_common.float16 import convert_float_to_float16
    except ImportError as exc:
        raise ImportError(
            "FP16 export requires onnxconverter-common. "
            "pip install onnxconverter-common"
        ) from exc

    import onnx

    model = onnx.load(str(src))
    model_fp16 = convert_float_to_float16(model, keep_io_types=True)
    onnx.save(model_fp16, str(dst))


def quantize_component(src_fp32: Path, dst: Path, quant: QuantComponent) -> None:
    """Create quantized variant from FP32 ONNX file."""
    if quant == "fp32":
        raise ValueError("fp32 is the base export; no separate quantize step")
    if not src_fp32.is_file():
        raise FileNotFoundError(f"Missing FP32 source: {src_fp32}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_file():
        dst.unlink()

    if quant == "int8":
        _quantize_int8(src_fp32, dst)
    elif quant == "int4":
        _quantize_int4(src_fp32, dst)
    elif quant == "fp16":
        _convert_fp16(src_fp32, dst)
    else:
        raise ValueError(f"Unknown component quant: {quant}")

    logger.info("Quantized %s -> %s (%s, %.1f MB)", src_fp32.name, dst.name, quant, file_size_mb(dst))


def export_quant_variants(
    onnx_dir: Path,
    mode: QuantMode,
    *,
    mixed_config: dict[str, QuantComponent] | None = None,
) -> list[str]:
    """
    After FP32 base export, build requested quantized artifacts.
    Always keeps text_encoder.onnx + fm_decoder.onnx as FP32 baseline.
    """
    created: list[str] = []
    base = {c: onnx_dir / component_filename(c, "fp32") for c in ONNX_COMPONENTS}

    if mode == "fp32":
        write_quant_manifest(onnx_dir, "fp32", created=[n.name for n in base.values()])
        return [n.name for n in base.values()]

    if mode in ("int8", "int4", "fp16"):
        for comp in ONNX_COMPONENTS:
            out = onnx_dir / component_filename(comp, mode)
            quantize_component(base[comp], out, mode)  # type: ignore[arg-type]
            created.append(out.name)
        write_quant_manifest(onnx_dir, mode, created=created)
        return created

    if mode == "mixed":
        cfg = mixed_config or DEFAULT_MIXED_CONFIG
        for comp in ONNX_COMPONENTS:
            q = cfg.get(comp, "fp32")
            if q == "fp32":
                continue
            out = onnx_dir / component_filename(comp, q)
            quantize_component(base[comp], out, q)
            created.append(out.name)
        write_quant_manifest(onnx_dir, "mixed", mixed_config=cfg, created=created)
        return created

    raise ValueError(f"Unknown quant mode: {mode}")
