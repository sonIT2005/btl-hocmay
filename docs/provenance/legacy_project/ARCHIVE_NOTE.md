# Bản dự án cũ để truy vết

Mục này giữ mã nguồn, cấu hình, báo cáo và metadata của bản người trước làm.
Được di chuyển vào bộ bàn giao, không sao chép thêm dữ liệu.

Đây là tư liệu lịch sử, không phải pipeline hoặc manifest dùng để huấn luyện.
Đọc `../../../../README.md` và `../../../../results/HANDOFF.md` cho bản hiện tại.

- Ảnh gốc LC25000 và LungHist700 được di chuyển tới `data/raw/` của bộ bàn giao.
- Bộ patch `dataset/patches/LungHist700_normalized` cũ không còn dùng và đã dọn.
- Gói LungHist700.rar đã được đối chiếu đủ 692 tệp với raw đang giữ rồi dọn.
- Các đường dẫn tương đối trong mã/báo cáo lịch sử mô tả cấu trúc cũ; không chạy
  pipeline cũ từ đây hoặc dùng các split cũ thay cho `splits/` ở thư mục gốc.

Phần ảnh hiện dùng cùng metadata, code đã sửa và bằng chứng kiểm chứng đều nằm
trong cấu trúc chính của `btl-histo/`.
