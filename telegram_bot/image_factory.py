from __future__ import annotations

from pathlib import Path
from typing import Dict

from PIL import Image, ImageDraw, ImageFont

IMAGE_TITLES: Dict[str, str] = {
    "start_screen.png": "PERIMETER",
    "dossier_card.png": "DOSSIER",
    "act1_bus.png": "LAST ROAD",
    "checkpoint_fedor.png": "CHECKPOINT",
    "gates_closed.png": "GATES CLOSED",
    "artem_photo.png": "SERGEY PHOTO",
    "marina_marks.png": "ENGINEER MARKS",
    "gleb_route.png": "OLD ROUTE",
    "eva_pulse.png": "MEDICAL NOTE",
    "generator_choice.png": "POWER ROUTING",
    "cafeteria_night.png": "FIRST NIGHT",
    "sergey_voice.png": "SERGEY?",
    "empty_seat.png": "EMPTY SEAT",
    "trial_table.png": "TABLE TRIAL",
    "server_radio.png": "PLAYER VOICE",
    "second_night.png": "SECOND NIGHT",
    "third_day_door.png": "THIRD DAY",
    "emergency_mode.png": "EMERGENCY MODE",
    "central_archive.png": "CENTRAL ARCHIVE",
    "zorin_glass.png": "ZORIN",
    "three_truths.png": "THREE TRUTHS",
    "final_choice.png": "FINAL CHOICE",
    "ending_truth.png": "TRUTH OUTSIDE",
    "ending_lie.png": "MERCIFUL LIE",
    "ending_sealed.png": "SEALED",
    "fedor_epilogue.png": "FEDOR REMEMBERS",
}


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def create_image(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (15, 19, 23))
    draw = ImageDraw.Draw(img, "RGBA")
    for y in range(h):
        a = int(20 + 80 * y / h)
        draw.line([(0, y), (w, y)], fill=(70, 78, 82, a // 3))
    for x in range(0, w, 150):
        draw.rectangle([x, 320 + (x % 90), x + 65, h], fill=(0, 0, 0, 110))
    draw.polygon([(230, h), (525, 320), (755, 320), (1050, h)], fill=(0, 0, 0, 95))
    draw.line([(525, 320), (120, h)], fill=(220, 220, 200, 45), width=2)
    draw.line([(755, 320), (1160, h)], fill=(220, 220, 200, 45), width=2)
    draw.ellipse([1040, 80, 1180, 220], outline=(180, 40, 34, 180), width=6)
    draw.rectangle([60, 490, 790, 640], fill=(0, 0, 0, 140), outline=(220, 220, 210, 60), width=2)
    draw.text((85, 515), "НИИ PERIMETER", font=_font(24), fill=(215, 215, 205, 200))
    draw.text((85, 550), title[:28], font=_font(52), fill=(235, 235, 225, 235))
    draw.text((85, 615), "PX-17 / ECHO PROTOCOL", font=_font(24), fill=(185, 185, 175, 180))
    img.save(path, "PNG", optimize=True)


def ensure_images(base_dir: Path) -> None:
    images = base_dir / "assets" / "images"
    images.mkdir(parents=True, exist_ok=True)
    for filename, title in IMAGE_TITLES.items():
        path = images / filename
        if not path.exists():
            create_image(path, title)
