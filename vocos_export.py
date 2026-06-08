"""
Export charactr/vocos-mel-24khz (100 mel) to ONNX for ZipVoice ONNX-GUI.

Full decode uses complex ISTFT — not ONNX-exportable with classic torch.onnx.export.
We export backbone + ISTFT head through mag / x(cos) / y(sin); inference completes
with librosa ISTFT (same as ZipVoice-Vietnamese-ONNX-GUI vocos_istft.py).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn

from config import VOCODER_DIR

logger = logging.getLogger("zipvoice_onnx")

VOCOS_ONNX_NAME = "mel_spec_24khz.onnx"
VOCOS_MEL_CHANNELS = 100
N_FFT = 1024
HOP_LENGTH = 256


@dataclass
class VocosExportResult:
    ok: bool
    message: str
    path: str | None
    size_mb: float | None


class VocosMagXYExport(nn.Module):
    """mels (B,100,T) -> mag, x=cos(p), y=sin(p) before ISTFT."""

    def __init__(self, vocos) -> None:
        super().__init__()
        self.backbone = vocos.backbone
        self.out = vocos.head.out

    def forward(self, mels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        x = self.out(self.backbone(mels)).transpose(1, 2)
        mag, p = x.chunk(2, dim=1)
        mag = torch.exp(mag).clamp(max=1e2)
        return mag, torch.cos(p), torch.sin(p)


def _load_vocos_pytorch():
    from vocos import Vocos

    config = VOCODER_DIR / "config.yaml"
    weights = VOCODER_DIR / "pytorch_model.bin"
    if not config.is_file() or not weights.is_file():
        raise FileNotFoundError(
            f"Missing vocoder under {VOCODER_DIR} — run install_cpu.bat first."
        )
    vocoder = Vocos.from_hparams(str(config))
    state = torch.load(weights, weights_only=True, map_location="cpu")
    vocoder.load_state_dict(state)
    vocoder.eval()
    n_mels = vocoder.backbone.input_channels
    if n_mels != VOCOS_MEL_CHANNELS:
        raise ValueError(
            f"Expected {VOCOS_MEL_CHANNELS} mel channels, got {n_mels} from config."
        )
    return vocoder


def decode_mag_xy_with_librosa(
    mag: "torch.Tensor | object",
    x: "torch.Tensor | object",
    y: "torch.Tensor | object",
) -> "object":
    """Complete vocoder decode from ONNX mag/x/y outputs (numpy or torch)."""
    import numpy as np

    try:
        import librosa
    except ImportError as exc:
        raise ImportError("librosa required for ISTFT — pip install librosa") from exc

    def _to_np(t):
        if hasattr(t, "detach"):
            t = t.detach().cpu().numpy()
        return np.asarray(t, dtype=np.float32)

    mag_np, x_np, y_np = _to_np(mag), _to_np(x), _to_np(y)
    if mag_np.ndim == 3:
        mag_np, x_np, y_np = mag_np[0], x_np[0], y_np[0]
    stft = mag_np * (x_np + 1j * y_np)
    wav = librosa.istft(
        stft,
        hop_length=HOP_LENGTH,
        win_length=N_FFT,
        n_fft=N_FFT,
        window="hann",
        center=True,
    )
    return np.clip(wav, -1.0, 1.0).astype(np.float32)


def export_vocos_onnx(
    out_dir: Path | None = None,
    *,
    opset_version: int = 17,
) -> VocosExportResult:
    """Write mel_spec_24khz.onnx (100 mel) under models/vocoder/ by default."""
    out_dir = out_dir or VOCODER_DIR
    out_path = out_dir / VOCOS_ONNX_NAME

    try:
        vocoder = _load_vocos_pytorch()
        wrapper = VocosMagXYExport(vocoder)
        dummy = torch.randn(1, VOCOS_MEL_CHANNELS, 128)
        with torch.inference_mode():
            ref_mag, ref_x, ref_y = wrapper(dummy)
            full = vocoder.decode(dummy)
            via_librosa = decode_mag_xy_with_librosa(ref_mag, ref_x, ref_y)
            import numpy as np

            diff = float(np.abs(via_librosa - full.numpy()[0]).max())
            logger.info("Vocos export sanity | max diff vs PyTorch %.2e", diff)

        out_dir.mkdir(parents=True, exist_ok=True)
        if out_path.is_file():
            out_path.unlink()

        torch.onnx.export(
            wrapper,
            dummy,
            str(out_path),
            input_names=["mels"],
            output_names=["mag", "x", "y"],
            dynamic_axes={
                "mels": {0: "batch", 2: "time"},
                "mag": {0: "batch", 2: "time"},
                "x": {0: "batch", 2: "time"},
                "y": {0: "batch", 2: "time"},
            },
            opset_version=opset_version,
            do_constant_folding=True,
        )

        size_mb = out_path.stat().st_size / (1024 * 1024)
        msg = (
            f"Exported `{out_path.name}` ({size_mb:.1f} MB, {VOCOS_MEL_CHANNELS} mel).\n"
            f"Outputs: mag, x(cos), y(sin) — ISTFT via librosa at inference.\n"
            f"Sanity max diff vs PyTorch decode: {diff:.2e}\n"
            f"Copy to ONNX-GUI `models/vocoder/` if needed."
        )
        logger.info(msg.replace("\n", " | "))
        return VocosExportResult(True, msg, str(out_path), size_mb)

    except Exception as exc:
        logger.exception("Vocos ONNX export failed")
        return VocosExportResult(False, f"Vocos export lỗi: {exc}", None, None)
