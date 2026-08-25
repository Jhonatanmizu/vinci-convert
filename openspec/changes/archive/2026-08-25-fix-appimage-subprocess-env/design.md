# Design: fix-appimage-subprocess-env

## Context

The app shells out to `ffmpeg`/`ffprobe` from four places: `probe()` and `run_ffmpeg()` in `converter.py` (used by the CLI/TUI), and two `subprocess.Popen` calls in `workers.py` (GUI convert/export workers). None of them pass an explicit `env`, so children inherit the process environment.

Under PyInstaller, the bootloader prepends the bundle directory to `LD_LIBRARY_PATH` so the frozen app finds its bundled shared libraries (in one-dir builds, `sys._MEIPASS` is `<exe_dir>/_internal`). Some bootloader versions also save the pre-launch value as `LD_LIBRARY_PATH_ORIG`. When the frozen app then spawns the **system** `ffprobe`, the dynamic linker searches the bundle first and loads incompatible bundled libs (e.g. `libcrypto`/`libssl`/`libz` shipped for Python's `ssl` module), so `ffprobe` dies before producing diagnostics — surfacing as a bare `CalledProcessError: Command '['ffprobe', …]' returned non-zero exit status …` with empty stderr. See proposal.md — Why.

Constraint: `ffmpeg`/`ffprobe` stay external, user-installed tools (decided during packaging work — no bundling).

## Goals / Non-Goals

**Goals:**

- External tool subprocesses behave identically under source runs and frozen builds (AppImage, Windows installer).
- One central place owns the subprocess environment; every spawn site uses it.
- Failures report exit status + stderr so this class of bug is diagnosable from a user screenshot.

**Non-Goals:**

- No bundling of `ffmpeg`/`ffprobe` into the AppImage/installer.
- No changes to conversion parameters, probing logic, or the progress-parsing code.
- No Windows-specific env handling beyond a safe no-op (the bootloader does not rewrite `PATH` on Windows; the defect is POSIX-specific).

## Decisions

### 1. Central helper in `converter.py`, not per-callsite fixes

Add one helper, e.g. `subprocess_env() -> dict`, in `converter.py` (the module already shared by CLI and GUI) and pass `env=…` at all four spawn sites. Alternatives considered:

- **Fix at each callsite independently** — rejected: four copies of the same logic, guaranteed to drift.
- **Sanitize `os.environ` globally at app startup** — rejected: the frozen app itself *needs* the modified `LD_LIBRARY_PATH` to load its bundled Qt libs at runtime (e.g. any later `dlopen`); mutating the whole process env risks breaking the app to fix the child.
- **AppRun wrapper that unsets `LD_LIBRARY_PATH`** — rejected for the same reason: the AppImage's own Qt libs are found through it.

### 2. Sanitization strategy: restore original, else strip bundle paths

When `getattr(sys, "frozen", False)` is true (PyInstaller):

1. If `LD_LIBRARY_PATH_ORIG` exists → set `LD_LIBRARY_PATH` to it (drop the `_ORIG` var). This is exactly what the dynamic linker would have seen before the bootloader intervened.
2. Else → split `LD_LIBRARY_PATH` on `:`, drop entries equal to / under `sys._MEIPASS` (and the executable dir, defensively), keep the rest; unset the var if nothing remains.

When not frozen, return `os.environ.copy()` untouched — zero behavior change for source runs and development. On Windows there is no `LD_LIBRARY_PATH`, so the helper is naturally a no-op beyond the copy.

Alternative considered: **unset `LD_LIBRARY_PATH` entirely** when frozen — simpler, but throws away legitimate user-set entries (e.g. a custom ffmpeg in `/opt` with private libs). Restore/strip preserves user intent.

### 3. Failure formatting helper

Add a small formatter, e.g. `format_spawn_error(exc) -> str`, that renders `CalledProcessError` as `exit status N` + stderr tail (falling back to `str(exc)` only when neither is available), and passes `FileNotFoundError` through as "tool not found on PATH". Use it in `workers.py` (GUI) and anywhere the CLI surfaces probe/spawn failures. Today `workers.py` does `getattr(exc, "stderr", None) or str(exc)` — an empty stderr collapses to the unhelpful `Command '[…]'` dump the user hit.

### 4. Verification via the real AppImage, not mocks

The defect only manifests inside a frozen bundle, so acceptance is: rebuild PyInstaller binaries + AppImage locally, run a real probe/convert through the AppImage GUI and `… cli convert …` path. The project has no test suite; a tiny `tests/` addition is optional and not required by this change (recorded as an assumption).

## Risks / Trade-offs

- [Bootloader neither sets `LD_LIBRARY_PATH_ORIG` nor leaves a recognizable bundle entry] → Mitigation: step 2 strips any path under `sys._MEIPASS`/exe dir, which is where the bootloader points; verified empirically against the produced AppImage before release.
- [User intentionally runs the AppImage with a custom `LD_LIBRARY_PATH` for a non-standard ffmpeg] → Mitigation: we restore the *original* user value (or strip only bundle-owned entries), never a blanket unset.
- [Over-stripping breaks the app itself] → Mitigation: sanitization applies only to child-process `env`, never to `os.environ` of the running app.
- [Fix confirmed on Linux AppImage but not on Windows installer] → Accepted trade-off: Windows is unaffected by this POSIX-only mechanism; the installer build keeps passing env through.

## Migration Plan

No data or config migration. Ship in the next tagged release; users on the broken AppImage simply download the new one. Rollback = revert the commit and re-tag.

## Open Questions

None.
