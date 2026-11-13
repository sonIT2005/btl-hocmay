# Bàn giao đối chiếu instruct2 — LC25000 / MPP / chuẩn bị chạy lại

Bàn giao ban đầu: **25/10/2026**. Cập nhật bộ đo dự thảo: **26/10/2026**. Cập nhật sau hợp nhất: code/metadata/tài liệu ở `btl-hocmay`; FrameView chỉ còn dataset. Xem [WORKSPACE_LAYOUT.md](WORKSPACE_LAYOUT.md). Đối tượng nhận: C3, C4, C5 và nhóm trưởng. Trạng thái: **đã sửa code và có bộ đo dự thảo 60 đối tượng trên raw; chưa đủ mẫu ba đối chứng, chưa review độc lập, chưa nghiệm thu MPP**. Bản hiện hành: `outputs/mpp_measurements_followup_2026-10-26/draft_v4`, chi tiết tại mục 12; mục 11 giữ mốc v3 trước bổ sung.

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
| Bộ đo chính thức đã khóa | `outputs/maintenance_2026-10-25/mpp_kit` trong repo; vẫn 0 dòng |
| Bộ đo dự thảo hiện hành | `outputs/mpp_measurements_followup_2026-10-26/draft_v4`; 60 dòng chưa review |
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
| Bước 1: đủ tế bào đúng loại, raw, tọa độ, H/V | **Có 60 dòng dự thảo**, đủ tọa độ D/H/V: CRC 30/16 ảnh, BACH 30/18 ảnh, BreakHis 0; chính thức vẫn 0 | Còn BreakHis 30 tế bào / 15 ảnh; xác nhận danh tính/biên và review độc lập | C3 tiếp tục đo, thành viên khác rà; xem mục 12 |
| ≥20% tế bào kiểm tra độc lập | **Chưa có**; đã rút 6 CRC + 6 BACH bằng seed 43 trên v4 | Rà danh tính/vị trí, đo lại mẫu được rút, ghi người rà thật; không ký thay C3 | Nhóm chỉ định người rà |
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
| Toàn bộ tests có PyTorch | **53/53 đạt** sau thêm tool dự thảo (42 trước đó + 11 mới) | Chạy lại nếu sửa code tiếp; rerun trước nghiệm thu dữ liệu mới | C3/C4 |
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
- Đợt pilot trước chỉ mở tổng quan 100 ảnh. Đợt tiếp tục hiện đã khảo sát đủ 180 ảnh (60/nguồn), mở thêm ROI raw, có 46 đường biên ở mốc v3 (mục 11) và 60 dòng hiện tại v4 (mục 12). 180 ảnh khảo sát không được ghi thành 180 ảnh đã đo hoặc tế bào đã được xác nhận.
- Kit chính thức vẫn 0 dòng đo. Chạy kiểm lại riêng `rbc` và `lymph_nucleus` đều trả **`incomplete`**, không có LOO hay MPP được phát hành.

Chưa thể kết luận hồng cầu/lympho hoàn toàn không có trong nguồn hoặc phương pháp chắc chắn thất bại. Việc chưa xác nhận được marker không được thay bằng giá trị mặc định 7,5 µm, phép đo mọi loại nhân, hay hệ số mong muốn.

### Gói người đo / người rà cần dùng

**Gói hiện hành để rà số đo:** `outputs/mpp_measurements_followup_2026-10-26/draft_v4/index.html`, `draft_measurements.csv`, `excluded_objects.csv`, `review_return.csv`; xem mục 12. Gói v3 giữ nguyên để truy vết.

Gói trước tại `outputs/handoff_2026-10-25/review_pack` vẫn giữ để truy vết và dùng biểu mẫu:

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

Chỉ sau khi người đo/người rà thật đã xác nhận hoặc vẽ lại số đo, nối `candidate_id` với kit, chuyển các cột hợp lệ vào `measurements.csv`, cập nhật `image_review.csv`. Không chuyển trực tiếp CSV `draft_unreviewed` hoặc chỉ sửa tên/trạng thái để qua gate. Không sửa nội dung protocol/candidates đã khóa. Giữ các hàng bị người rà loại kèm tên/lý do và đo mẫu thay thế theo cùng tiêu chí.

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
| Bộ đo đủ mẫu đã xác nhận | Có 60 dòng dự thảo và 43 đối tượng/vùng bị tách riêng; thiếu BreakHis và review cụ thể ở mục 12; sau đó LC/Lung nếu qua kiểm chứng | Đã có tọa độ/ảnh để rà, nhưng chưa đủ mẫu ba nguồn và chưa có MPP có căn cứ |
| C4 scores đầy đủ / checkpoint | Logits hoặc probabilities chưa làm tròn; checkpoint đúng run nếu cần tái chạy diagnostics | Chốt restricted accuracy và tái lập các thí nghiệm chẩn đoán |
| Review/commit code đã gộp | Root code/data đã tích hợp; còn review và commit đủ file mới | Giữ đúng phiên bản cho bàn giao/chạy sau này |
| Quyết định nhóm | Duyệt hệ số khi đạt; hoặc ghi nhận nhánh phương pháp không đạt sau đủ mẫu và quyết định tiếp tục với giới hạn cũ | Không mặc định mọi nhánh đều dẫn tới dữ liệu hiệu chỉnh mới |
| Môi trường C4/C5 | CUDA smoke thực tế, lưu artifacts cũ; C5 chốt cách gộp ảnh | Chưa có bằng chứng end-to-end train mới tại máy local |

Bước tiếp theo là rà bộ `draft_v4`, trả `review_return.csv` và bổ sung BreakHis như mục 12. Có thể tự tiếp tục khảo sát/đo theo hàng đợi; việc nghiệm thu độc lập vẫn cần người khác người đo, không tự ký thay. **Chưa cần sinh ảnh, đổi MPP, tải lại dataset hay chạy 15 model.** Không cần chờ liên hệ tác giả nếu phương pháp tế bào tham chiếu có thể hoàn tất đúng tiêu chí; thông tin calibration từ tác giả là nhánh thay thế mạnh hơn nếu nhận được.

## 10. Bằng chứng kèm theo và phạm vi kiểm tra

- [Audit predictions, mapping, hash code và file frozen](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/legacy_metric_verification.json).
- [Snapshot đã tạo](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/snapshot_verification.json) và [SHA snapshot](C:/Users/Admin/Documents/GitHub/btl-hocmay/snapshots/2026-10-16/SHA256SUMS.csv).
- [Manifest gói 180 ảnh đối chứng](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/pack_manifest.json), [biểu mẫu đo](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/scale_calibration_TEMPLATE.csv), [5 yêu cầu nhận diện](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/review_pack/pilot_identity_requests.csv).
- [Báo cáo pilot và lý do chưa suy MPP](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_pilot_2026-10-25/REPORT.md), [ảnh đánh dấu](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_pilot_2026-10-25/pilot_annotations.png).
- [Kiểm kit RBC](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/formal_rbc_check/analysis.json) và [kit lympho](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/handoff_2026-10-25/formal_lymph_check/analysis.json): đều incomplete, không có bảng đo hiệu chỉnh phát hành.
- [Bằng chứng 37 tests](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_tests.txt), [preflight ConvNeXt](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_convnext_preflight.json), [preflight Swin](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/maintenance_2026-10-25/applied_swin_preflight.json), [hướng dẫn code/model](C:/Users/Admin/Documents/GitHub/btl-hocmay/docs/MPP_AND_SMOKE.md).

Đợt bàn giao trước kiểm 180 raw và các file được bảo vệ. Sau hợp nhất đã hash lại toàn bộ **41.180 raw + 114.112 processed**, 0 lỗi, và đối chiếu 64 file được bảo vệ qua ánh xạ vị trí/snapshot. Code đường dẫn có hash mới và 42/42 tests đạt; các hash patch cũ chỉ còn là dấu vết lịch sử. Không thay đổi dữ liệu, split, MPP hoặc freeze; không train, không gửi thông tin cho bên ngoài. Các đường dẫn local trong file này cần đi kèm đúng cây dữ liệu/evidence khi chuyển sang máy khác; không gửi riêng file MD rồi coi như đã chuyển toàn bộ bằng chứng.

**Kết luận bàn giao:** phần sửa lỗi và khả năng chuẩn bị kỹ thuật đã có bằng chứng. Để hoàn tất yêu cầu khoa học ban đầu còn thiếu bộ đo đủ mẫu đã xác nhận, review độc lập và quyết định theo kết quả; để xác minh trọn bộ run đầu còn cần scores đầy đủ/checkpoint từ C4. Chưa có căn cứ tuyên bố MPP mới, dữ liệu hiệu chỉnh mới hoặc 15 run mới đã sẵn sàng nghiệm thu.

## 11. Mốc dự thảo v3 trước đợt bổ sung ngày 26/10

**Mốc lịch sử: các số dưới đây thuộc v3. Bản hiện hành và số thiếu mới nằm ở mục 12.**

**Đã có bộ đo để rà trực tiếp tại `outputs/mpp_measurements_draft_v1/draft_v3`, chưa có bộ đo nghiệm thu.** `CURRENT.json` chỉ đến phiên này; `draft_v1` và `draft_v2` là lịch sử tự QA, không dùng làm bản hiện hành. Các đường biên mới được đặt bằng mắt trên pixel raw, tách hoàn toàn khỏi các đường kính mask ở pilot cũ. Mọi dòng vẫn là `draft_unreviewed`, `measurer=Codex_visual_assist`, `checked_by` trống. Không có chữ ký C3 hoặc người kiểm tra được tự điền.

### Kết quả thực tế và phần còn thiếu

| Marker | Nguồn | Đối tượng được tính trong dự thảo | Ảnh có số đo | Còn thiếu so với 30 tế bào / 15 ảnh | Mẫu review seed 43 |
|---|---|---:|---:|---|---:|
| Nhân nghi lympho | CRC | 27 | 14 | 3 tế bào, trong đó phải bổ sung ít nhất 1 ảnh khác | 6 |
| Nhân nghi lympho | BACH | 19 | 16 | 11 tế bào; vẫn giữ tối đa 3 tế bào/ảnh | 4 |
| Nhân nghi lympho | BreakHis 40× | 0 | 0 | 30 tế bào từ ít nhất 15 ảnh | 0 |
| Hồng cầu | CRC | 0 | 0 | 30 tế bào / 15 ảnh nếu tiếp tục nhánh này | 0 |
| Hồng cầu | BACH | 0 | 0 | 30 tế bào / 15 ảnh; 2 vật thể nghi hồng cầu chưa được tính | 0 |
| Hồng cầu | BreakHis 40× | 0 | 0 | 30 tế bào / 15 ảnh; 3 vùng nghi hồng cầu chưa được tính | 0 |

Tổng cộng **46 đối tượng có hình thái tạm phù hợp** trong thống kê nhân lympho; **36 đối tượng/vùng nghi ngờ bị tách riêng**: CRC 13 nhân, BACH 8 nhân + 2 hồng cầu, BreakHis 10 nhân + 3 vùng hồng cầu. Trong 82 bản ghi, 55 có đường vẽ để kiểm tra hình học (46 dự thảo + 9 bị loại khỏi thống kê), 27 chỉ đánh dấu vị trí vì chưa tách được đối tượng. Các số này **không phải số tế bào đã được người khác xác nhận**; số đo chính thức được chấp nhận vẫn bằng 0.

Đã khảo sát **60/60 ảnh ứng viên của từng nguồn**, theo hàng đợi seed 42 đã khóa: xem tổng quan, tối đa 3 vùng chỉ điểm nhân và tối đa 2 vùng chỉ điểm màu đỏ mỗi ảnh, rồi mở raw phóng lớn để đặt biên cho đối tượng được ghi. Riêng BreakHis đã xem thêm toàn bộ 60 khung raw ở tỷ lệ 1:1 và 13 vùng có lưới phóng 8×. Các blob màu/tối chỉ hỗ trợ định vị; không được nhập thành đường kính tế bào. Không thay ảnh bằng lớp CRC-LYM ngoài hàng đợi và không đổi seed hay tiêu chí hình thái.

Giới hạn tìm kiếm: khảo sát ảnh không đồng nghĩa kiểm đếm mọi tế bào trên toàn bộ ảnh. BACH 2048×1536 mới xem tổng quan và các ROI được chỉ ra; những vùng khác vẫn có thể có tế bào phù hợp. “Không có đối tượng được chọn” không chứng minh nguồn không có marker. Ở BreakHis, các vùng đã mở có biên mờ, nhân trong biểu mô, vật thể rời hoặc đám đỏ không tách được từng tế bào; vì vậy không ép đủ số mẫu. Chưa đủ mẫu để gọi phương pháp đã thất bại.

Ưu tiên khảo sát RBC được giữ nguyên. Vì chưa xác nhận được một bộ RBC đủ ở cả ba nguồn, nhân nghi lympho được khảo sát riêng trên cả ba. **Chưa tính LOO cho bất kỳ nhánh nào**, nên không có việc chọn loại tế bào theo sai số LOO đẹp hơn. Ba đối tượng CRC được loại thêm khi tự QA lớp đánh dấu do hình dạng/biên chưa rõ (`D1_CRC_q18_1`, `D1_CRC_q33_2`, `D1_CRC_q60_3`), trước mọi LOO; vẫn giữ hình và lý do trong bảng loại.

### Cách đo và thống kê dự thảo

- Tọa độ `x,y` đếm từ 0 trên raw, x sang phải/y xuống dưới; số nguyên đặt tại tâm pixel. Ảnh phóng dùng nearest-neighbour, không thêm chi tiết ảnh.
- Mỗi đối tượng có đường biên lồi 8 đỉnh đặt bằng mắt. D là dây dài nhất giữa các đỉnh; H và V là dây ngang/dọc dài nhất **bên trong đường biên**, không phải kích thước bbox hoặc đường kính blob ngưỡng. Lưu đủ 6 đầu mút D/H/V cùng polygon để kiểm lại.
- Đây là xấp xỉ đường biên nhìn thấy. D lớn nhất trên polygon không tự chứng minh đã chạm đúng hai đầu dài nhất của nhân thật. Cần người rà xác nhận hoặc vẽ lại; không diễn giải các chữ số thập phân tính toán là độ chính xác dưới pixel. `boundary_uncertainty_px` 1 px ở CRC / 2 px ở BACH và BreakHis là ghi chú độ mơ hồ khi đặt biên, chưa phải khoảng tin cậy được kiểm chứng.
- Tính trung vị D theo từng ảnh rồi trung vị các ảnh theo nguồn: **CRC 10,6053 px**, **BACH 18,9493 px**; BreakHis không có giá trị. Có CSV trung vị H/V theo ảnh. Không pool các tế bào để thay trung vị theo ảnh.
- Bảng xem trước ghi `leave_one_out=null`, `method_failed=false`, `approved_mpp=null`, không có target MPP. Thiếu mẫu hiện tại không kích hoạt nhánh mở rộng sau LOO hay nhánh loại phương pháp của instruct2.

### Các file để mở và trả review

| File trong phiên hiện hành | Nội dung |
|---|---|
| [index.html](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/index.html) | Xem từng đối tượng: ROI nguyên pixel cạnh ROI đánh dấu, link ảnh bối cảnh đúng kích thước raw; có cả đối tượng bị loại |
| [draft_measurements.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/draft_measurements.csv) | 46 dòng: nguồn/SHA, tọa độ D/H/V, chiều dài, polygon, phương pháp đặt biên và trạng thái chưa rà |
| [excluded_objects.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/excluded_objects.csv) | 36 dòng không tính vào cỡ mẫu; ghi rõ lý do và vị trí/đường vẽ nếu có |
| [review_return.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/review_return.csv) | Biểu mẫu trả xác nhận danh tính, biên, đường kính vẽ lại, người rà và ghi chú; 10 dòng được đánh dấu `selected_for_review=True` |
| [selected_review_cells.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/selected_review_cells.csv) | Danh sách 6 CRC + 4 BACH, rút từ ID sắp xếp bằng seed 43; không chọn tay |
| [image_medians.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/image_medians.csv), [cohort_summary.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/cohort_summary.csv) | Trung vị theo ảnh và số mẫu/thiếu mẫu theo nguồn, tách marker |
| [draft_preview.json](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/draft_v3/draft_preview.json) | Chỉ thống kê dự thảo; chưa có LOO hoặc MPP phát hành |
| [image_screening.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/image_screening.csv) | Dấu vết đủ 180 ảnh, mức khảo sát và số ROI chỉ điểm; không tự đánh dấu eligible trong kit chính thức |
| [final_verification.json](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/final_verification.json) | Số kiểm tra thực tế, hash code và kết luận bảo toàn file khóa |
| [geometry_and_roi_checks.csv](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/geometry_and_roi_checks.csv) | 82 ROI đối chiếu pixel raw; 55 bộ đường đo tính lại khoảng cách đầu mút; tự QA không phải review độc lập |

Danh sách rút review hiện tại: CRC `q03_2, q06_2, q20_1, q20_3, q24_1, q39_1`; BACH `q15_1, q20_1, q29_1, q50_1` (ID đầy đủ trong CSV). Đây là danh sách cho bộ dự thảo hiện tại. Khi bổ sung/loại mẫu, rút lại đúng seed 43 trên bộ ID mới và lưu phiên bản; không thay mẫu khó bằng mẫu thuận mắt.

### Người kiểm tra cần xác nhận

- Trong mẫu rà, xác nhận danh tính các nhân được đề xuất: nhân lympho nhỏ, tròn/bầu dục, đậm tương đối đồng nhất, tách khỏi nhân biểu mô/nhân u; không chỉ duyệt blob tối. Có thể loại bất kỳ dòng nào không đủ bằng chứng.
- Rà độc lập ít nhất 10 đối tượng được rút ngẫu nhiên về danh tính/vị trí, kiểm trực tiếp biên và đo lại D/H/V trên raw. Đánh giá biên ngoài toàn nhân, không dừng ở nucleolus hoặc lõi nhuộm đậm.
- Rà các bản ghi bị loại riêng, đặc biệt 2 vật thể BACH nghi RBC và các vùng BreakHis. Chỉ đưa vào mẫu sau khi xác nhận được loại tế bào và biên; không bù số thiếu bằng đối tượng mơ hồ.
- Bổ sung đúng thiếu hụt trong bảng trên, theo cùng hàng đợi/tiêu chí, tối đa 3 tế bào/ảnh. CRC phải có thêm ít nhất 1 ảnh. Nếu chỉ rà những ROI hiện có chưa đủ, khảo sát tiếp raw trong các ảnh đã khóa và ghi phạm vi đã xem; không tự thay hàng đợi bằng ảnh khác dễ đạt hơn.
- Ghi tên người rà thật, ngày và thay đổi đường vẽ/lý do loại. Không chỉ đổi trạng thái sang `checked`, điền tên C3 thay cho `Codex_visual_assist` hoặc chép số vào bộ chính thức khi người đó chưa thực sự đo/xác nhận lại.
- Khi đủ mẫu cùng marker ở cả ba nguồn, chạy **LOO dự thảo** để kiểm số học; chỉ sau độc lập review đầy đủ mới đưa số đo hợp lệ sang kit chính thức và phân tích theo quy trình cũ. Chưa chuyển sang ước lượng LC25000 ở thời điểm hiện tại.

### Công cụ, kiểm chứng và điểm dừng

Đã thêm `tools/draft_mpp.py` và 11 test. Tool kiểm hash protocol/candidates/FROZEN, SHA + kích thước 180 ảnh đối chứng, polygon lồi/không tự cắt, tọa độ trong raw, giới hạn tổng 3 đối tượng dự thảo/ảnh, marker tách riêng và seed review. Công cụ chính thức `tools/measure_mpp.py` không được sửa trong đợt này. Thử nhập CSV dự thảo vào **bản sao kit tạm** bị chặn ở `review_status=draft_unreviewed`; kit thật vẫn 0 dòng, hai nhánh `incomplete`. Xem [formal_safety_check.json](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/formal_safety_check.json).

Đã đối chiếu 82 ảnh ROI với pixel raw; tính lại D/H/V từ đầu mút và đối chiếu vùng hiển thị cho 55 đối tượng có đường vẽ. Đã mở QA lớp đánh dấu của toàn bộ 55 đối tượng; đây là **tự QA của Codex**, không ký thay kiểm tra độc lập. 36 file trong `splits`, `configs` và kit không đổi SHA; protocol, seed, freeze và bảng chính thức giữ nguyên. Toàn bộ **53/53 tests đạt**, không skip, gồm kiểm chặn review của bộ chính thức và kiểm preview không tạo MPP đã duyệt; log [tests.txt](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_draft_v1/tests.txt).

Để tái xuất từ cùng tọa độ sang một phiên mới (trong môi trường Python của repo):

```powershell
Set-Location 'C:\Users\Admin\Documents\GitHub\btl-hocmay'
python tools/draft_mpp.py `
  --kit outputs/maintenance_2026-10-25/mpp_kit `
  --annotations outputs/mpp_measurements_draft_v1/draft_v3/annotations_input.json `
  --out outputs/mpp_measurements_draft_v1/rebuild_v1
```

Tool từ chối ghi đè output đã có và từ chối output trong kit/data/splits/configs. Dữ liệu đầu vào là tọa độ vẽ bằng mắt; chạy tool không thay thế việc nhận diện/đặt biên. Không có lệnh sinh ảnh nghiên cứu hoặc chạy model trong quy trình dự thảo này. FrameView chỉ giữ dataset; code, bảng đo và bằng chứng ở `btl-hocmay`. Các PNG bị ignore khỏi Git, nên khi bàn giao review phải gửi kèm thư mục output hiện hành và navigation/evidence, không chỉ gửi file MD hoặc commit code.

**Điểm dừng hiện tại:** bộ đo dự thảo có thể kiểm tra lại đã được tạo, còn thiếu mẫu và xác nhận độc lập. Không đổi MPP, không regenerate, không chạy model, không tuyên bố đã hoàn tất phần nghiệm thu khoa học của instruct2.


## 12. Bổ sung mẫu và phần còn thiếu — v4 ngày 26/10

Đã hoàn thiện phần có thể làm tại máy: bổ sung 14 đường biên raw (3 CRC + 11 BACH), giữ nguyên 82 bản ghi v3 và mọi file dữ liệu khóa. Hiện **CRC 30 đối tượng / 16 ảnh, BACH 30 / 18 ảnh, BreakHis 0**; 60 dòng đều `draft_unreviewed`, 43 đối tượng/vùng tách riêng. Có 6 CRC + 6 BACH rút lại đúng seed 43 để review; không có người rà/chữ ký tự điền. V3 được giữ nguyên và không còn là bản mới nhất.

Xem [trang ảnh v4](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/draft_v4/index.html), [bảng đo](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/draft_v4/draft_measurements.csv), [biểu mẫu review](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/draft_v4/review_return.csv) và [STATUS_C3.md — đầy đủ thiếu hụt, cách rà và nội dung gửi người rà](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/STATUS_C3.md).

**Còn thiếu ngay để đi tiếp C3:** (1) BreakHis 30 tế bào đúng loại, đủ biên từ ≥15 ảnh, tối đa 3/ảnh; (2) review độc lập ít nhất 6 CRC + 6 BACH hiện tại, sau này thêm mẫu BreakHis; (3) đủ ba đối chứng mới tính LOO, chưa suy MPP LC25000. Đã xem thêm 360 ROI trên 60 ảnh BreakHis nhưng vẫn không nhận diện chắc; đây là thiếu mẫu, không phải đã kiểm định phương pháp thất bại. Không thay marker, nguồn hoặc seed để đạt số lượng. Không thể dùng GPU hay tên người rà tự sinh để hoàn tất hai đầu vào này.

Khi đủ mẫu/review, mới tiếp tục LOO theo ngưỡng đã khóa, rồi LC25000 train/CI/H/V và nhóm chốt. Instruct2 đầy đủ còn yêu cầu C4 gửi scores đủ precision/checkpoint gốc, nghiệm thu dữ liệu và CUDA/train sau đó; các bước này chưa được coi là hoàn tất.

Code thêm cột group/kích thước raw, ô trống cho tọa độ/H/V đo lại và liên kết tới mẫu review. **53/53 test đạt** sau thay đổi. Kiểm 180 SHA raw, 103 ROI khớp pixel, 69 bộ đường đo khớp đầu mút, tối đa 3 đối tượng có caliper/ảnh; 36 file split/config/kit không đổi. Công cụ chính thức nguyên hash, import CSV draft vào kit tạm bị chặn. Xem [final_verification.json](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/final_verification.json), [test log](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/tests.txt). Không đổi MPP, freeze, nhãn/group/split; không regenerate hoặc chạy model. Giai đoạn này không cần GPU.

Gói ZIP phục vụ rà nội bộ: [C3_DRAFT_v4_review.zip](C:/Users/Admin/Documents/GitHub/btl-hocmay/outputs/mpp_measurements_followup_2026-10-26/C3_DRAFT_v4_review.zip). Gói chứa bản v4, ảnh bối cảnh/ROI, navigation, biểu mẫu review và manifest SHA; không chứa bản raw dataset hoặc checkpoint. Không tự gửi cho người khác.
