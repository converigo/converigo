from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "app" / "static" / "images"
LOGO_PATH = IMAGES_DIR / "converigo-logo.png"
OUTPUTS = [
    (IMAGES_DIR / "og-home.png", "Converigo\nFast, Free & Secure Online File Converter"),
    (IMAGES_DIR / "og-default.png", "Converigo\nConvert files fast and securely"),
]

WIDTH, HEIGHT = 1200, 630


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "DejaVuSans-Bold.ttf",
        "arial.ttf",
        "Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_image(output_path: Path, title: str) -> None:
    if not LOGO_PATH.exists():
        raise FileNotFoundError(f"Missing logo asset: {LOGO_PATH}")

    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo = logo.resize((220, 220))

    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (248, 250, 252, 255))
    draw = ImageDraw.Draw(canvas)

    accent = (31, 120, 255)
    accent_dark = (17, 71, 155)

    draw.rounded_rectangle((60, 60, WIDTH - 60, HEIGHT - 60), radius=36, fill=(255, 255, 255, 255), outline=(230, 234, 242, 255), width=3)
    draw.rounded_rectangle((80, 80, WIDTH - 80, HEIGHT - 80), radius=28, fill=(245, 248, 255, 255))

    draw.rectangle((80, 80, 120, HEIGHT - 80), fill=accent)
    draw.rectangle((WIDTH - 120, 80, WIDTH - 80, HEIGHT - 80), fill=accent_dark)

    x_offset = 160
    y_offset = 140
    canvas.alpha_composite(logo, (x_offset, y_offset - 20))

    title_font = load_font(54)
    subtitle_font = load_font(28)
    tag_font = load_font(24)

    title_lines = [line.strip() for line in title.split("\n") if line.strip()]
    title_y = 230
    for index, line in enumerate(title_lines):
        text_width = draw.textbbox((0, 0), line, font=title_font)[2]
        x = (WIDTH - text_width) / 2
        draw.text((x, title_y + index * 70), line, font=title_font, fill=(20, 30, 50, 255))

    draw.text((160, 430), "Secure • Fast • Polished", font=tag_font, fill=accent_dark)
    draw.text((160, 470), "Online file conversion for students, creators, and teams", font=subtitle_font, fill=(84, 97, 114, 255))

    canvas = canvas.convert("RGB")
    canvas.save(output_path, "PNG")


if __name__ == "__main__":
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for output_path, title in OUTPUTS:
        create_image(output_path, title)
        print(f"Created: {output_path}")
