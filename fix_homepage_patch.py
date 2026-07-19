from pathlib import Path

# Update hero.html
hero_path = Path('app/templates/components/hero.html')
text = hero_path.read_text(encoding='utf-8')
needle = '                    <strong>{{ request.state.t(\'hero.callout\', \'Convert and Go!\') }}<br>{{ request.state.t(\'hero.callout_tagline\', \'Fast, Simple, Ready.\') }}</strong>\n\n                </p>\n'
if needle in text:
    replacement = (
        '                    <strong>{{ request.state.t(\'hero.callout\', \'Convert and Go!\') }}<br>{{ request.state.t(\'hero.callout_tagline\', \'Fast, Simple, Ready.\') }}</strong>\n\n'
        '                <div class=\"hero-detail-list\">\n'
        '                    <span>Supports 200+ file types</span>\n'
        '                    <span>Zero install, browser-based</span>\n'
        '                    <span>Secure uploads removed after conversion</span>\n'
        '                </div>\n\n'
        '                </p>\n'
    )
    text = text.replace(needle, replacement, 1)
    hero_path.write_text(text, encoding='utf-8')
    print('hero updated')
else:
    print('hero needle missing or already updated')

# Update upload_card.html
upload_path = Path('app/templates/components/upload_card.html')
text = upload_path.read_text(encoding='utf-8')
old_status = ("<div\n"
              "\n    class=\"selected-file\"\n"
              "\n    id=\"selectedStatus\"\n"
              "\n>\n")
new_status = ("<div\n"
              "\n    class=\"selected-file\"\n"
              "\n    id=\"selectedStatus\"\n"
              "\n    hidden\n>\n")
if old_status in text:
    text = text.replace(old_status, new_status, 1)
old_hint = '<div id="uploadHint" class="upload-hint">\n'
new_hint = '<div id="uploadHint" class="upload-hint" hidden>\n'
if old_hint in text:
    text = text.replace(old_hint, new_hint, 1)
old_smart = ("<div\n"
             "\n    id=\"smartRecommendation\"\n"
             "\n    class=\"smart-recommendation\"\n"
             "\n>\n")
new_smart = ("<div\n"
             "\n    id=\"smartRecommendation\"\n"
             "\n    class=\"smart-recommendation\"\n"
             "\n    hidden\n\n>\n")
if old_smart in text:
    text = text.replace(old_smart, new_smart, 1)
# Remove malformed closing tags after last </section>
idx = text.rfind('</section>')
if idx != -1:
    text = text[:idx + len('</section>')] + '\n'
upload_path.write_text(text, encoding='utf-8')
print('upload updated')
