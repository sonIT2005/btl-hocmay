"""
Module trích xuất patch (Patch Extraction) và lọc nền trống (Tissue Filtering)
cho các dataset ảnh mô bệnh học kích thước lớn (LungHist700, BACH).
Phụ trách: Đông / Huy (Module C3)
"""

import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image

# Đảm bảo UTF-8 cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def compute_tissue_mask(img_np, white_threshold=220):
    """
    Tạo mask phân biệt vùng mô thực sự và vùng kính trống.
    Pixel nền kính hiển vi thường có màu trắng sáng (R, G, B > 220).
    """
    # Nếu cả 3 kênh đều sáng hơn ngưỡng thì là nền trắng
    is_background = (img_np[:, :, 0] > white_threshold) & \
                    (img_np[:, :, 1] > white_threshold) & \
                    (img_np[:, :, 2] > white_threshold)
    is_tissue = ~is_background
    return is_tissue

def extract_patches_from_image(
    image_path,
    patch_size=(224, 224),
    stride=224,
    min_tissue_ratio=0.50,
    normalizer=None
):
    """
    Trích xuất danh sách các patch hợp lệ từ một ảnh lớn.
    image_path: đường dẫn file ảnh lớn.
    patch_size: (chiều rộng, chiều cao) của patch, mặc định (224, 224).
    stride: bước trượt (stride = patch_size[0] nghĩa là không overlap).
    min_tissue_ratio: tỷ lệ pixel chứa mô tối thiểu để giữ lại patch (lọc nền trống).
    normalizer: đối tượng MacenkoNormalizer (tùy chọn) để chuẩn hóa màu ngay khi cắt.
    """
    patches = []
    try:
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size
            img_np = np.array(img_rgb)
            
            pw, ph = patch_size
            tissue_mask = compute_tissue_mask(img_np)
            
            for y in range(0, h - ph + 1, stride):
                for x in range(0, w - pw + 1, stride):
                    patch_mask = tissue_mask[y:y+ph, x:x+pw]
                    tissue_ratio = np.mean(patch_mask)
                    
                    # Chỉ lấy patch có đủ lượng mô tế bào
                    if tissue_ratio >= min_tissue_ratio:
                        patch_crop = img_rgb.crop((x, y, x + pw, y + ph))
                        
                        # Áp dụng chuẩn hóa Macenko nếu có
                        if normalizer is not None:
                            patch_crop = normalizer.transform(patch_crop)
                            
                        patches.append({
                            "patch_image": patch_crop,
                            "bbox": (x, y, x + pw, y + ph),
                            "tissue_ratio": float(tissue_ratio)
                        })
    except Exception as e:
        print(f"[-] Lỗi khi xử lý {image_path}: {e}")
        
    return patches

def process_dataset_patches(
    input_dir,
    output_dir,
    patch_size=(224, 224),
    stride=224,
    min_tissue_ratio=0.50,
    normalizer=None
):
    """Quét toàn bộ thư mục dataset ảnh lớn và cắt patch lưu ra output_dir"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff"]
    all_images = [f for f in input_path.rglob("*.*") if f.suffix.lower() in image_extensions]
    
    print(f"[+] Tìm thấy {len(all_images)} ảnh gốc trong {input_dir}.")
    print(f"[+] Kích thước patch: {patch_size}, Stride: {stride}, Tỷ lệ mô tối thiểu: {min_tissue_ratio*100}%")
    
    total_patches_extracted = 0
    for idx, img_file in enumerate(all_images):
        patches = extract_patches_from_image(
            img_file,
            patch_size=patch_size,
            stride=stride,
            min_tissue_ratio=min_tissue_ratio,
            normalizer=normalizer
        )
        
        # Lưu các patch giữ nguyên cấu trúc thư mục con (class)
        rel_parent = img_file.relative_to(input_path).parent
        save_folder = output_path / rel_parent
        save_folder.mkdir(parents=True, exist_ok=True)
        
        base_name = img_file.stem
        for p_idx, p_data in enumerate(patches):
            patch_name = f"{base_name}_p{p_idx:04d}.png"
            p_data["patch_image"].save(save_folder / patch_name)
            total_patches_extracted += 1
            
        if (idx + 1) % 50 == 0 or (idx + 1) == len(all_images):
            print(f"  -> Đã cắt {idx + 1}/{len(all_images)} ảnh gốc -> {total_patches_extracted} patches...")
            
    print(f"\n[+] HOÀN THÀNH CẮT PATCH! Tổng số patch trích xuất được: {total_patches_extracted}")
    return total_patches_extracted
