"""
Génère assets/icon.ico — icône Pynote (toque de diplômé stylisée).
Usage : python scripts/generate_icon.py
"""
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw

SIZES = [256, 128, 64, 48, 32, 16]

# Palette
BG       = (30,  30,  46)   # fond sombre bleu-nuit
ACCENT   = (94, 129, 244)   # bleu Pynote
LIGHT    = (255, 255, 255)  # blanc
GOLD     = (250, 215,  90)  # or


def draw_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)
    s    = size
    pad  = max(2, s // 16)

    # ── Fond arrondi ──────────────────────────────────────────────────────────
    r = s // 5
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BG)

    # ── Chapeau (losange plat) ─────────────────────────────────────────────────
    # centre horizontal, un peu au-dessus du milieu
    cx = s / 2
    cy = s * 0.42

    hw = s * 0.40          # demi-largeur losange
    hh = s * 0.14          # demi-hauteur losange

    hat_poly = [
        (cx,       cy - hh),   # sommet haut
        (cx + hw,  cy),        # droite
        (cx,       cy + hh),   # bas
        (cx - hw,  cy),        # gauche
    ]
    d.polygon(hat_poly, fill=GOLD)

    # contour subtil
    d.line(hat_poly + [hat_poly[0]], fill=(*GOLD[:3], 180), width=max(1, s // 64))

    # ── Bord du chapeau (bande plus sombre) ───────────────────────────────────
    bh = hh * 0.35
    band_poly = [
        (cx,       cy - bh),
        (cx + hw,  cy),
        (cx,       cy + bh),
        (cx - hw,  cy),
    ]
    d.polygon(band_poly, fill=(200, 165, 50, 230))

    # ── Tasseau (carré sur le dessus) ─────────────────────────────────────────
    ts = s * 0.10
    tx = cx - ts / 2
    ty = cy - hh - ts * 0.6
    d.rectangle([tx, ty, tx + ts, ty + ts], fill=GOLD)

    # ── Gland (cordon) ────────────────────────────────────────────────────────
    # cordon : ligne courbe simplifiée via arc
    cord_r  = s * 0.17
    cord_cx = cx + s * 0.20
    cord_cy = cy + s * 0.01
    lw = max(2, s // 48)

    d.arc(
        [cord_cx - cord_r, cord_cy - cord_r,
         cord_cx + cord_r, cord_cy + cord_r],
        start=200, end=340,
        fill=ACCENT, width=lw,
    )

    # boule du gland
    br  = max(2, s // 18)
    bx  = cord_cx + cord_r * math.cos(math.radians(340))
    by  = cord_cy + cord_r * math.sin(math.radians(340))
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=ACCENT)

    # ── Texte "P" centré en bas ────────────────────────────────────────────────
    if size >= 32:
        from PIL import ImageFont
        font_size = max(10, int(s * 0.26))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        letter = "P"
        bbox   = d.textbbox((0, 0), letter, font=font)
        tw     = bbox[2] - bbox[0]
        th     = bbox[3] - bbox[1]
        lx     = cx - tw / 2 - bbox[0]
        ly     = s * 0.68 - th / 2 - bbox[1]
        d.text((lx, ly), letter, fill=LIGHT, font=font)

    return img


def main():
    out_dir = Path(__file__).parent.parent / "assets"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "icon.ico"

    frames = [draw_icon(sz) for sz in SIZES]
    frames[0].save(
        out_path,
        format="ICO",
        sizes=[(sz, sz) for sz in SIZES],
        append_images=frames[1:],
    )
    print(f"✅  Icône générée : {out_path}")


if __name__ == "__main__":
    main()
