# Kiểm chứng phản hồi lệch tỷ lệ LC25000

Ngày kiểm tra: **24/10/2026**. Phạm vi: bản bàn giao local tại `C:\Users\Admin\Documents\FrameView\btl-histo` và tài liệu người dùng gửi, được lưu lại trong `input_request.md`.

**Kết luận: xác nhận lỗi cấu hình MPP và tái quan sát được dấu hiệu LC25000 có cấu trúc lớn hơn trên ảnh xử lý. Chưa đủ bằng chứng để chốt MPP 0,25–0,33, quy toàn bộ suy giảm test chéo cho tỷ lệ, hoặc xác nhận hoàn tất hiệu chỉnh.**

Người dùng xác nhận kết quả chạy ngày 22/10 đang ở phía người đưa phản hồi, có thể chưa có trong workspace này. Các metric của lần chạy đó được xem là số liệu được cung cấp, chưa xác minh độc lập. Bản local hiện vẫn là mốc đóng băng **2026-10-16T10:03:56.478461+00:00**.

## 1. Bằng chứng chạy trực tiếp

| Kiểm tra | Kết quả hiện tại | Ý nghĩa và giới hạn |
|---|---|---|
| SHA-256 của các file liệt kê trong FROZEN | **17/17 khớp** | Config, code và manifest local vẫn khớp mốc 16/10 |
| Ảnh raw trong `raw_checksums.csv` | **41.180/41.180 khớp**, 0 lỗi | Kiểm tra hash mới; không tuyên bố vừa giải mã lại toàn bộ ảnh |
| Ảnh xử lý trong `processed_checksums.csv` | **114.112/114.112 khớp**, 0 lỗi | Hai nhánh vẫn là dữ liệu cũ, chưa được hiệu chỉnh |
| Tính lại split trong bộ nhớ từ config/group hiện tại | **57.056 dòng, 0 khác biệt** | Đối chiếu `label,organ,source,group_id,split,split_random`; không ghi lại manifest |
| Group xuất hiện trong nhiều grouped split | **0** | Đây là kiểm tra group đã cung cấp, không chứng minh độc lập bệnh nhân tuyệt đối |
| Probe thay đổi MPP LC25000 trong config | **Lỗi được tái hiện** | Chi tiết ở mục 2 |
| Unit tests hiện tại | **11 test thành công; 1 lỗi import module grouping** | Thiếu `torch`, nên 3 test grouping chưa chạy; không công bố toàn bộ 14 test đã pass lại |

Số mẫu mỗi nhánh vẫn là 57.056: LC25000 24.949, BreakHis 1.995, LungHist700 14.557, CRC 1.974, BACH 13.581.

Chi tiết máy đọc được: `audit_results.json`. Log tests: `test_results.txt`. Script tái lập: `audit_scale.py`.

Môi trường audit dùng Python 3.12.14, numpy 2.3.5, Pillow 12.3.0, PyYAML 6.0.3, OpenCV 4.12.0.88 và threadpoolctl 3.6.0. Các thư viện bổ sung được đặt trong thư mục tạm; môi trường này khác `requirements-cpu.lock`, không phải tái lập nguyên môi trường huấn luyện. Không cài PyTorch chỉ để giải quyết phụ thuộc import của grouping trong cuộc kiểm tra này.

## 2. Lỗi `catalog.py`: xác nhận

Trong `src/data/catalog.py:34`, `collect(data, config)` gọi `make_record` cho LC25000 mà không truyền config. `make_record` tại dòng 82, 88–90 gán cứng MPP bằng 0,5 và status bằng `estimated_unverified`.

Probe dùng một cây thư mục LC25000 tạm, chỉ xét catalog, không xử lý pixel:

| `scale.LC25000.mpp` đưa vào | Status đưa vào | MPP nhận được | Status nhận được |
|---:|---|---:|---|
| 0,50 | `calibrated_rbc` | 0,50 | `estimated_unverified` |
| 0,25 | `calibrated_rbc` | 0,50 | `estimated_unverified` |
| 0,33 | `calibrated_rbc` | 0,50 | `estimated_unverified` |

Vì vậy, nhận định “chỉ sửa YAML không đổi tỷ lệ LC25000” là đúng. LungHist700 được ghi đè MPP/status từ config tại dòng 57–58; các nguồn còn lại đang dùng giá trị gán trong code. `tests/test_catalog.py` hiện chỉ có 3 test mapping/identity, chưa có test MPP hoặc status theo config.

Khi sửa, test cần kiểm tra cả `native_mpp` và `scale_status`. Riêng BreakHis phải bảo toàn ánh xạ theo từng magnification, vì catalog còn ghi nhận cả các ảnh raw 100×/200×/400× dù chúng bị loại khỏi thí nghiệm.

## 3. Đo lại chỉ báo kích thước trên ảnh cũ

Đã đọc và kiểm tra kích thước 224×224 của **750 ảnh `none`**, 150 ảnh mỗi nguồn. LC25000 lấy 30 ảnh train mỗi lớp; BreakHis lấy train 40×; các nguồn test chéo lấy trong manifest tương ứng. Seed 42, chọn từ danh sách đường dẫn đã sort.

Diễn giải thuật toán: lấy pixel kênh R nhỏ hơn hoặc bằng percentile 15 của từng ảnh, tương đương chọn vùng OD đỏ cao; thành phần liên thông 8 hướng, diện tích ít nhất 8 pixel; đường kính tương đương `2*sqrt(area/pi)`. Pool các thành phần của 150 ảnh để tính median/P75. Pixel bằng ngưỡng có thể làm mask vượt 15%.

| Nguồn | Median tài liệu (px) | Median audit (px) | P75 audit (px) | Median/CRC audit |
|---|---:|---:|---:|---:|
| LC25000 | 8,2 | **8,41** | 17,26 | **1,46×** |
| BACH | 6,5 | 6,28 | 11,91 | 1,09× |
| LungHist700 | 6,1 | 6,48 | 12,05 | 1,13× |
| CRC-VAL-HE-7K | 5,4 | 5,75 | 8,81 | 1,00× |
| BreakHis 40× | 4,7 | 4,92 | 6,77 | 0,85× |

Kết quả **cùng chiều** với dấu hiệu được báo: thành phần tối LC25000 lớn hơn CRC. Tuy nhiên đây không phải tái lập chính xác bảng ban đầu: tài liệu không cung cấp đường dẫn 150 ảnh, seed, quy tắc pooling, connectivity hoặc xác định “≥8 px” là diện tích hay đường kính. Ví dụ, median của các median từng ảnh LC25000 là 9,25 px, khác median pool 8,41 px.

Đây là **phép đo đốm tối**, không phải segmentation nhân đã được xác nhận và càng không phải phép đo hồng cầu. Khác biệt loại tế bào, tỷ lệ mô, nhuộm màu, nhân dính nhau và cách chọn mẫu đều ảnh hưởng kết quả. Không chuyển tỷ lệ 1,46× thành MPP hiệu chuẩn.

Các đường dẫn, ngưỡng, số thành phần và median từng ảnh được lưu trong `coarse_diagnostic_samples.csv`. `old_processed_contact_sheet.png` hiển thị crop cũ 224×224, không resize khi ghép; cột LC25000 có đủ 5 lớp. Đây không phải contact sheet sau hiệu chỉnh.

## 4. Phương pháp hồng cầu: cần sửa phát biểu và bổ sung bằng chứng

Phát biểu “đường kính khoảng 7,5 µm, gần như không đổi giữa các mô và bệnh viện” quá chắc đối với ảnh mô cắt. Terzakis và Santagada đo trực tiếp và ghi nhận hồng cầu trong vật liệu cắt nhỏ hơn khoảng **25–35%** so với giá trị sách giáo khoa. Nghiên cứu này không chứng minh sai số cụ thể của LC25000, nhưng đủ bác bỏ việc coi 7,5 µm là thước chuẩn tuyệt đối cho mọi nguồn. [Bài nghiên cứu, PMID 10872042](https://pubmed.ncbi.nlm.nih.gov/10872042/).

Vì vậy:

1. Công thức `mpp = 7,5/median(diameter_px)` chỉ cho ước lượng dưới giả định kích thước hồng cầu thực tế phù hợp. Không được gắn `calibrated_rbc` trước khi có bằng chứng kiểm chứng.
2. Giữ điều kiện kiểm chứng từng nguồn CRC/BACH/BreakHis: `abs(mpp_est/mpp_published - 1) <= 0,15`. Báo riêng sai số của cả ba, không lấy trung bình để che nguồn không đạt. Qua điều kiện này vẫn chưa chứng minh sai số chuyển giao sang LC25000 cũng ≤15%.
3. Nếu chuyển sang lympho, phải định nghĩa rõ đo đường kính tế bào hay nhân và dùng giả định kích thước tương ứng. Không dùng nguyên hằng số 7,5 cho phép đo lympho 7 µm, không trộn hai loại đường kính vào một median.
4. Mỗi nguồn cần ít nhất 30 tế bào từ ít nhất 15 ảnh. Với LC25000 nên lấy các train group khác nhau để giảm việc đo lặp cùng tế bào qua biến thể augmentation, bao phủ cả phổi và đại tràng. LungHist700 cần kiểm tra riêng 20× và 40×.
5. Ngoài 4 cột tối thiểu được yêu cầu, nên giữ tọa độ hai đầu phép đo, người đo, loại tế bào, group, magnification và ảnh đánh dấu để người khác kiểm tra được. Hiện chưa có các annotation này, không có phép đo vật lý nào được tự tạo để điền cho đủ số lượng.

Nguồn sơ cấp xác nhận các giá trị đối chứng:

- CRC-VAL-HE-7K: 224×224 ở **0,5 MPP**. [Record của tác giả](https://zenodo.org/records/1214456).
- BACH microscopy: 2048×1536, **0,42 µm/pixel**. [Bài BACH, mục 2.2.1](https://arxiv.org/pdf/1808.04277).
- BreakHis 40×: objective 4×, effective pixel size **0,49 µm**, Table I. [Bài BreakHis](https://www.inf.ufpr.br/lesoliveira/download/TBME-00608-2015-R2-preprint.pdf).

Bài LC25000 xác nhận ảnh gốc thu nhận được crop từ 1024×768 thành 768×768, rồi tăng cường bằng Augmentor; không đưa MPP định lượng trong bài. “Raw” trong workspace là ảnh trước pipeline của nhóm, không đồng nghĩa ảnh gốc chưa augmentation. Không có căn cứ từ bài này để chốt 0,25–0,33 MPP. [Bài LC25000](https://arxiv.org/pdf/1912.12142).

LC25000 có bằng chứng biến dạng hai trục trong bộ test grouping đã tồn tại, nhưng phép resize đẳng hướng theo một MPP trung vị không khôi phục hết biến dạng affine từng ảnh. Nếu dùng một hệ số nguồn, phải báo đây là hiệu chỉnh quy mô điển hình với giới hạn còn lại.

## 5. Các kết luận về model cần hạ mức khẳng định

| Nội dung phản hồi | Kết quả kiểm chứng |
|---|---|
| CRC có 1.233 TUM và 741 NORM | **Khớp manifest local** |
| BreakHis benign có 436 ảnh train | **Khớp manifest local** |
| 1.205 TUM và 702 NORM bị đoán breast_malignant | Chưa xác minh tử số; cần predictions từ người phản hồi |
| Tỷ lệ nhầm cơ quan 97%/84% và toàn bộ bảng accuracy | Chưa xác minh; không có predictions/logits/log local |
| Test nội bộ không nhầm cơ quan nên code train/predict không lỗi | **Suy luận không hợp lệ**: kết quả nội bộ không loại trừ mapping/loader/transform sai riêng ngoại miền |
| Suy giảm chủ yếu do tỷ lệ, RQ1 mất ý nghĩa | **Chưa được chứng minh** từ một lần chạy và chỉ báo đốm tối; scale là một nhiễu khả dĩ cạnh stain, nguồn thu nhận, thành phần mô và nhãn patch |
| 15 lần chạy lại mất 6 giờ GPU | Chưa xác minh; không có config chạy, log timing hay thông tin GPU tại đây |

Nếu chấp nhận hai tử số được báo, `(1205+702)/1974 = 96,61%` ảnh CRC được dự đoán riêng là breast_malignant; phép tính phù hợp mức làm tròn khoảng 97%, nhưng không xác minh bản thân dự đoán hoặc toàn bộ lỗi cơ quan.

Metric “accuracy trong cơ quan đúng” phù hợp làm chẩn đoán bổ sung: với mỗi mẫu, chỉ lấy argmax logits/probabilities trong các lớp thuộc **cơ quan thật**; lung={0,1,2}, colon={3,4}, breast={5,6}; mẫu số là toàn bộ mẫu đang đánh giá. Đây là đánh giá có thông tin cơ quan thật, không phải hiệu năng triển khai khi cơ quan chưa biết. Không nhầm nó với accuracy chỉ trên các mẫu mà argmax 7 lớp đã đoán đúng cơ quan. Cần logits/probabilities đầy đủ, không tính lại được metric này từ hard prediction một lớp.

## 6. Những thiếu sót trong quy trình sửa/sinh lại/đóng băng

1. **Sao lưu trước bước sinh lại ảnh.** `prepare.py` ghi đè `inventory.csv`, các split CSV, `reference.json` và một số báo cáo. Giữ riêng `FROZEN.json` ở bước 6 là quá muộn để giữ nội dung manifest cũ phục vụ so sánh nếu trước đó chưa snapshot. Hash cũ không khôi phục được CSV cũ. Cần giữ cả manifest mở rộng, hai manifest model, config, reference, grouping/quarantine và quyết định cũ trước bước 5.
2. `prepare.py:160` gọi lại `assign_splits`. Với cấu hình hiện tại, phép đối chiếu trong bộ nhớ cho 0 thay đổi. Tuy vậy phải dùng phép so sánh với snapshot để chặn drift khi hiệu chỉnh; tính tái lập theo seed không thay cho đối chiếu baseline.
3. Bộ lọc mô <50% tại `prepare.py:114` chỉ áp dụng cho LungHist700/BACH. LC25000/BreakHis center crop không bị bộ lọc này loại ảnh trong code hiện tại. Vì vậy nếu số ảnh nội bộ thay đổi, cần điều tra nguyên nhân khác.
4. `choose_reference` không khóa cứng `colonca1.jpeg`: nó chọn ứng viên train đầu tiên qua kiểm tra mô ≥70% và fit được. Tỷ lệ mới có thể làm ứng viên khác được chọn. Profile tham chiếu thực tế được fit từ **toàn ảnh đã resize**, không chỉ crop center 224. Muốn giữ đúng `colonca1.jpeg` phải kiểm tra/khóa rõ và kiểm tra chất lượng; không tự động khẳng định nó sẽ giữ nguyên.
5. Fingerprint có config, reference SHA, `stain.py` và `prepare.py`, **không có `catalog.py`**. Trong quy trình đề xuất, thay YAML sẽ đổi fingerprint; nhưng chỉ sửa catalog có thể không đổi fingerprint nếu các đầu vào khác không đổi. Cần kiểm tra đường dẫn mới và scale metadata thực tế.
6. `validate.py --freeze` hiện không kiểm tra phương pháp hiệu chuẩn, ngưỡng sai số 15%, chốt hệ số trước model, đối chiếu 6 cột với snapshot, hoặc chỉ báo kích thước sau sửa. Nó còn ghi cứng giới hạn MPP chưa hiệu chuẩn trong kết quả. Vì vậy freeze thành công không tự chứng nhận hoàn tất tài liệu; cập nhật logic trạng thái theo bằng chứng thực tế, không xóa giới hạn LungHist700 nếu vẫn chưa đo.
7. Yêu cầu “mọi nguồn có median nhân 0,85–1,15× CRC” không phải tiêu chuẩn vật lý phổ quát, vì các loại mô/tế bào khác nhau. Có thể giữ như chỉ báo QA cần điều tra, so cặp cùng loại mô và annotation xác nhận, nhưng không được chỉnh MPP để ép đạt tỷ lệ này. BACH/BreakHis phải giữ MPP công bố dù heuristic không đạt.
8. Cần cho phép các trường dẫn xuất hợp lệ như image paths, crop coordinates, reference và fingerprint đổi theo scale, trong khi 6 trường identity/split bắt buộc giữ nguyên. Với nguồn nhiều patch, so metadata theo source image và so số patch riêng; không giả định `source_image_path` là khóa duy nhất của mỗi dòng mẫu.
9. Bước 7 không chạy được trong bản C1–C3 này: chưa có `configs/runs`, `src/train/train.py` hay `tests/test_train_configs.py`. Chưa thể xác nhận “code train không cần sửa”. Khi C4 chạy phải kiểm tra hợp đồng loader và transform thực tế. Vòng lặp shell trong tài liệu dùng cú pháp Bash, không chạy nguyên văn trong PowerShell của workspace.

## 7. Đối chiếu 7 tiêu chí hoàn thành

| # | Tiêu chí tài liệu | Trạng thái ở bản local |
|---:|---|---|
| 1 | `scale_calibration.csv`, ≥30 phép đo mỗi nguồn | **Chưa đạt** — file chưa có; chưa có annotation hồng cầu/lympho |
| 2 | Sai số phương pháp ≤15% trên CRC/BACH/BreakHis | **Chưa kiểm chứng** — chưa có phép đo vật lý |
| 3 | Hệ số mới trong C1_DECISIONS trước khi chạy model | **Chưa đạt** — tài liệu vẫn ghi LC25000 0,5 chưa hiệu chuẩn |
| 4 | Catalog đọc config, có test đi kèm | **Chưa đạt** — lỗi gán cứng được tái hiện, test yêu cầu chưa có |
| 5 | Nhãn/nhóm/split giống mốc 16/10 | **Mốc cũ còn nguyên**; chưa có bản hiệu chỉnh để nghiệm thu so sánh trước–sau |
| 6 | Chỉ báo nhân sau xử lý trong 0,85–1,15× CRC | **Chưa đạt ở ảnh cũ** — LC25000 khoảng 1,46×; chưa có ảnh mới; tính hợp lệ của tiêu chí cần sửa như mục 6.7 |
| 7 | FROZEN mới và giữ FROZEN_2026-10-16 | **Chưa đạt** — FROZEN vẫn ngày 16/10; chưa có bản sao theo tên yêu cầu |

Việc chưa có file hiệu chỉnh ở một bản bàn giao cũ không chứng minh người phản hồi bịa số liệu; nó giới hạn phạm vi nghiệm thu tại máy này.

## 8. Điều kiện để tiếp tục

Nên xử lý lỗi config đã xác nhận và hoàn thiện phương pháp/annotation trước khi chốt hệ số. Không chọn 0,25 hoặc 0,33 chỉ vì các giá trị này có vẻ làm hình giống CRC hoặc tăng accuracy. Nếu phép đo sinh học không qua kiểm chứng, ưu tiên metadata hệ chụp/thước chuẩn hoặc thông tin hiệu chuẩn từ người cung cấp dữ liệu; giữ trạng thái chưa hiệu chuẩn nếu chưa có căn cứ.

Sau khi có hệ số được chốt độc lập với model: snapshot baseline, sửa catalog và test, sinh ảnh ở fingerprint mới, kiểm tra các bất biến và ảnh thực tế, cập nhật giới hạn/decision/handoff, rồi mới freeze và bàn giao C4. Thông tin “đã xem kết quả test chéo để phát hiện vấn đề” phải được giữ trong báo cáo; chạy lại không làm tập test đó trở lại trạng thái chưa từng được xem.

Trong cuộc kiểm chứng này **không sửa code/config sản xuất, không sinh lại dataset, không đổi split/group/nhãn, không ghi đè FROZEN và không chạy model**. Đầu ra mới chỉ là thư mục bằng chứng audit này. Kiểm tra cuối script xác nhận 17 file được đóng băng không đổi trong suốt quá trình.
