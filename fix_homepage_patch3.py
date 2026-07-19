from pathlib import Path
import re

# Hero HTML fix
hero_path = Path('app/templates/components/hero.html')
text = hero_path.read_text(encoding='utf-8')
pattern = re.compile(
    r'(\s*</p>\n\s*<div class="hero-detail-list">\n(?:[\s\S]*?)\n\s*</div>\n\n)\s*</p>\n',
    flags=re.MULTILINE,
)
new_text, count = pattern.subn(r'\1', text, count=1)
if count > 0:
    hero_path.write_text(new_text, encoding='utf-8')
    print('hero extra closing </p> removed')
else:
    print('hero extra closing </p> not found or already fixed')

# Hero CSS cleanup
hero_css = Path('app/static/css/components/hero.css')
css_text = hero_css.read_text(encoding='utf-8')
old_block = re.compile(r'\.hero-workspace \{\s*\n\s*margin-top:18px;\s*\n\s*\}\s*\n\n', flags=re.MULTILINE)
new_css_text, css_count = old_block.subn('', css_text, count=1)
if css_count > 0:
    hero_css.write_text(new_css_text, encoding='utf-8')
    print('hero CSS duplicate block removed')
else:
    print('hero CSS duplicate block not found')

# Recommendation manager JS improvement
js_path = Path('app/static/js/recommendation/recommendation_manager.js')
js_text = js_path.read_text(encoding='utf-8')
marker = '        this.formatContainer.innerHTML = "";\n\n\n\n        const choices = [];' 
if marker in js_text:
    js_text = js_text.replace(marker, '        this.formatContainer.innerHTML = "";\n\n        if(this.conversionArea){\n            this.conversionArea.hidden = true;\n        }\n\n        const choices = [];')
    print('recommendation.js conversionArea initial hidden inserted')
else:
    print('recommendation.js initial hidden marker not found')

loop_end = '                this.formatContainer.appendChild(\n                    button\n                );\n\n\n            }\n        );'
if loop_end in js_text:
    js_text = js_text.replace(loop_end, loop_end + '\n\n        if(this.conversionArea){\n            this.conversionArea.hidden = choices.length === 0;\n        }')
    print('recommendation.js conversionArea toggle inserted')
else:
    print('recommendation.js loop end marker not found')

js_path.write_text(js_text, encoding='utf-8')

# Upload card cleanup
upload_path = Path('app/templates/components/upload_card.html')
upload_text = upload_path.read_text(encoding='utf-8')
idx = upload_text.find('</section>')
if idx != -1:
    cleaned = upload_text[: idx + len('</section>')] + '\n'
    if cleaned != upload_text:
        upload_path.write_text(cleaned, encoding='utf-8')
        print('upload_card trailing junk removed')
    else:
        print('upload_card already clean')
else:
    print('upload_card </section> not found')
