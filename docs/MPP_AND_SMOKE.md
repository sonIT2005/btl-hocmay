# Chuẩn bị đo MPP và chạy kiểm tra — giữ dữ liệu 16/10

Code mới nằm trong repo `C:\Users\Admin\Documents\GitHub\btl-hocmay`. Dữ liệu canonical tiếp tục nằm ở `C:\Users\Admin\Documents\FrameView\btl-histo\data`; đọc bằng đường dẫn, không copy hoặc tạo junction. Các split, nhãn, group, ảnh và FROZEN hiện tại không được sinh lại trong đợt này.

Các sửa code không biến dữ liệu cũ thành dữ liệu đã hiệu chuẩn. `FROZEN.json` cũ là bằng chứng lịch sử của code/data 16/10; code mới có thể khác hash source cũ. Không chạy `--freeze` để che khác biệt đó. Preflight training kiểm tra hash manifest/label map theo FROZEN và lưu phiên bản code riêng.

## 1. Những gì đã sửa

- Git ignore `/data/` ở gốc, giữ được `src/data` trong working tree. `.gitattributes` bảo toàn byte các data-contract files trên checkout sau này; không chạy renormalize dữ liệu cũ.
- Catalog đọc MPP/status từ config, BreakHis có đủ mapping 40/100/200/400×; LungHist700 hỗ trợ status riêng từng magnification. Các MPP và trạng thái đang dùng vẫn giữ nguyên.
- Prepare bị chặn khi đã có FROZEN nếu không có opt-in rõ. Fingerprint gồm catalog/scale; kiểm tra trùng trước ghi đầu ra; giữ nguyên split đã có thay vì chia lại. Không dùng lệnh prepare trong các bước đo/preflight dưới đây.
- Run/checkpoint có provenance gồm fingerprint, hash FROZEN/manifest/label map, công thức và code train. Khác phiên bản hoặc thiếu provenance thì không tự skip/resume. Checkpoint được ghi qua file tạm rồi thay thế.
- Export probabilities giữ precision, không round 6 chữ số; không ghi đè predictions có sẵn.
- Smoke chỉ dùng train/val nội bộ, tên `_smoke`, output tách riêng và không chấm xtest. Không coi kết quả smoke là kết quả nghiên cứu.

## 2. Bộ đo đã chuẩn bị

Bộ đang dùng: `C:\Users\Admin\Documents\FrameView\btl-histo\outputs\maintenance_2026-10-25\mpp_kit`.

- `candidates.csv`: 420 ảnh ứng viên, 60 mỗi hàng đợi: CRC, BACH, BreakHis 40×, LC25000 phổi, LC25000 đại tràng, LungHist700 20×, LungHist700 40×. Đây là số ứng viên để tìm tế bào phù hợp, không yêu cầu đo đủ 420 ảnh.
- LC25000 chỉ train, tối đa một ảnh mỗi group. Các ảnh quarantine không được chọn.
- `image_review.csv`: ghi ảnh eligible/skipped/pending và lý do bỏ qua; xét theo thứ tự hàng đợi, không chọn theo kết quả model hoặc hệ số mong muốn.
- `measurements.csv`: chỉ có header, chưa có số đo hay hệ số được tạo sẵn.
- `protocol.json` và `protocol.sha256`: seed chọn ảnh 42, seed review 43, seed bootstrap 20261025; không sửa tiêu chí sau khi xem số đo. Muốn sửa quy trình phải tạo kit mới có lý do.

Mở ảnh raw theo `image_path` tính từ data root. Dùng Fiji/ImageJ hoặc viewer hiển thị tọa độ pixel gốc; không resize/crop ảnh trước khi đo, không dùng kích thước hiển thị trên màn hình làm pixel gốc. TIFF của CRC/BACH cần viewer đọc TIFF; không đo thumbnail.

### Đối tượng và cỡ mẫu

- `rbc`: hồng cầu tròn, tách biệt, nhìn thẳng mặt, bờ rõ; đo đường kính dài nhất.
- `lymph_nucleus`: chỉ dùng khi RBC không đủ và đã đo loại nhân này trên cả ba nguồn đối chứng; báo cáo riêng, không pool với RBC.
- Mỗi nguồn/cohort: ≥30 tế bào từ ≥15 ảnh, tối đa 3 tế bào/ảnh. LC25000 có ≥15 tế bào phổi và ≥15 đại tràng. LungHist700 kiểm tra riêng 20× và 40× nếu thực hiện.
- Điền người đo. Người kiểm tra phải khác người đo; tối thiểu 20% mẫu trong mỗi cohort được chọn ngẫu nhiên bằng seed đã khóa. Không có bác sĩ xác nhận phải ghi giới hạn đó.

### Điền bảng

Mỗi hàng là một tế bào thật: `measurement_id` duy nhất; `candidate_id` từ hàng đợi; `cell_type`; tọa độ raw `x1,y1,x2,y2`; `measurer`. `diameter_px` có thể để trống vì công cụ tính khoảng cách hai điểm. Nếu nhập thì phải khớp trong 0,01 px. Trục ngang/dọc là tùy chọn QA, không dùng để chứng minh đã khử méo affine.

Đánh dấu ảnh đó `eligible` trong image_review. `review_status` để trống khi chưa kiểm; `checked` khi người kiểm tra điền `checked_by`; `rejected` phải có người kiểm tra và lý do, giữ hàng bị loại để truy vết và đo mẫu thay thế. Không dùng cùng tên người đo/người kiểm tra.

Chạy analyze lần đầu để nhận danh sách `review_measurement_ids`; người kiểm tra xem đúng các annotation đó, cập nhật CSV rồi xuất báo cáo phiên bản mới. Khi bổ sung mẫu, danh sách cần kiểm có thể thay đổi theo bộ dữ liệu mới; các lần báo cáo cũ được giữ riêng.

```powershell
Set-Location C:\Users\Admin\Documents\GitHub\btl-hocmay
$kit = 'C:\Users\Admin\Documents\FrameView\btl-histo\outputs\maintenance_2026-10-25\mpp_kit'
$data = 'C:\Users\Admin\Documents\FrameView\btl-histo\data'
python tools/measure_mpp.py analyze --kit $kit --cell-type rbc --out "$kit/analysis_v1.json"
python tools/measure_mpp.py render --kit $kit --cell-type rbc --data-root $data --out "$kit/annotations_v1"
```

Analyzer trả `incomplete` khi thiếu mẫu hoặc review; không suy MPP trong trạng thái đó. Render giữ nguyên kích thước raw và kiểm SHA ảnh trước khi vẽ; ảnh đầu ra là annotation mới, raw không đổi. Lệnh không ghi đè kit/báo cáo đã có.

### Quy tắc kết luận

- Trung vị theo ảnh rồi theo nguồn; đổi sang µm bằng MPP công bố CRC 0,5/BACH 0,42/BreakHis 40× 0,49.
- Leave-one-source-out phải có sai số ≤15% ở từng nguồn. Không đạt thì đo bổ sung một lần lên ≥60 tế bào/nguồn, rồi phân tích `--stage expanded` với file báo cáo mới. Vẫn không đạt: giữ MPP và trạng thái hiện tại, ghi thất bại; không tìm hệ số khác để đủ checklist.
- Qua kiểm chứng thì đề xuất `estimated_reference_cell`; CI 95% bootstrap 2.000 lần ảnh của cả ba nguồn tham chiếu và nguồn đích, giữ phân tầng phổi/đại tràng của LC.
- CI không bao hàm sai nhận dạng tế bào/sai số hệ thống, và kiểm chứng ba nguồn không bảo đảm sai số LC cũng ≤15%. Nguồn chưa đo giữ nguyên MPP. Không chốt giá trị bằng accuracy/F1 xtest hoặc ép kích thước nhân/CRC bằng nhau.
- Công cụ không ghi config hay cấp quyền regenerate. Phải review độc lập, báo rõ dùng ảnh các nguồn xtest làm tham chiếu sau lần đánh giá đầu, rồi nhóm duyệt mới xem xét đổi pixel. Nếu phép đo thất bại, nhóm quyết định tiếp tục với giới hạn MPP cũ hay dừng; không tự dỡ tạm dừng 14 run.

## 3. Preflight không train, không tải pretrained weights

Dùng Python có các thư viện trong environment của C4. Môi trường CPU tạm đã dùng kiểm tra tại máy này không thay môi trường CUDA của C4.

```powershell
$data = 'C:\Users\Admin\Documents\FrameView\btl-histo\data'
$splits = 'C:\Users\Admin\Documents\FrameView\btl-histo\splits'
$cfg = 'configs/runs/e2_convnext_group_none_s0.yaml'
python tools/check_training.py $cfg --data-root $data --splits-dir $splits --tensor-check --forward --device cpu
```

Lệnh kiểm hash data contract, toàn bộ đường dẫn, mapping, sample image SHA, tensor loader so với đọc PNG trực tiếp, rồi forward model với trọng số ngẫu nhiên. Không chấm accuracy, không train. Có thể đổi cfg sang Swin để kiểm kiến trúc còn lại.

`run_state=blocked_old_artifacts` là bảo vệ kết quả cũ, không phải lý do bỏ qua cảnh báo rồi chạy đè. Các kết quả run đầu không có provenance mới phải được giữ lại; trial dùng output root mới.

## 4. Nếu cần smoke trên máy GPU

Chỉ thực hiện sau khi preflight đạt. Dùng môi trường CUDA đã được C4 kiểm tra; GPU vật lý có mặt chưa chứng minh wheel PyTorch hỗ trợ GPU. Kiểm trước:

```powershell
python -c "import torch; print(torch.__version__, torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA'); print(torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False)"
python tools/check_training.py $cfg --data-root $data --splits-dir $splits --tensor-check --forward --device cuda
python -m src.train.train $cfg --data-root $data --splits-dir $splits --smoke --num-workers 0 --output-root outputs/trials/mpp_readiness_01
```

Smoke chỉ 2 epoch trên subset train/val; dùng một thư mục trial mới nếu chạy công thức khác. Không đổi 15 config nghiên cứu chỉ để sửa lỗi môi trường. Không chạy vòng lặp 15 run trong đợt chuẩn bị này.

Resume cùng config/data/code được kiểm tra provenance. Resume sau khởi động lại không hứa tái lập bit-for-bit luồng augmentation của persistent workers; seed cho run mới và dấu vết input vẫn được lưu. Nếu export predictions bị ngắt giữa chừng, giữ các file một phần và dùng output root mới để export lại từ checkpoint; không ghi đè bằng một lần train mới.

## 5. Xuất lại probabilities đầy đủ từ checkpoint cũ ở máy C4

Không cần train lại. C4 phải có checkpoint gốc và đúng dữ liệu 16/10. Checkpoint cũ chưa có provenance nên bắt buộc opt-in legacy và xuất vào thư mục mới, không thay CSV gốc:

```powershell
python -m src.train.predict $cfg --data-root $data --splits-dir $splits --checkpoint outputs/checkpoints/e2_convnext_group_none_s0.pt --allow-legacy-checkpoint --output-root outputs/trials/legacy_full_precision_01
```

Sidecar ghi `legacy_unverified`; việc opt-in không tự chứng minh nguồn gốc checkpoint. C4/C5 dùng xác suất này tính metric cơ quan thật trước làm tròn. Tại máy local hiện chưa có checkpoint nên chưa thực hiện lệnh này.

## 6. Kiểm tra và Git

Để chạy cả fixture C1–C3 mà không copy dataset:

```powershell
$env:BTL_TEST_DATA_ROOT = $data
$env:BTL_TEST_SPLITS_DIR = $splits
python -m unittest discover -s tests -v
git diff --check
git status --short
```

Trong đợt sửa hiện tại không commit/push, không stage index, không chạy group/prepare/validate --freeze. Các source mới và docs cần được review rồi thêm vào commit cùng thay đổi .gitignore; dataset vẫn bị ignore.
