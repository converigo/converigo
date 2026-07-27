const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const url = process.argv[2] || 'http://localhost:8000';
  const viewports = [
    { name: '1920x1080', width: 1920, height: 1080 },
    { name: '1440x900', width: 1440, height: 900 },
    { name: '768x1024', width: 768, height: 1024 },
    { name: '390x844', width: 390, height: 844 }
  ];

  const outDir = 'artifacts/hero_final_validation';
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: null });
  const page = await context.newPage();

  const results = {};

  for (const vp of viewports) {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(700);

    const screenshotPath = `${outDir}/hero_${vp.name}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: false });

    const heroTitle = await page.$eval('.hero-title', el => el.innerText.trim()).catch(()=>null);
    const heroDesc = await page.$eval('.hero-description', el => el.innerText.trim()).catch(()=>null);

    const geometry = await page.evaluate(() => {
      const hero = document.querySelector('.homepage-hero');
      const headline = document.querySelector('.hero-title');
      const desc = document.querySelector('.hero-description');
      const heroRect = hero ? hero.getBoundingClientRect() : null;
      const headlineRect = headline ? headline.getBoundingClientRect() : null;
      const descRect = desc ? desc.getBoundingClientRect() : null;
      const cards = Array.from(document.querySelectorAll('.floating-format-card'));
      const results = cards.map((card) => {
        const rect = card.getBoundingClientRect();
        const top = Math.round(rect.top);
        const bottom = Math.round(rect.bottom);
        const centerY = Math.round(rect.top + rect.height / 2);
        const insideHero = heroRect ? (top >= Math.round(heroRect.top) && bottom <= Math.round(heroRect.bottom)) : null;
        const overlapsHeadline = headlineRect ? (bottom > Math.round(headlineRect.top) && top < Math.round(headlineRect.bottom)) : null;
        const overlapsText = descRect ? (bottom > Math.round(descRect.top) && top < Math.round(descRect.bottom)) : null;
        return {
          selector: card.className,
          top,
          bottom,
          centerY,
          insideHero,
          overlapsHeadline,
          overlapsText,
          gapToHeadline: headlineRect ? Math.round(top - headlineRect.bottom) : null,
          gapToSubtitle: descRect ? Math.round(descRect.top - bottom) : null
        };
      });
      return {
        heroRect: heroRect ? { top: Math.round(heroRect.top), bottom: Math.round(heroRect.bottom) } : null,
        headlineRect: headlineRect ? { top: Math.round(headlineRect.top), bottom: Math.round(headlineRect.bottom) } : null,
        descRect: descRect ? { top: Math.round(descRect.top), bottom: Math.round(descRect.bottom) } : null,
        count: results.length,
        visible: results.filter(r => r.top !== 0 || r.bottom !== 0).length,
        cards: results
      };
    });

    const uploadVisible = await page.$eval('.drop-zone', el => {
      const title = el.querySelector('.drop-zone-copy h2')?.innerText?.trim() || null;
      const chooseText = el.querySelector('#chooseFile')?.innerText?.trim() || null;
      const support = el.querySelector('.upload-support')?.innerText?.trim() || null;
      return { title, chooseText, support };
    }).catch(() => null);

    const floating = await Promise.all(['.card-pdf','.card-docx','.card-xlsx','.card-mp3','.card-pptx','.card-mp4','.card-jpg','.card-zip'].map(async sel => {
      const el = await page.$(sel);
      if (!el) return { sel, present: false };
      const box = await el.boundingBox();
      return { sel, present: true, box };
    }));

    results[vp.name] = { screenshot: screenshotPath, heroTitle, heroDesc, uploadVisible, geometry, floating };
    console.log('Captured', vp.name);
    const topRow = geometry.cards.filter(item => item.selector.includes('card-pdf') || item.selector.includes('card-pptx'));
    console.log('Top-row geometry', JSON.stringify(topRow, null, 2));
  }

  await browser.close();
  fs.writeFileSync(`${outDir}/hero_validation_results.json`, JSON.stringify(results, null, 2));
  console.log('Results saved to', outDir);
})();
