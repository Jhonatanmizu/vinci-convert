"""CLI entry point — built with Typer.

Usage examples:
    vinci-convert convert video.mp4
    vinci-convert convert ./my_videos/
    vinci-convert export ~/Videos/vinci-convert/converted/clip.mov
    vinci-convert export-all
    vinci-convert clean
"""

from __future__ import annotations

from pathlib import Path

import typer

from . import theme
from .converter import (
    collect_videos,
    default_output_dir,
    ensure_dirs,
    ffmpeg_available,
)
from .tui import convert_with_progress, export_with_progress

app = typer.Typer(
    name="vinci-convert",
    help="Convert videos to DaVinci Resolve compatible formats (ProRes) using ffmpeg.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)


def _check_ffmpeg() -> None:
    if not ffmpeg_available():
        theme.console.print(
            "[status.error]Error:[/] ffmpeg and ffprobe must be installed "
            "and available on your PATH."
        )
        raise typer.Exit(1)


@app.command()
def convert(
    path: Path = typer.Argument(
        ...,
        exists=True,
        help="A single video file or a directory of videos to convert.",
    ),
) -> None:
    """Convert video(s) to ProRes for DaVinci Resolve."""
    _check_ffmpeg()

    videos = collect_videos(path)
    if not videos:
        theme.console.print(
            "[status.warning]No video files found in the given path.[/]"
        )
        raise typer.Exit(1)

    mode = "Single File" if path.is_file() else f"Directory ({len(videos)} files)"
    converted_dir, _ = ensure_dirs(default_output_dir())

    theme.console.print()
    theme.console.print("[app.title]🎬 Vinci Convert[/]")
    theme.console.print(f"[app.subtitle]DaVinci Resolve Video Converter · ProRes[/]")

    successes = 0
    for i, src in enumerate(videos, 1):
        theme.console.print(
            f"\n[status.info]({i}/{len(videos)})[/] Processing [info.input]{src.name}[/]"
        )
        dst = converted_dir / f"{src.stem}.mov"
        ok = convert_with_progress(src, dst, mode)
        if ok:
            successes += 1
            theme.console.print(
                f"  [status.success]✓[/] {src.name} → {dst.name}"
            )
        else:
            theme.console.print(
                f"  [status.error]✕[/] Failed to convert {src.name}"
            )

    theme.console.print(
        f"\n[status.success]Done![/] {successes}/{len(videos)} files converted."
    )
    theme.console.print(
        f"[dim]Output: {converted_dir}[/]"
    )


@app.command()
def export(
    file: Path = typer.Argument(
        ...,
        exists=True,
        help="A converted ProRes .mov file to export back to H264.",
    ),
) -> None:
    """Export a converted ProRes file back to H264."""
    _check_ffmpeg()

    _, exported_dir = ensure_dirs(default_output_dir())
    dst = exported_dir / f"{file.stem}.mp4"

    theme.console.print()
    theme.console.print("[app.title]🎬 Vinci Convert[/]")
    theme.console.print(f"[app.subtitle]Export to H264[/]")

    ok = export_with_progress(file, dst)
    if ok:
        theme.console.print(
            f"\n[status.success]✓[/] {file.name} → {dst.name}"
        )
        theme.console.print(f"[dim]Output: {exported_dir}[/]")
    else:
        theme.console.print(f"\n[status.error]✕[/] Export failed.")
        raise typer.Exit(1)


@app.command(name="export-all")
def export_all() -> None:
    """Export all converted videos in ~/Videos/vinci-convert/converted/ to H264."""
    _check_ffmpeg()

    base = default_output_dir()
    converted_dir, exported_dir = ensure_dirs(base)

    videos = sorted(converted_dir.glob("*.mov"))
    if not videos:
        theme.console.print(
            "[status.warning]No converted .mov files found in "
            f"{converted_dir}[/]"
        )
        raise typer.Exit(1)

    theme.console.print()
    theme.console.print("[app.title]🎬 Vinci Convert[/]")
    theme.console.print(f"[app.subtitle]Bulk export to H264 ({len(videos)} files)[/]")

    successes = 0
    for i, src in enumerate(videos, 1):
        dst = exported_dir / f"{src.stem}.mp4"
        theme.console.print(
            f"\n[status.info]({i}/{len(videos)})[/] Exporting [info.codec]{src.name}[/]"
        )
        ok = export_with_progress(src, dst)
        if ok:
            successes += 1
            theme.console.print(
                f"  [status.success]✓[/] {src.name} → {dst.name}"
            )
        else:
            theme.console.print(
                f"  [status.error]✕[/] Failed to export {src.name}"
            )

    theme.console.print(
        f"\n[status.success]Done![/] {successes}/{len(videos)} files exported."
    )
    theme.console.print(f"[dim]Output: {exported_dir}[/]")


@app.command()
def clean() -> None:
    """Remove all converted videos in ~/Videos/vinci-convert/converted/."""
    converted_dir, _ = ensure_dirs(default_output_dir())

    confirm = typer.confirm(
        f"Delete ALL files in {converted_dir}?", default=False
    )
    if not confirm:
        theme.console.print("[dim]No changes made.[/]")
        raise typer.Exit()

    for f in converted_dir.iterdir():
        if f.is_file():
            f.unlink()

    theme.console.print(f"[status.success]✓[/] Cleaned {converted_dir}")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        None, "--version", "-v", help="Show version and exit.", is_eager=True
    ),
) -> None:
    if version:
        theme.console.print("[app.title]vinci-convert[/] v0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
