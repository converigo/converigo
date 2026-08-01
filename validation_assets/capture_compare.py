from pathlib import Path
import asyncio
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

out_dir = Path(__file__).resolve().parent
blueprint_path = out_dir / 'blueprint_screenshot.png'
converigo_path = out_dir / 'converigo_screenshot.png'
combined_path = out_dir / 'blueprint_vs_converigo_side_by_side.png'

async def capture(url: str, path: Path) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1440, 'height': 1200})
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.screenshot(path=str(path), full_page=True)
        await browser.close()

async def main() -> None:
    await capture('file:///c:/converigo/design/workspace-prototype/index.html', blueprint_path)
    await capture('http://127.0.0.1:8011/tools/png-to-jpg', converigo_path)

    img1 = Image.open(blueprint_path).convert('RGB')
    img2 = Image.open(converigo_path).convert('RGB')

    h = 900
    w1 = int(img1.width * h / img1.height)
    w2 = int(img2.width * h / img2.height)
    img1 = img1.resize((w1, h), Image.Resampling.LANCZOS)
    img2 = img2.resize((w2, h), Image.Resampling.LANCZOS)

    canvas_w = w1 + w2 + 40
    canvas_h = h + 160
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    canvas.paste(img1, (20, 80))
    canvas.paste(img2, (w1 + 40, 80))

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((20, 20), 'Blueprint Claude', fill='#111827', font=font)
    draw.text((w1 + 40, 20), 'Converigo Terbaru', fill='#111827', font=font)

    label_y = 100
    for x, y, text in [
        (20 + 70, label_y, 'Hero'),
        (w1 + 40 + 70, label_y, 'Hero'),
        (20 + 70, label_y + 260, 'Upload Card'),
        (w1 + 40 + 70, label_y + 260, 'Upload Card'),
        (20 + 70, label_y + 330, 'Heading'),
        (w1 + 40 + 70, label_y + 330, 'Heading'),
        (20 + 70, label_y + 400, 'Spacing'),
        (w1 + 40 + 70, label_y + 400, 'Spacing'),
        (20 + 70, label_y + 470, 'Alignment'),
        (w1 + 40 + 70, label_y + 470, 'Alignment'),
    ]:
        draw.text((x, y), text, fill='#111827', font=font)

    status_y = canvas_h - 70
    for x, text in [
        (20, 'Hero: NOT MATCH'),
        (220, 'Upload Card: NOT MATCH'),
        (430, 'Heading: MATCH'),
        (620, 'Spacing: NOT MATCH'),
        (810, 'Alignment: NOT MATCH'),
    ]:
        draw.text((x, status_y), text, fill='#111827', font=font)

    canvas.save(combined_path)
    print('saved', blueprint_path, converigo_path, combined_path)

asyncio.run(main())
