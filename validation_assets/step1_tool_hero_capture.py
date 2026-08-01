from pathlib import Path
import asyncio
from PIL import Image
from playwright.async_api import async_playwright
import os

out_dir = Path(__file__).resolve().parent
blueprint_path = out_dir / 'step1_blueprint.png'
current_path = out_dir / 'step1_before.png'
combined_path = out_dir / 'step1_before_vs_blueprint.png'

BASE = os.environ.get("CONVERIGO_BASE_URL", "http://127.0.0.1:8000")

async def capture(url: str, path: Path) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1440, 'height': 1400})
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.screenshot(path=str(path), full_page=True)
        await browser.close()

async def main() -> None:
    await capture('file:///c:/converigo/design/workspace-prototype/index.html', blueprint_path)
    # Capture current site homepage for comparison (use configured BASE)
    await capture(f"{BASE}/", current_path)

    img1 = Image.open(blueprint_path).convert('RGB')
    img2 = Image.open(current_path).convert('RGB')

    target_h = 900
    w1 = int(img1.width * target_h / img1.height)
    w2 = int(img2.width * target_h / img2.height)
    img1 = img1.resize((w1, target_h), Image.Resampling.LANCZOS)
    img2 = img2.resize((w2, target_h), Image.Resampling.LANCZOS)

    canvas = Image.new('RGB', (w1 + w2 + 40, target_h + 60), 'white')
    canvas.paste(img1, (20, 20))
    canvas.paste(img2, (w1 + 40, 20))
    canvas.save(combined_path)
    print('saved', blueprint_path, current_path, combined_path)

asyncio.run(main())
