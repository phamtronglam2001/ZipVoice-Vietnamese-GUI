"""
Download all model weights into ./models/ for offline use.
Run once during setup (requires internet).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

from config import (
    HF_VOCODER_REPO,
    HF_ZIPVOICE_REPO,
    MODELS_DIR,
    ROOT,
    VENDOR_DIR,
    VOCODER_DIR,
    ZIPVOICE_DIR,
)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def clone_zipvoice() -> None:
    if (VENDOR_DIR / "zipvoice").is_dir():
        print(f"[OK] ZipVoice source already at {VENDOR_DIR}")
        return

    VENDOR_DIR.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/k2-fsa/ZipVoice.git",
            str(VENDOR_DIR),
        ]
    )


def download_zipvoice_weights() -> None:
    ZIPVOICE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {HF_ZIPVOICE_REPO} -> {ZIPVOICE_DIR}")
    snapshot_download(
        repo_id=HF_ZIPVOICE_REPO,
        local_dir=str(ZIPVOICE_DIR),
        local_dir_use_symlinks=False,
    )


def download_vocoder() -> None:
    VOCODER_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {HF_VOCODER_REPO} -> {VOCODER_DIR}")
    snapshot_download(
        repo_id=HF_VOCODER_REPO,
        local_dir=str(VOCODER_DIR),
        local_dir_use_symlinks=False,
    )


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    clone_zipvoice()
    download_zipvoice_weights()
    download_vocoder()
    print("\n[OK] All assets downloaded. Folder is ready for offline use.")
    print(f"     Project root: {ROOT}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"\n[ERROR] Command failed: {exc}", file=sys.stderr)
        sys.exit(1)
