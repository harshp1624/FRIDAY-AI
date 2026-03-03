from PIL import Image
import os

png_path = r"c:\Users\harsh\OneDrive\Desktop\FRIDAY\friday_ai_logo.png"
ico_path = r"c:\Users\harsh\OneDrive\Desktop\FRIDAY\icon.ico"

print(f"Converting {png_path} to {ico_path}...")
img = Image.open(png_path)
img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Conversion complete.")
