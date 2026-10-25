"""
Script gom nhóm ảnh trùng trong LC25000, chia tập Train/Val/Test chống rò rỉ dữ liệu và xuất splits.csv.
Phụ trách: Đông / Huy (Module C2)
"""

import os
import sys
import json
import random
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
from collections import defaultdict

# Đảm bảo UTF-8 cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Đưa thư mục gốc dự án vào sys.path
sys.path.insert(0, os.path.abspath("."))

from src.c2_clustering.perceptual_hash import compute_canonical_phash

def process_single_image(args):
    """Xử lý tính canonical hash cho 1 ảnh"""
    img_path, original_label, label_7class, dataset_name = args
    chash = compute_canonical_phash(img_path)
    return {
        "filepath": str(img_path).replace("\\", "/"),
        "filename": Path(img_path).name,
        "dataset": dataset_name,
        "original_label": original_label,
        "label_7class": label_7class,
        "canonical_hash": chash
    }

def run_clustering_and_splitting(
    dataset_dir="dataset/lung_colon_image_set",
    config_path="configs/mapping_7class.json",
    train_ratio=0.70,
    val_ratio=0.15,
    test_ratio=0.15,
    seed=42,
    max_workers=8
):
    print("=" * 65)
    print(" BẮT ĐẦU GOM CỤM ẢNH TRÙNG & CHIA TẬP KHÔNG RÒ RỈ (MODULE C2)")
    print("=" * 65)
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    lc_map = cfg["dataset_mappings"]["LC25000"]["mappings"]
    
    # 1. Thu thập danh sách ảnh
    image_tasks = []
    base_path = Path(dataset_dir)
    for subdir in ["colon_image_sets", "lung_image_sets"]:
        sub_path = base_path / subdir
        if not sub_path.exists():
            continue
        for class_dir in sub_path.iterdir():
            if not class_dir.is_dir():
                continue
            orig_lbl = class_dir.name
            if orig_lbl in lc_map:
                lbl_7 = lc_map[orig_lbl]
                for img_file in class_dir.glob("*.jpeg"):
                    image_tasks.append((img_file, orig_lbl, lbl_7, "LC25000"))

    total_images = len(image_tasks)
    print(f"[+] Tìm thấy tổng cộng: {total_images} ảnh LC25000.")
    print(f"[+] Đang tính Rotation-Invariant pHash song song trên {max_workers} worker CPU...")

    # 2. Xử lý song song bằng ProcessPoolExecutor
    processed_records = []
    completed = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_image, task) for task in image_tasks]
        for f in as_completed(futures):
            res = f.result()
            if res and res["canonical_hash"] is not None:
                processed_records.append(res)
            completed += 1
            if completed % 2500 == 0 or completed == total_images:
                print(f"  -> Tiến độ băm tri giác: {completed}/{total_images} ({completed/total_images*100:.1f}%)")

    # 3. Gom nhóm theo canonical hash (Tạo cluster_id)
    print("\n[+] Đang gom cụm các biến thể ảnh trùng lặp...")
    hash_to_cluster = {}
    cluster_counter = defaultdict(int)
    
    # Tạo cluster_id gắn với từng nhãn để tường minh
    for r in processed_records:
        lbl = r["original_label"]
        h = r["canonical_hash"]
        key = (lbl, h)
        if key not in hash_to_cluster:
            cluster_counter[lbl] += 1
            hash_to_cluster[key] = f"{lbl}_cl{cluster_counter[lbl]:04d}"
        r["cluster_id"] = hash_to_cluster[key]

    # Thống kê cụm
    cluster_stats = {}
    for lbl in cluster_counter:
        cluster_stats[lbl] = cluster_counter[lbl]
    total_clusters = sum(cluster_counter.values())
    print(f"[+] Hoàn thành gom cụm! Tìm thấy tổng cộng: {total_clusters} cụm gốc trên 5 phân lớp:")
    for lbl, count in cluster_stats.items():
        print(f"    - {lbl:<12}: {count:>4} cụm gốc (từ 5000 ảnh)")

    # 4. Phân chia tập dữ liệu chống rò rỉ (Leak-free Group Stratified Split)
    print("\n[+] Phân chia Train/Val/Test theo cụm (Group-based Split)...")
    random.seed(seed)
    
    # Phân bổ cụm cho từng lớp
    cluster_split_map = {}
    for orig_lbl in cluster_counter:
        clusters_of_label = [c for (l, h), c in hash_to_cluster.items() if l == orig_lbl]
        random.shuffle(clusters_of_label)
        
        n_total = len(clusters_of_label)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        train_clusters = set(clusters_of_label[:n_train])
        val_clusters = set(clusters_of_label[n_train:n_train + n_val])
        test_clusters = set(clusters_of_label[n_train + n_val:])
        
        for c in train_clusters:
            cluster_split_map[c] = "train"
        for c in val_clusters:
            cluster_split_map[c] = "val"
        for c in test_clusters:
            cluster_split_map[c] = "test"

    # Gán split cho từng ảnh
    for r in processed_records:
        r["split"] = cluster_split_map[r["cluster_id"]]

    # 5. Xuất DataFrame và lưu splits.csv
    df = pd.DataFrame(processed_records)
    df = df[["filename", "filepath", "dataset", "original_label", "label_7class", "cluster_id", "split"]]
    
    os.makedirs("outputs", exist_ok=True)
    out_csv = "outputs/splits.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Đã lưu thành công file phân chia dữ liệu: {out_csv}")

    # 6. Thống kê kiểm tra rò rỉ dữ liệu (Leakage Verification)
    split_summary = df.groupby(["split", "original_label"]).size().unstack(fill_value=0)
    print("\n" + "=" * 65)
    print(" BẢNG PHÂN BỐ DỮ LIỆU SAU KHI CHIA TẬP:")
    print("=" * 65)
    print(split_summary)
    
    # Kiểm tra rò rỉ: Có cluster_id nào xuất hiện ở > 1 split không?
    leakage_check = df.groupby("cluster_id")["split"].nunique()
    leaks = (leakage_check > 1).sum()
    print("-" * 65)
    if leaks == 0:
        print("[VERIFIED 100%] KHÔNG CÓ RÒ RỈ DỮ LIỆU! (0 cluster bị chia cắt giữa các tập).")
    else:
        print(f"[CẢNH BÁO] Phát hiện {leaks} cluster bị rò rỉ!")
    print("=" * 65)

    # Lưu tóm tắt kết quả C2
    c2_summary = {
        "total_images": len(df),
        "total_clusters": total_clusters,
        "clusters_per_class": cluster_stats,
        "split_counts": df["split"].value_counts().to_dict(),
        "leakage_count": int(leaks),
        "split_file": out_csv
    }
    with open("outputs/c2_clustering_summary.json", "w", encoding="utf-8") as f:
        json.dump(c2_summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_clustering_and_splitting()
