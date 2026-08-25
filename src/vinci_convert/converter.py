"""ffmpeg-based conversion logic — ported from davinconv (bash) to Python.

Two operations:
  * convert   — transcode to ProRes (DaVinci Resolve friendly on Linux)
  * export    — transcode back to H264 for delivery
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ── Types ─────────────────────────────────────────────────────────


class ConversionType(str, Enum):
    """Which ProRes flavour to produce."""

    STANDARD = "standard"  # prores_ks profile 3 (HQ), yuv422p10le
    ALPHA = "alpha"  # prores_ks profile 4444, yuva444p10le
    COPY = "copy"  # stream copy (already suitable)


@dataclass
class ProbeResult:
    pix_fmt: str
    conversion: ConversionType


# ── Video extensions we recognise ─────────────────────────────────
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".mov", ".webm", ".flv", ".ts"}


# ── Helpers ───────────────────────────────────────────────────────


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def default_output_dir() -> Path:
    return Path.home() / "Videos" / "vinci-convert"


def ensure_dirs(base: Path) -> tuple[Path, Path]:
    """Create ~/Videos/vinci-convert/{converted,exported} and return both."""
    converted = base / "converted"
    exported = base / "exported"
    converted.mkdir(parents=True, exist_ok=True)
    exported.mkdir(parents=True, exist_ok=True)
    return converted, exported


def subprocess_env() -> dict:
    """Return a copy of the environment for spawning external tools.

    When running frozen (PyInstaller), ``LD_LIBRARY_PATH`` is sanitized
    so the child process loads system libraries instead of bundled ones.
    """
    env = os.environ.copy()
    if not getattr(sys, "frozen", False):
        return env

    # Frozen (PyInstaller/AppImage/Windows installer)
    orig = env.get("LD_LIBRARY_PATH_ORIG")
    if orig is not None:
        env["LD_LIBRARY_PATH"] = orig
        env.pop("LD_LIBRARY_PATH_ORIG", None)
        return env

    current = env.get("LD_LIBRARY_PATH", "")
    if current:
        exe_dir = Path(sys.executable).parent
        meipass = getattr(sys, "_MEIPASS", None)
        keep: list[str] = []
        for entry in current.split(":"):
            p = Path(entry)
            if p == exe_dir or (meipass and p.is_relative_to(meipass)):
                continue
            keep.append(entry)
        if keep:
            env["LD_LIBRARY_PATH"] = ":".join(keep)
        else:
            env.pop("LD_LIBRARY_PATH", None)
    return env


def format_spawn_error(exc: Exception) -> str:
    """Format a subprocess or spawn error for user-facing display."""
    if isinstance(exc, FileNotFoundError):
        return "ffmpeg/ffprobe not found on PATH — please install ffmpeg."
    if isinstance(exc, subprocess.CalledProcessError):
        parts = [f"exit status {exc.returncode}"]
        stderr = getattr(exc, "stderr", None)
        if stderr:
            parts.append(stderr.rstrip())
        if parts:
            return " — ".join(parts)
        return str(exc)
    return str(exc)


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS and path.is_file()


def collect_videos(path: Path) -> list[Path]:
    """Return video files from a single file or a directory (recursive)."""
    if path.is_file():
        return [path] if is_video(path) else []
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if is_video(p))
    return []


# ── ffprobe ───────────────────────────────────────────────────────


def probe(path: Path) -> ProbeResult:
    """Detect the pixel format of the first video stream."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=pix_fmt",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=subprocess_env(),
    )
    pix_fmt = result.stdout.strip()

    if "yuva" in pix_fmt or "rgba" in pix_fmt:
        if "12" in pix_fmt and path.suffix.lower() == ".mov":
            return ProbeResult(pix_fmt, ConversionType.COPY)
        return ProbeResult(pix_fmt, ConversionType.ALPHA)

    return ProbeResult(pix_fmt, ConversionType.STANDARD)


# ── Conversion ────────────────────────────────────────────────────


def build_convert_cmd(
    src: Path, dst: Path, probe_res: ProbeResult
) -> list[str]:
    """Build the ffmpeg command for a ProRes conversion."""
    if probe_res.conversion is ConversionType.COPY:
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            str(dst),
        ]

    if probe_res.conversion is ConversionType.ALPHA:
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4444",
            "-pix_fmt",
            "yuva444p10le",
            "-c:a",
            "pcm_s16be",
            str(dst),
        ]

    # standard
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-c:v",
        "prores_ks",
        "-profile:v",
        "3",
        "-pix_fmt",
        "yuv422p10le",
        "-c:a",
        "pcm_s16be",
        str(dst),
    ]


def build_export_cmd(src: Path, dst: Path) -> list[str]:
    """Build the ffmpeg command for an H264 export."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "0",
        str(dst),
    ]


def run_ffmpeg(cmd: list[str]) -> subprocess.Popen:
    """Start ffmpeg as a subprocess, returning the Popen handle.

    The caller can poll ``handle.poll()`` and read ``handle.stderr`` for
    progress parsing.
    """
    return subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True,
        universal_newlines=True,
        env=subprocess_env(),
    )
