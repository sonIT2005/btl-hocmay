import kagglehub
import shutil
import os

# Tải dataset về cache của máy
path = kagglehub.dataset_download("andrewmvd/lung-and-colon-cancer-histopathological-images")
print("Dữ liệu đã tải về tại:", path)

# (Tùy chọn) Copy dữ liệu về thư mục dự án hiện tại
destination = "./dataset"
if not os.path.exists(destination):
    shutil.copytree(path, destination)
    print(f"Đã sao chép dữ liệu vào: {os.path.abspath(destination)}")

