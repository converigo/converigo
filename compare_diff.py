import os
from PIL import Image, ImageChops
base = "design/workspace-prototype/mainpage.png"
cur = "desktop-en.png"
print("base exists", os.path.exists(base))
print("cur exists", os.path.exists(cur))
d = Image.open(base).convert("RGB")
c = Image.open(cur).convert("RGB")
if d.size != c.size:
    c = c.resize(d.size, Image.LANCZOS)
diff = ImageChops.difference(d, c)
diff.save("desktop-en-diff.png")
total_pixels = d.size[0] * d.size[1]
diff_pixels = sum(1 for px in diff.getdata() if px != (0,0,0))
max_diff = max(e[1] for e in diff.getextrema())
total_diff = sum(diff.histogram())
print("SIZE", d.size)
print("MAX_DIFF", max_diff)
print("TOTAL_DIFF", total_diff)
print("DIFF_PIXELS", diff_pixels)
print("DIFF_PERCENTAGE", diff_pixels/total_pixels*100)
