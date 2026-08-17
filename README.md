# 🎬 Vinci Convert

> Convert videos to **DaVinci Resolve** compatible formats (ProRes) on Linux — with a **Catppuccin-themed** CLI *and* desktop GUI.

A Python reimagining of [davinconv](https://github.com/gohny/davinconv) by Gohny, originally a bash script. This version adds a beautiful live progress TUI, a PySide6 desktop app, recursive directory scanning, and modern Python tooling via [`uv`](https://docs.astral.sh/uv/).

## Features

- **Convert** single files or entire directories (recursive) to ProRes
- **Auto-detect** pixel format — switches between ProRes HQ (422), ProRes 4444 (alpha), or stream copy
- **Export** back to H264 for delivery
- **Catppuccin Mocha** themed — both the terminal UI *and* the desktop GUI
- **Two interfaces**: a `rich`/`typer` CLI and a PySide6 desktop window
- Built with `ffmpeg` / `ffprobe` — no quality loss in copy mode

## Requirements

- Python ≥ 3.11
- `ffmpeg` and `ffprobe` on your `PATH`
- [`uv`](https://docs.astral.sh/uv/) for dependency management

## Install

### 1. Install ffmpeg

```bash
# Fedora
sudo dnf install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

### 2. Install uv (if you don't have it yet)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install vinci-convert

**Option A — run from source (recommended for development):**

```bash
git clone https://github.com/jhonatanmizu/vinci-convert.git
cd vinci-convert
uv sync          # creates .venv and installs dependencies
```

Then run everything through `uv run`:

```bash
uv run vinci-convert --help      # CLI
uv run vinci-convert-gui         # Desktop GUI
```

**Option B — install globally as a CLI tool:**

```bash
git clone https://github.com/jhonatanmizu/vinci-convert.git
cd vinci-convert
uv tool install .
```

This puts `vinci-convert` and `vinci-convert-gui` on your `PATH`, so you can run them from anywhere:

```bash
vinci-convert convert video.mp4
vinci-convert-gui
```

> **Note:** make sure `~/.local/bin` is on your `PATH` for Option B (the `uv` installer usually sets this up; run `uv tool update-shell` if the commands aren't found).

**Updating / uninstalling (Option B):**

```bash
uv tool upgrade vinci-convert     # after pulling new changes, re-run: uv tool install . --force
uv tool uninstall vinci-convert
```

## Usage

### Desktop GUI

```bash
uv run vinci-convert-gui
```

A Catppuccin Mocha themed window with:
- **Single File / Directory** mode toggle
- **Browse** button with native file/folder picker
- Live **info panel** (Input / Output / Codec / Pixel Format / Audio — auto-probed)
- **Progress bar** with elapsed / ETA / size stats
- **Convert / Export H264 / Clean / Quit** buttons
- A scrollable **log panel**

### CLI

```bash
# Convert a single file
uv run vinci-convert convert video.mp4

# Convert all videos in a directory (recursive)
uv run vinci-convert convert ./my_videos/

# Export a converted ProRes file back to H264
uv run vinci-convert export ~/Videos/vinci-convert/converted/clip.mov

# Export all converted files to H264
uv run vinci-convert export-all

# Clean converted files
uv run vinci-convert clean

# Help
uv run vinci-convert --help
```

### Output locations

| Operation | Output directory |
|-----------|-----------------|
| Convert   | `~/Videos/vinci-convert/converted/` |
| Export    | `~/Videos/vinci-convert/exported/` |

## Conversion logic

The tool probes the source with `ffprobe` to detect the pixel format, then picks the right ProRes profile:

| Condition | Codec | Pixel format |
|-----------|-------|-------------|
| Alpha (`yuva`/`rgba`), 12-bit `.mov` | stream copy | — |
| Alpha (`yuva`/`rgba`) | `prores_ks` profile 4444 | `yuva444p10le` |
| Standard | `prores_ks` profile 3 (HQ) | `yuv422p10le` |

Audio is always encoded as `pcm_s16be` (uncompressed, Resolve-friendly).

## Project structure

```
vinci-convert/
├── pyproject.toml
├── README.md
└── src/vinci_convert/
    ├── __init__.py
    ├── __main__.py      # python -m vinci_convert
    ├── cli.py           # Typer CLI
    ├── converter.py     # ffmpeg logic (shared by CLI + GUI)
    ├── theme.py         # Catppuccin palette (Rich terminal)
    ├── tui.py           # Rich live progress UI (CLI)
    ├── qss.py           # Catppuccin palette + QSS stylesheet (GUI)
    ├── workers.py       # QThread ffmpeg workers (GUI)
    └── gui.py           # PySide6 desktop window (GUI)
```

## License

GPL-3.0 — same as the original [davinconv](https://github.com/gohny/davinconv).
