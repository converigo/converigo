from playwright.sync_api import sync_playwright
import json, time
BASE='http://127.0.0.1:8000'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1366,'height':768})
    page = context.new_page()
    t0 = time.time()
    page.goto(BASE, wait_until='networkidle')
    # small delay as earlier script
    time.sleep(0.5)
    metrics = {}
    metrics['timestamp'] = time.time()
    metrics['devicePixelRatio'] = page.evaluate('() => window.devicePixelRatio')
    metrics['innerWidth'] = page.evaluate('() => window.innerWidth')
    metrics['innerHeight'] = page.evaluate('() => window.innerHeight')
    metrics['outerWidth'] = page.evaluate('() => window.outerWidth')
    metrics['outerHeight'] = page.evaluate('() => window.outerHeight')
    metrics['screenWidth'] = page.evaluate('() => window.screen.width')
    metrics['screenHeight'] = page.evaluate('() => window.screen.height')
    metrics['documentClientWidth'] = page.evaluate('() => document.documentElement.clientWidth')
    metrics['documentClientHeight'] = page.evaluate('() => document.documentElement.clientHeight')
    metrics['devicePixelRatio'] = page.evaluate('() => window.devicePixelRatio')
    metrics['fontFamily'] = page.evaluate('() => window.getComputedStyle(document.body).fontFamily')
    # fonts
    fonts = page.evaluate('''() => {
        try{
            const arr = [];
            if(document.fonts && typeof document.fonts.forEach==='function'){
                document.fonts.forEach(f=>arr.push({family:f.family, loaded:f.loaded, status:f.status, display:f.display}));
            }
            return {supported: !!document.fonts, items: arr};
        }catch(e){return {error: String(e)}}
    }''')
    metrics['fonts'] = fonts
    # images
    images = page.evaluate('''() => {
        const imgs = Array.from(document.images || []);
        return imgs.map(i=>({src:i.currentSrc||i.src, complete:i.complete, naturalWidth:i.naturalWidth, naturalHeight:i.naturalHeight}));
    }''')
    metrics['images'] = {'count': len(images), 'samples': images[:10]}
    # readyState
    metrics['readyState'] = page.evaluate('() => document.readyState')
    # take screenshot size
    path='ui_screenshots/runtime_metrics.png'
    page.screenshot(path=path, full_page=True)
    metrics['screenshot_path'] = path
    browser.close()
    print(json.dumps(metrics, indent=2))
