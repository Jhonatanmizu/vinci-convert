# Proposal: fix-appimage-subprocess-env

## Why

The AppImage build of vinci-convert launches fine, but every conversion fails at the probe step with a raw `CalledProcessError` dump: `Command '['ffprobe', '-v', 'error', '-select_streams', 'v:0', ...]' returned non-zero exit status …`. The system `ffprobe` binary exists and works outside the app — it crashes only when spawned from inside the frozen (PyInstaller/AppImage) process, because the subprocess inherits `LD_LIBRARY_PATH` pointing at the app's bundled libraries and loads incompatible shared libs. The packaged app is currently unusable for its core purpose.

## What Changes

- Spawn all external tool subprocesses (`ffprobe` probe, `ffmpeg` convert/export) with a **sanitized environment** when the app runs frozen: restore `LD_LIBRARY_PATH_ORIG` when the bootloader provides it, otherwise strip bundle paths (`sys._MEIPASS` / executable dir) from `LD_LIBRARY_PATH`.
- Apply the sanitization centrally in `converter.py` so every spawn site benefits: `probe()`, `run_ffmpeg()`, and the two `subprocess.Popen` calls in `workers.py` (GUI convert/export workers).
- Improve failure diagnostics: when an external tool exits non-zero, surface the exit status **and** captured stderr (currently an empty stderr collapses to an unhelpful `Command '[…]'` dump).
- No change when running from source (non-frozen): the environment passes through unchanged.

## Capabilities

### New Capabilities

- `external-tool-execution`: how the app locates and spawns `ffmpeg`/`ffprobe` — environment sanitization under frozen (PyInstaller/AppImage) runtimes, PATH passthrough under source runs, and diagnosable failure reporting.

### Modified Capabilities

<!-- None — openspec/specs/ has no existing capabilities. -->

## Impact

- **Code**: `src/vinci_convert/converter.py` (new env helper, used by `probe()` and `run_ffmpeg()`), `src/vinci_convert/workers.py` (pass sanitized env to both `Popen` calls, better error text). `tui.py` and `cli.py` inherit the fix via `converter.py` — no direct edits.
- **Behavior**: conversions/exports work in the AppImage (and Windows frozen builds, defensively); source runs are unchanged.
- **Packaging**: none — `ffmpeg`/`ffprobe` remain external user-installed dependencies; no bundling, no spec/installer changes.
- **Dependencies**: none added (stdlib only).
