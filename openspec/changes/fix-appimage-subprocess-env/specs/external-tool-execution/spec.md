# external-tool-execution (delta)

## Purpose

Defines how vinci-convert locates and spawns the external `ffmpeg`/`ffprobe` binaries so that probing, converting, and exporting behave identically whether the app runs from source or from a frozen package (PyInstaller build, AppImage, Windows installer).

## ADDED Requirements

### Requirement: External tools are resolved from the user's system

The app SHALL locate `ffmpeg` and `ffprobe` via the user's `PATH` at spawn time, and SHALL NOT require bundled copies of either tool.

#### Scenario: Tools present on PATH

- **WHEN** the user runs any probe, convert, or export operation and `ffmpeg`/`ffprobe` are installed on the system `PATH`
- **THEN** the app spawns the system binaries successfully

#### Scenario: Tools missing

- **WHEN** `ffmpeg` or `ffprobe` is not found on `PATH`
- **THEN** the app reports that the tools must be installed, without attempting conversion

### Requirement: Sanitized subprocess environment under frozen runtimes

When the app runs as a frozen package (PyInstaller one-dir build, including the AppImage and Windows installer forms), every external tool subprocess SHALL be spawned with an environment in which the dynamic-library search path no longer points at the app's bundled libraries: the pre-launch value of `LD_LIBRARY_PATH` SHALL be restored when the bootloader preserved it (`LD_LIBRARY_PATH_ORIG`), otherwise entries belonging to the bundle SHALL be removed from `LD_LIBRARY_PATH`.

#### Scenario: Conversion from the AppImage

- **WHEN** the user probes or converts a video using the AppImage (or any PyInstaller-frozen build)
- **THEN** the spawned `ffprobe`/`ffmpeg` process loads system shared libraries and runs to completion exactly as if launched directly from a shell

#### Scenario: Source run is unaffected

- **WHEN** the app runs from source (e.g. `uv run vinci-convert …`, not frozen)
- **THEN** external tool subprocesses inherit the parent environment unchanged

### Requirement: Diagnosable external tool failures

When an external tool exits non-zero or cannot be spawned, the app SHALL report the failure with the exit status (or spawn error) and the tool's captured stderr output, in both the CLI and the GUI.

#### Scenario: Tool exits non-zero with empty stderr

- **WHEN** `ffprobe`/`ffmpeg` exits non-zero and produced no stderr output
- **THEN** the reported error still states the command's exit status, so the failure is distinguishable from a missing binary or a parse error

#### Scenario: Tool exits non-zero with stderr output

- **WHEN** `ffprobe`/`ffmpeg` exits non-zero and wrote diagnostics to stderr
- **THEN** the reported error includes that stderr content
