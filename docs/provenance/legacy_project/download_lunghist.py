"""
Script tải LungHist700 từ Figshare chính thức (639.3 MB) và tự động giải nén.
DOI: 10.6084/m9.figshare.25459174
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path

# Đảm bảo UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DOWNLOAD_URL = "https://ndownloader.figshare.com/files/45206104"
TARGET_DIR = Path("dataset/LungHist700")
RAR_PATH = Path("dataset/LungHist700.rar")
WINRAR_EXE = r"C:\Program Files\WinRAR\WinRAR.exe"

def download_with_progress(url, dest_path):
    print(f"[+] Bắt đầu tải LungHist700 từ Figshare...")
    print(f"    URL: {url}")
    print(f"    Lưu tạm tại: {dest_path}")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(dest_path, 'wb') as out_file:
        total_size = int(resp.headers.get('content-length', 0))
        downloaded = 0
        block_size = 1024 * 1024  # 1MB
        
        while True:
            buffer = resp.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if total_size > 0:
                percent = downloaded / total_size * 100
                mb_down = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  -> Tiến độ tải: {mb_down:.1f}/{mb_total:.1f} MB ({percent:.1f}%)")
                sys.stdout.flush()
    print("\n[+] Tải file RAR thành công!")

def extract_rar(rar_path, extract_to):
    print(f"[+] Đang giải nén vào: {extract_to}...")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(WINRAR_EXE):
        cmd = [WINRAR_EXE, "x", "-ibck", "-y", str(rar_path.resolve()), str(extract_to.resolve()) + "\\"]
        subprocess.run(cmd, check=True)
        print(f"[+] Giải nén thành công bằng WinRAR!")
    else:
        print("[-] Cảnh báo: Không tìm thấy WinRAR. Hãy giải nén file thủ công tại:", rar_path)

def main():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Tải nếu chưa có
    if not RAR_PATH.exists() or RAR_PATH.stat().st_size < 600 * 1024 * 1024:
        download_with_progress(DOWNLOAD_URL, RAR_PATH)
    else:
        print(f"[+] File {RAR_PATH} đã tồn tại ({RAR_PATH.stat().st_size / (1024*1024):.1f} MB). Bỏ qua bước tải.")

    # 2. Giải nén
    extract_rar(RAR_PATH, TARGET_DIR)
    
    # 3. Kiểm tra số file đã giải nén
    files = list(TARGET_DIR.rglob("*.*"))
    image_files = [f for f in files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]]
    print(f"\n" + "=" * 60)
    print(f" HOÀN TẤT! ĐÃ GIẢI NÉN ĐƯỢC {len(image_files)} FILE ẢNH VÀO {TARGET_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
