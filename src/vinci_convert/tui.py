"""Rich-based terminal UI for vinci-convert.

Provides a live, Catppuccin-themed progress view during conversion.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from . import theme
from .converter import (
    ConversionType,
    build_convert_cmd,
    build_export_cmd,
    probe,
    run_ffmpeg,
)

# Regex to parse ffmpeg progress lines
_TIME_RE = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
_DURATION_RE = re.compile(
    r"Duration:\s*(\d+:\d+:\d+\.\d+)"
)


def _time_to_seconds(t: str) -> float:
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _render_info_panel(
    src: Path,
    dst: Path,
    probe_res,
    mode: str,
) -> Panel:
    """Render the file-info panel (mirrors the canvas mockup)."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="info.label", no_wrap=True)
    table.add_column(style="white")

    conversion_label = {
        ConversionType.STANDARD: "prores_ks · profile 3 (HQ)",
        ConversionType.ALPHA: "prores_ks · profile 4444",
        ConversionType.COPY: "stream copy (already compatible)",
    }[probe_res.conversion]

    pixfmt_note = {
        ConversionType.ALPHA: " (alpha detected)",
        ConversionType.COPY: " (12-bit .mov)",
        ConversionType.STANDARD: "",
    }[probe_res.conversion]

    table.add_row("Mode", mode)
    table.add_row("Input", str(src))
    table.add_row("Output", str(dst))
    table.add_row("Codec", conversion_label)
    table.add_row(
        "Pixel Format", f"{probe_res.pix_fmt}{pixfmt_note}"
    )
    table.add_row("Audio", "pcm_s16be")

    return Panel(
        table,
        border_style=theme.SURFACE2,
        padding=(1, 2),
        title=f"[app.title]🎬 Vinci Convert[/]",
        subtitle="[app.subtitle]DaVinci Resolve Video Converter[/]",
    )


def convert_with_progress(
    src: Path,
    dst: Path,
    mode: str,
) -> bool:
    """Convert a single file with a live progress bar. Returns True on success."""
    probe_res = probe(src)
    cmd = build_convert_cmd(src, dst, probe_res)
    info_panel = _render_info_panel(src, dst, probe_res, mode)

    progress = Progress(
        SpinnerColumn(style=theme.MAUVE),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=theme.MAUVE, finished_style=theme.GREEN),
        TaskProgressColumn(style=theme.MAUVE),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=theme.console,
        expand=True,
    )

    task_id = progress.add_task(
        f"Converting: {src.name} → {dst.name}", total=None
    )

    proc = run_ffmpeg(cmd)
    duration: float | None = None
    live = Live(
        Group(info_panel, progress),
        console=theme.console,
        refresh_per_second=10,
        vertical_overflow="visible",
    )

    with live:
        assert proc.stderr is not None
        for line in proc.stderr:
            if duration is None:
                m = _DURATION_RE.search(line)
                if m:
                    duration = _time_to_seconds(m.group(1))
                    progress.update(task_id, total=duration)
                    continue

            m = _TIME_RE.search(line)
            if m and duration:
                current = _time_to_seconds(m.group(1))
                progress.update(task_id, completed=min(current, duration))

        proc.wait()
        progress.update(task_id, completed=progress.tasks[task_id].total or 1)

    return proc.returncode == 0


def export_with_progress(src: Path, dst: Path) -> bool:
    """Export a ProRes file back to H264 with a live progress bar."""
    cmd = build_export_cmd(src, dst)

    progress = Progress(
        SpinnerColumn(style=theme.BLUE),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=theme.BLUE, finished_style=theme.GREEN),
        TaskProgressColumn(style=theme.BLUE),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=theme.console,
        expand=True,
    )

    task_id = progress.add_task(
        f"Exporting: {src.name} → {dst.name}", total=None
    )

    proc = run_ffmpeg(cmd)
    duration: float | None = None
    live = Live(
        progress,
        console=theme.console,
        refresh_per_second=10,
    )

    with live:
        assert proc.stderr is not None
        for line in proc.stderr:
            if duration is None:
                m = _DURATION_RE.search(line)
                if m:
                    duration = _time_to_seconds(m.group(1))
                    progress.update(task_id, total=duration)
                    continue

            m = _TIME_RE.search(line)
            if m and duration:
                current = _time_to_seconds(m.group(1))
                progress.update(task_id, completed=min(current, duration))

        proc.wait()
        progress.update(task_id, completed=progress.tasks[task_id].total or 1)

    return proc.returncode == 0
