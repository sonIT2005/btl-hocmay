# BTL mô bệnh học — bàn giao C1–C3

Workspace sửa và kiểm chứng dữ liệu theo scope 6 tuần. Đây là thư mục bàn giao
độc lập: cả 5 dataset nằm thật trong `data/raw/`, mỗi nguồn được giữ một bản.
LC25000 và LungHist700 đã được di chuyển từ bản cũ vào đây trên cùng ổ đĩa,
không sao chép. Thư mục không còn phụ thuộc junction hoặc thư mục bên ngoài.

Để bàn giao, chuyển nguyên thư mục `btl-histo/`. Ảnh gốc được giữ để truy vết
và tái lập; hai nhánh ảnh xử lý `none`/`macenko` là hai đầu vào thí nghiệm khác
nhau và dùng chung nhãn, nhóm, cách chia tập. File nén đã giải nén, cache đặc
trưng/CNN và môi trường Python cục bộ đã được dọn. Không tạo thêm ZIP bản sao.
Kết quả kiểm tra sau thu gọn nằm ở `results/delivery_integrity.json`;
nhật ký và dung lượng nằm ở `results/cleanup_summary.json`.
Mã nguồn, tài liệu và metadata của bản cũ được giữ trong
`data/downloads/provenance/legacy_project/` để truy vết baseline; ảnh xử lý cũ
đã bỏ. Các file trong mục lịch sử này không phải đầu vào huấn luyện hiện tại.

## Đọc kết quả

- `results/HANDOFF.md`: tình trạng thực tế và các giới hạn phải đưa vào báo cáo.
- `results/validation.json`: kiểm tra độc lập trên file bàn giao và ảnh đã sinh.
- `results/grouping_summary.json`: nhóm ảnh được khôi phục và bằng chứng kiểm chứng.
- `splits/FROZEN.json`: checksum của cấu hình và manifest sau khi kiểm tra thành công.
- `splits/inventory.csv`: toàn bộ ảnh nguồn, gồm cả ảnh loại khỏi scope và lý do.
- `splits/grouping_review_required.csv`: ảnh LC25000 còn nghi ngờ phân mảnh nhóm,
  giữ raw và metadata nhưng tạm không vào manifest thí nghiệm.
- `outputs/qa/`: ảnh đối chiếu Macenko, contact sheet nhóm ảnh (không đưa lên Git).

## File bàn giao cho C4/C8

`splits/splits_none.csv` và `splits/splits_macenko.csv` có đúng 7 cột:

```text
image_path,label,organ,source,group_id,split,split_random
```

Chọn manifest theo nhánh stain trong config của lần train. Đường dẫn ảnh luôn
tính từ `data/`. Hai manifest có cùng thứ tự, nhãn, nhóm và split, khác đường dẫn
ảnh. `splits/splits.csv` chứa thêm đường dẫn nguồn, nhánh Macenko, tọa độ cắt,
tỷ lệ mô, tỷ lệ pixel và thông tin bệnh nhân để truy vết.

- `split`: `train/val/test` theo nhóm cho LC25000 và theo mã ca bảo thủ cho BreakHis;
  cả ba nguồn ngoài miền chỉ có `xtest`.
- `split_random`: phép chia ngẫu nhiên theo ảnh nguồn phục vụ đối chứng E1.
- Nhãn: 0 lung_benign, 1 lung_aca, 2 lung_scc, 3 colon_benign, 4 colon_aca,
  5 breast_benign, 6 breast_malignant.
- Không mask đầu ra model theo cơ quan ở test chéo; model vẫn dự đoán 7 lớp.

## Các quyết định xử lý dữ liệu

1. BreakHis dùng riêng 40× (1.995 ảnh); bài gốc công bố pixel size 0,49 µm.
   Mã gốc gồm hậu tố section vẫn được giữ; `group_id` gộp theo năm và mã ca số
   để AB/CD/EF của cùng ca không nằm ở nhiều tập. Đây là gộp bảo thủ, không
   phải phát hiện lại danh tính người bệnh.
2. Mục tiêu là 0,5 µm/pixel và vùng mô 112×112 µm trước đầu vào 224×224.
   Nguồn nội bộ lấy center crop sau quy đổi tỷ lệ; LungHist700/BACH lấy lưới
   không chồng lấn. Việc cùng crop vật lý tránh resize cả ảnh 768 px và patch
   224 px thành cùng 224 px rồi coi là cùng tỷ lệ.
3. **LC25000 và LungHist700 chưa có MPP được hiệu chuẩn.** Các giá trị tương ứng
   0,5; 0,5 (20×); 0,25 (40×) là ước lượng trong config. Không được viết rằng
   đã khớp chính xác µm/pixel giữa tất cả nguồn. Đây là giới hạn của thí nghiệm.
4. Lọc patch ngoài miền có tỷ lệ mô <50% trước chuẩn hóa. Mọi patch giữ lại
   có cả hai nhánh `none` và `macenko`; không chọn patch bằng kết quả model.
5. Một ảnh LC25000 thuộc train là tham chiếu Macenko dùng chung mọi cơ quan.
   Tên ảnh, crop, SHA-256 và điều kiện số học nằm trong `configs/reference.json`.
   Không thay đổi tham chiếu theo tập test hoặc theo cơ quan.
6. LungHist700 gộp cả ba mức biệt hóa của ACA và SCC. CRC chỉ dùng NORM/TUM;
   BACH gộp Normal/Benign và InSitu/Invasive theo scope. Nhãn ảnh không đảm bảo
   mọi patch ác tính đều chứa tế bào u; phải ghi giới hạn này trong báo cáo.

## Tái chạy

Môi trường cài đặt không nằm trong bộ bàn giao; giữ `environment.yml` và
`requirements-cpu.lock` để tạo lại Python 3.11 và các thư viện Torch CPU.
Trên máy nhận, chạy từ thư mục này:

```powershell
conda env create -f environment.yml
conda activate btl-histo-data
```

Môi trường CUDA/cu128 dành cho C4/C6 phải được thiết lập và kiểm tra riêng;
workspace này chưa huấn luyện các model thí nghiệm.

Ảnh gốc và ảnh đã xử lý đều đã có sẵn. Để kiểm tra lại bộ bàn giao chỉ cần
`python tools/validate.py`; không cần tải hoặc sinh lại ảnh, không dùng
`--freeze` khi chỉ kiểm tra để giữ nguyên mốc đóng băng. Các bước dưới đây
là quy trình tái lập khi thật sự cần tính lại; tải dữ liệu và gom nhóm sẽ tạo
lại file nén/cache, và gom nhóm có thể tải lại trọng số ResNet18.

```powershell
python tools/download_sources.py breakhis
python tools/download_sources.py crc
python tools/download_sources.py bach-catalog
python tools/download_sources.py bach-tail
python tools/capture_sources.py
python tools/audit_raw.py
python tools/group_lc.py
python tools/group_lc.py --sift-refine
python tools/group_lc.py --verify-cached
python tools/group_lc.py --sift-refine --representatives 3
python tools/group_lc.py --sift-refine --representatives 3 --rescue-small
python tools/group_lc.py --cnn-rescue-small
python tools/group_lc.py --verify-cached --rescue-small --representatives 3
python tools/group_lc.py --cnn-rescue-small --neighbors 160
python tools/prepare.py
python tools/validate.py --freeze
python -m unittest discover -s tests -v
```

`tools/group_lc.py` đọc bản pHash cũ làm baseline và kiểm chứng lại các cạnh;
CNN ImageNet dùng để tìm ứng viên, SIFT/RANSAC và tương quan pixel để kiểm
chứng. `--sift-refine` tìm thêm ứng viên bằng descriptor cục bộ khi CNN bỏ sót
ảnh xoay/lật. Có checkpoint cạnh đã kiểm chứng; không ép về đúng 1.250 nhóm.
Mã nhóm là hash của tên các ảnh thành viên, không phụ thuộc thứ tự worker.
Các nhóm này không chứng minh chia theo bệnh nhân của LC25000.

Sau các lượt tìm/kiểm chứng, nhóm LC25000 chỉ có 1–4 ảnh được giữ riêng chờ
rà soát thay vì giả định đó là ảnh gốc độc lập. Ngưỡng này nằm trong config,
áp dụng giống nhau cho E1/E2 trước mọi huấn luyện. Dữ liệu raw không bị xóa.

Affine có thể co giãn hai trục khác nhau; các cặp thực tế có tương quan sau
đăng ký >0,99 nhưng tỷ lệ trục >1,5 đã được kiểm tra trực quan. Dùng giới hạn
hình học để loại biến đổi suy biến, đồng thời yêu cầu inlier, coverage và tương
quan pixel; không lấy riêng khoảng cách CNN làm chứng cứ nhận dạng. Các lượt
rescue chỉ tìm thêm ứng viên cho nhóm nhỏ, không thay đổi nhãn hoặc dùng metric
phân loại. Báo cáo từng lượt được giữ trong `results/`.

Pipeline fail rõ nếu chuẩn hóa số học không hợp lệ, không âm thầm giữ nguyên
ảnh nguồn rồi gọi là Macenko. Đường dẫn xử lý có fingerprint của code/config/
tham chiếu để không dùng lẫn cache của hai phiên bản.

Macenko dùng covariance đã trừ trung bình và tọa độ góc không đứt ở -pi/pi.
Ước lượng profile màu từ toàn ảnh nguồn bằng lấy mẫu pixel đều (tối đa khoảng
200.000 pixel), rồi dùng cùng profile cho tất cả crop của ảnh đó. Bắt đầu bằng
ngưỡng transparency chuẩn beta=0,15; chỉ hạ ngưỡng khi ảnh quá sáng khiến
không đủ pixel, có sàn độ lớn OD để loại kính. Beta thực dùng và bước lấy mẫu
được ghi vào manifest. Không gom thống kê nhiều ảnh xtest để fit tham chiếu.
Có kiểm chứng độc lập với torchstain và regression test giữ tương phản cấu trúc.

## Nguồn và điều kiện sử dụng

Tài liệu gốc, license và metadata record được giữ trong
`data/downloads/provenance/`, chỉ mục URL ở `results/source_access.json`.
CRC được xác minh MD5 toàn ZIP; BACH chỉ tải vùng ZIP chứa 400 ảnh microscopy
và xác minh CRC từng thành viên, không tải WSI và không tuyên bố đã xác minh
MD5 toàn ZIP BACH. BreakHis được kiểm tra gzip/tar khi giải nén.

BACH là CC BY-NC-ND 4.0; giữ nguyên ảnh gốc, các bản xử lý chỉ dùng trong
nghiên cứu local và không phát hành các ảnh biến đổi như dữ liệu mở.
Phikon có license phi thương mại riêng, giới hạn nghiên cứu của tổ chức phi lợi
nhuận; C1 lưu điều kiện sử dụng, chưa tải trọng số hoặc chạy E4.
Không commit dữ liệu, checkpoint, cache hay ảnh đối chiếu. Báo cáo chỉ kết luận
theo `results/validation.json`, không dựa vào việc script kết thúc mà thiếu lỗi.

