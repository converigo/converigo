import os
import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('CONVERIGO_BASE_URL', 'http://127.0.0.1:8000')

BREAKPOINTS = [(360,800),(375,812),(412,915),(768,1024)]
LOCALES = ["id","en","ja"]

OUT_DIR = Path('qa_reports')

def ensure_dirs():
    (OUT_DIR / 'screenshots').mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'console_logs').mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'summary').mkdir(parents=True, exist_ok=True)

def run_one(page, w, h, locale, screenshot_path, console_path):
    logs = []
    def on_console(msg):
        logs.append({'type': msg.type, 'text': msg.text})

    page.on('console', on_console)
    page.set_viewport_size({'width': w, 'height': h})
    # set Accept-Language header via context extraHTTPHeaders was not available here, use evaluate to set navigator.language fallback
    page.goto(f"{BASE}/", wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(500)
    # take screenshot
    page.screenshot(path=str(screenshot_path), full_page=True)

    # run layout checks in page context
    results = page.evaluate('''(size)=>{
        const issues = {};
        const w = size.w, h = size.h;
        issues.hasHorizontalScroll = document.documentElement.scrollWidth > (window.innerWidth || w);
        // overflow candidates
        const overflows = [];
        const els = Array.from(document.querySelectorAll('body *'));
        for (const el of els){
            try{
                if (el.clientWidth>0 && el.scrollWidth > el.clientWidth + 1){
                    overflows.push({selector: el.tagName.toLowerCase() + (el.id?('#'+el.id):'') + (el.className?('.'+el.className.split(' ').join('.')):''), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth});
                    if (overflows.length>30) break;
                }
            }catch(e){}
        }
        issues.overflowCandidates = overflows;

        // overlapping buttons
        const btns = Array.from(document.querySelectorAll('button, a.button, .btn'));
        const overlaps = [];
        function intersect(a,b){
            return !(a.right<=b.left || a.left>=b.right || a.bottom<=b.top || a.top>=b.bottom);
        }
        for (let i=0;i<btns.length;i++){
            for (let j=i+1;j<btns.length;j++){
                const a = btns[i].getBoundingClientRect();
                const b = btns[j].getBoundingClientRect();
                if (intersect(a,b)) overlaps.push({a: btns[i].outerHTML.substring(0,200), b: btns[j].outerHTML.substring(0,200)});
                if (overlaps.length>20) break;
            }
            if (overlaps.length>20) break;
        }
        issues.overlappingButtons = overlaps;

        // existence checks for required sections
        const selectors = {
            hero: '#hero, .hero',
            header: 'header.site-header, header',
            navigation: 'nav.main-nav, nav',
            upload: '#uploadSection, .upload-wrapper, .upload-card',
            floating_logo: 'header.site-header a.logo img.brand-logo, header a.logo img',
            recommendation_cards: '.popular-tools, .recommendation, .recommendation-cards, .recommendation-card, .card',
            footer: 'footer, .site-footer'
        };
        const presence = {};
        for (const k of Object.keys(selectors)){
            presence[k] = !!document.querySelector(selectors[k]);
        }
        issues.presence = presence;

        // logo comparison: find header logo and upload logo
        const headerLogo = document.querySelector('header.site-header a.logo img, header a.logo img');
        const uploadLogo = document.querySelector('#uploadSection img, .upload-wrapper img, .upload-card img');
        if (headerLogo && uploadLogo){
            const ha = headerLogo.getBoundingClientRect();
            const ua = uploadLogo.getBoundingClientRect();
            const cs = window.getComputedStyle(headerLogo);
            const cu = window.getComputedStyle(uploadLogo);
            issues.logo = {header:{w:ha.width,h:ha.height,borderRadius:cs.borderRadius,opacity:cs.opacity,boxShadow:cs.boxShadow,transform:cs.transform}, upload:{w:ua.width,h:ua.height,borderRadius:cu.borderRadius,opacity:cu.opacity,boxShadow:cu.boxShadow,transform:cu.transform}};
        } else {
            issues.logo = {headerExists: !!headerLogo, uploadExists: !!uploadLogo};
        }

        return issues;
    }''', {'w': w, 'h': h})

    # write console logs
    with open(console_path, 'w', encoding='utf-8') as fh:
        for m in logs:
            fh.write(f"[{m['type']}] {m['text']}\n")

    return results, logs

def main():
    ensure_dirs()
    env_locale = os.environ.get('CONVERIGO_LOCALE')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        all_results = {}
        for w,h in BREAKPOINTS:
            for loc in LOCALES:
                name = f"{w}x{h}-{loc}"
                screenshot_path = OUT_DIR / 'screenshots' / f"{w}x{h}-{loc}.png"
                console_path = OUT_DIR / 'console_logs' / f"{w}x{h}-{loc}.log"

                # set Accept-Language header per scenario by creating new context
                context.close()
                context = browser.new_context(extra_http_headers={"Accept-Language": loc})
                page = context.new_page()

                print(f"Testing {name} -> {BASE}/")
                res, logs = run_one(page, w, h, loc, screenshot_path, console_path)
                all_results[name] = {'results': res, 'console_count': len(logs), 'screenshot': str(screenshot_path), 'console': str(console_path)}

        browser.close()

    # write summary files
    report_md = OUT_DIR / 'MOBILE_CERTIFICATION_REPORT.md'
    with open(OUT_DIR / 'summary' / 'issues.md', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    with open(report_md, 'w', encoding='utf-8') as fh:
        fh.write('# Mobile Certification Report\n\n')
        fh.write(f'*Base URL*: {BASE}\n\n')
        fh.write('## Scenarios\n')
        for k,v in all_results.items():
            fh.write(f"- {k}: screenshot={v['screenshot']}, console={v['console']}, console_messages={v['console_count']}\n")

    print('Done. Reports in', OUT_DIR)

if __name__ == '__main__':
    main()
