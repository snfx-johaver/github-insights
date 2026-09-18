"""Generate deterministic placeholder brand PNGs for repository validation."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).parents[1]
BRAND = ROOT / "custom_components" / "github_insights" / "brand"
SIZE = 256


def chunk(kind: bytes, data: bytes) -> bytes:
    """Encode a PNG chunk."""
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def create_png(path: Path, dark: bool) -> None:
    """Create a simple GitHub Insights placeholder icon."""
    background = (24, 26, 32, 255) if dark else (245, 247, 250, 255)
    foreground = (117, 79, 254, 255) if dark else (72, 50, 165, 255)
    rows = []
    center = (SIZE - 1) / 2
    for y in range(SIZE):
        row = bytearray([0])
        for x in range(SIZE):
            radius = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
            color = foreground if 54 < radius < 92 else background
            row.extend(color)
        rows.append(bytes(row))
    data = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(data, level=9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


BRAND.mkdir(parents=True, exist_ok=True)
create_png(BRAND / "icon.png", dark=False)
create_png(BRAND / "dark_icon.png", dark=True)

