from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).with_name("demo_input.png")
image = Image.new("RGB", (1000, 650), "white")
d = ImageDraw.Draw(image)
try:
    font = ImageFont.truetype("DejaVuSans.ttf", 28)
except OSError:
    font = ImageFont.load_default()

# Geometric elements similar to the intended workflow example.
d.rectangle((390, 245, 650, 525), outline="black", width=5)
d.line((520, 70, 520, 245), fill="black", width=5)
d.line((650, 385, 900, 385), fill="black", width=5)
d.ellipse((480, 120, 560, 200), outline="black", width=5)

# Organic contour and facial features.
d.arc((420, 270, 605, 500), 75, 300, fill="black", width=6)
d.polygon([(440, 330), (460, 280), (495, 325)], outline="black")
d.polygon([(535, 322), (575, 280), (592, 340)], outline="black")
d.ellipse((485, 355, 497, 367), fill="black")
d.ellipse((545, 355, 557, 367), fill="black")
d.arc((493, 365, 552, 415), 10, 170, fill="black", width=4)

# Larger labels so the example also exercises glyph-contour equations.
d.text((325, 150), "circular equations", fill="black", font=font)
d.text((85, 370), "curved Bézier contours", fill="black", font=font)
d.text((720, 335), "straight line", fill="black", font=font)

image.save(out)
print(out)
