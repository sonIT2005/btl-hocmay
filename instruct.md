# Lệch tỷ lệ phóng đại LC25000: phát hiện và hướng dẫn hiệu chỉnh

Người nhận chính: người làm C3 (tiền xử lý). Cả nhóm cần đọc mục 1, 2 và 4.
Ngày phát hiện: 22/10/2026, sau lần chạy thật đầu tiên `e2_convnext_group_none_s0`.

## 1. Tóm tắt

- Ảnh LC25000 đang được xử lý như thể chụp ở 0,5 µm/pixel. Đo kích thước nhân tế bào
  cho thấy LC25000 phóng đại hơn mức này khoảng **1,5–2 lần** (giá trị thật có thể
  khoảng 0,25–0,33 µm/pixel).
- Hậu quả: mô hình học mẹo "ảnh trông khác LC25000 thì là vú". 97% ảnh CRC (đại tràng)
  và 84% ảnh BACH bị đoán sang cơ quan khác. Mức sụt Δ khi test chéo vì vậy chủ yếu đo
  độ lệch tỷ lệ, không đo khác biệt giữa convolution và attention, nên RQ1 mất ý nghĩa.
- Đề xuất: hiệu chỉnh µm/pixel của LC25000 bằng **phép đo vật lý trên ảnh gốc**, sinh lại
  ảnh, giữ nguyên nhãn, nhóm và cách chia tập, rồi chạy lại toàn bộ 15 lần E1/E2.
- **Tạm dừng các lần chạy E1/E2 còn lại** cho đến khi hiệu chỉnh xong.

## 2. Bằng chứng

### 2.1. Kết quả lần chạy đầu (ConvNeXt-T, không Macenko, seed 0)

| Tập | Accuracy 7 lớp | Tỷ lệ nhầm cơ quan | Accuracy khi chỉ chọn trong cơ quan đúng |
|---|---:|---:|---:|
| Test nội bộ | 0,920 | 0% | 0,920 |
| LungHist700 | 0,384 | 29% | 0,489 |
| CRC-VAL-HE-7K | 0,025 | 97% | 0,734 |
| BACH | 0,062 | 84% | 0,502 |

Với CRC-VAL-HE-7K: 1.205/1.233 ảnh TUM và 702/741 ảnh NORM bị đoán là `breast_malignant`.
Test nội bộ không có ca nào nhầm cơ quan, nên lỗi không nằm ở code train/predict.

### 2.2. Kích thước nhân tế bào trên ảnh đã xử lý (`none`, 224×224)

Lấy 150 ảnh mỗi nguồn, ngưỡng hóa 15% pixel tối nhất theo kênh OD đỏ, tính đường kính
tương đương của các đốm ≥ 8 px. Nếu các nguồn đã cùng tỷ lệ thì nhân phải có cỡ xấp xỉ nhau.

| Nguồn | Đường kính trung vị (px) | Bách phân vị 75 (px) | So với CRC |
|---|---:|---:|---:|
| LC25000 (train) | 8,2 | 17,2 | **1,52×** (bách phân vị 75: 2,1×) |
| BACH | 6,5 | 12,2 | 1,20× |
| LungHist700 | 6,1 | 11,0 | 1,12× |
| CRC-VAL-HE-7K | 5,4 | 8,1 | 1,00 |
| BreakHis 40× | 4,7 | 6,4 | 0,86× |

Đây là phép đo thô: nhân dính nhau bị tính thành một đốm, và thành phần mô khác nhau giữa
các nguồn. Chỉ dùng nó để **phát hiện** vấn đề, không dùng làm hệ số hiệu chỉnh. Ảnh mẫu
xếp cạnh nhau cũng cho thấy rõ: nhân LC25000 rất to, còn CRC thấy được cả tuyến ruột.

### 2.3. Lỗi trong code

`src/data/catalog.py`, hàm `make_record`, gán cứng `native_mpp` theo nguồn
(`'LC25000': .5`). Khóa `scale.LC25000.mpp` trong `configs/preparation.yaml`
**không được đọc** cho LC25000 (chỉ LungHist700 đọc từ config). Sửa riêng file config
sẽ không thay đổi ảnh sinh ra.

## 3. Nguyên tắc khi hiệu chỉnh

Phải giữ đúng R01 và quyết định ở `results/C1_DECISIONS.md` ("không dùng accuracy/F1 trên
xtest để thay đổi mức phóng đại"):

1. Hệ số mới chỉ được lấy từ **phép đo vật lý trên ảnh raw**. Không thử nhiều giá trị
   rồi chọn giá trị cho accuracy test chéo cao nhất.
2. Chốt hệ số và ghi lại cách đo **trước** khi chạy lại bất kỳ model nào.
3. Không đổi `label`, `group_id`, `split`, `split_random`. Chỉ pixel ảnh và các cột tỷ lệ
   được phép thay đổi.
4. Báo cáo ghi trung thực trình tự: phát hiện sau lần chạy đầu, sửa bằng phép đo vật lý,
   chạy lại toàn bộ. Giữ kết quả lần chạy cũ làm bằng chứng (mục 5, bước 7).

## 4. Phân việc và hạn

| Việc | Người làm | Hạn |
|---|---|---|
| Đo và chốt µm/pixel cho LC25000 (và LungHist700 nếu lệch) | C3 | 1 ngày |
| Sửa code, sinh lại ảnh, kiểm tra, đóng băng lại | C3 | 1 ngày |
| Duyệt hệ số và đồng ý chạy lại | Cả nhóm | Trước khi chạy lại |
| Chạy lại 15 lần E1/E2 (khoảng 6 giờ GPU) | C4/C6 | Sau khi đóng băng lại |
| Thêm metric "accuracy trong cơ quan đúng" | C5 | Song song |

## 5. Quy trình hiệu chỉnh (người làm C3)

### Bước 1. Đo bằng thước vật lý trên ảnh raw

Dùng **hồng cầu** làm thước: đường kính khoảng 7,5 µm, gần như không đổi giữa các mô và
các bệnh viện. Tế bào lympho nhỏ (khoảng 7 µm) dùng thay khi không có hồng cầu.

- Mở ảnh **raw** (`data/raw/...`, LC25000 là ảnh 768×768), không đo trên ảnh đã xử lý.
- Đo tối thiểu **30 hồng cầu** cho mỗi nguồn cần hiệu chỉnh, từ ít nhất 15 ảnh khác nhau.
  Chọn hồng cầu nằm riêng, tròn, không chồng lên nhau; đo đường kính dài nhất.
- Với LC25000: lấy ảnh thuộc split `train`, trải đều cả phổi và đại tràng. Ảnh LC25000 đã
  bị augment bằng affine nên mỗi trục có thể co giãn khác nhau; vì vậy lấy **trung vị**
  của nhiều phép đo, không lấy một ảnh.
- Công cụ: Fiji/ImageJ (Straight Line + Measure) hoặc bất kỳ viewer nào hiện tọa độ pixel.
  Ghi kết quả vào `results/scale_calibration.csv` với các cột:
  `source,image_path,cell_type,diameter_px`.

Công thức: `mpp = 7,5 / trung_vị(diameter_px)`.

### Bước 2. Kiểm chứng phương pháp đo trước khi tin vào nó

Áp dụng đúng cách đo ở bước 1 cho các nguồn **đã biết µm/pixel**: CRC-VAL-HE-7K (0,5),
BACH (0,42), BreakHis 40× (0,49). Việc này chỉ đọc ảnh raw, không dùng nhãn hay kết quả model.

- Nếu giá trị đo được lệch không quá **15%** so với giá trị công bố ở cả 3 nguồn, phương
  pháp đáng tin; dùng nó cho LC25000.
- Nếu lệch hơn 15%: đo thêm cho nhiều tế bào hơn hoặc đổi sang tế bào lympho. Không chuyển
  sang bước 3 khi phương pháp chưa qua kiểm chứng.

Kiểm tra chéo thêm (không bắt buộc): so cỡ nhân giữa các cặp cùng loại mô trên ảnh raw,
`colon_aca` (LC25000) với `TUM` (CRC), `colon_n` với `NORM`. Kết quả nên cùng chiều với bước 1.

### Bước 3. Chốt hệ số

- Ghi vào `results/C1_DECISIONS.md` một mục mới: giá trị mpp chốt cho LC25000, số tế bào
  đã đo, sai số kiểm chứng ở bước 2, ngày chốt.
- LungHist700 (20× và 40×) cũng là giá trị ước lượng. Đo theo cùng cách; chỉ sửa nếu lệch
  quá 15% so với 0,5 và 0,25 hiện tại.
- BreakHis, CRC, BACH giữ giá trị công bố.

### Bước 4. Sửa code

1. `configs/preparation.yaml`: cập nhật `scale.LC25000.mpp` và đổi
   `status: estimated_unverified` thành `calibrated_rbc`.
2. `src/data/catalog.py`, `make_record`: đọc `native_mpp` và `scale_status` của LC25000
   (và các nguồn khác) từ `config['scale']` thay cho dict gán cứng. `collect()` đã nhận
   `config`, chỉ cần truyền xuống `make_record`.
3. Thêm test trong `tests/test_catalog.py`: đổi `scale.LC25000.mpp` trong config thì
   `native_mpp` của bản ghi LC25000 phải đổi theo.

Ở 0,25–0,33 µm/pixel, ảnh LC25000 768 px thu về khoảng 384–507 px, vẫn đủ cho center crop
224 px. Vùng mô thật trong mỗi ảnh đầu vào sẽ rộng hơn trước.

### Bước 5. Sinh lại ảnh

```bash
python -m unittest discover -s tests -v
python tools/prepare.py
```

- **Không** chạy lại `tools/group_lc.py`: các nhóm ảnh không phụ thuộc tỷ lệ.
- Fingerprint xử lý đổi nên ảnh mới ra thư mục `data/processed/<fingerprint mới>/`. Giữ
  thư mục cũ đến khi bước 6 qua hết rồi mới xóa (khoảng vài GB).
- Ảnh tham chiếu Macenko vẫn là `colonca1.jpeg`, nhưng vùng crop đổi theo tỷ lệ mới nên
  `configs/reference.json` sẽ được sinh lại. Đây là thay đổi hợp lệ.

### Bước 6. Kiểm tra rồi đóng băng lại

1. Sao lưu mốc cũ: `cp splits/FROZEN.json splits/FROZEN_2026-10-16.json`
2. So với bản cũ, các cột sau phải **giống hệt** theo `source_image_path`: `label`,
   `organ`, `source`, `group_id`, `split`, `split_random`. Số ảnh LC25000 và BreakHis mỗi
   split phải giữ nguyên; nếu bộ lọc tỷ lệ mô dưới 50% loại thêm ảnh nào thì liệt kê và báo
   cả nhóm. LungHist700 và BACH chỉ đổi số patch nếu đổi tỷ lệ của chính chúng.
3. Đo lại kích thước nhân trên ảnh mới bằng cách ở mục 2.2. Mong đợi mọi nguồn nằm trong
   khoảng 0,85–1,15× so với CRC. Lưu contact sheet vào `outputs/qa/`.
4. `python tools/validate.py --freeze`
5. Cập nhật `results/HANDOFF.md`: mpp mới, ngày đóng băng mới, giới hạn còn lại.

### Bước 7. Bàn giao cho C4

Báo C4 khi xong bước 6. C4 làm như sau:

```bash
mkdir -p outputs/precalibration
mv outputs/predictions/e2_convnext_group_none_s0__* outputs/logs/e2_convnext_group_none_s0.* outputs/checkpoints/e2_convnext_group_none_s0.pt outputs/precalibration/
python -m unittest tests.test_train_configs
for f in configs/runs/*.yaml; do python -m src.train.train "$f" || break; done
```

Code train không phải sửa: nó đọc `splits/splits_{stain}.csv`, và hai file này sẽ trỏ
sang thư mục ảnh mới.

## 6. Tiêu chí hoàn thành

- [ ] `results/scale_calibration.csv` có ít nhất 30 phép đo cho mỗi nguồn đã đo
- [ ] Phương pháp lệch không quá 15% trên CRC, BACH, BreakHis
- [ ] Hệ số mới ghi trong `C1_DECISIONS.md` trước khi chạy lại model
- [ ] `catalog.py` đọc mpp từ config, có test kèm theo
- [ ] Nhãn, nhóm, split giống hệt bản đóng băng 16/10
- [ ] Kích thước nhân sau xử lý nằm trong 0,85–1,15× so với CRC
- [ ] `FROZEN.json` mới, bản cũ giữ lại thành `FROZEN_2026-10-16.json`

## 7. Ghi vào báo cáo

- Phần phương pháp: µm/pixel của LC25000 được hiệu chỉnh bằng hồng cầu (n tế bào), phương
  pháp được kiểm chứng trên 3 nguồn có µm/pixel công bố (sai số x%).
- Phần hạn chế: lỗi tỷ lệ phát hiện sau lần chạy đầu; hệ số mới chỉ dựa trên đo vật lý,
  không dựa trên kết quả test chéo; toàn bộ thí nghiệm được chạy lại sau hiệu chỉnh.
- Có thể đưa kết quả lần chạy cũ (`outputs/precalibration/`) vào phụ lục làm ví dụ về
  shortcut theo nguồn dữ liệu. Phát hiện này có giá trị và củng cố lý do đề tài cần test chéo.

## 8. Ghi chú khác

- **Lớp vú yếu ngay trong test nội bộ** (macro-F1 0,59; 71% ảnh `breast_benign` bị đoán
  là ác tính). Có thể do BreakHis 40× có nhân rất nhỏ (khoảng 4–5 px) và chỉ có 436 ảnh
  lành tính để train. Không sửa trong đợt này; theo dõi lại sau khi chạy lại.
- **Metric phụ cho C5:** "accuracy trong cơ quan đúng", tức là chọn argmax chỉ trong các
  lớp thuộc cơ quan thật của ảnh. Báo cáo cạnh tỷ lệ nhầm cơ quan (R07) để tách hai loại
  lỗi: nhầm cơ quan do khác nguồn, và nhầm lành/ác trong cùng cơ quan.
