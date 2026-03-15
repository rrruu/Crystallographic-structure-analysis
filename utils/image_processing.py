import os
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

# ======= 以脚本所在目录为根目录 =======
ROOT = Path(__file__).resolve().parent


def bmp_to_png():
    input_dir = ROOT / "bmp"
    output_dir = ROOT / "png"

    input_file = input_dir / "untitled.bmp"
    output_file = output_dir / "untitled.png"

    if not input_file.exists():
        print(f"Error: Input file not found -> {input_file}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        img = Image.open(str(input_file))
        img.save(str(output_file), format="PNG")

        print(f"Successfully converted:")
        print(f"{input_file}  -->  {output_file}")

        return True

    except Exception as e:
        print("An error occurred during BMP to PNG conversion:")
        print(e)
        return False


def remove_white_background():
    input_dir = ROOT / "png"
    # output_dir = ROOT / "remove"
    output_dir = ROOT / "images" / "origin"

    input_file = input_dir / "untitled.png"
    # output_file = output_dir / "untitled_no_bg.png"
    output_file = output_dir / "1.png"

    output_dir.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(input_file), cv2.IMREAD_COLOR)
    if img is None:
        print(f"Error: Cannot read image -> {input_file}")
        return False

    white = np.array([255, 255, 255], dtype=np.uint8)
    mask_white = cv2.inRange(img, white, white)

    alpha = np.where(mask_white == 255, 0, 255).astype(np.uint8)

    out = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    out[:, :, 3] = alpha

    cv2.imwrite(str(output_file), out)

    print(f"Background removed successfully:")
    print(f"{input_file}  -->  {output_file}")

    return True


def main():
    print("===== Step 1: BMP to PNG =====")
    if not bmp_to_png():
        return

    print("\n===== Step 2: Remove White Background =====")
    remove_white_background()


if __name__ == "__main__":
    main()
