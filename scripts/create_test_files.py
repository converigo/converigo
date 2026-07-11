"""
====================================================
Project : Converigo
Author  : Pico Lala & ChatGPT

Create Integration Test Files
Version : 1.0.0

Generate:
- sample.jpg
- sample.webp
- sample.png
====================================================
"""


from pathlib import Path

from PIL import Image, ImageDraw



OUTPUT = Path(
    "test_files"
)


OUTPUT.mkdir(
    exist_ok=True
)



def create_image():

    img = Image.new(
        "RGB",
        (800,600),
        "white"
    )


    draw = ImageDraw.Draw(img)


    draw.rectangle(
        (100,100,700,500),
        outline="blue",
        width=8
    )


    draw.text(
        (250,280),
        "Converigo Test",
        fill="black"
    )


    img.save(
        OUTPUT / "sample.jpg",
        quality=90
    )


    img.save(
        OUTPUT / "sample.png"
    )


    img.save(
        OUTPUT / "sample.webp",
        "WEBP",
        quality=90
    )


    print(
        "Image test files created"
    )



if __name__ == "__main__":

    create_image()