# Kế hoạch triển khai C1–C3

1. Khi triển khai: giữ nguyên bản người trước, tạo workspace riêng và Python 3.11.
2. Tái sử dụng LC25000/LungHist700; bổ sung BreakHis, CRC-VAL-HE-7K và BACH
   microscopy từ nguồn chính thức; lưu metadata/license và kiểm tra giải nén.
3. Sửa mapping 7 lớp; giữ nhãn gốc, mã ca và lý do loại; chỉ lấy BreakHis 40×.
4. So baseline pHash với CNN và kiểm chứng hình học; mở rộng ứng viên SIFT
   khi CNN bỏ sót; xuất nhóm có thể truy vết mà không ép số nhóm.
5. Chia 70/15/15 theo nhóm, seed 42; tạo đối chứng random riêng; giữ xtest riêng.
6. Sửa lỗi góc Macenko, dùng một tham chiếu train, quy đổi FOV có khai báo
   tỷ lệ nào chỉ là ước lượng; sinh các nhánh none/Macenko trên cùng crop.
7. Kiểm tra manifest, nhãn, đường dẫn, nhóm, bệnh nhân và giải mã ảnh thực;
   kiểm tra ảnh so sánh; đóng băng bằng checksum khi không có lỗi chặn.

Trạng thái và số liệu cuối được ghi ở `results/HANDOFF.md` và các báo cáo JSON.
Không làm C4–C9, thêm dataset TCGA hoặc thí nghiệm ECE ngoài scope rút gọn.

Sau khi hoàn thành, theo yêu cầu thu gọn bộ bàn giao: di chuyển LC25000 và
LungHist700 vào `data/raw/` không sao chép; bỏ bản dữ liệu lặp, ảnh xử lý cũ,
archive, cache và môi trường cài đặt. Chỉ giữ một thư mục `btl-histo/` độc lập,
ảnh gốc cùng hai nhánh thí nghiệm, metadata, code và báo cáo kiểm chứng.
