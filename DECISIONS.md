# Quyết định và giới hạn

Nhật ký các quyết định của đề tài. Mỗi mục: ngày, trạng thái, nội dung ngắn.
Trạng thái: **Chốt** (đã áp dụng), **Đề xuất** (chờ nhóm duyệt), **Đang làm**.
Khi chốt thêm điều gì, thêm hoặc sửa mục ở đây. Không tạo file tài liệu mới.

## Đề tài

**D1. Câu hỏi nghiên cứu** · 01/10 · Chốt
- RQ1 (trọng tâm): cùng pretrain ImageNet, ConvNeXt-T (convolution) hay Swin-T (attention) giữ hiệu
  năng tốt hơn khi test chéo sang nguồn dữ liệu khác?
- RQ2 (bổ sung): cùng ViT-B/16 và linear probe, pretrain ImageNet hay pretrain mô bệnh học (Phikon)
  cho đặc trưng bền hơn?
- Chỉ số chính: Δ = metric nội bộ − metric test chéo, tính theo từng cơ quan.
- RQ2 dừng ở đề cương, chuyển thành hướng phát triển (xem D14).

**D2. Dữ liệu và nhãn** · 16/10 · Chốt
- 7 lớp: 0 lung_benign, 1 lung_aca, 2 lung_scc, 3 colon_benign, 4 colon_aca, 5 breast_benign,
  6 breast_malignant. Ánh xạ nhãn gốc nằm ở `splits/label_map.json`.
- Train/val/test nội bộ: LC25000 (phổi, đại tràng) và BreakHis (vú).
- Test chéo, chỉ dùng để đánh giá (R01): LungHist700 (phổi), CRC-VAL-HE-7K chỉ NORM/TUM (đại tràng),
  BACH 400 ảnh microscopy (vú).

## Dữ liệu

**D3. BreakHis lấy riêng 40×** · 16/10 · Chốt
- 1.995 ảnh, 0,49 µm/pixel theo Table I của bài gốc.
- Chia theo mã ca, gộp các hậu tố section AB/CD/EF của cùng ca: 70 nhóm. Đây là gộp bảo thủ,
  không phải xác minh lại danh tính bệnh nhân.

**D4. Giấy phép** · 16/10 · Chốt
- BACH: CC BY-NC-ND 4.0. Không phát hành ảnh đã biến đổi; ảnh QA không đưa lên Git.
- Phikon (`owkin/phikon`): giấy phép phi thương mại riêng của Owkin, dùng cho mục đích học thuật.

**D5. Gom nhóm LC25000 và chia tập** · 16/10 · Chốt
- LC25000 sinh từ khoảng 1.250 ảnh gốc bằng augmentation (xoay đến 25°, lật). Tái dựng 1.263 nhóm
  bằng kiểm chứng hình học. 51 ảnh thuộc nhóm 1–4 ảnh được cách ly, không vào thí nghiệm
  (mẫu số nội bộ 24.949/25.000).
- Chia 70/15/15 theo nhóm, giữ tỷ lệ lớp, seed 42. Không nhóm nào nằm ở 2 tập.
- `split_random` là phép chia ngẫu nhiên theo ảnh, chỉ dùng cho E1.

**D6. Tiền xử lý** · 16/10 · Chốt
- Mục tiêu 0,5 µm/pixel, vùng mô 112×112 µm, đầu vào 224×224.
- Nội bộ: center crop. LungHist700, BACH: lưới không chồng lấn. Bộ lọc mô ≥50% chỉ áp cho
  LungHist700 và BACH.
- Hai nhánh `none` và `macenko` dùng chung crop, nhãn, nhóm, split.
- Macenko: một ảnh tham chiếu chung cho mọi cơ quan, lấy từ LC25000 train (`colonca1.jpeg`),
  chọn bằng quy tắc tự động trong `tools/prepare.py`.

**D7. Đóng băng dữ liệu** · 16/10 · Chốt
- Fingerprint `f5c641abf5b155b1`, checksum ở `splits/FROZEN.json`.
- Không chỉnh split sau khi xem kết quả model. Lỗi phát hiện sau đó ghi vào mục giới hạn.

## Huấn luyện

**D8. Công thức chung, không tuning** · 22/10 · Chốt
- `configs/train_base.yaml`: AdamW 1e-4, weight decay 0,05, cosine + warmup 2 epoch, tối đa 30 epoch,
  dừng sớm sau 5 epoch, batch 32, bf16, class-weighted loss, chỉ augmentation hình học (R05).
- Chọn checkpoint theo macro-F1 val nội bộ (R06). Mỗi cấu hình 3 seed.
- 15 run: E1 (ConvNeXt, chia ngẫu nhiên, 3 seed) và E2 ({ConvNeXt, Swin} × {none, Macenko} × 3 seed).
- Mỗi run ghi provenance (fingerprint, SHA của FROZEN/manifest/recipe/code). Code từ chối resume hoặc
  ghi đè khi provenance khác (25/10).

## Lần chạy đầu và lỗi tỷ lệ

**D9. Kết quả `e2_convnext_group_none_s0`** · 22/10 · Chốt (Đông đã xác minh lại 25/10)

| Tập | n | Accuracy 7 lớp | Nhầm cơ quan |
|---|---:|---:|---:|
| Test nội bộ | 4.044 | 0,920 | 0% |
| LungHist700 | 14.557 patch | 0,384 | 29% |
| CRC-VAL-HE-7K | 1.974 | 0,025 | 97% (gần hết bị đoán là vú) |
| BACH | 13.581 patch | 0,062 | 84% (mô vú bị đoán sang phổi 6.911, đại tràng 4.541) |

Kết quả và checkpoint cũ được lưu ở `outputs/precalibration/`.

**D10. µm/pixel của LC25000 nhiều khả năng sai** · 22–25/10 · Chốt: không hiệu chỉnh (30/10)
- **Kết cục:** đến hết hạn 29/10 (D12) chưa có phép đo tế bào đạt chuẩn. Theo nhánh "không đạt" đã định
  trước, giữ 0,5 µm/pixel và trạng thái `estimated_unverified`, không sinh lại ảnh. Dữ liệu dùng cho mọi
  thí nghiệm là bản đóng băng 16/10. Phần dưới đây giữ lại để ghi vào báo cáo.
- Bằng chứng: nhân tế bào LC25000 to khoảng 1,5× (bách phân vị 75: 2,1×) so với CRC trên ảnh đã xử lý.
  Đây là phép đo thô, chỉ để phát hiện.
- Code từng gán cứng 0,5 µm/pixel cho LC25000 trong `catalog.py`. Đã sửa ngày 25/10: đọc từ
  `configs/preparation.yaml`, fingerprint tính cả `catalog.py`/`scale.py`.
- Metadata hệ chụp (Borkowski 2019, Fed Pract): Olympus BX41, vật kính 60×, camera Leica MC190 HD,
  ảnh 1024×768. Chưa biết adapter camera nên không suy được µm/pixel duy nhất. Khoảng tham khảo
  0,10–0,20 µm/pixel (adapter 1× đến 0,5×) **chỉ dùng để đối chiếu, không dùng để chốt hệ số**.
- Cách hiệu chỉnh: đo tế bào tham chiếu (hồng cầu, hoặc nhân lympho) trên ảnh raw. Cỡ tham chiếu
  ước lượng trên CRC (0,5), BACH (0,42), BreakHis (0,49). Phương pháp đạt khi sai số leave-one-out
  ≤15% **ở từng nguồn**. Mỗi nguồn ≥30 tế bào từ ≥15 ảnh; LC25000 mỗi `group_id` tối đa 1 ảnh;
  ≥20% tế bào được người khác kiểm tra.
- Không đạt sau một lần đo bổ sung lên 60 tế bào/nguồn: giữ 0,5 và trạng thái `estimated_unverified`.
  Đạt: trạng thái `estimated_reference_cell` (không gọi là calibrated), sinh lại ảnh ở fingerprint mới,
  chạy lại 15 run.
- Không bao giờ chọn hệ số theo accuracy/F1 trên xtest.

**D11. Tỷ lệ chưa chắc là nguyên nhân nhầm cơ quan** · 24/10 · Chốt
- Thử trên ảnh nội bộ (không dùng xtest, `tools/diagnose_shift.py`): thu nhỏ LC25000 đến 0,5×, phóng to
  BreakHis đến 2×, đổi màu, nén JPEG đều **không** tái hiện lỗi nhầm cơ quan.
- Vì vậy sửa tỷ lệ là sửa cho đúng dữ liệu, không hứa cải thiện test chéo. Nguyên nhân nhầm cơ quan
  chưa xác định; nhánh Macenko của E2 sẽ kiểm tra yếu tố màu.

**D12. Hạn chót cho việc đo µm/pixel** · 26/10 · Chốt
- Đo đến hết 29/10. Không kịp hoặc không đạt thì đi theo nhánh "không đạt" ở D10.
- Chạy ngay 15 run trên dữ liệu đóng băng 16/10, song song với việc đo. Kết quả này dùng được cho cả
  hai nhánh (kết quả chính, hoặc đối chứng trước hiệu chỉnh).
- Kết cục 30/10: không đạt (xem D10), 15 run này là kết quả chính.

## Đánh giá

**D13. Metric** · 22/10 · Chốt
- Theo từng cơ quan: balanced accuracy, macro-F1, AUROC lành/ác; confusion matrix 7 lớp.
- Test chéo: model vẫn dự đoán 7 lớp, dự đoán sang cơ quan khác tính là sai (R07). Báo cáo riêng
  tỷ lệ nhầm cơ quan và accuracy khi chỉ chọn trong các lớp của cơ quan thật (mẫu số là toàn bộ mẫu,
  tính từ xác suất đầy đủ).
- Báo cáo thêm recall từng lớp: accuracy che giấu lớp yếu (run đầu: accuracy 0,92 nhưng recall
  `breast_benign` chỉ 0,29).
- Độ biến thiên: mean ± SD qua 3 seed. Bootstrap 1.000 lần theo `group_id` nếu còn thời gian (D14).

## Phạm vi

**D14. Phạm vi rút gọn** · 30/10 · Chốt
- Giữ: dữ liệu đóng băng 16/10, E1 và E2 (15 run), test chéo trên 3 nguồn ngoài (chỉ báo cáo như một phát
  hiện về domain shift, không điều tra thêm nguyên nhân).
- Bỏ: hiệu chỉnh µm/pixel; E4/RQ2 (Phikon); ECE.
- Thêm: baseline (đoán lớp đa số; Logistic Regression trên embedding ConvNeXt đóng băng); learning curve
  từ log từng epoch; Grad-CAM khoảng 8 ảnh (4 đúng, 4 sai).
- Kết quả chính báo mean ± SD qua 3 seed. Bootstrap theo `group_id` là tùy chọn.

## Giới hạn phải ghi trong báo cáo

1. µm/pixel của LC25000 và LungHist700 là ước lượng chưa kiểm chứng. Nhóm đã thử hiệu chỉnh bằng tế bào
   tham chiếu nhưng dừng khi hết hạn (D10, D12).
2. Phát hiện lỗi tỷ lệ sau khi đã xem kết quả xtest của run đầu.
3. Nhóm LC25000 tái dựng họ augmentation, không phải danh tính bệnh nhân.
4. BACH và CRC không có mã bệnh nhân đầy đủ; bootstrap theo `group_id` có thể chưa phản ánh hết tương quan.
5. Patch mang nhãn của ảnh gốc (nhãn yếu); đủ mô không có nghĩa có tế bào u.
6. `none` nghĩa là nhóm không áp thêm Macenko, không có nghĩa ảnh gốc chưa từng chuẩn hóa màu.
7. Nguyên nhân nhầm cơ quan ở test chéo chưa xác định (D11).

## Quy ước làm việc

- Trao đổi và review trong comment PR hoặc GitHub Issues. Kết luận cuối ghi vào file này.
- Không đưa ảnh, `data/`, checkpoint lên Git. Ảnh và checkpoint để trên Google Drive.
- Tài liệu cũ (instruct, VERIFICATION, bàn giao) xem lại qua git tag `truoc-gon-tai-lieu`.
