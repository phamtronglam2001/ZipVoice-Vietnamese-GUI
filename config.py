"""
Portable path configuration for ZipVoice Vietnamese TTS.
All paths are relative to this project folder so the whole directory
can be copied to another machine and run offline after setup.
"""
from __future__ import annotations

import os
from pathlib import Path

# Project root (folder containing this file)
ROOT = Path(__file__).resolve().parent

# User content folders
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
REF_INFO_JSON = ASSETS_DIR / "ref_info.json"

# Bundled ffmpeg (copied by setup_ffmpeg.ps1)
FFMPEG_BIN = ROOT / "ffmpeg" / "bin"
SYSTEM_FFMPEG_BIN = Path(r"C:\ffmpeg\bin")

# Vendor ZipVoice library (cloned by setup script)
VENDOR_DIR = ROOT / "vendor" / "ZipVoice"

# Local model weights (downloaded by download_models.py)
MODELS_DIR = ROOT / "models"
ZIPVOICE_DIR = MODELS_DIR / "zipvoice"
VOCODER_DIR = MODELS_DIR / "vocoder"

# ZipVoice checkpoint files
ZIPVOICE_CONFIG = ZIPVOICE_DIR / "config.json"
ZIPVOICE_TOKENS = ZIPVOICE_DIR / "tokens.txt"
ZIPVOICE_CKPT = ZIPVOICE_DIR / "iter-525000-avg-2.pt"

# Exported ONNX artifacts
ONNX_DIR = MODELS_DIR / "onnx"

# HuggingFace repo IDs (used only during initial download)
HF_ZIPVOICE_REPO = "hynt/ZipVoice-Vietnamese-2500h"
HF_VOCODER_REPO = "charactr/vocos-mel-24khz"


def ensure_ffmpeg_on_path() -> None:
    """Prepend bundled or system ffmpeg to PATH for pydub."""
    candidates = [FFMPEG_BIN, SYSTEM_FFMPEG_BIN]
    for bin_dir in candidates:
        ffmpeg_exe = bin_dir / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            path = os.environ.get("PATH", "")
            bin_str = str(bin_dir)
            if bin_str not in path.split(os.pathsep):
                os.environ["PATH"] = bin_str + os.pathsep + path
            return


def ensure_vendor_on_path() -> None:
    """Add vendored ZipVoice source to PYTHONPATH."""
    vendor = str(VENDOR_DIR)
    if vendor not in os.sys.path:
        os.sys.path.insert(0, vendor)


def is_force_cpu() -> bool:
    """True when ZIPVOICE_FORCE_CPU=1 (CPU-only install/run)."""
    return os.environ.get("ZIPVOICE_FORCE_CPU", "").strip() in {"1", "true", "yes"}


def apply_cpu_env() -> None:
    """Hide CUDA and pin runtime to CPU when force-cpu mode is enabled."""
    if is_force_cpu():
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ.setdefault("ZIPVOICE_FORCE_CPU", "1")


def set_offline_env() -> None:
    """Force HuggingFace / transformers to use local files only."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")


def models_ready() -> bool:
    """Return True when all required local model files exist."""
    zipvoice_ok = all(
        p.exists()
        for p in (ZIPVOICE_CONFIG, ZIPVOICE_TOKENS, ZIPVOICE_CKPT)
    )
    vocoder_ok = (VOCODER_DIR / "config.yaml").exists() and (
        VOCODER_DIR / "pytorch_model.bin"
    ).exists()
    vendor_ok = (VENDOR_DIR / "zipvoice").is_dir()
    return zipvoice_ok and vocoder_ok and vendor_ok
