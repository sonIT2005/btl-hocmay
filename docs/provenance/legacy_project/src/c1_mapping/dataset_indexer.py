"""
Script quét dữ liệu, ánh xạ sang hệ thống 7 lớp và thống kê tổng quan dataset.
Phụ trách: Đông / Huy (Module C1)
"""

import os
import sys
import json
import glob
from pathlib import Path
from collections import defaultdict, Counter

# Đảm bảo in unicode ra console Windows không bị lỗi charmap
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_mapping_config(config_path="configs/mapping_7class.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def scan_lc25000(base_dir="dataset/lung_colon_image_set", mapping_cfg=None):
    """Quét bộ LC25000 và gán nhãn 7 lớp"""
    records = []
    lc_map = mapping_cfg["dataset_mappings"]["LC25000"]["mappings"]
    
    # Duyệt cả 2 thư mục con colon_image_sets và lung_image_sets
    subdirs = ["colon_image_sets", "lung_image_sets"]
    for subdir in subdirs:
        dir_path = Path(base_dir) / subdir
        if not dir_path.exists():
            continue
        for class_folder in dir_path.iterdir():
            if not class_folder.is_dir():
                continue
            orig_label = class_folder.name
            if orig_label in lc_map:
                class_7 = lc_map[orig_label]
                for img_file in class_folder.glob("*.jpeg"):
                    records.append({
                        "filepath": str(img_file).replace("\\", "/"),
                        "filename": img_file.name,
                        "dataset": "LC25000",
                        "original_label": orig_label,
                        "label_7class": class_7,
                        "class_name": mapping_cfg["classes"][str(class_7)]["name"],
                        "organ": mapping_cfg["classes"][str(class_7)]["organ"],
                        "type": mapping_cfg["classes"][str(class_7)]["type"]
                    })
    return records

def scan_generic_dataset(dataset_name, dataset_dir, mapping_cfg):
    """Hỗ trợ quét các dataset khác khi được thêm vào (LungHist700, BACH...)"""
    records = []
    if dataset_name not in mapping_cfg["dataset_mappings"]:
        return records
    ds_map = mapping_cfg["dataset_mappings"][dataset_name]["mappings"]
    dir_path = Path(dataset_dir)
    if not dir_path.exists():
        return records

    for ext in ["*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff"]:
        for img_file in dir_path.rglob(ext):
            parent_name = img_file.parent.name
            if parent_name in ds_map:
                class_7 = ds_map[parent_name]
                records.append({
                    "filepath": str(img_file).replace("\\", "/"),
                    "filename": img_file.name,
                    "dataset": dataset_name,
                    "original_label": parent_name,
                    "label_7class": class_7,
                    "class_name": mapping_cfg["classes"][str(class_7)]["name"],
                    "organ": mapping_cfg["classes"][str(class_7)]["organ"],
                    "type": mapping_cfg["classes"][str(class_7)]["type"]
                })
    return records

def main():
    print("=" * 60)
    print(" BẮT ĐẦU QUÉT VÀ ÁNH XẠ DỮ LIỆU SANG 7 LỚP (MODULE C1)")
    print("=" * 60)
    
    config_path = "configs/mapping_7class.json"
    if not os.path.exists(config_path):
        print(f"Lỗi: Không tìm thấy file config {config_path}")
        return

    mapping_cfg = load_mapping_config(config_path)
    all_records = []

    # 1. Quét LC25000
    lc_records = scan_lc25000("dataset/lung_colon_image_set", mapping_cfg)
    all_records.extend(lc_records)
    print(f"[+] LC25000: Đã quét được {len(lc_records)} ảnh.")

    # 2. Quét các dataset khác nếu có trong dataset/
    for extra_ds in ["LungHist700", "BACH", "BreakHis"]:
        extra_path = f"dataset/{extra_ds}"
        if os.path.exists(extra_path):
            records = scan_generic_dataset(extra_ds, extra_path, mapping_cfg)
            all_records.extend(records)
            print(f"[+] {extra_ds}: Đã quét được {len(records)} ảnh.")
        else:
            print(f"[-] {extra_ds}: Chưa tìm thấy thư mục {extra_path} (Sẽ cập nhật ở C3).")

    # Thống kê phân bố
    class_counts = Counter(r["label_7class"] for r in all_records)
    dataset_counts = Counter(r["dataset"] for r in all_records)

    summary = {
        "total_images": len(all_records),
        "dataset_distribution": dict(dataset_counts),
        "class_distribution": {
            str(k): {
                "count": class_counts.get(k, 0),
                "name": mapping_cfg["classes"][str(k)]["name"],
                "display_name": mapping_cfg["classes"][str(k)]["display_name"],
                "organ": mapping_cfg["classes"][str(k)]["organ"]
            }
            for k in range(7)
        }
    }

    os.makedirs("outputs", exist_ok=True)
    summary_path = "outputs/c1_dataset_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(" KẾT QUẢ THỐNG KÊ PHÂN BỐ 7 LỚP:")
    print("=" * 60)
    for class_id, info in summary["class_distribution"].items():
        print(f"  Lớp {class_id} [{info['name']:<18} | {info['organ']:<6}]: {info['count']:>6} ảnh ({info['display_name']})")
    print(f"\n=> Tổng số ảnh đã lập chỉ mục: {summary['total_images']}")
    print(f"=> Báo cáo tóm tắt đã lưu tại: {summary_path}")

if __name__ == "__main__":
    main()
