"""
Generate high-resolution, multi-size Windows .ico and .png branding assets for CleanGuard.
Creates 256x256, 128x128, 64x64, 48x48, 32x32, and 16x16 icon sizes embedded in a valid .ico file.
"""

import os
import sys
import struct

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import (
    QImage,
    QPainter,
    QPainterPath,
    QLinearGradient,
    QRadialGradient,
    QColor,
    QPen,
    QBrush,
)
from PyQt5.QtCore import Qt, QPointF, QBuffer, QIODevice


def draw_cleanguard_logo(size: int = 512) -> QImage:
    """Draw a state-of-the-art CleanGuard shield logo with modern gradients and bevels."""
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    scale = size / 512.0
    center_x = size / 2.0

    # 1. Subtle Outer Glow / Drop Shadow
    shadow_path = QPainterPath()
    top = 44 * scale
    bottom = 472 * scale
    left = 56 * scale
    right = size - left
    mid_y = 280 * scale

    shadow_path.moveTo(center_x, top)
    shadow_path.cubicTo(right + 4 * scale, top + 36 * scale, right, mid_y, center_x, bottom)
    shadow_path.cubicTo(left, mid_y, left - 4 * scale, top + 36 * scale, center_x, top)
    shadow_path.closeSubpath()

    painter.fillPath(shadow_path, QColor(0, 0, 0, 80))

    # 2. Main Outer Shield with Emerald Gradient
    shield_path = QPainterPath()
    s_top = 40 * scale
    s_bottom = 464 * scale
    s_left = 60 * scale
    s_right = size - s_left
    s_mid_y = 276 * scale

    shield_path.moveTo(center_x, s_top)
    shield_path.cubicTo(s_right, s_top + 34 * scale, s_right, s_mid_y, center_x, s_bottom)
    shield_path.cubicTo(s_left, s_mid_y, s_left, s_top + 34 * scale, center_x, s_top)
    shield_path.closeSubpath()

    grad = QLinearGradient(0, s_top, size, s_bottom)
    grad.setColorAt(0.0, QColor("#059669"))   # Emerald 600
    grad.setColorAt(0.4, QColor("#10B981"))   # Emerald 500
    grad.setColorAt(1.0, QColor("#047857"))   # Emerald 700

    painter.fillPath(shield_path, grad)

    # 3. Outer Shield Border (Glossy specular accent)
    border_pen = QPen(QColor("#34D399"), 6.0 * scale)
    painter.strokePath(shield_path, border_pen)

    # 4. Inner Recessed Shield Plate (Deep Dark Glassmorphism)
    inner_path = QPainterPath()
    in_top = 64 * scale
    in_bottom = 436 * scale
    in_left = 86 * scale
    in_right = size - in_left
    in_mid_y = 264 * scale

    inner_path.moveTo(center_x, in_top)
    inner_path.cubicTo(in_right, in_top + 28 * scale, in_right, in_mid_y, center_x, in_bottom)
    inner_path.cubicTo(in_left, in_mid_y, in_left, in_top + 28 * scale, center_x, in_top)
    inner_path.closeSubpath()

    inner_grad = QLinearGradient(0, in_top, 0, in_bottom)
    inner_grad.setColorAt(0.0, QColor("#064E3B"))  # Deep emerald
    inner_grad.setColorAt(0.6, QColor("#065F46"))
    inner_grad.setColorAt(1.0, QColor("#022C22"))  # Dark emerald base

    painter.fillPath(inner_path, inner_grad)

    inner_border_pen = QPen(QColor(16, 185, 129, 120), 2.5 * scale)
    painter.strokePath(inner_path, inner_border_pen)

    # 5. Radial Specular Light Burst (Top Highlight)
    radial_highlight = QRadialGradient(center_x, in_top + 40 * scale, 160 * scale)
    radial_highlight.setColorAt(0.0, QColor(255, 255, 255, 90))
    radial_highlight.setColorAt(0.5, QColor(110, 231, 183, 40))
    radial_highlight.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.fillPath(inner_path, radial_highlight)

    # 6. Central Emblem: Dynamic Speed Lightning & Clean Checkmark Symbol
    crest_path = QPainterPath()
    # Crisp geometric high-velocity check / spark shape
    p1 = QPointF(center_x - 76 * scale, 240 * scale)
    p2 = QPointF(center_x - 16 * scale, 310 * scale)
    p3 = QPointF(center_x + 92 * scale, 172 * scale)
    p4 = QPointF(center_x + 104 * scale, 186 * scale)
    p5 = QPointF(center_x - 16 * scale, 344 * scale)
    p6 = QPointF(center_x - 90 * scale, 258 * scale)

    crest_path.moveTo(p1)
    crest_path.lineTo(p2)
    crest_path.lineTo(p3)
    crest_path.lineTo(p4)
    crest_path.lineTo(p5)
    crest_path.lineTo(p6)
    crest_path.closeSubpath()

    crest_grad = QLinearGradient(p1, p3)
    crest_grad.setColorAt(0.0, QColor("#ECFDF5"))  # Pure luminous white/mint
    crest_grad.setColorAt(0.5, QColor("#FFFFFF"))
    crest_grad.setColorAt(1.0, QColor("#A7F3D0"))  # Soft emerald mint

    painter.fillPath(crest_path, crest_grad)

    # Add crisp crest stroke
    crest_pen = QPen(QColor(255, 255, 255, 200), 2.0 * scale)
    painter.strokePath(crest_path, crest_pen)

    # 7. Geometric Velocity Sparkles (Cleanliness & Speed)
    star_brush = QBrush(QColor("#FDE68A"))  # Warm golden amber spark
    painter.setBrush(star_brush)
    painter.setPen(Qt.NoPen)

    # Star dot top-right
    s1_x = center_x + 64 * scale
    s1_y = 126 * scale
    s1_r = 6.0 * scale
    painter.drawEllipse(QPointF(s1_x, s1_y), s1_r, s1_r)

    # Star dot bottom-left
    s2_x = center_x - 60 * scale
    s2_y = 350 * scale
    s2_r = 4.5 * scale
    painter.drawEllipse(QPointF(s2_x, s2_y), s2_r, s2_r)

    painter.end()
    return img


def qimage_to_png_bytes(img: QImage) -> bytes:
    """Convert QImage to PNG byte string."""
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    data = bytes(buf.data())
    buf.close()
    return data


def create_windows_ico(png_data_dict: dict) -> bytes:
    """
    Construct a valid Windows .ico binary containing PNG-compressed images.
    png_data_dict: mapping of size (e.g. 256, 128, 64, 48, 32, 16) -> png bytes.
    """
    num_images = len(png_data_dict)
    ico_header = struct.pack("<HHH", 0, 1, num_images)
    offset = 6 + (16 * num_images)

    entries = []
    data_blobs = []

    for size in sorted(png_data_dict.keys(), reverse=True):
        png_bytes = png_data_dict[size]
        length = len(png_bytes)

        w_byte = 0 if size >= 256 else size
        h_byte = 0 if size >= 256 else size

        entry = struct.pack(
            "<BBBBHHII",
            w_byte,
            h_byte,
            0,      # color count
            0,      # reserved
            1,      # planes
            32,     # bpp
            length,
            offset,
        )
        entries.append(entry)
        data_blobs.append(png_bytes)
        offset += length

    return ico_header + b"".join(entries) + b"".join(data_blobs)


def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(root_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print(f"Generating CleanGuard branding assets in: {assets_dir}")

    # Generate master 512x512 vector render
    master_512 = draw_cleanguard_logo(512)
    png_512_path = os.path.join(assets_dir, "cleanguard_512.png")
    master_512.save(png_512_path, "PNG")
    print(f"Saved master 512x512 PNG: {png_512_path}")

    # Save 256x256 standard PNG
    master_256 = master_512.scaled(256, 256, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    png_256_path = os.path.join(assets_dir, "cleanguard.png")
    master_256.save(png_256_path, "PNG")
    print(f"Saved primary 256x256 PNG: {png_256_path}")

    # Standard Windows ICO resolutions
    sizes = [256, 128, 64, 48, 32, 16]
    png_dict = {}

    for s in sizes:
        scaled_img = master_512.scaled(s, s, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        png_dict[s] = qimage_to_png_bytes(scaled_img)
        print(f"  - Rendered {s}x{s} frame ({len(png_dict[s])} bytes)")

    ico_bytes = create_windows_ico(png_dict)
    ico_path = os.path.join(assets_dir, "cleanguard.ico")
    with open(ico_path, "wb") as f:
        f.write(ico_bytes)

    print(f"Successfully generated Windows multi-resolution ICO: {ico_path} ({len(ico_bytes)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
