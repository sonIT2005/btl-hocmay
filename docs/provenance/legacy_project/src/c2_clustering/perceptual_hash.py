"""
Module tính hàm băm tri giác bất biến xoay/lật (Rotation-Invariant Perceptual Hash).
Phục vụ gom cụm ảnh mô bệnh học bị augment xoay/lật trong LC25000.
Phụ trách: Đông / Huy (Module C2)
"""

import sys
import numpy as np
from PIL import Image
import imagehash

# Đảm bảo UTF-8 cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def compute_canonical_phash(img_path, hash_size=8):
    """
    Tính canonical pHash bất biến với phép xoay 90/180/270 độ và lật ngang/dọc (Dihedral group D4).
    Thuật toán:
      - Tạo ra 8 biến thể hình học của ảnh (4 góc xoay x lật).
      - Tính pHash của cả 8 biến thể.
      - Chọn hash có biểu diễn nhị phân/chuỗi hex nhỏ nhất làm 'canonical hash' đại diện.
      - Bất kể ảnh bị xoay hay lật góc nào, canonical hash sinh ra luôn trùng nhau 100%!
    """
    try:
        with Image.open(img_path) as img:
            img = img.convert("L").resize((128, 128), Image.Resampling.BILINEAR)
            
            hashes = []
            for rotate_deg in [0, 90, 180, 270]:
                if rotate_deg == 0:
                    rotated = img
                elif rotate_deg == 90:
                    rotated = img.transpose(Image.Transpose.ROTATE_90)
                elif rotate_deg == 180:
                    rotated = img.transpose(Image.Transpose.ROTATE_180)
                elif rotate_deg == 270:
                    rotated = img.transpose(Image.Transpose.ROTATE_270)
                
                h1 = imagehash.phash(rotated, hash_size=hash_size)
                h2 = imagehash.phash(rotated.transpose(Image.Transpose.FLIP_LEFT_RIGHT), hash_size=hash_size)
                hashes.append(str(h1))
                hashes.append(str(h2))
            
            # Chọn chuỗi hex nhỏ nhất làm canonical hash
            canonical = min(hashes)
            return canonical
    except Exception as e:
        return None
