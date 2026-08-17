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

### Option 0 — Download a prebuilt package (no Python needed)

Grab the latest release from [GitHub Releases](https://github.com/jhonatanmizu/vinci-convert/releases):

| Platform | Package | Notes |
|----------|---------|-------|
| Linux    | `vinci-convert-*-x86_64.AppImage` | Portable — `chmod +x` and run |
| Windows  | `vinci-convert-*-windows-x86_64-setup.exe` | Per-user installer, no admin needed |

> **ffmpeg is still required** — the app calls `ffmpeg`/`ffprobe` from your `PATH`. See [Install ffmpeg](#1-install-ffmpeg) below.

**Linux (AppImage):**

```bash
chmod +x vinci-convert-*-x86_64.AppImage
./vinci-convert-*-x86_64.AppImage          # launches the GUI
./vinci-convert-*-x86_64.AppImage cli --help   # runs the CLI
```

**Windows:** run the setup exe. It installs into `%LOCALAPPDATA%\Programs\Vinci Convert` (no UAC prompt), adds a Start Menu entry for the GUI, and a **"Vinci Convert CLI"** shortcut that opens a terminal with `vinci-convert` on `PATH`.

### Build from source

#### 1. Install ffmpeg

```bash
# Fedora
sudo dnf install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

#### 2. Install uv (if you don't have it yet)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 3. Install vinci-convert

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

## Building the installers

The prebuilt packages are produced by [`.github/workflows/release.yml`](.github/workflows/release.yml) on every `v*` tag (or manual dispatch). To build locally:

**Linux (AppImage):**

```bash
uv sync                                                   # includes PyInstaller (dev group)
uv run pyinstaller packaging/vinci-convert.spec --noconfirm
uv run pyinstaller packaging/vinci-convert-gui.spec --noconfirm
packaging/linux/build-appimage.sh                         # → dist/vinci-convert-<version>-x86_64.AppImage
```

**Windows (Inno Setup):** on a Windows machine with [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed:

```powershell
uv sync
uv run pyinstaller packaging/vinci-convert.spec --noconfirm
uv run pyinstaller packaging/vinci-convert-gui.spec --noconfirm
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\installer.iss
# → dist\installer\vinci-convert-<version>-windows-x86_64-setup.exe
```

To regenerate the app icons: `QT_QPA_PLATFORM=offscreen uv run python packaging/generate_icons.py`

## Project structure

```
vinci-convert/
├── pyproject.toml
├── README.md
├── .github/workflows/
│   └── release.yml      # CI: builds AppImage + Windows installer, publishes releases
├── packaging/
│   ├── cli_launcher.py  # PyInstaller entry scripts
│   ├── gui_launcher.py
│   ├── vinci-convert.spec       # PyInstaller spec (CLI)
│   ├── vinci-convert-gui.spec   # PyInstaller spec (GUI)
│   ├── generate_icons.py        # icon generator (QPainter, Catppuccin)
│   ├── assets/          # generated vinci-convert.png / .ico
│   ├── linux/           # AppRun, .desktop, AppStream metadata, AppImage script
│   └── windows/
│       └── installer.iss        # Inno Setup installer
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
