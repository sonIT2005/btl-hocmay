\# Bàn giao C1–C3 — scope 6 tuần



Trạng thái kiểm tra: \*\*passed\_with\_identity\_and\_scale\_limitations\*\*. Đã chuẩn bị dữ liệu và file bàn

giao local; kết quả này không phải kết quả huấn luyện/đánh giá các model E1–E4.

Bộ bàn giao độc lập trong `btl-histo/`: cả 5 dataset nằm thật trong `data/raw/`.

LC25000/LungHist700 được di chuyển từ bản cũ, không sao chép thêm tài nguyên.

File nén đã giải nén, cache trung gian, môi trường cục bộ và bản xử lý cũ đã

được dọn theo yêu cầu. Giữ ảnh gốc để truy vết và hai nhánh none/Macenko cho

thí nghiệm so sánh. Xem `cleanup\_summary.json`, `delivery\_integrity.json` và

`../README.md` để chuyển máy, kiểm tra và tạo lại môi trường.

Mã/tài liệu/metadata cũ được giữ gọn ở

`../data/downloads/provenance/legacy\_project/` để truy vết baseline.



\## Dữ liệu thực tế



| Dataset | Ảnh raw kiểm tra đủ | Ảnh nguồn chọn theo scope | Mẫu model / mỗi nhánh |

|---|---:|---:|---:|

| LC25000 | 25,000 | 25,000 | 24,949 |

| BreakHis | 7,909 | 1,995 | 1,995 |

| LungHist700 | 691 | 691 | 14,557 |

| CRC-VAL-HE-7K | 7,180 | 1,974 | 1,974 |

| BACH | 400 | 400 | 13,581 |



\- Giải mã và SHA-256 \*\*41,180 ảnh raw\*\*, lỗi: 0.

\- Giải mã \*\*114,112 ảnh model\*\* thuộc hai nhánh,

&#x20; kiểm tra kích thước 224×224/RGB, đường dẫn và ghép cặp none/Macenko.

\- CRC-VAL-HE-7K dùng riêng NORM/TUM; BreakHis dùng riêng 40×. Các ảnh khác

&#x20; vẫn giữ trong raw và inventory có lý do loại, không lẫn vào train.

\- BACH đủ 100 ảnh/lớp, đối chiếu ground truth; không lấy WSI vào pipeline.

\- BreakHis có 74 ảnh raw cao 456 px thay vì 460 px; không tự loại các ảnh này.

\- \*\*51 ảnh LC25000 trong nhóm 1–4 ảnh\*\*

&#x20; được giữ riêng ở `splits/grouping\_review\_required.csv`, chưa đưa vào cả E1/E2.

&#x20; Đây là chưa đủ bằng chứng về họ hàng ảnh, không phải ảnh hỏng hay sai nhãn.



\## Nhóm ảnh và chia tập



Baseline pHash cũ: \*\*20,443 nhóm\*\*. Kết quả mới:

\*\*1,263 nhóm được tái dựng\*\*, 23,737

cạnh nối đã qua kiểm chứng pixel/hình học. \*\*1,226 nhóm LC25000\*\*

được dùng trong thí nghiệm sau khi giữ riêng các nhóm 1–4 ảnh. Không ép số nhóm về 1.250.



| Lớp nguồn LC25000 | Nhóm tái dựng | Nhóm vào thí nghiệm |

|---|---:|---:|

| colon\_aca | 255 | 249 |

| colon\_n | 255 | 246 |

| lung\_aca | 247 | 241 |

| lung\_n | 252 | 245 |

| lung\_scc | 254 | 245 |



Group ID là hash tên thành viên. BreakHis giữ mã gốc nhưng gộp các hậu tố section

của cùng mã ca số: 70 nhóm bảo thủ, không diễn giải là xác minh 70 bệnh nhân.

Chia theo lớp và nhóm với seed 42; quota nhóm 70/15/15 dùng largest remainder,

thử các hoán vị có seed để cân bằng số ảnh, không sử dụng kết quả mô hình.



| Nhãn nội bộ | Train | Val | Test |

|---|---:|---:|---:|

| 0 lung\_benign | 3,494 | 748 | 749 |

| 1 lung\_aca | 3,496 | 749 | 749 |

| 2 lung\_scc | 3,490 | 748 | 749 |

| 3 colon\_benign | 3,491 | 748 | 747 |

| 4 colon\_aca | 3,493 | 749 | 749 |

| 5 breast\_benign | 436 | 93 | 96 |

| 6 breast\_malignant | 959 | 206 | 205 |



\- Nhóm xuất hiện ở nhiều split: \*\*0\*\*.

\- Mã bệnh nhân được cung cấp xuất hiện ở nhiều split: \*\*0\*\*.

\- Ba nguồn test chéo chỉ có `xtest`; không dùng làm train/val hay chọn tham chiếu.

\- `split\_random` là đối chứng chia theo ảnh cho E1, cùng danh sách mẫu.



\## Tiền xử lý và kiểm chứng



FOV mục tiêu 112×112 µm tại 0,5 µm/pixel, đầu vào 224×224. Nội bộ dùng center

crop; LungHist700/BACH dùng lưới không overlap sau quy đổi scale. Loại

\*\*419 patch ngoài miền\*\* có mô <50%.

Hai nhánh dùng cùng crop, label, group và split; fingerprint:

`f5c641abf5b155b1`.



Macenko đã sửa lỗi góc qua biên -pi/pi, dùng covariance đã trừ trung bình và

kiểm tra basis suy biến. Profile nguồn lấy mẫu đều từ toàn ảnh để dùng chung

cho các patch; beta transparency thực dùng được ghi vào metadata. Có kiểm

chứng độc lập với torchstain và regression test tương phản cấu trúc. Mọi lỗi

số học được báo rõ, không âm thầm trả ảnh gốc như kết quả chuẩn hóa thành công.



Tham chiếu duy nhất: `raw/LC25000/colon\_image\_sets/colon\_aca/colonca1.jpeg`, split \*\*train\*\*,

group `LC25000:bdc57ff988aae588`; condition number

\*\*3.921\*\*. Crop và SHA-256 nằm trong

`configs/reference.json`. Không chọn tham chiếu từ test hoặc theo cơ quan.



Đã pass \*\*14 tests\*\* về mapping, giữ section

cùng ca, split tái lập/không cắt nhóm, xoay góc lẻ/co giãn hai trục, trường hợp

ảnh xanh sáng và Macenko. Xem `test\_results.txt`, `raw\_audit.json`,

`validation.json`; ảnh đối chiếu tại `../outputs/qa/`.



\## Dùng cho C4/C8



Đọc `splits/splits\_none.csv` hoặc `splits/splits\_macenko.csv` theo config stain.

Cả hai có đúng 7 cột `image\_path,label,organ,source,group\_id,split,split\_random`.

Đường dẫn tính từ thư mục `data/`. Bản `splits/splits.csv` có metadata mở rộng

để truy ngược về ảnh nguồn và tọa độ crop. Nhãn và source map nằm trong

`splits/label\_map.json`, nguyên liệu kiểm kê trong `splits/inventory.csv`.



Đóng băng: `2026-10-16T10:03:56.478461+00:00`; checksum ở `splits/FROZEN.json`.

Không chỉnh split sau khi xem kết quả model. Nếu phát hiện vấn đề sau đó,

ghi rõ ảnh hưởng/giới hạn và trao đổi với cả nhóm theo scope.



\## Giới hạn phải đưa vào báo cáo



1\. \*\*MPP LC25000 và LungHist700 là ước lượng, chưa hiệu chuẩn.\*\* Affine do

&#x20;  augmentation LC25000 còn có thể làm thay đổi scale theo từng trục. Không

&#x20;  tuyên bố đã khớp chính xác tỷ lệ vật lý của tất cả nguồn.

2\. LC25000 không cung cấp patient/source IDs đầy đủ; các nhóm khôi phục bằng

&#x20;  hình học không chứng minh độc lập theo bệnh nhân hoặc không còn rò rỉ tuyệt đối.

&#x20;  51 ảnh cần rà soát không vào thí nghiệm; phải báo mẫu số 24.949/25.000 và

&#x20;  khả năng việc loại các biến thể khó này làm thay đổi phân bố ảnh nội bộ.

3\. BACH/CRC thiếu patient IDs đầy đủ; bootstrap theo image/patch group có thể

&#x20;  chưa phản ánh hết tương quan giữa mẫu cùng bệnh nhân.

4\. Nhãn ảnh truyền xuống patch là weak label; đủ mô không đồng nghĩa có tế bào u.

5\. `none` là không áp dụng thêm Macenko của nhóm; không mặc định nguồn chưa

&#x20;  từng xử lý màu. Phải nêu giới hạn upstream stain khi diễn giải CRC.

6\. Dữ liệu/ảnh biến đổi không đưa lên Git. BACH CC BY-NC-ND 4.0 và điều kiện

&#x20;  phi thương mại của Phikon được lưu trong `C1\_DECISIONS.md` và provenance.

7\. Bàn giao nguyên thư mục `btl-histo/`, gồm dữ liệu và metadata với cấu trúc

&#x20;  hiện tại. Không cần thư mục dữ liệu cũ hoặc junction bên ngoài. Môi trường

&#x20;  Python phải tạo lại từ các file cấu hình đã giữ, cache sẽ sinh lại khi cần.



