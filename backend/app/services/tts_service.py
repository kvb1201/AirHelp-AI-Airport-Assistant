"""
Offline English TTS via **piper-tts** (PyPI).

1. ``pip install piper-tts`` in the project ``.venv``.
2. Run ``scripts/download_piper_voices.sh`` (English voice into ``backend/app/data/piper_voices/``),
   or set ``PIPER_VOICE_EN`` to a ``.onnx`` file.

Optional: ``PIPER_BINARY`` if ``piper`` is not ``.venv/bin/piper`` and not on ``PATH``.
Optional dev fallback: ``PIPER_TEST_VOICE_ONNX`` → path to a small English ``.onnx`` (do not commit vendor trees).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

_MAX_CHARS = 2800


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _venv_piper() -> Optional[Path]:
    p = _repo_root() / ".venv" / "bin" / "piper"
    return p if p.is_file() else None


def _bundled_test_voice_en() -> Optional[Path]:
    """Optional tiny English model for dev (not in repo). Set PIPER_TEST_VOICE_ONNX to an .onnx path."""
    raw = os.getenv("PIPER_TEST_VOICE_ONNX", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if p.is_file():
            return p
    return None


def _data_piper_voices_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "piper_voices"


def _english_voice_path() -> Optional[Path]:
    raw = os.getenv("PIPER_VOICE_EN", "").strip()
    if raw:
        p = Path(raw).expanduser()
        if p.is_file():
            return p
    data = _data_piper_voices_dir() / "en_US-lessac-medium.onnx"
    if data.is_file():
        return data
    return _bundled_test_voice_en()


def _piper_binary_env() -> Optional[str]:
    v = os.getenv("PIPER_BINARY", "").strip()
    return v or None


def _is_piper_release_bundle_dir(d: Path) -> bool:
    exe = (d / "piper").is_file() or (d / "piper.exe").is_file()
    return (d / "espeak-ng-data").is_dir() and exe


def missing_piper_dylibs(piper_exe: Optional[str]) -> List[str]:
    if not piper_exe:
        return []
    d = Path(piper_exe).resolve().parent
    if not _is_piper_release_bundle_dir(d):
        return []
    ext = ".dylib" if sys.platform == "darwin" else ".so"
    names = {p.name for p in d.iterdir() if p.suffix == ext and p.is_file()}
    missing: List[str] = []
    for prefix in ("libonnxruntime", "libespeak-ng", "libpiper_phonemize"):
        if not any(n.startswith(prefix) for n in names):
            missing.append(f"{prefix}*{ext}")
    return missing


def resolve_piper_exe() -> Optional[str]:
    cfg = _piper_binary_env()
    if cfg:
        explicit = Path(cfg).expanduser()
        if explicit.is_file():
            return str(explicit.resolve())
        found = shutil.which(cfg)
        if found:
            return found
        return None
    vp = _venv_piper()
    if vp:
        return str(vp.resolve())
    return shutil.which("piper")


def tts_status() -> Dict[str, Any]:
    bin_env = _piper_binary_env()
    piper_path = resolve_piper_exe()
    en = _english_voice_path()
    dy_miss = missing_piper_dylibs(piper_path)
    vp = _venv_piper()
    mode = "piper-tts"
    if vp and piper_path and Path(piper_path).resolve() == vp.resolve():
        mode = "piper-tts (.venv)"
    return {
        "piper_installer": mode,
        "piper_binary_env": bin_env,
        "piper_resolved": piper_path,
        "piper_found": bool(piper_path),
        "english_voice_path": str(en) if en else None,
        "piper_voices_dir": str(_data_piper_voices_dir()),
        "voices_configured": {"en": bool(en)},
        "piper_dylibs_missing": dy_miss,
        "ready": bool(piper_path) and bool(en) and len(dy_miss) == 0,
    }


def synthesize_wav(text: str, language: str = "en") -> bytes:
    """English only; ``language`` is ignored."""
    model = _english_voice_path()
    if not model:
        raise ValueError(
            "No English Piper voice. Run scripts/download_piper_voices.sh or set PIPER_VOICE_EN "
            "to an .onnx file path."
        )

    piper_exe = resolve_piper_exe()
    if not piper_exe:
        raise FileNotFoundError(
            "Piper not found. Run `pip install piper-tts` in the project .venv, or set PIPER_BINARY."
        )

    dy_miss = missing_piper_dylibs(piper_exe)
    if dy_miss:
        raise RuntimeError(
            "Legacy Piper tarball is incomplete. Use `pip install piper-tts` in .venv instead."
        )

    clean = text.strip().replace("\x00", "")
    if not clean:
        raise ValueError("Empty text")
    if len(clean) > _MAX_CHARS:
        clean = clean[:_MAX_CHARS]

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name

    piper_dir = Path(piper_exe).resolve().parent
    cwd = str(piper_dir) if (piper_dir / "espeak-ng-data").is_dir() else None

    try:
        proc = subprocess.run(
            [piper_exe, "-m", str(model), "-f", out_path],
            input=clean.encode("utf-8"),
            capture_output=True,
            timeout=90,
            check=False,
            cwd=cwd,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or b"").decode("utf-8", errors="replace")[:1200]
            raise RuntimeError(f"Piper exited {proc.returncode}: {err or 'no stderr'}")

        wav = Path(out_path).read_bytes()
        if len(wav) < 100:
            raise RuntimeError("Piper produced an empty or invalid WAV file")
        return wav
    finally:
        try:
            Path(out_path).unlink(missing_ok=True)
        except OSError:
            pass
