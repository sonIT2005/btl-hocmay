# Bàn giao đối chiếu instruct2 — LC25000 / MPP / chuẩn bị chạy lại

Ngày: **25/10/2026**. Cập nhật sau hợp nhất: code/metadata/tài liệu ở `btl-hocmay`; FrameView chỉ còn dataset. Xem [WORKSPACE_LAYOUT.md](WORKSPACE_LAYOUT.md). Đối tượng nhận: C3, C4, C5 và nhóm trưởng. Trạng thái: **đã sửa code và chuẩn bị bằng chứng; chưa nghiệm thu ước lượng MPP, chưa cho rằng đã hoàn thành toàn bộ instruct2**.

## 1. Có thể đáp ứng yêu cầu ban đầu không?

**Có thể thực hiện quy trình mà instruct2 yêu cầu, nhưng hiện chưa có đủ dữ liệu để bảo đảm nhánh “ước lượng MPP mới thành công → sinh lại ảnh → chạy lại 15 run”.** Phần kỹ thuật đã có code và kiểm tra. Phần còn thiếu chính là tế bào tham chiếu đủ tin cậy, đủ cỡ mẫu và kiểm tra độc lập; một số bằng chứng chỉ C4 đang giữ.

Phân biệt ba kết luận:

- **Quy trình có thể hoàn thành:** đo đúng đối tượng, kiểm chứng ba nguồn, ghi nhận kết quả và thực hiện nhánh đạt/không đạt đã chốt.
- **Ước lượng MPP mới thành công:** chưa biết; phải có số đo hợp lệ và sai số leave-one-source-out ≤15% ở từng nguồn. Không hứa trước hệ số 0,25 hay 0,33.
- **Cải thiện test chéo sau khi đổi MPP:** chưa chứng minh và không phải điều kiện để chọn hệ số. Không được chọn MPP theo accuracy/F1 ngoài miền.

Pilot hiện tại **chưa đủ điều kiện phân tích**, không phải đã kiểm định và loại phương pháp. Nếu sau khi đủ mẫu, đo bổ sung đúng một lần lên 60 tế bào/nguồn mà vẫn không đạt, instruct2 cho phép giữ `estimated_unverified` và MPP cũ. Khi đó nhóm phải ghi nhận nhánh không đạt và quyết định việc tiếp tục thí nghiệm; không đánh dấu như đã hiệu chỉnh thành công hoặc đã có dữ liệu mới.

Người dùng đã đồng ý xem xét đổi MPP/sinh ảnh khi bằng chứng đủ tốt. Hiện điều kiện bằng chứng đó chưa đạt; không cần xin lại quyền khảo sát hay sửa lỗi kỹ thuật đã được giao.

## 2. Các mốc và đường dẫn cần giữ đúng

| Thành phần | Vị trí / mốc |
|---|---|
| Ảnh/dataset | `C:\Users\Admin\Documents\FrameView\btl-histo\data` |
| Git checkout C4 chứa code đã sửa | `C:\Users\Admin\Documents\GitHub\btl-hocmay` |
| Freeze đang dùng | 16/10/2026; fingerprint `f5c641abf5b155b1` |
| SHA-256 FROZEN.json | `1d777e01cc4f30a860458e85e998d2f44698450bfa419b1ec0b9c8c9d59693c1` |
| Snapshot canonical đầy đủ | `C:\Users\Admin\Documents\GitHub\btl-hocmay\snapshots\2026-10-16` |
| Bộ đo chính thức đã khóa | `outputs/maintenance_2026-10-25/mpp_kit` trong repo |
| Pilot ban đầu | `outputs/mpp_pilot_2026-10-25` trong repo |
| Bằng chứng và gói rà ảnh mới | `outputs/handoff_2026-10-25` trong repo |

Snapshot được **tạo ngày 25/10**, lưu trạng thái frozen 16/10; tên thư mục không có nghĩa đã chụp snapshot từ ngày 16/10. Đã sao lưu và đối chiếu SHA-256 **50 file, 65.533.092 byte** thuộc `splits`, `configs`, `results`, `src`, `tools`. Có `SHA256SUMS.csv` và `SNAPSHOT.json`. Không sao chép thêm dataset; ảnh cũ tiếp tục ở vị trí canonical. Snapshot này là cây C1–C3, không tự nhận là snapshot đầy đủ môi trường train/checkpoint C4.

**Repo `btl-hocmay` hiện là root code, config, split và tài liệu duy nhất. FrameView chỉ còn `btl-histo/data`.** Code đang dùng đã tích hợp data_root riêng; snapshot giữ code/config nguyên byte của freeze cũ. Không chạy entrypoint từ snapshot/staging để thay cho code hiện hành.

## 3. Ma trận đáp ứng các yêu cầu trong instruct2

| Yêu cầu | Trạng thái hiện tại | Còn thiếu / điều kiện hoàn tất | Chủ việc tiếp theo |
|---|---|---|---|
| Bước 0: snapshot đầy đủ + SHA | **Đã có** snapshot canonical 50 file; ảnh cũ giữ tại chỗ | Trước regenerate kiểm lại snapshot còn khớp; C4 lưu riêng recipe/log/predictions/checkpoint cũ | C3, C4 |
| Xác minh bằng chứng run đầu | **Đã tính lại** accuracy 7 lớp, nhầm cơ quan, mẫu số và mapping từ 34.156 dòng predictions | Restricted accuracy chính xác cần scores đầy đủ; chưa tái chạy checkpoint/chẩn đoán | C4 gửi scores hoặc checkpoint; C3 đối chiếu |
| Tìm metadata hệ chụp LC25000 | **Đã tìm được** camera, kính, vật kính, độ phân giải trong bài thu nhận liên quan | Chưa có MPP hoặc calibration đủ để suy MPP duy nhất | C4/nhóm xác nhận với tác giả nếu cần |
| Bước 1: đủ tế bào đúng loại, raw, tọa độ, H/V | **Chưa đạt**; có kit và biểu mẫu; không có tế bào được chấp nhận chính thức | ≥30 tế bào / ≥15 ảnh mỗi nguồn; tối đa 3 tế bào/ảnh; điền đủ H/V | C3 đo, thành viên khác rà |
| ≥20% tế bào kiểm tra độc lập | **Chưa có** | Người khác C3 xem mẫu tế bào được chọn ngẫu nhiên, xác nhận danh tính + biên, ghi tên | Nhóm chỉ định người rà |
| Bước 2: LOO ≤15% từng nguồn | **Chưa thể tính hợp lệ** | Cùng marker, đủ mẫu, đủ review; nếu sai số vượt ngưỡng mở rộng một lần lên 60 tế bào/nguồn | C3 |
| Bước 3: MPP LC + CI 95%, IQR, méo hai trục | **Chưa có hệ số**; analyzer/bootstrap và công cụ xuất H/V đã chuẩn bị | Đối chứng đạt trước; LC train, mỗi group tối đa một ảnh, ≥15 tế bào phổi và ≥15 đại tràng | C3 |
| LungHist700 20× / 40× riêng | **Chưa đo**, giữ 0,5 / 0,25 và trạng thái unverified | Chỉ sửa nhánh có bằng chứng lệch >15%; ghi rõ nếu chưa làm | C3 |
| Bước 4: C1_DECISIONS, người duyệt | **Chưa chốt MPP** | Kết quả đo thật, CI, bảng LOO, tên người đo/rà và nhóm duyệt | C3, nhóm trưởng |
| Catalog đọc MPP/status từ config | **Đã sửa, có test** ở C4 | Review/commit các source mới; root code/data đã tích hợp và kiểm bằng preflight | C3/C4 |
| Fingerprint tính catalog/scale, tránh ghi đè | **Đã sửa, có test** | Chưa có fingerprint sản phẩm mới vì chưa regenerate | C3 |
| Validate ghi giới hạn từ trạng thái | **Đã sửa** | Freeze chỉ chứng nhận tính toàn vẹn, không chứng nhận MPP đúng | C3 |
| Bước 6: sinh ảnh fingerprint mới | **Chưa thực hiện** | MPP được chốt, snapshot còn khớp; chạy code repo với đúng data_root và opt-in regeneration | C3 |
| Bước 7: so 6 trường theo ảnh nguồn + số lượng | **Mốc cũ không đổi**; đã có snapshot để so | Chưa có dữ liệu mới để kiểm tra phép chuyển đổi | C3 |
| Chỉ báo QA nhân / contact sheet sau regenerate | Có pilot/raw contact sheet; **chưa có QA sau regenerate** | Làm sau khi sinh ảnh, không chọn MPP theo mức gần CRC | C3 |
| Toàn bộ tests có PyTorch | **37/37 đạt** trước hợp nhất; **42/42 đạt** sau tích hợp đường dẫn | Chạy lại nếu sửa code tiếp; rerun trước nghiệm thu dữ liệu mới | C3/C4 |
| Loader/mapping ngoài miền | **Đã kiểm trên dữ liệu cũ**, thêm audit predictions không sai mapping | Kiểm lại trên dữ liệu mới sau regenerate | C3/C4 |
| Provenance fingerprint/FROZEN trong run | **Đã bổ sung code** | Chưa có run mới tạo log/checkpoint theo contract mới | C4 |
| Bước 8: nghiệm thu và thông báo chạy lại | **Chưa có** | Bộ bằng chứng sau đo/regenerate hoặc quyết định rõ nhánh thất bại | Người rà, nhóm trưởng |
| Bước 9: 15 run trên cùng freeze | **Chưa chạy lại**; có preflight/smoke tách outputs | Nghiệm thu, môi trường GPU thật đạt, lưu run cũ; không tự bỏ tạm dừng | C4 |
| Gộp cấp ảnh và metric theo cơ quan | Đã kiểm metric patch; **chưa gộp cấp ảnh** | C5 chốt cách gộp/đơn vị và báo cáo | C5 |

**Không thể đánh dấu toàn bộ checklist hoàn thành chỉ bằng số lượng code đã sửa hoặc lệnh freeze thành công.**

## 4. Kết quả run đầu đã xác minh lại

Nguồn: bốn CSV `outputs/predictions/e2_convnext_group_none_s0__*.csv` trong Git checkout C4. Mẫu số là **toàn bộ mẫu của từng tập**, không lọc riêng các mẫu đã đoán đúng cơ quan.

| Tập | Số mẫu | Số ảnh raw | Đúng 7 lớp | Accuracy 7 lớp | Nhầm cơ quan | Accuracy trong cơ quan đúng từ CSV làm tròn |
|---|---:|---:|---:|---:|---:|---:|
| Test nội bộ | 4.044 | 4.044 | 3.722 | 0,920376 | 0 / 4.044 = 0% | 0,920376 |
| LungHist700 | 14.557 | 691 | 5.587 | 0,383802 | 4.273 / 14.557 = 29,3536% | 0,489387 |
| CRC-VAL-HE-7K | 1.974 | 1.974 | 49 | 0,024823 | 1.914 / 1.974 = 96,9605% | 0,734043 |
| BACH | 13.581 | 400 | 847 | 0,062367 | 11.452 / 13.581 = 84,3237% | 0,501951 |

Đã đối chiếu từng `image_path`, `true_label`, `group_id`, danh sách mẫu mong đợi và mapping từ nhãn raw: **0 thiếu, 0 dư, 0 trùng, 0 lỗi nhãn/group/mapping**. Argmax 7 lớp từ probabilities đang lưu cũng khớp `pred_label` ở mọi dòng.

### Câu diễn giải cần sửa

Câu “CRC và BACH hầu hết bị đoán thành vú” trong phần tóm tắt instruct2 **không đúng với BACH**:

- CRC: 1.907 mẫu đoán là vú, 60 là đại tràng, 7 là phổi. Phần “hầu hết thành vú” phù hợp cho CRC.
- BACH vốn là mô vú: **2.129 mẫu đoán là vú (15,6763%)**, **6.911 là phổi**, **4.541 là đại tràng**. 84,3237% là nhầm *ra khỏi* cơ quan vú.

### Giới hạn do xác suất làm tròn

CSV cũ có probabilities làm tròn 6 chữ số thập phân. Restricted argmax lấy giá trị lớn nhất chỉ trong các lớp của cơ quan thật; khi các xác suất đó rất nhỏ, làm tròn có thể đổi thứ hạng. Các giá trị 0,734043 và 0,501951 tính lại được từ CSV nhưng chưa chứng minh đúng bằng scores gốc.

Khoảng dưới đây là **giới hạn bảo thủ do lượng tử hóa ±0,5×10⁻⁶ mỗi xác suất**, không phải CI thống kê và không phải khoảng sai số của mô hình:

| Tập | Restricted accuracy khả dĩ theo giới hạn làm tròn |
|---|---:|
| Test nội bộ | 0,920376–0,920870 |
| LungHist700 | 0,489112–0,489730 |
| CRC | 0,728470–0,747214 |
| BACH | 0,499816–0,503939 |

C4 cần xuất probabilities đầy đủ hoặc logits từ checkpoint cũ vào thư mục mới. Máy local hiện **không có checkpoint gốc**, nên chưa thể hoàn tất phần xác minh này hoặc tái chạy các perturbation trong mục 2.3. Không cần train lại chỉ để khôi phục precision. Việc kiểm đúng nhãn và tensor không chứng minh chẩn đoán về nguyên nhân domain shift đã đầy đủ.

## 5. MPP: đã làm gì và đang thiếu gì

### Pilot và mở rộng hàng đợi

- Pilot: 30 raw, 10 mỗi nguồn; 10 vùng pixel được đo thử. Có 5 vùng bị loại khỏi vai trò tham chiếu và 5 ứng viên cần nhận diện lại. **0 tế bào được chấp nhận chính thức**.
- Một thước thủ công nháp bị lệch tọa độ khi QA; toàn bộ thước nháp được loại khỏi phân tích. Các thước vùng mask thay thế chỉ là hình học pixel có thể tái lập. Không đưa chúng vào phép ước lượng MPP và không coi đường kính đốm ngưỡng là đường kính tế bào thật.
- Đã chuẩn bị **180 ảnh đối chứng**, 60 mỗi nguồn, cùng hàng đợi/seed đã chốt, kèm 18 contact sheet. Kiểm SHA-256 **180/180 đạt**.
- Đã mở sàng lọc **tổng quan 100 ảnh**: CRC 1–20, BACH 1–20, BreakHis 1–60. Đây là sàng lọc bối cảnh mô, không phải xác nhận danh tính/biên của từng tế bào. 180 ảnh chuẩn bị không được ghi thành 180 ảnh đã đo.
- Kit chính thức vẫn 0 dòng đo. Chạy kiểm lại riêng `rbc` và `lymph_nucleus` đều trả **`incomplete`**, không có LOO hay MPP được phát hành.

Chưa thể kết luận hồng cầu/lympho hoàn toàn không có trong nguồn hoặc phương pháp chắc chắn thất bại. Việc chưa xác nhận được marker không được thay bằng giá trị mặc định 7,5 µm, phép đo mọi loại nhân, hay hệ số mong muốn.

### Gói người đo / người rà cần dùng

Trong repo, tại `outputs/handoff_2026-10-25/review_pack`:

| File | Cách dùng |
|---|---|
| `control_queue.csv` | 180 ảnh có ID, path raw, group và SHA, theo đúng thứ tự |
| `*_01_10.png` đến `*_51_60.png` | Điều hướng tìm bối cảnh; **không đo trên thumbnail** |
| `overview_screening_log.csv` | Dấu vết 100 ảnh chỉ mới xem tổng quan |
| `pilot_identity_requests.csv` | 5 ứng viên cần xác nhận/loại; phải vẽ lại đường đo tế bào thật, không chỉ duyệt mask |
| `image_review_return.csv` | Ghi ảnh có/không có đối tượng đạt tiêu chí, người rà và lý do; hiện pending |
| `scale_calibration_TEMPLATE.csv` | Biểu mẫu trống đủ trường instruct2, có ID để nối lại kit |

Người đo mở **ảnh raw thật** bằng viewer có tọa độ pixel, nhận diện tế bào trước khi đo. Ghi đường kính dài nhất, đường kính theo H/V, tên người đo và ghi chú. Nếu không đủ hồng cầu, nhân lympho phải đo riêng trên cả ba nguồn; không trộn hai loại.

Người kiểm tra phải khác C3/người đo, rà ít nhất 20% **tế bào** được chọn ngẫu nhiên theo kit; không thay bằng 20% ảnh tổng quan. Instruct2 **không bắt buộc có bác sĩ giải phẫu bệnh**: nhóm có thể cử thành viên nhận diện được marker làm kiểm tra độc lập và ghi hạn chế không có bác sĩ. Hiện chưa có người rà được ghi tên hoặc kết quả rà để nhận về.

Sau khi có số đo thật, nối `candidate_id` với kit, chuyển các cột đo vào `measurements.csv`, cập nhật `image_review.csv`. Không sửa nội dung protocol/candidates đã khóa. Giữ các hàng bị người rà loại kèm tên/lý do và đo mẫu thay thế theo cùng tiêu chí.

### Bổ sung để đáp ứng đúng trường H/V và file bàn giao

`tools/measure_mpp.py` hiện cho H/V trống, nên chỉ dùng kết quả analyzer chưa đủ để tuyên bố đã đáp ứng phần méo hai trục của instruct2. Đã bổ sung **wrapper bàn giao** `export_verified_mpp.py` trong thư mục bàn giao này:

- Tái dùng kiểm tra kit, cỡ mẫu, review và LOO của tool hiện tại.
- Chặn xuất bảng khi còn thiếu H/V; không tự điền H/V từ đường kính hoặc bbox mask.
- Khi bộ đo đủ điều kiện mới xuất `scale_calibration.csv` đúng các trường instruct2 và `axis_ratio_summary.json` có phân bố H/V theo stratum.
- Không tự sửa config, ký tên người rà, tạo tế bào giả hoặc phê duyệt thí nghiệm.

Đã kiểm trên kit thật đang trống: cả hai marker trả `incomplete`, không xuất bảng hiệu chỉnh. **Nhánh xuất bảng có dữ liệu thật chưa được chạy**; phải kiểm tra đầu ra khi nhận đủ số đo.

### Quy tắc quyết định giữ nguyên

1. Mỗi đối chứng ≥30 tế bào / ≥15 ảnh, tối đa 3 tế bào/ảnh; cùng marker.
2. Lấy trung vị theo ảnh, rồi theo nguồn; nhân MPP công bố CRC 0,5, BACH 0,42, BreakHis 40× 0,49 để có `d_s`.
3. LOO: tham chiếu bỏ một nguồn là trung bình `d` hai nguồn còn lại; `mpp_hat_s = d_ref(-s) / px_s`. **Từng nguồn riêng** phải sai số ≤15%.
4. Không đạt mới mở rộng một lần lên 60 **tế bào**/nguồn. Việc đã chuẩn bị 60 **ảnh** không phải đã hoàn thành bước mở rộng này.
5. Đối chứng đạt mới đo LC train, mỗi group tối đa một ảnh, đủ cả phổi/đại tràng. Tính bootstrap 2.000 lần theo ảnh, CI 95%, IQR và phân bố H/V. CI không bao hàm sai nhận dạng hay thiên lệch kích thước tế bào giữa nguồn.
6. LungHist700 xét riêng 20× và 40×; không sửa chỉ vì LC có hệ số mới. Trạng thái sau ước lượng bằng tế bào là `estimated_reference_cell`, không gọi `calibrated`.

## 6. Thông tin hệ chụp đã tìm được

Bản toàn văn trên trang nhà xuất bản của nghiên cứu thu nhận ảnh liên quan ghi: **Leica MC190 HD**, **Olympus BX41**, **vật kính khô 60×**, ảnh **1024×768**, phần mềm Leica Acquire 9072. [Nguồn: Borkowski et al., Federal Practitioner 2019, Methods](https://www.mdedge.com/fedprac/avaho/article/209325/health-policy/comparing-artificial-intelligence-platforms/page/0/1).

Điều này giải quyết được phần “tìm model kính/vật kính/camera”, dù PMC vẫn bị CAPTCHA. **Chưa giải quyết được MPP.** Chỉ số vật kính 60× không xác định duy nhất µm/px của ảnh phân phối; còn thiếu hiệu chuẩn hoặc thông tin đầy đủ về đường quang, cách đọc camera, xử lý kích thước và liên hệ chính xác với ảnh LC25000 cuối cùng. Không tự suy 0,25–0,33 từ tên vật kính.

Nếu dùng kênh tác giả, cần hỏi: MPP x/y của ảnh gốc và ảnh LC25000 phân phối; calibration/scale bar hoặc kích thước trường nhìn; camera adapter/binning; crop/resize trước và sau augmentation. **Chưa gửi email hay liên hệ ai.**

## 7. Code và khả năng chạy model

Đã sửa trong checkout C4: config-driven MPP/status; mapping BreakHis theo độ phóng đại; fingerprint gồm catalog/scale; chặn regenerate mặc định và trùng fingerprint; giữ split cũ; validate sinh giới hạn theo trạng thái; provenance run/checkpoint; export probabilities đủ precision và tránh ghi đè; preflight và smoke tách outputs.

Bằng chứng hiện có:

- Trước hợp nhất **37/37 unit tests đạt**. Sau tích hợp data_root, đã chạy lại **42/42 tests đạt**, không skip, gồm fixture ảnh thật và 5 test resolver. Môi trường Torch CPU 2.7.1; log mới ở `outputs/reorganization_2026-10-25/tests.txt`. Hash code trước hợp nhất được giữ trong backup; không coi nó là hash code hiện hành.
- ConvNeXt và Swin đều đã forward CPU trọng số ngẫu nhiên, logits `[2,7]` hữu hạn; tensor loader khớp đọc PNG trực tiếp cho cả năm nguồn. Đây không phải train thử hay xác minh CUDA.
- **64/64 file được bảo vệ không đổi**, **17/17 file mốc FROZEN được giữ nguyên byte trong snapshot**. Dữ liệu vẫn giữ nguyên nhãn, organ, source, group_id, split, split_random và 51 ảnh cách ly.
- `git diff --check` kiểm lại đạt. Có source mới chưa tracked, đặc biệt `src/data`, `src/train/provenance.py` và các tools/tests/docs mới. **Chưa commit/push/stage**; cần đưa đủ source mới vào commit khi review xong.
- Máy có GPU vật lý không đồng nghĩa runtime đang dùng có CUDA. Chưa chạy GPU smoke, optimizer hoặc 15 run; chưa chứng minh thời gian chạy tại máy này bằng 6–7 giờ C4 ước tính.

### Điểm triển khai cần lưu ý trước regenerate

`prepare.py` và `validate.py` hiện dùng root repo cho code/config/manifest, còn ảnh được đọc qua data_root riêng. Đã bổ sung `--data-root` và resolver chung (`BTL_DATA_ROOT` hoặc `configs/paths.local.json`). Vì vậy có thể chạy đúng code trong repo để dùng dataset FrameView mà không copy/junction. Guard regeneration vẫn giữ; không chạy source lịch sử từ snapshot.

Lệnh regenerate mới có guard `--allow-regenerate`; lệnh trần trong instruct2 sẽ bị chặn trên cây đã freeze. Không dùng `--catalog-only` để thử vì nó cũng có thể ghi inventory. Không chạy lại `group_lc.py`.

Sau regenerate phải có fingerprint mới, giữ thư mục ảnh cũ. So bất biến **theo `source_image_path`**, không so từng dòng patch: sáu trường phải duy nhất theo ảnh và khớp snapshot; LC/BreakHis giữ số ảnh mỗi split; BACH/Lung so số patch theo ảnh nguồn nếu MPP chính nguồn đó đổi. Macenko dùng đúng quy tắc chọn reference tự động, ghi lại nếu ảnh reference thay đổi. Chỉ sau QA và kiểm invariants mới freeze mới và cập nhật C1_DECISIONS/HANDOFF.

## 8. Lệnh chuẩn bị tiếp theo

Các lệnh dưới đây dành cho Python có đúng dependency của dự án, không hàm ý môi trường CUDA đã đạt. Dùng tên output **mới** mỗi lần để giữ lịch sử.

### Khi nhận số đo thật

```powershell
$root = 'C:\Users\Admin\Documents\GitHub\btl-hocmay'
$kit = "$root\outputs\maintenance_2026-10-25\mpp_kit"
$repo = 'C:\Users\Admin\Documents\GitHub\btl-hocmay'
Set-Location $repo

# Chỉ sau khi đã điền số đo tế bào thật và trạng thái ảnh/review.
python "$root\outputs\handoff_2026-10-25\export_verified_mpp.py" `
  --kit $kit --cell-type rbc --stage initial `
  --out "$root\outputs\handoff_2026-10-25\measurement_rbc_v1"
python tools/measure_mpp.py render --kit $kit --cell-type rbc `
  --data-root 'C:\Users\Admin\Documents\FrameView\btl-histo\data' --out "$root\outputs\qa\scale\rbc_v1"
```

Nhánh lympho chạy riêng với `--cell-type lymph_nucleus` và output khác. Nếu LOO yêu cầu mở rộng, bổ sung thật lên 60 tế bào/nguồn rồi dùng `--stage expanded`; không sửa số đếm trong report để qua điều kiện. File CSV xuất từ wrapper chỉ là đầu ra để review; chốt kết luận bằng toàn bộ bảng LOO, review và quyết định nhóm.

### Nếu cần kiểm hạ tầng model

```powershell
Set-Location $repo
$data = 'C:\Users\Admin\Documents\FrameView\btl-histo\data'
$splits = "$root\splits"
$cfg = 'configs/runs/e2_convnext_group_none_s0.yaml'
python tools/check_training.py $cfg --data-root $data --splits-dir $splits `
  --tensor-check --forward --device cpu
```

GPU preflight/smoke chỉ thử hạ tầng, output riêng, không dùng kết quả chọn MPP hay thay nghiên cứu. Hiện các run nghiên cứu vẫn tạm dừng. Khi đến lượt GPU, làm theo `docs/MPP_AND_SMOKE.md`: kiểm CUDA thật, forward CUDA rồi `--smoke --num-workers 0` ở thư mục trial mới. Không tự chạy vòng 15 run trước nghiệm thu.

### C4 xuất lại probabilities cũ

```powershell
python -m src.train.predict $cfg --data-root $data --splits-dir $splits `
  --checkpoint outputs/checkpoints/e2_convnext_group_none_s0.pt `
  --allow-legacy-checkpoint --output-root outputs/trials/legacy_full_precision_v1
```

Lệnh này cần checkpoint gốc trên máy C4. Sidecar legacy không tự chứng minh nguồn gốc checkpoint; phải đối chiếu đúng recipe/data cũ. Không ghi đè CSV đã dùng trong báo cáo. Gửi lại scores đầy đủ cho C3 tính restricted accuracy; C5 xử lý gộp cấp ảnh theo cách đã chốt.

## 9. Đầu vào cần bên nhận bổ sung để hoàn tất

| Cần bổ sung | Nội dung cụ thể | Vì sao cần |
|---|---|---|
| Người đo / người rà | Tên người đo và người khác C3 rà đúng marker, biên và ≥20% tế bào chọn ngẫu nhiên; trả CSV + ảnh có thước | Không thể thay bằng chữ ký tự sinh hoặc mask tự động |
| Bộ đo thật | Đủ cỡ mẫu ba đối chứng, H/V, lý do bỏ ảnh/loại tế bào; sau đó LC/Lung nếu qua kiểm chứng | Hiện mới có pilot/điều hướng, chưa có MPP có căn cứ |
| C4 scores đầy đủ / checkpoint | Logits hoặc probabilities chưa làm tròn; checkpoint đúng run nếu cần tái chạy diagnostics | Chốt restricted accuracy và tái lập các thí nghiệm chẩn đoán |
| Review/commit code đã gộp | Root code/data đã tích hợp; còn review và commit đủ file mới | Giữ đúng phiên bản cho bàn giao/chạy sau này |
| Quyết định nhóm | Duyệt hệ số khi đạt; hoặc ghi nhận nhánh phương pháp không đạt sau đủ mẫu và quyết định tiếp tục với giới hạn cũ | Không mặc định mọi nhánh đều dẫn tới dữ liệu hiệu chỉnh mới |
| Môi trường C4/C5 | CUDA smoke thực tế, lưu artifacts cũ; C5 chốt cách gộp ảnh | Chưa có bằng chứng end-to-end train mới tại máy local |

Để bắt đầu ngay, nhóm chỉ cần phân công người rà và dùng gói `review_pack` để trả số đo/nhận diện. **Chưa cần sinh ảnh, đổi MPP, tải lại dataset hay chạy 15 model.** Không cần chờ liên hệ tác giả nếu phương pháp tế bào tham chiếu có thể hoàn tất đúng tiêu chí; thông tin calibration từ tác giả là nhánh thay thế mạnh hơn nếu nhận được.

## 10. Bằng chứng kèm theo và phạm vi kiểm tra

- [Audit predictions, mapping, hash code và file frozen](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/legacy_metric_verification.json).
- [Snapshot đã tạo](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/snapshot_verification.json) và [SHA snapshot](C:/Users/Admin/Documents/GitHub/btl-hocmay/snapshots/2026-10-16/SHA256SUMS.csv).
- [Manifest gói 180 ảnh đối chứng](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/pack_manifest.json), [biểu mẫu đo](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/scale_calibration_TEMPLATE.csv), [5 yêu cầu nhận diện](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/pilot_identity_requests.csv).
- [Báo cáo pilot và lý do chưa suy MPP](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_pilot_2026-10-25/REPORT.md), [ảnh đánh dấu](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_pilot_2026-10-25/pilot_annotations.png).
- [Kiểm kit RBC](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/formal_rbc_check/analysis.json) và [kit lympho](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/formal_lymph_check/analysis.json): đều incomplete, không có bảng đo hiệu chỉnh phát hành.
- [Bằng chứng 37 tests](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_tests.txt), [preflight ConvNeXt](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_convnext_preflight.json), [preflight Swin](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_swin_preflight.json), [hướng dẫn code/model](C:/Users/Admin/Documents/GitHub/btl-hocmay/docs/MPP_AND_SMOKE.md).

Đợt bàn giao trước kiểm 180 raw và các file được bảo vệ. Sau hợp nhất đã hash lại toàn bộ **41.180 raw + 114.112 processed**, 0 lỗi, và đối chiếu 64 file được bảo vệ qua ánh xạ vị trí/snapshot. Code đường dẫn có hash mới và 42/42 tests đạt; các hash patch cũ chỉ còn là dấu vết lịch sử. Không thay đổi dữ liệu, split, MPP hoặc freeze; không train, không gửi thông tin cho bên ngoài. Các đường dẫn local trong file này cần đi kèm đúng cây dữ liệu/evidence khi chuyển sang máy khác; không gửi riêng file MD rồi coi như đã chuyển toàn bộ bằng chứng.

**Kết luận bàn giao:** phần sửa lỗi và khả năng chuẩn bị kỹ thuật đã có bằng chứng. Để hoàn tất yêu cầu khoa học ban đầu còn thiếu phép đo tế bào thật, review độc lập và quyết định theo kết quả; để xác minh trọn bộ run đầu còn cần scores đầy đủ/checkpoint từ C4. Chưa có căn cứ tuyên bố MPP mới, dữ liệu hiệu chỉnh mới hoặc 15 run mới đã sẵn sàng nghiệm thu.
