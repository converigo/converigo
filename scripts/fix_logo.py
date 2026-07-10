from PIL import Image

input_file = "app/static/images/convertin-logo.png"
output_file = "app/static/images/convertin-logo-fixed.png"


img = Image.open(input_file).convert("RGBA")

pixels = img.load()

width, height = img.size


for y in range(height):
    for x in range(width):

        r, g, b, a = pixels[x, y]

        # hapus background putih / abu sangat terang
        if r > 235 and g > 235 and b > 235:
            pixels[x, y] = (255, 255, 255, 0)


img.save(
    output_file,
    "PNG",
    optimize=True
)


print("DONE")
print(output_file)