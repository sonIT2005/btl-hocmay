# C1 — quyết định và giới hạn dữ liệu

Ngày kiểm tra: 16/10/2026. Áp dụng scope 6 tuần trong tài liệu người dùng cung cấp.
Không viết lại giả thuyết nghiên cứu, không thêm TCGA/ECE/calibration.

## 1. BreakHis: chọn 40×

Bài gốc, Table I công bố: visual magnification 40× tương ứng objective 4× và
effective pixel size 0,49 µm; 100×/200×/400× lần lượt khoảng 0,20/0,10/0,05 µm.
Vì vậy không so trực tiếp con số “40×” của hai hệ chụp khác nhau rồi kết luận
khớp độ phóng đại. Chọn riêng 40× của BreakHis (1.995 ảnh) để gần mục tiêu
0,5 µm/pixel đã biết của CRC và giữ trường nhìn rộng hơn.

Nguồn: https://www.inf.ufpr.br/lesoliveira/download/TBME-00608-2015-R2-preprint.pdf
Lưu bản gốc ở `data/downloads/provenance/breakhis_paper.pdf`.

LC25000 chưa có hiệu chuẩn MPP. Vì vậy lựa chọn trên có căn cứ đối với nguồn
đã biết, nhưng **chưa chứng minh khớp chính xác với LC25000**. Không dùng
accuracy/F1 trên xtest để thay đổi mức phóng đại hoặc tỷ lệ cắt.

BreakHis raw có 7.909 ảnh, 82 thư mục ca theo cách tổ chức nguồn; một số mã
khác hậu tố section AB/CD/EF. Giữ mã gốc trong `patient_id`/`slide_id`, gộp
bảo thủ theo năm và phần số trong `group_id`. Quy tắc này tạo 70 nhóm mã ca;
không diễn giải là xác minh lại rằng bộ dữ liệu chỉ có 70 bệnh nhân.

## 2. BACH: lấy microscopy có nhãn, không lấy WSI

Nguồn: https://zenodo.org/records/3632035

Lấy 400 ảnh thuộc Photos/Normal, Benign, InSitu, Invasive và file ground truth.
Mặc dù Zenodo gọi đây là phần training của challenge, trong đề tài này toàn bộ
400 ảnh chỉ là test chéo `xtest`; không dùng để train/chọn epoch/tuning.
Không dùng bộ challenge test 100 ảnh hoặc WSI vì nằm ngoài scope đã thống nhất.

Tải các đoạn ZIP chứa Photos thay vì toàn ZIP 10,4 GB; kiểm tra CRC-32 và độ
dài từng file giải nén. Không khẳng định đã xác minh MD5 của toàn ZIP khi chỉ
tải phần microscopy.

License trong record: CC BY-NC-ND 4.0. Lưu LICENSE và README nguyên bản;
giữ raw không đổi. Crop/chuẩn hóa local phục vụ nghiên cứu; không phát hành
ảnh biến đổi như dữ liệu mở hoặc dùng thương mại. Điều kiện upstream phải
đi kèm dữ liệu nếu chuyển giao.

## 3. Phikon: chỉ xác nhận khả năng dùng cho E4

Model: `owkin/phikon` (ViT-B, iBOT), không tự thay bằng Phikon-v2.
Model card: https://huggingface.co/owkin/phikon
License: https://github.com/owkin/HistoSSLscaling/blob/main/LICENSE.txt

Đây là license riêng của Owkin, giới hạn nghiên cứu phi thương mại của tổ chức
phi lợi nhuận và các điều kiện dẫn xuất/kết quả. Đề tài học phần áp dụng mục
đích học thuật phi thương mại; lưu license đầy đủ cho người chạy E4 kiểm tra.
C1 không cần tải trọng số hoặc fine-tune Phikon. Nếu mục đích/tổ chức sử dụng
thay đổi thì phải đối chiếu điều kiện gốc.

## 4. Scale và stain cần đưa vào phần hạn chế

- CRC: MPP 0,5 theo nguồn; chỉ NORM 741 + TUM 1.233 = 1.974 patch.
- BACH: MPP 0,42 theo tài liệu challenge, resample về mục tiêu trước cắt.
- LC25000: MPP 0,5 là ước lượng chưa hiệu chuẩn.
- LungHist700: chỉ có metadata 20×/40×; ước lượng tương ứng 0,5/0,25 MPP,
  không dùng DPI 96 của JPEG làm pixel size vật lý.
- Mọi nguồn dùng FOV mục tiêu 112 µm và đầu vào 224×224; nội bộ center crop,
  BACH/LungHist700 lưới không chồng lấn. Giữ tọa độ và scale_status để truy vết.
- `none` nghĩa là không áp dụng thêm Macenko của nhóm. Không suy ra rằng ảnh
  upstream chắc chắn chưa từng chuẩn hóa màu; lịch sử xử lý của CRC phải được
  nêu khi diễn giải mức cải thiện stain theo cơ quan.
- Ngưỡng mô ≥50% chỉ loại nền kính, không chứng minh patch chứa tế bào u.
- Không có patient ID đầy đủ cho BACH/CRC; group_id ảnh/patch không bảo đảm
  bootstrap đã phản ánh hết tương quan theo bệnh nhân của các nguồn này.

## 5. C2 và C3

Mã nhóm LC25000 là ảnh cùng trường mô được tái dựng bằng kiểm chứng hình học;
không gọi là patient split hoặc chứng nhận “0% leakage tuyệt đối”. Bản pHash
cũ chỉ được dùng như baseline/ứng viên và kiểm chứng lại. Mục tiêu ~1.250 ảnh
gốc là kiểm tra hợp lý theo tài liệu, không phải điều kiện ép merge.

Macenko sửa lỗi percentile góc đi qua biên -pi/pi, kiểm tra basis không suy biến,
không âm thầm trả ảnh gốc khi lỗi. Một tham chiếu train dùng cho mọi cơ quan.
Covariance được trừ trung bình theo triển khai Macenko chuẩn. Profile màu dùng
toàn ảnh nguồn được lấy mẫu đều, thay vì ước lượng riêng trên từng patch ít mô.
Beta transparency khởi điểm 0,15; nếu thiếu pixel có cơ chế hạ beta được ghi
rõ trong metadata, vẫn loại kính theo độ lớn OD. Có đối chiếu độc lập với
torchstain: https://github.com/EIDOSLAB/torchstain .
Kết quả thực tế và tình trạng hoàn thành nằm trong `HANDOFF.md` sau khi kiểm
tra ảnh và manifest; tài liệu quyết định này không tự chứng nhận hoàn thành.
