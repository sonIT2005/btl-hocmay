"""
Pipeline thực thi toàn diện Module C3:
- Cắt patch cho LungHist700 và lọc nền trắng (Otsu/Threshold).
- Khởi tạo Macenko Stain Normalizer từ ảnh mẫu tham chiếu chuẩn.
- Chuẩn hóa toàn bộ patch về cùng hệ màu quang học H&E.
Phụ trách: Đông / Huy (Module C3)
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Đảm bảo UTF-8 cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm root vào sys.path
sys.path.insert(0, os.path.abspath("."))

from src.c3_preprocessing.macenko_normalizer import MacenkoNormalizer
from src.c3_preprocessing.patch_extractor import process_dataset_patches

def select_default_reference_image():
    """Tự động chọn 1 ảnh tiêu bản mô rõ nét từ LC25000 làm mốc màu chuẩn"""
    ref_candidates = [
        "dataset/lung_colon_image_set/lung_image_sets/lung_aca/lungaca1.jpeg",
        "dataset/lung_colon_image_set/lung_image_sets/lung_n/lungn1.jpeg",
        "dataset/lung_colon_image_set/colon_image_sets/colon_aca/colonca1.jpeg"
    ]
    for p in ref_candidates:
        if os.path.exists(p):
            return p
    return None

def main():
    print("=" * 65)
    print(" BẮT ĐẦU PIPELINE C3: CẮT PATCH & MACENKO STAIN NORMALIZATION")
    print("=" * 65)

    # 1. Chọn và thiết lập ảnh tham chiếu màu (Reference Image)
    ref_img_path = select_default_reference_image()
    if not ref_img_path:
        print("[-] Không tìm thấy ảnh tham chiếu từ LC25000!")
        return

    print(f"[+] Sử dụng ảnh mốc màu tham chiếu (Reference): {ref_img_path}")
    normalizer = MacenkoNormalizer()
    normalizer.fit(ref_img_path)
    
    # Lưu lại ảnh tham chiếu ra thư mục outputs để trực quan hóa
    os.makedirs("outputs", exist_ok=True)
    Image.open(ref_img_path).save("outputs/macenko_reference_template.png")
    print(f"[+] Đã lưu mẫu màu chuẩn tham chiếu tại: outputs/macenko_reference_template.png")

    # 2. Kiểm tra thư mục LungHist700
    lunghist_dir = "dataset/LungHist700/data/images"
    if not os.path.exists(lunghist_dir):
        lunghist_dir = "dataset/LungHist700"
        
    all_imgs = list(Path(lunghist_dir).rglob("*.*"))
    image_files = [f for f in all_imgs if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]]
    if len(image_files) == 0:
        print(f"[-] Không tìm thấy ảnh trong {lunghist_dir}.")
        return

    print(f"[+] Tìm thấy {len(image_files)} ảnh gốc trong {lunghist_dir}.")

    # 3. Chạy cắt patch và chuẩn hóa màu đồng thời
    output_patch_dir = "dataset/patches/LungHist700_normalized"
    print(f"\n[+] Bắt đầu trích xuất patch 224x224 và chuẩn hóa màu Macenko...")
    total = process_dataset_patches(
        input_dir=lunghist_dir,
        output_dir=output_patch_dir,
        patch_size=(224, 224),
        stride=224,
        min_tissue_ratio=0.50,
        normalizer=normalizer
    )

    print("\n" + "=" * 65)
    print(f" HOÀN TẤT MODULE C3!")
    print(f"  - Tổng số patch đã tạo: {total}")
    print(f"  - Thư mục lưu patch: {output_patch_dir}")
    print("=" * 65)

if __name__ == "__main__":
    main()
