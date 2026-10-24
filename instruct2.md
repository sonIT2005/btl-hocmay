# Lệch tỷ lệ LC25000 — bản sửa (instruct2)

File này **thay thế `instruct.md`** sau khi nhóm review. `instruct.md` giữ nguyên để truy vết.
Người nhận chính: người làm C3. Cả nhóm đọc mục 1, 2, 4 và 8.

Thay đổi so với `instruct.md`:

1. Lệch tỷ lệ được xếp là **lỗi dữ liệu cần sửa**, không còn là "nguyên nhân chính" gây lỗi
   test chéo. Thí nghiệm chẩn đoán (mục 2.3) không ủng hộ vai trò nhân quả của nó.
2. Bỏ giả định hồng cầu 7,5 µm. Cỡ tham chiếu được **ước lượng thực nghiệm** trên 3 nguồn đã
   biết µm/pixel và kiểm chứng kiểu leave-one-out (mục 6, bước 2).
3. Trạng thái sau khi sửa gọi là `estimated_reference_cell`, không gọi là `calibrated`.
4. Tiêu chí "nhân 0,85–1,15× so với CRC" chỉ còn là chỉ báo QA, không phải điều kiện nghiệm thu.
5. Có quy tắc chốt trước cho trường hợp phương pháp không đạt, có snapshot đầy đủ, có người
   kiểm tra độc lập.
6. Cập nhật 24/10 theo `VERIFICATION.md` của C3:
   - fingerprint chưa tính `catalog.py`;
   - bộ lọc mô chỉ áp cho LungHist700 và BACH;
   - `validate.py` ghi cứng giới hạn µm/pixel;
   - so bất biến theo ảnh nguồn, không theo dòng;
   - kiểm tra loader/mapping ngoài miền;
   - lệnh cho PowerShell;
   - danh sách file gửi để C3 xác minh số liệu run đầu.

## 1. Tóm tắt

- **Đã quan sát:** run `e2_convnext_group_none_s0` đạt 0,92 trên test nội bộ, nhưng nhầm
  cơ quan 97% trên CRC-VAL-HE-7K và 84% trên BACH (hầu hết bị đoán thành vú).
- **Đã đo:** trên ảnh đã xử lý, nhân tế bào LC25000 to khoảng 1,5× (bách phân vị 75: 2,1×)
  so với CRC. Như vậy giả định 0,5 µm/pixel cho LC25000 nhiều khả năng sai.
- **Chưa chứng minh:** lệch tỷ lệ là nguyên nhân gây nhầm cơ quan. Đổi riêng tỷ lệ, màu hay
  nén JPEG trên ảnh nội bộ đều không tái hiện được lỗi. Nguyên nhân hiện chưa xác định.
- **Việc cần làm:** ước lượng lại µm/pixel của LC25000 bằng phép đo vật lý, sửa code, sinh lại
  ảnh, đóng băng lại, rồi chạy lại 15 run. Mục đích là để pipeline **đúng với điều nó tuyên bố**
  (mọi nguồn ở 0,5 µm/pixel). **Không hứa** việc này sẽ cải thiện kết quả test chéo.
- 14 run E1/E2 còn lại tiếp tục tạm dừng đến khi dữ liệu mới được nghiệm thu.

## 2. Bằng chứng

### 2.1. Lần chạy đầu (ConvNeXt-T, không Macenko, seed 0)

| Tập | Đơn vị | n | Accuracy 7 lớp | Nhầm cơ quan | Accuracy khi chỉ chọn trong cơ quan đúng |
|---|---|---:|---:|---:|---:|
| Test nội bộ | ảnh | 4.044 | 0,920 | 0% | 0,920 |
| LungHist700 | patch (từ 691 ảnh) | 14.557 | 0,384 | 29% | 0,489 |
| CRC-VAL-HE-7K | ảnh 224 px | 1.974 | 0,025 | 97% | 0,734 |
| BACH | patch (từ 400 ảnh) | 13.581 | 0,062 | 84% | 0,502 |

Mọi metric tính ở cấp patch, mẫu số là toàn bộ mẫu của tập. Chưa gộp lên cấp ảnh (việc của C5).
Bộ kết quả gốc gồm `configs/runs/e2_convnext_group_none_s0.yaml`, `outputs/logs/`,
`outputs/checkpoints/` và `outputs/predictions/e2_convnext_group_none_s0__*.csv` (xác suất
`prob_0..6`; logits sinh lại được từ checkpoint bằng `src/train/predict.py`). Dữ liệu là bản
đóng băng 2026-10-16, fingerprint `f5c641abf5b155b1`. Môi trường: torch 2.14.1+cu130, timm 1.0.30.

Các số trong bảng hiện **chỉ C4 xác minh**: theo `VERIFICATION.md`, bản của C3 không có predictions
hay log. Để C3 xác minh độc lập, C4 gửi các file sau (khoảng 6 MB, không cần checkpoint 107 MB):

- `outputs/predictions/`, `outputs/logs/`;
- `configs/runs/`, `configs/train_base.yaml`, `src/train/`;
- `tools/diagnose_shift.py`, `results/diagnostics_e2_convnext_group_none_s0.json`.

C3 đã xác nhận các mẫu số khớp manifest local: CRC có 1.233 TUM và 741 NORM; BreakHis có 436
ảnh `breast_benign` train.

### 2.2. Đo thô kích thước nhân (chỉ dùng để phát hiện)

150 ảnh đã xử lý mỗi nguồn; ngưỡng 15% pixel tối nhất theo kênh OD đỏ; đường kính tương đương
của các đốm ≥ 8 px.

| Nguồn | Trung vị (px) | Bách phân vị 75 (px) | So với CRC |
|---|---:|---:|---:|
| LC25000 | 8,2 | 17,2 | 1,52× |
| BACH | 6,5 | 12,2 | 1,20× |
| LungHist700 | 6,1 | 11,0 | 1,12× |
| CRC-VAL-HE-7K | 5,4 | 8,1 | 1,00 |
| BreakHis 40× | 4,7 | 6,4 | 0,86× |

Phép đo này gộp các nhân dính nhau và phụ thuộc vào thành phần mô. **Không dùng làm hệ số.**
Khoảng 0,25–0,33 µm/pixel nêu trong `instruct.md` chỉ là giả thuyết suy từ 0,5/2,1 và 0,5/1,52.

### 2.3. Thí nghiệm chẩn đoán (chỉ dùng ảnh nội bộ, không dùng xtest)

Tái lập bằng:
`python tools/diagnose_shift.py configs/runs/e2_convnext_group_none_s0.yaml`
Kết quả lưu ở `results/diagnostics_e2_convnext_group_none_s0.json`. Dùng 500 ảnh val LC25000
(100 mỗi lớp) và 299 ảnh val BreakHis.

| Thay đổi trên ảnh | Mức | Nhầm cơ quan | Đoán là vú | Accuracy 7 lớp |
|---|---|---:|---:|---:|
| Thu nhỏ LC25000 | 1 / 0,85 / 0,75 / 0,66 / 0,5× | 0% ở mọi mức | 0% | 0,94–0,96 |
| Phóng to BreakHis | 1 / 1,5 / 2 / 3× | 0 / 1 / 5 / 30% | 100 / 99 / 95 / 70% | 0,93 → 0,61 |
| Giảm bão hòa màu LC25000 | 1 / 0,6 / 0,3 / 0 | 0 / 0 / 0 / 19% | 0 / 0 / 0 / 8% | 0,95 → 0,59 |
| Nén JPEG BreakHis | gốc / q95 / q75 / q50 | ≤ 0,7% | ≥ 99% | 0,92–0,93 |
| Chuyển màu LC25000 sang thống kê BreakHis | lành / ác | 22% / 5% | 5% / 1% | 0,72 / 0,86 |

Diễn giải:

- Trong khoảng tỷ lệ hợp lý (0,5–2×), mô hình gần như **không đổi quyết định cơ quan**. Tỷ lệ
  đơn lẻ không giải thích được việc 97% ảnh CRC bị đoán thành vú.
- Màu và nén JPEG đơn lẻ cũng không tái hiện được lỗi. (LC25000 là JPEG chất lượng 75, đúng bảng
  lượng tử của PIL q75; BreakHis là PNG; CRC và BACH là TIFF.)
- Khả năng còn lại: tổ hợp nhiều khác biệt giữa các nguồn, hoặc đặc trưng mô học riêng của CRC.
  Chưa tách được. Yếu tố màu nhuộm sẽ được kiểm tra trực tiếp bằng các run E2 có Macenko.
- Loader và ánh xạ nhãn: kết quả tốt trên test nội bộ **không loại trừ** được lỗi chỉ xảy ra với
  dữ liệu ngoài miền. Hiện có các dấu hiệu sau, nhưng chưa phải bằng chứng đầy đủ:
  - ảnh nội bộ và ảnh ngoài đi qua cùng `ManifestDataset` và cùng phép biến đổi;
  - nhãn thật của CRC trong predictions là lớp 3 và 4;
  - accuracy khi chỉ chọn trong cơ quan đúng của CRC đạt 0,73.

  Kiểm tra đầy đủ nằm ở mục 6, bước 9.

### 2.4. Lỗi trong code

Đã được C3 tái hiện độc lập (`VERIFICATION.md`, mục 2) và C4 kiểm tra lại trên code:

1. `src/data/catalog.py`: `collect()` gọi `make_record` cho LC25000 mà không truyền config.
   `make_record` gán cứng `native_mpp` (`'LC25000': .5`) và `scale_status`. Đổi
   `scale.LC25000.mpp` trong YAML thành 0,25 hay 0,33 thì bản ghi vẫn nhận 0,5 và
   `estimated_unverified`. Chỉ LungHist700 đọc µm/pixel và trạng thái từ config.
2. `tools/prepare.py:163-164`: fingerprint xử lý gồm config, SHA của ảnh tham chiếu, `stain.py` và
   `prepare.py`, **không có `catalog.py`**. Sửa riêng catalog có thể không đổi fingerprint, và ảnh
   mới có thể ghi vào thư mục cũ.
3. `tools/validate.py:93`: dòng "LC25000 and LungHist700 physical pixel scale is estimated, not
   calibrated" được ghi cứng. Script không kiểm tra gì về hiệu chỉnh. Vì vậy freeze thành công không
   chứng nhận việc hiệu chỉnh đã xong.

### 2.5. Metadata của LC25000

- Bài gốc (Borkowski et al., arXiv:1912.12142): ảnh gốc 1024×768 được cắt thành 768×768;
  augment bằng Augmentor, xoay trái/phải tối đa 25° (xác suất 1,0) và lật ngang/dọc (xác suất 0,5).
  **Không có độ phóng đại, µm/pixel hay scale bar.**
- Phần thu nhận ảnh dẫn sang Borkowski et al., *Fed Pract* 2019; 36(10):456–463 (PMC6837334).
  Chưa đọc được toàn văn (PMC chặn bằng CAPTCHA). **Việc mở:** một thành viên mở bài này trên
  trình duyệt để tìm model kính hiển vi, vật kính và camera. Có thể email tác giả (andrew@usf.edu,
  ghi trong bài). Nếu có µm/pixel công bố thì dùng giá trị đó và bỏ qua mục 6, bước 1–3.

## 3. Mục tiêu và cách gọi tên

- **Mục tiêu:** ước lượng µm/pixel vật lý của LC25000 (và của LungHist700 nếu có bằng chứng lệch),
  để mọi nguồn được đưa về 0,5 µm/pixel như thiết kế. Không ép cỡ cấu trúc giữa các nguồn cho bằng nhau.
- **Trạng thái sau khi sửa:** `estimated_reference_cell`. Không có thước chuẩn (micrometer slide)
  nên không gọi là `calibrated`.
- **Nếu phương pháp không đạt** (bước 2): giữ `estimated_unverified` và 0,5 như hiện tại, ghi hạn
  chế. Không tự chọn 0,25, 0,33 hay giá trị nào khác.

## 4. Nguyên tắc (R01 và `C1_DECISIONS.md`)

1. Hệ số chỉ lấy từ phép đo vật lý trên ảnh raw. Không thử nhiều tỷ lệ rồi chọn theo accuracy/F1 xtest.
2. Tiêu chí chọn tế bào, cỡ mẫu, cách tổng hợp, ngưỡng 15% và quy tắc khi không đạt được chốt
   **trong file này, trước khi đo**. Không đổi sau khi thấy số đo.
3. Cả nhóm duyệt hệ số trước khi chạy lại bất kỳ model nào.
4. Không đổi `label`, `organ`, `source`, `group_id`, `split`, `split_random`. Không gom nhóm lại.
   51 ảnh đang cách ly vẫn để ngoài thí nghiệm.
5. Báo cáo ghi rõ: vấn đề phát hiện **sau khi đã xem kết quả xtest** của run đầu, đây là sửa đổi
   quy trình sau lần đánh giá đầu, và toàn bộ thí nghiệm được chạy lại trên dữ liệu mới.

## 5. Phân việc

| Việc | Người làm | Ghi chú thời gian |
|---|---|---|
| Gửi bằng chứng run đầu cho C3 (mục 2.1) | C4 | Làm ngay |
| Xác minh độc lập số liệu run đầu từ predictions | C3 | Song song với bước 0–1 |
| Mở PMC6837334 / email tác giả (mục 2.5) | 1 thành viên bất kỳ | Làm ngay, song song |
| Snapshot, đo, tổng hợp (bước 0–4) | C3 | Ước tính, chưa có căn cứ: đo khoảng 200–300 tế bào |
| Kiểm tra độc lập phép đo (bước 1, 8) | 1 thành viên **không phải C3** | Duyệt ít nhất 20% tế bào |
| Sửa `catalog.py` + test (bước 5) | C3; C4 review | |
| Sinh lại, kiểm tra, đóng băng (bước 6–7) | C3 | Thời gian chạy `prepare.py` chưa đo |
| Duyệt cuối, thông báo được chạy lại | Cả nhóm (nhóm trưởng ký) | |
| Chạy lại 15 run (bước 9) | C4 | Có căn cứ: 38 s/epoch ConvNeXt, 51 s/epoch Swin (đã đo); cận trên khoảng 6–7 giờ |
| Metric "accuracy trong cơ quan đúng", gộp cấp ảnh | C5 | Song song |

## 6. Quy trình

Bước 0–8 do C3 làm trên Windows, nên lệnh cho các bước này viết cho **PowerShell**. Các lệnh
`python ...` chạy được trên cả hai hệ điều hành. Bước 9 do C4 chạy trên Linux nên dùng bash.

### Bước 0. Snapshot mốc cũ (trước bước 5, trước khi chạy `prepare.py`)

`prepare.py` ghi đè `inventory.csv`, các manifest, `reference.json` và một số báo cáo. Hash cũ
không khôi phục được nội dung CSV cũ, nên phải chép **trước** khi sửa. Chỉ sao lưu `FROZEN.json`
là không đủ. Ảnh cũ để nguyên ở `data/processed/f5c641abf5b155b1/` đến khi nghiệm thu xong.

```powershell
$snap = "snapshots/2026-10-16"
New-Item -ItemType Directory -Force $snap | Out-Null
"splits","configs","results","src","tools" | ForEach-Object { Copy-Item $_ -Destination $snap -Recurse }
Get-ChildItem $snap -Recurse -File | Get-FileHash -Algorithm SHA256 |
  Select-Object Hash, Path | Export-Csv "$snap/SHA256SUMS.csv" -NoTypeInformation
```

### Bước 1. Tiêu chí đo (chốt trước, không đổi sau)

**Đối tượng đo.** Hai loại, mỗi loại có cỡ tham chiếu và công thức riêng, **không gộp**:

- `rbc`: hồng cầu tròn, nằm riêng, nhìn thẳng mặt, không chồng lên tế bào khác, bờ rõ.
  Đo đường kính dài nhất.
- `lymph_nucleus`: nhân lympho nhỏ, tròn, đậm màu đều, nằm riêng. Đo đường kính dài nhất của nhân.

Dùng `rbc` là chính. Chỉ dùng `lymph_nucleus` cho nguồn không đủ 30 hồng cầu đạt tiêu chí, và khi
đó loại tham chiếu đó phải được đo trên cả 3 nguồn đối chứng.

**Lấy mẫu.**

- Ảnh **raw** (`data/raw/...`), không đo trên ảnh đã xử lý.
- Mỗi nguồn: ít nhất 30 tế bào từ ít nhất 15 ảnh, tối đa 3 tế bào mỗi ảnh.
- LC25000: chỉ ảnh `train`, ít nhất 15 tế bào từ phổi và 15 từ đại tràng. **Mỗi `group_id` lấy
  tối đa 1 ảnh**, vì các bản augment trong cùng nhóm chứa cùng tế bào.
- Chọn ảnh ngẫu nhiên có seed từ danh sách ứng viên, bỏ qua ảnh không có tế bào đạt tiêu chí,
  ghi lại cả ảnh đã bỏ qua.

**Ghi lại.** `results/scale_calibration.csv` với các cột:
`source, image_path, group_id, cell_type, x1, y1, x2, y2, diameter_px, axis_h_px, axis_v_px, measurer, checked_by, note`.
`axis_h_px` và `axis_v_px` là đường kính theo trục ngang và trục dọc của ảnh, dùng cho phần biến
dạng hai trục. Ảnh có vẽ đường đo lưu ở `outputs/qa/scale/`.

**Kiểm tra.** Người kiểm tra (không phải C3) xem ít nhất 20% tế bào chọn ngẫu nhiên và đánh dấu
`checked_by`. Tế bào bị loại thì đo thay bằng tế bào khác theo cùng tiêu chí. Nhóm không có bác sĩ
giải phẫu bệnh xác nhận; ghi điều này vào hạn chế.

### Bước 2. Ước lượng cỡ tham chiếu và kiểm chứng phương pháp

Đo theo bước 1 trên 3 nguồn đã biết µm/pixel: CRC-VAL-HE-7K (0,5), BACH (0,42), BreakHis 40× (0,49).

1. Với mỗi nguồn `s`: lấy trung vị theo từng ảnh, rồi trung vị giữa các ảnh, được `px_s`.
   Đổi sang µm: `d_s = px_s × mpp_s`.
2. Kiểm chứng leave-one-out: với mỗi nguồn `s`, `d_ref(−s)` = trung bình `d` của 2 nguồn còn lại;
   `mpp_hat_s = d_ref(−s) / px_s`; sai số `|mpp_hat_s − mpp_s| / mpp_s`.
3. **Phương pháp đạt** khi sai số **không quá 15% ở từng nguồn riêng**. Báo bảng gồm n tế bào,
   n ảnh, `px_s`, `d_s`, `mpp_hat_s` và sai số của từng nguồn.
4. **Không đạt:** đo bổ sung **một lần** lên 60 tế bào mỗi nguồn, cùng tiêu chí. Vẫn không đạt thì
   phương pháp bị loại, dừng ở mục 3 (giữ `estimated_unverified`). Không đổi tiêu chí hay phương pháp
   để cố đạt ngưỡng.
5. Đạt thì `d_ref` = trung vị của `d_s` trên 3 nguồn.

### Bước 3. Đo LC25000 và LungHist700

- LC25000: `mpp_LC = d_ref / px_LC`.
- LungHist700: đo **riêng** 20× và 40×. Chỉ sửa nhánh nào có `mpp_hat` lệch quá 15% so với giá
  trị hiện tại (0,5 và 0,25).
- **Độ bất định:** bootstrap 2.000 lần theo ảnh, báo khoảng tin cậy 95% của `mpp`, cùng IQR của
  đường kính.
- **Biến dạng hai trục (LC25000):** báo phân bố `axis_h_px / axis_v_px`. Một hệ số resize đồng
  nhất chỉ sửa tỷ lệ điển hình; phần méo còn lại ghi vào hạn chế, kèm khoảng tỷ lệ trục đo được.

### Bước 4. Chốt

Ghi vào `results/C1_DECISIONS.md` một mục mới gồm: giá trị chốt và khoảng tin cậy 95%, loại tế bào,
số tế bào và số ảnh, bảng kiểm chứng ở bước 2, người đo, người kiểm tra, ngày. Cả nhóm duyệt trước
khi sang bước 5.

### Bước 5. Sửa code

1. `configs/preparation.yaml`: cập nhật `scale.LC25000.mpp`, đặt
   `status: estimated_reference_cell` (LungHist700 chỉ sửa nếu bước 3 yêu cầu).
2. `src/data/catalog.py`: truyền `config` vào `make_record`. Hàm này đọc `native_mpp` **và**
   `scale_status` từ `config['scale']` cho mọi nguồn, thay cho dict gán cứng. BreakHis giữ ánh xạ
   theo từng độ phóng đại (40/100/200/400×), vì catalog vẫn ghi cả ảnh 100–400× dù chúng bị loại
   khỏi thí nghiệm.
3. `tools/prepare.py`: thêm nội dung `src/data/catalog.py` vào `signature_input` (dòng 163–164),
   để mọi thay đổi catalog đều sinh fingerprint mới.
4. `tools/validate.py`: thay dòng giới hạn ghi cứng (dòng 93) bằng giới hạn sinh ra từ `scale.*.status`
   trong config. Nguồn nào còn `estimated_unverified` (ví dụ LungHist700 nếu chưa đo) thì vẫn phải
   có trong danh sách giới hạn.
5. `tests/test_catalog.py`: đổi `scale.LC25000.mpp` và `status` trong config thì `native_mpp` và
   `scale_status` của bản ghi LC25000 phải đổi theo. BreakHis vẫn đúng 0,49/0,20/0,10/0,05 theo
   độ phóng đại.

### Bước 6. Sinh lại ảnh

```powershell
python -m unittest discover -s tests -v
python tools/prepare.py
```

- Không chạy `tools/group_lc.py`.
- Ảnh mới phải ra thư mục fingerprint mới. Sau khi chạy, kiểm tra fingerprint trong
  `splits/splits_none.csv` **khác** `f5c641abf5b155b1`. Nếu trùng thì dừng lại, vì thư mục cũ đã
  bị ghi đè; khôi phục từ snapshot. Thư mục cũ giữ đến khi nghiệm thu xong.
- `prepare.py` gọi lại `assign_splits` (dòng 160). Seed giống nhau chưa đủ để đảm bảo split không
  đổi; phải so với snapshot ở bước 7.
- **Ảnh tham chiếu Macenko:** `choose_reference` chọn tự động ảnh LC25000 train đầu tiên theo thứ
  tự tên file mà vùng crop có ít nhất 70% là mô và qua được kiểm tra số học (hiện là `colonca1.jpeg`).
  Giữ nguyên quy tắc này. Nếu ảnh được chọn khác `colonca1.jpeg` thì chấp nhận nhưng ghi lại, không
  chọn tay. Lưu ý Macenko được fit trên toàn ảnh đã đổi tỷ lệ, nên thống kê màu tham chiếu sẽ đổi nhẹ.

### Bước 7. Kiểm tra và đóng băng

1. **Bất biến theo ảnh nguồn:** `source_image_path` không phải khóa duy nhất của mỗi dòng
   (LungHist700 và BACH có nhiều patch mỗi ảnh). Vì vậy gom manifest theo `source_image_path`, mỗi
   ảnh nguồn phải có đúng một giá trị cho từng trường `label, organ, source, group_id, split,
   split_random`, và giá trị đó trùng với snapshot. Mọi chênh lệch phải liệt kê và giải thích.
   Các trường dẫn xuất **được phép** đổi theo tỷ lệ: `image_path`, `image_path_macenko`,
   `native_mpp`, `scale_status`, `x_scaled`, `y_scaled`, `tissue_ratio`, các cột Macenko,
   `reference.json` và fingerprint.
2. **Số lượng:** bộ lọc mô dưới 50% chỉ áp cho LungHist700 và BACH (`prepare.py:114`); LC25000 và
   BreakHis dùng center crop, không qua bộ lọc này. Vì vậy số ảnh LC25000 và BreakHis mỗi split
   **phải giữ nguyên**; nếu đổi thì có lỗi khác, phải điều tra. Số patch LungHist700 và BACH so
   riêng theo từng ảnh nguồn, và chỉ được đổi nếu tỷ lệ của chính nguồn đó đổi.
3. **Chỉ báo QA (không phải điều kiện nghiệm thu):** đo lại kích thước nhân như mục 2.2 và làm
   contact sheet các nguồn. Nguồn nào lệch quá 0,85–1,15× so với CRC thì ghi nhận và điều tra, không
   chỉnh µm/pixel theo chỉ báo này.
4. `python tools/validate.py --freeze`, chạy sau khi `validate.py` đã được sửa ở bước 5. Freeze chỉ
   kiểm tra tính toàn vẹn, **không** chứng nhận việc hiệu chỉnh; phần đó do bước 8 nghiệm thu.
   Cập nhật `results/HANDOFF.md` và các giới hạn trong `C1_DECISIONS.md`, ghi rõ nguồn nào vẫn chưa
   hiệu chỉnh.
5. Chạy toàn bộ unit test **trong môi trường có PyTorch**. Theo `VERIFICATION.md`, 3 test gom nhóm
   chưa chạy được vì thiếu torch.

### Bước 8. Nghiệm thu

Người kiểm tra độc lập xác nhận: bảng đo và ảnh đánh dấu, bảng kiểm chứng 3 nguồn, kết quả kiểm tra
bất biến và số lượng, contact sheet. Nhóm trưởng thông báo dữ liệu đủ điều kiện chạy lại.

### Bước 9. Chạy lại (C4)

```bash
mkdir -p outputs/precalibration
cp -r src/train configs outputs/precalibration/
mv outputs/predictions/e2_convnext_group_none_s0__* outputs/logs/e2_convnext_group_none_s0.* outputs/checkpoints/e2_convnext_group_none_s0.pt results/diagnostics_e2_convnext_group_none_s0.json outputs/precalibration/
python -m unittest tests.test_train_configs
for f in configs/runs/*.yaml; do python -m src.train.train "$f" || break; done
```

- 15 run: `e1_convnext_random_none_s{0,1,2}` và `e2_{convnext,swin}_group_{none,macenko}_s{0,1,2}`,
  tất cả trên **cùng một** bản dữ liệu mới đã đóng băng.
- Trước khi chạy, kiểm tra mọi `image_path` trong `splits_none.csv` và `splits_macenko.csv` trỏ vào
  fingerprint mới.
- **Kiểm tra loader và ánh xạ nhãn ngoài miền** (C4 viết script, C3 duyệt), trên dữ liệu mới:
  - `true_label` trong mỗi file predictions trùng `label` của manifest theo `image_path`, và trùng
    ánh xạ trong `label_map.json` từ nhãn gốc của nguồn (ví dụ CRC: NORM→3, TUM→4);
  - số dòng predictions của mỗi tập test chéo bằng số dòng `xtest` của nguồn đó trong manifest;
  - với mỗi nguồn, đọc vài ảnh qua `ManifestDataset` và so tensor với ảnh PNG đọc trực tiếp rồi
    chuẩn hóa bằng tay. Hai kết quả phải giống nhau, không có xoay/lật hay đổi kênh màu ngoài ý muốn.
- C4 bổ sung vào `outputs/logs/{run}.json` fingerprint dữ liệu và SHA-256 của `FROZEN.json` (hiện
  code chưa ghi).
- Sau khi chạy lại, chạy `tools/diagnose_shift.py` trên checkpoint mới để so với mục 2.3.

## 7. Tiêu chí hoàn thành

- [ ] Snapshot `snapshots/2026-10-16/` kèm SHA-256
- [ ] `scale_calibration.csv` đủ cỡ mẫu theo bước 1, ít nhất 20% tế bào đã được kiểm tra
- [ ] Bảng leave-one-out: sai số không quá 15% ở cả 3 nguồn (hoặc ghi rõ "không đạt", giữ trạng thái cũ)
- [ ] Hệ số, khoảng tin cậy 95% và người duyệt ghi trong `C1_DECISIONS.md` trước khi chạy lại model
- [ ] C3 đã nhận bộ bằng chứng run đầu và xác minh lại các con số ở mục 2.1
- [ ] `catalog.py` đọc µm/pixel và trạng thái từ config, có test (gồm BreakHis theo độ phóng đại)
- [ ] `catalog.py` nằm trong fingerprint; fingerprint mới khác `f5c641abf5b155b1`
- [ ] `validate.py` sinh giới hạn từ trạng thái trong config, không ghi cứng
- [ ] 6 trường bất biến giống hệt theo từng ảnh nguồn; số ảnh LC25000/BreakHis không đổi
- [ ] Toàn bộ unit test chạy trong môi trường có PyTorch
- [ ] Kiểm tra loader và ánh xạ nhãn ngoài miền đạt (bước 9)
- [ ] Chỉ báo QA và contact sheet đã lưu
- [ ] `FROZEN.json` mới; `HANDOFF.md` và `C1_DECISIONS.md` đã cập nhật
- [ ] Nghiệm thu bởi người kiểm tra độc lập; nhóm trưởng thông báo

## 8. Kỳ vọng và cách diễn giải sau khi chạy lại

- Kết quả test chéo **có thể không cải thiện**, vì mục 2.3 cho thấy tỷ lệ không phải yếu tố quyết
  định. Đó vẫn là kết quả hợp lệ cho RQ1 (Δ lớn ở cả hai kiến trúc).
- Để RQ1 không bị "chạm đáy" do lỗi nhầm cơ quan, C5 báo **cả** accuracy 7 lớp theo R07, tỷ lệ nhầm
  cơ quan **và** accuracy khi chỉ chọn trong cơ quan đúng (mẫu số là toàn bộ mẫu).
- Các run có Macenko trả lời trực tiếp màu nhuộm góp phần bao nhiêu vào lỗi nhầm cơ quan.
- Kết quả của run đầu (`outputs/precalibration/`) và mục 2.3 có thể đưa vào phụ lục, làm ví dụ về
  shortcut theo nguồn dữ liệu.

## 9. Ghi vào báo cáo

- **Phương pháp:** µm/pixel của LC25000 được ước lượng bằng tế bào tham chiếu (loại tế bào, n tế bào,
  n ảnh). Cỡ tham chiếu ước lượng thực nghiệm trên 3 nguồn có µm/pixel công bố; sai số leave-one-out
  x / y / z%; khoảng tin cậy 95% của hệ số.
- **Hạn chế:**
  - phát hiện sau khi xem kết quả xtest của run đầu;
  - hệ số chỉ dựa trên đo vật lý;
  - không có thước chuẩn hay xác nhận của bác sĩ giải phẫu bệnh;
  - còn biến dạng hai trục ở LC25000;
  - nguyên nhân của lỗi nhầm cơ quan chưa được xác định.
