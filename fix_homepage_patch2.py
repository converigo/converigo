from pathlib import Path

# Hero HTML fix
hero_path = Path('app/templates/components/hero.html')
text = hero_path.read_text(encoding='utf-8')
needle = '<strong>{{ request.state.t(\'hero.callout\', \'Convert and Go!\') }}<br>{{ request.state.t(\'hero.callout_tagline\', \'Fast, Simple, Ready.\') }}</strong>\n\n                <div class="hero-detail-list">'
if needle in text:
    text = text.replace(
        needle,
        '<strong>{{ request.state.t(\'hero.callout\', \'Convert and Go!\') }}<br>{{ request.state.t(\'hero.callout_tagline\', \'Fast, Simple, Ready.\') }}</strong>\n\n                </p>\n\n                <div class="hero-detail-list">',
        1,
    )
    hero_path.write_text(text, encoding='utf-8')
    print('hero closed paragraph fixed')
else:
    print('hero detail list fix not needed or needle missing')

# Hero CSS fix
hero_css_path = Path('app/static/css/components/hero.css')
css = hero_css_path.read_text(encoding='utf-8')
marker = '.hero p {'
if 'hero-detail-list' not in css:
    insert_at = css.find('    padding:0 12px;\n}')
    if insert_at != -1:
        css = css.replace(
            '    padding:0 12px;\n}',
            '    padding:0 12px;\n}\n\n.hero-detail-list {\n    display:flex;\n    justify-content:center;\n    flex-wrap:wrap;\n    gap:12px;\n    margin-top:22px;\n    color:#334155;\n    font-size:0.95rem;\n}\n\n.hero-detail-list span {\n    background:rgba(37,99,235,.08);\n    color:#1d4ed8;\n    padding:10px 16px;\n    border-radius:999px;\n    font-weight:600;\n}\n\n.hero-content {\n    display:grid;\n    grid-template-columns:1fr minmax(320px, 1.05fr);\n    gap:42px;\n    align-items:center;\n    max-width:1180px;\n    margin:0 auto;\n    padding-top:14px;\n}\n\n.hero-workspace {\n    margin-top:0;\n}\n',
            1,
        )
        hero_css_path.write_text(css, encoding='utf-8')
        print('hero css updated')
    else:
        print('hero css marker not found')
else:
    print('hero css already contains hero-detail-list')

# Clean upload_card trailing junk
upload_path = Path('app/templates/components/upload_card.html')
text = upload_path.read_text(encoding='utf-8')
idx = text.rfind('</section>')
if idx != -1:
    new_text = text[:idx + len('</section>')] + '\n'
    if new_text != text:
        upload_path.write_text(new_text, encoding='utf-8')
        print('upload_card trailing junk removed')
    else:
        print('upload_card already clean')
else:
    print('upload_card </section> not found')
