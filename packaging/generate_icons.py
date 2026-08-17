"""Generate the vinci-convert app icons (PNG + multi-size ICO).

Renders a Catppuccin Mocha themed icon with QPainter:
  rounded-square gradient (mauve -> blue) with a white play triangle.

Usage:
    QT_QPA_PLATFORM=offscreen uv run python packaging/generate_icons.py

Outputs (committed to the repo):
    packaging/assets/vinci-convert.png    256x256 PNG (AppImage / .desktop)
    packaging/assets/vinci-convert.ico    multi-size ICO (Windows exe/installer)
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)

ASSETS = Path(__file__).parent / "assets"

# Catppuccin Mocha
MAUVE = QColor("#cba6f7")
BLUE = QColor("#89b4fa")
TEXT = QColor("#ffffff")


def render_icon(size: int) -> QImage:
    """Render the icon at the given pixel size."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = size * 0.02
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    radius = size * 0.22

    # Background: rounded square with a diagonal mauve -> blue gradient
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, MAUVE)
    gradient.setColorAt(1.0, BLUE)

    bg = QPainterPath()
    bg.addRoundedRect(rect, radius, radius)
    painter.fillPath(bg, QBrush(gradient))

    # Foreground: white play triangle, slightly right of optical center
    w = size * 0.34
    h = size * 0.40
    cx = size * 0.54
    cy = size * 0.50
    tri = QPainterPath()
    tri.moveTo(QPointF(cx - w / 2, cy - h / 2))
    tri.lineTo(QPointF(cx - w / 2, cy + h / 2))
    tri.lineTo(QPointF(cx + w / 2, cy))
    tri.closeSubpath()
    painter.fillPath(tri, QBrush(TEXT))

    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buf, "PNG")
    buf.close()
    return bytes(data)


def write_ico(path: Path, sizes: list[int]) -> None:
    """Write a multi-size ICO using PNG-compressed entries (Vista+)."""
    images = [(s, png_bytes(render_icon(s))) for s in sizes]

    header = struct.pack("<HHH", 0, 1, len(images))
    entries = b""
    offset = 6 + 16 * len(images)
    blobs = b""
    for size, blob in images:
        width = size if size < 256 else 0  # 0 means 256 in ICO
        entries += struct.pack(
            "<BBBBHHII", width, width, 0, 0, 1, 32, len(blob), offset
        )
        blobs += blob
        offset += len(blob)

    path.write_bytes(header + entries + blobs)


def main() -> int:
    app = QGuiApplication(sys.argv)  # noqa: F841  (needed for QPainter)

    ASSETS.mkdir(parents=True, exist_ok=True)

    png_path = ASSETS / "vinci-convert.png"
    render_icon(256).save(str(png_path), "PNG")
    print(f"wrote {png_path}")

    ico_path = ASSETS / "vinci-convert.ico"
    write_ico(ico_path, [16, 24, 32, 48, 64, 128, 256])
    print(f"wrote {ico_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
