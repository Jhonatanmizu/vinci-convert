"""Qt worker threads for running ffmpeg without blocking the UI."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from .converter import (
    build_convert_cmd,
    build_export_cmd,
    probe,
)

_TIME_RE = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
_DURATION_RE = re.compile(r"Duration:\s*(\d+:\d+:\d+\.\d+)")
_OUT_TIME_RE = re.compile(r"out_time_us=(\d+)")


def _time_to_seconds(t: str) -> float:
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _parse_out_time_us(line: str) -> float | None:
    """Return seconds from an ffmpeg 'out_time_us=...' line, or None if N/A."""
    value = line.split("=", 1)[1]
    try:
        return int(value) / 1_000_000.0
    except ValueError:
        return None


class ConvertWorker(QObject):
    """Convert a list of files to ProRes, emitting progress signals."""

    started_file = Signal(str, str, str, str)  # src, dst, codec, pixfmt
    progress = Signal(int, str)  # percent, status
    file_done = Signal(str, bool)  # filename, success
    finished_all = Signal(int, int)  # successes, total
    log = Signal(str)
    error = Signal(str)

    def __init__(self, files: list[Path], converted_dir: Path) -> None:
        super().__init__()
        self._files = files
        self._converted_dir = converted_dir
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        successes = 0
        total = len(self._files)
        try:
            for idx, src in enumerate(self._files, 1):
                if self._cancel:
                    break
                dst = self._converted_dir / f"{src.stem}.mov"
                try:
                    probe_res = probe(src)
                except Exception as exc:
                    msg = getattr(exc, "stderr", None) or str(exc)
                    self.error.emit(f"ffprobe failed on {src.name}: {msg}")
                    self.file_done.emit(src.name, False)
                    continue

                codec_label = {
                    "standard": "prores_ks · profile 3 (HQ)",
                    "alpha": "prores_ks · profile 4444",
                    "copy": "stream copy (already compatible)",
                }[probe_res.conversion.value]

                self.started_file.emit(
                    str(src), str(dst), codec_label, probe_res.pix_fmt
                )
                self.log.emit(
                    f"[{idx}/{total}] Converting {src.name} → {dst.name}  "
                    f"({codec_label}, {probe_res.pix_fmt})"
                )

                try:
                    cmd = build_convert_cmd(src, dst, probe_res)
                    ok = self._run_ffmpeg(cmd, src.name, dst.name)
                except Exception as exc:
                    self.error.emit(f"ffmpeg crashed on {src.name}: {exc}")
                    ok = False

                if ok:
                    successes += 1
                    self.log.emit(f"  ✓ {src.name} → {dst.name}")
                else:
                    self.log.emit(f"  ✕ Failed: {src.name}")
                self.file_done.emit(src.name, ok)
        except Exception as exc:
            self.error.emit(f"Worker crashed: {exc}")
        finally:
            self.finished_all.emit(successes, total)

    def _run_ffmpeg(self, cmd: list[str], src_name: str, dst_name: str) -> bool:
        # Use ffmpeg's machine-readable progress on stdout (-progress pipe:1)
        # for reliable, newline-delimited updates. stderr is captured for
        # diagnostics only.
        progress_cmd = list(cmd)
        if "-progress" not in progress_cmd:
            # insert before the output path (last arg)
            progress_cmd[-1:-1] = ["-progress", "pipe:1", "-nostats"]

        proc = subprocess.Popen(
            progress_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
        )
        assert proc.stdout is not None
        assert proc.stderr is not None

        # drain stderr (banner / warnings / errors) on a thread so it
        # can't deadlock the pipe while we read progress from stdout.
        import threading
        stderr_lines: list[str] = []
        dur: dict[str, float] = {"v": 0.0}
        def drain_stderr() -> None:
            assert proc.stderr is not None
            for line in proc.stderr:
                stderr_lines.append(line)
                if dur["v"] == 0.0:
                    m = _DURATION_RE.search(line)
                    if m:
                        dur["v"] = _time_to_seconds(m.group(1))
        t = threading.Thread(target=drain_stderr, daemon=True)
        t.start()

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if line.startswith("out_time_us="):
                current = _parse_out_time_us(line)
                if current is None:
                    continue
                d = dur["v"]
                if d > 0:
                    pct = int(min(current / d * 100, 100))
                    self.progress.emit(
                        max(pct, 0),
                        f"Converting: {src_name} → {dst_name}",
                    )
            elif line == "progress=end":
                self.progress.emit(100, f"Converting: {src_name} → {dst_name}")

        proc.wait()
        t.join(timeout=2)
        if proc.returncode != 0:
            tail = "".join(stderr_lines[-20:])
            self.error.emit(f"ffmpeg exit {proc.returncode} for {src_name}:\n{tail}")
        return proc.returncode == 0


class ExportWorker(QObject):
    """Export ProRes files back to H264."""

    started_file = Signal(str, str)
    progress = Signal(int, str)
    file_done = Signal(str, bool)
    finished_all = Signal(int, int)
    log = Signal(str)
    error = Signal(str)

    def __init__(self, files: list[Path], exported_dir: Path) -> None:
        super().__init__()
        self._files = files
        self._exported_dir = exported_dir
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        successes = 0
        total = len(self._files)
        try:
            for idx, src in enumerate(self._files, 1):
                if self._cancel:
                    break
                dst = self._exported_dir / f"{src.stem}.mp4"
                self.started_file.emit(str(src), str(dst))
                self.log.emit(f"[{idx}/{total}] Exporting {src.name} → {dst.name}")
                try:
                    cmd = build_export_cmd(src, dst)
                    ok = self._run_ffmpeg(cmd, src.name, dst.name)
                except Exception as exc:
                    self.error.emit(f"ffmpeg crashed on {src.name}: {exc}")
                    ok = False
                if ok:
                    successes += 1
                    self.log.emit(f"  ✓ {src.name} → {dst.name}")
                else:
                    self.log.emit(f"  ✕ Failed: {src.name}")
                self.file_done.emit(src.name, ok)
        except Exception as exc:
            self.error.emit(f"Worker crashed: {exc}")
        finally:
            self.finished_all.emit(successes, total)

    def _run_ffmpeg(self, cmd: list[str], src_name: str, dst_name: str) -> bool:
        progress_cmd = list(cmd)
        if "-progress" not in progress_cmd:
            progress_cmd[-1:-1] = ["-progress", "pipe:1", "-nostats"]

        proc = subprocess.Popen(
            progress_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
        )
        assert proc.stdout is not None
        assert proc.stderr is not None

        import threading
        stderr_lines: list[str] = []
        dur: dict[str, float] = {"v": 0.0}
        def drain_stderr() -> None:
            assert proc.stderr is not None
            for line in proc.stderr:
                stderr_lines.append(line)
                if dur["v"] == 0.0:
                    m = _DURATION_RE.search(line)
                    if m:
                        dur["v"] = _time_to_seconds(m.group(1))
        t = threading.Thread(target=drain_stderr, daemon=True)
        t.start()

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if line.startswith("out_time_us="):
                current = _parse_out_time_us(line)
                if current is None:
                    continue
                d = dur["v"]
                if d > 0:
                    pct = int(min(current / d * 100, 100))
                    self.progress.emit(
                        max(pct, 0), f"Exporting: {src_name} → {dst_name}"
                    )
            elif line == "progress=end":
                self.progress.emit(100, f"Exporting: {src_name} → {dst_name}")

        proc.wait()
        t.join(timeout=2)
        if proc.returncode != 0:
            tail = "".join(stderr_lines[-20:])
            self.error.emit(f"ffmpeg exit {proc.returncode} for {src_name}:\n{tail}")
        return proc.returncode == 0
