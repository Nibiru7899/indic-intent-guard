"""Offline audio conditions for the benchmark (no API calls, no ffmpeg needed).

clean       : original, resampled to 16 kHz mono
narrowband  : 8 kHz telephone band (300-3400 Hz), mu-law-like quantization
noisy       : narrowband + additive noise at a fixed SNR

Listen to every transformed file before using it: a condition is only valid
if a human can still clearly understand the utterance.
"""
from pathlib import Path
import zlib

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt

CONDITIONS = ("clean", "narrowband", "noisy")


def load_mono(path: str | Path, target_sr: int = 16000) -> np.ndarray:
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != target_sr:
        g = np.gcd(sr, target_sr)
        x = resample_poly(x, target_sr // g, sr // g).astype(np.float32)
    return x


def _mulaw(x: np.ndarray, mu: int = 255) -> np.ndarray:
    y = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
    y = np.round((y + 1) / 2 * mu) / mu * 2 - 1
    return np.sign(y) * ((1 + mu) ** np.abs(y) - 1) / mu


def narrowband(x16k: np.ndarray) -> np.ndarray:
    """16 kHz in -> 8 kHz telephone-band out."""
    x8 = resample_poly(x16k, 1, 2)
    sos = butter(6, [300, 3400], btype="bandpass", fs=8000, output="sos")
    y = sosfiltfilt(sos, x8)
    peak = np.max(np.abs(y)) or 1.0
    return _mulaw(y / peak * 0.9).astype(np.float32)


def add_noise(x: np.ndarray, snr_db: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(len(x)).astype(np.float32)
    p_sig = np.mean(x ** 2) or 1e-10
    noise *= np.sqrt(p_sig / (10 ** (snr_db / 10)) / np.mean(noise ** 2))
    y = x + noise
    return (y / max(1.0, np.max(np.abs(y)))).astype(np.float32)


def make_conditions(src: str | Path, out_dir: str | Path, snr_db: float = 10.0) -> dict[str, Path]:
    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    x = load_mono(src, 16000)
    nb = narrowband(x)
    outputs = {
        "clean": (x, 16000),
        "narrowband": (nb, 8000),
        "noisy": (add_noise(nb, snr_db, seed=zlib.crc32(src.stem.encode())), 8000),
    }
    paths = {}
    for name, (sig, sr) in outputs.items():
        p = out_dir / f"{src.stem}__{name}.wav"
        sf.write(str(p), sig, sr, subtype="PCM_16")
        paths[name] = p
    return paths
