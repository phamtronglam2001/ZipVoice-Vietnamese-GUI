"""
ZipVoice Vietnamese TTS inference engine.
Loads models from local paths for fully offline operation.
"""
from __future__ import annotations

import gc
import json
import logging
import os
from typing import Optional

import torch
import torchaudio
from vocos import Vocos

from config import (
    VOCODER_DIR,
    ZIPVOICE_CKPT,
    ZIPVOICE_CONFIG,
    ZIPVOICE_TOKENS,
    apply_cpu_env,
    ensure_vendor_on_path,
    is_force_cpu,
    set_offline_env,
)

apply_cpu_env()
ensure_vendor_on_path()
set_offline_env()

from zipvoice.models.zipvoice import ZipVoice  # noqa: E402
from zipvoice.tokenizer.tokenizer import EspeakTokenizer  # noqa: E402
from zipvoice.utils.checkpoint import load_checkpoint  # noqa: E402
from zipvoice.utils.feature import VocosFbank  # noqa: E402

SAMPLING_RATE = 24000
FEAT_SCALE = 0.1
TARGET_RMS = 0.1

logger = logging.getLogger("zipvoice_gui")

if is_force_cpu():
    # Limit CPU threads to reduce RAM spikes / system freeze on Windows.
    threads = os.environ.get("ZIPVOICE_CPU_THREADS", "4")
    try:
        torch.set_num_threads(int(threads))
    except Exception:
        pass


def _pick_device() -> torch.device:
    if is_force_cpu() or not torch.cuda.is_available():
        print("[ZipVoice] Using CPU")
        return torch.device("cpu")
    print("[ZipVoice] Using GPU (CUDA)")
    return torch.device("cuda")


def _load_vocoder(device: torch.device) -> Vocos:
    vocoder = Vocos.from_hparams(str(VOCODER_DIR / "config.yaml"))
    state_dict = torch.load(
        VOCODER_DIR / "pytorch_model.bin",
        weights_only=True,
        map_location="cpu",
    )
    vocoder.load_state_dict(state_dict)
    return vocoder.to(device).eval()


def _load_model(device: torch.device):
    with open(ZIPVOICE_CONFIG, encoding="utf-8") as f:
        model_config = json.load(f)

    tokenizer = EspeakTokenizer(token_file=str(ZIPVOICE_TOKENS), lang="vi")
    tokenizer_config = {
        "vocab_size": tokenizer.vocab_size,
        "pad_id": tokenizer.pad_id,
    }

    model = ZipVoice(
        **model_config["model"],
        **tokenizer_config,
    )
    load_checkpoint(filename=str(ZIPVOICE_CKPT), model=model, strict=True)
    model = model.to(device).eval()

    if model_config["feature"]["type"] != "vocos":
        raise NotImplementedError(
            f"Unsupported feature type: {model_config['feature']['type']}"
        )

    feature_extractor = VocosFbank()
    return model, tokenizer, feature_extractor, model_config


class ZipVoiceEngine:
    """Lazy-loaded singleton for Gradio inference."""

    _instance: Optional["ZipVoiceEngine"] = None

    def __init__(self) -> None:
        self.device = _pick_device()
        self.model, self.tokenizer, self.feature_extractor, self.model_config = (
            _load_model(self.device)
        )
        self.vocoder = _load_vocoder(self.device)
        self.sampling_rate = self.model_config["feature"]["sampling_rate"]

    @classmethod
    def get(cls) -> "ZipVoiceEngine":
        if cls._instance is None:
            print("[ZipVoice] Loading models (first run may take a minute)...")
            cls._instance = cls()
            print("[ZipVoice] Models ready.")
        return cls._instance

    def generate(
        self,
        prompt_text: str,
        prompt_wav: str,
        text: str,
        speed: float = 1.0,
        num_step: int = 16,
        guidance_scale: float = 1.0,
        t_shift: float = 0.5,
    ) -> torch.Tensor:
        logger.info("Generating TTS chunk (%d chars)...", len(text))
        with torch.inference_mode():
            tokens = self.tokenizer.texts_to_token_ids([text])
            prompt_tokens = self.tokenizer.texts_to_token_ids([prompt_text])

            prompt_audio, prompt_sr = torchaudio.load(prompt_wav)
            if prompt_sr != self.sampling_rate:
                prompt_audio = torchaudio.transforms.Resample(
                    orig_freq=prompt_sr, new_freq=self.sampling_rate
                )(prompt_audio)

            prompt_rms = torch.sqrt(torch.mean(torch.square(prompt_audio)))
            if prompt_rms < TARGET_RMS:
                prompt_audio = prompt_audio * TARGET_RMS / prompt_rms

            prompt_features = self.feature_extractor.extract(
                prompt_audio, sampling_rate=self.sampling_rate
            ).to(self.device)
            prompt_features = prompt_features.unsqueeze(0) * FEAT_SCALE
            prompt_features_lens = torch.tensor(
                [prompt_features.size(1)], device=self.device
            )

            (
                pred_features,
                _pred_features_lens,
                _pred_prompt_features,
                _pred_prompt_features_lens,
            ) = self.model.sample(
                tokens=tokens,
                prompt_tokens=prompt_tokens,
                prompt_features=prompt_features,
                prompt_features_lens=prompt_features_lens,
                speed=speed,
                t_shift=t_shift,
                duration="predict",
                num_step=num_step,
                guidance_scale=guidance_scale,
            )

            pred_features = pred_features.permute(0, 2, 1) / FEAT_SCALE
            wav = self.vocoder.decode(pred_features).squeeze(1).clamp(-1, 1)

            if prompt_rms < TARGET_RMS:
                wav = wav * prompt_rms / TARGET_RMS

            out = wav.cpu()
            del prompt_audio, prompt_features, pred_features, wav
            if is_force_cpu():
                gc.collect()
            return out
