from pathlib import Path
import re

file_path = Path('app/static/js/recommendation/recommendation_manager.js')
text = file_path.read_text(encoding='utf-8')

# Insert initial conversionArea hidden logic after clearing formatContainer
text, first_count = re.subn(
    r'(this\.formatContainer\.innerHTML\s*=\s*"";\s*\n)(\s*\n)(\s*const choices = \[\];)',
    r"\1\2        if(this.conversionArea){\n            this.conversionArea.hidden = true;\n        }\n\2\3",
    text,
    count=1,
    flags=re.MULTILINE
)

# Insert conversionArea toggle after choices loop
text, second_count = re.subn(
    r'(\s*this\.formatContainer\.appendChild\(\s*\n\s*button\s*\n\s*\);\s*\n\s*\n\s*\)\s*;\s*\n\s*\n)(\s*}\s*\n\s*}\s*\n\s*\n)',
    r"\1\2        if(this.conversionArea){\n            this.conversionArea.hidden = choices.length === 0;\n        }\n\n\2",
    text,
    count=1,
    flags=re.MULTILINE
)

if first_count == 0:
    print('did not insert initial conversionArea hidden logic')
else:
    print('inserted initial conversionArea hidden logic')

if second_count == 0:
    print('did not insert conversionArea toggle logic')
else:
    print('inserted conversionArea toggle logic')

file_path.write_text(text, encoding='utf-8')
print('done')
