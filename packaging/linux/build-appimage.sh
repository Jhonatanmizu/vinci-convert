#!/usr/bin/env bash
# Build the vinci-convert AppImage from the PyInstaller one-dir builds.
#
# Prerequisites:
#   dist/vinci-convert/      (pyinstaller --onedir build of the CLI)
#   dist/vinci-convert-gui/  (pyinstaller --onedir build of the GUI)
#
# Usage:
#   packaging/linux/build-appimage.sh [version]
#
# Output:
#   dist/vinci-convert-<version>-x86_64.AppImage

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

VERSION="${1:-$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)}"
ARCH="x86_64"
BUILD_DIR="build/appimage"
APPDIR="$BUILD_DIR/vinci-convert.AppDir"
APPIMAGETOOL="$BUILD_DIR/appimagetool-$ARCH.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
OUTPUT="dist/vinci-convert-$VERSION-$ARCH.AppImage"

# ── Sanity checks ──────────────────────────────────────────────────
for d in dist/vinci-convert dist/vinci-convert-gui; do
    if [ ! -d "$d" ]; then
        echo "error: $d not found — run the PyInstaller builds first:" >&2
        echo "  uv run pyinstaller packaging/vinci-convert.spec --noconfirm" >&2
        echo "  uv run pyinstaller packaging/vinci-convert-gui.spec --noconfirm" >&2
        exit 1
    fi
done

# ── Assemble the AppDir ────────────────────────────────────────────
echo "==> Assembling AppDir for v$VERSION"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

cp -r dist/vinci-convert "$APPDIR/usr/bin/vinci-convert"
cp -r dist/vinci-convert-gui "$APPDIR/usr/bin/vinci-convert-gui"

DESKTOP_ID="io.github.jhonatanmizu.vinci_convert"

cp packaging/linux/AppRun "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

cp "packaging/linux/$DESKTOP_ID.desktop" "$APPDIR/$DESKTOP_ID.desktop"
cp packaging/assets/vinci-convert.png "$APPDIR/vinci-convert.png"

# Also provide the freedesktop-style locations for tools that look there.
mkdir -p "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/metainfo"
cp "packaging/linux/$DESKTOP_ID.desktop" "$APPDIR/usr/share/applications/"
cp packaging/assets/vinci-convert.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/"
cp "packaging/linux/$DESKTOP_ID.appdata.xml" "$APPDIR/usr/share/metainfo/"

# ── Fetch appimagetool (cached in build/) ──────────────────────────
mkdir -p "$BUILD_DIR"
if [ ! -x "$APPIMAGETOOL" ]; then
    echo "==> Downloading appimagetool"
    curl -fSL "$APPIMAGETOOL_URL" -o "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# ── Pack the AppImage ──────────────────────────────────────────────
# appimagetool is itself an AppImage and needs FUSE; fall back to
# --appimage-extract-and-run inside containers / CI without it.
echo "==> Packing $OUTPUT"
rm -f "$OUTPUT"
if [ -e /dev/fuse ]; then
    ARCH="$ARCH" "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
else
    echo "    (no /dev/fuse — using --appimage-extract-and-run)"
    ARCH="$ARCH" "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$OUTPUT"
fi

chmod +x "$OUTPUT"
echo "==> Done: $OUTPUT"
