# Dữ liệu (không commit)

- `raw/LC25000`: bản LC25000 có sẵn, 25.000 JPEG.
- `raw/LungHist700`: bản có sẵn với images/ và data.csv, 691 JPEG.
- `raw/BreakHis`: giải nén BreaKHis_v1.tar.gz từ UFPR, 7.909 PNG.
- `raw/CRC-VAL-HE-7K`: bộ 7.180 TIFF từ Zenodo, dùng riêng NORM/TUM.
- `raw/BACH`: chỉ Photos/ 400 microscopy TIFF và ground truth, không có WSI.
- `processed/`: crop/patch none và Macenko theo fingerprint code/config/reference.
- `downloads/provenance/`: tài liệu, license, record nguồn và baseline pHash cũ.

Link nguồn chính thức và điều kiện sử dụng ở `../results/C1_DECISIONS.md`.
Hướng dẫn tái lập ba nguồn bổ sung ở `../README.md`. Cả 5 nguồn hiện là thư mục
thật bên trong `raw/`, không dùng junction. LC25000/LungHist700 được di chuyển
từ bản cũ, không sao chép lại. Chuyển nguyên thư mục bàn giao để giữ đúng cấu
trúc đường dẫn tương đối trong manifest. Các gói nén đã giải nén đã được dọn;
`downloads/` chỉ giữ provenance và chỉ mục cấu trúc ZIP BACH nhỏ để truy vết.

Không commit ảnh, archive, feature cache hoặc checkpoint. Các CSV trong
`../splits/` là metadata bàn giao và kiểm kê, không phải ảnh.
