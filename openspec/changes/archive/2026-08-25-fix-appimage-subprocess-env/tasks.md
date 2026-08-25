# Tasks: fix-appimage-subprocess-env

## 1. Subprocess environment sanitization (converter.py)

- [x] 1.1 Add `subprocess_env() -> dict` to `src/vinci_convert/converter.py`: return `os.environ.copy()` unchanged when not frozen (`getattr(sys, "frozen", False)` is false); when frozen, restore `LD_LIBRARY_PATH` from `LD_LIBRARY_PATH_ORIG` if present, else remove entries under `sys._MEIPASS` / the executable directory from `LD_LIBRARY_PATH` (unset it if empty)
- [x] 1.2 Pass `env=subprocess_env()` in `probe()`'s `subprocess.run(...)`
- [x] 1.3 Pass `env=subprocess_env()` in `run_ffmpeg()`'s `subprocess.Popen(...)`

## 2. GUI workers (workers.py)

- [x] 2.1 Import the helper and pass `env=subprocess_env()` in `ConvertWorker._run_ffmpeg()`'s `subprocess.Popen(...)`
- [x] 2.2 Same for `ExportWorker._run_ffmpeg()`'s `subprocess.Popen(...)`

## 3. Diagnosable failure reporting

- [x] 3.1 Add `format_spawn_error(exc) -> str` to `converter.py`: for `CalledProcessError` include exit status and stderr tail (fall back to `str(exc)` when both are empty); for `FileNotFoundError` report the tool as missing from `PATH`
- [x] 3.2 Use `format_spawn_error()` for the probe-failure message in `ConvertWorker.run()` (replacing `getattr(exc, "stderr", None) or str(exc)`)
- [x] 3.3 Use `format_spawn_error()` for ffmpeg failures reported by the CLI path (`cli.py`/`tui.py` probe call site)

## 4. Verification

- [x] 4.1 Source-run regression: `uv run vinci-convert convert <sample>` and a GUI conversion still work (env passthrough unchanged)
- [x] 4.2 Helper sanity check: run `subprocess_env()` under a simulated frozen context (set `sys.frozen`/`sys._MEIPASS` and `LD_LIBRARY_PATH` in a throwaway `python -c`) and assert bundle paths are stripped / `_ORIG` restored
- [x] 4.3 Rebuild PyInstaller binaries + AppImage locally (`pyinstaller` specs, then `packaging/linux/build-appimage.sh`)
- [x] 4.4 AppImage end-to-end: `… cli convert <the file that failed>` succeeds, and a conversion via the AppImage GUI succeeds — reproducing the original report before marking done
- [x] 4.5 Push a `v*` tag (or `workflow_dispatch`) and confirm the CI Linux job's AppImage artifact converts a file on a clean machine/VM
