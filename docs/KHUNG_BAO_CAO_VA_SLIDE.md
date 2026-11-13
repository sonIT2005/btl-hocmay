# KHUNG BÁO CÁO TOÀN VĂN VÀ SLIDE THUYẾT TRÌNH BÀI TẬP LỚN
**Dự án:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Học Sâu trên Ảnh Mô Bệnh Học Đa Trung Tâm

**Học phần:** Học máy (Machine Learning)

**Ngày cập nhật:** 13/11/2026

---

# PHẦN 1: KHUNG BÁO CÁO TOÀN VĂN (FULL REPORT STRUCTURE)
*Dung lượng đề xuất: 20 – 30 trang (Chuẩn báo cáo đồ án môn học)*

## BÌA VÀ MỞ ĐẦU
- **Trang bìa chính & phụ:** Trường/Viện, Bộ môn, Tên đề tài, Giảng viên hướng dẫn, Danh sách sinh viên thực hiện và phân công đóng góp.
- **Tóm tắt báo cáo (Abstract) - Tiếng Việt & Tiếng Anh:** Nêu bối cảnh, nguy cơ rò rỉ ở LC25000, so sánh chia theo ảnh với chia theo nhóm, đối chiếu ConvNeXt-Tiny và Swin-Tiny với hai nhánh màu, kết quả kiểm thử chéo và giới hạn của MPP ước lượng.
- **Mục lục, Danh mục chữ viết tắt, Danh mục bảng biểu, Danh mục hình vẽ.**

---

## CHƯƠNG 1: GIỚI THIỆU & ĐẶT VẤN ĐỀ (INTRODUCTION)
### 1.1. Bối cảnh giải phẫu bệnh số (Computational Pathology - CPath)
- Sự chuyển dịch từ chẩn đoán qua kính hiển vi quang học sang quét tiêu bản số hóa toàn phần (Whole Slide Imaging - WSI).
- Nhu cầu cấp thiết về các hệ thống AI hỗ trợ chẩn đoán (Computer-Aided Diagnosis - CAD) nhằm giảm tải cho chuyên gia giải phẫu bệnh và chuẩn hóa chất lượng chẩn đoán.
### 1.2. Tính cấp thiết của phân loại đa cơ quan (Multi-Organ Histopathology)
- Tầm quan trọng của việc chẩn đoán phân biệt giữa các mô lành và khối u biểu mô ác tính phổ biến: Phổi (Adenocarcinoma, Squamous Cell Carcinoma), Đại tràng (Adenocarcinoma), Tuyến vú (Benign, Malignant).
### 1.3. Thách thức cốt lõi trong thực tế y tế
- **Thách thức 1 - Sai lệch miền dữ liệu (Domain Shift / Batch Effect):** Khác biệt về nồng độ hóa chất nhuộm H&E, máy quét WSI (Leica, Aperio, Hamamatsu) và độ phân giải vật lý giữa các bệnh viện.
- **Thách thức 2 – Rò rỉ dữ liệu:** Khi chia LC25000 theo ảnh, các biến thể của cùng một ảnh nguồn có thể xuất hiện ở cả train và test. Chênh lệch giữa hai cách chia được báo cáo ở mục 4.3.

### 1.4. Câu hỏi nghiên cứu và đối chiếu thực nghiệm

- **RQ1:** Cùng khởi tạo từ ImageNet-1k, ConvNeXt-Tiny và Swin-Tiny khác nhau thế nào về mức suy giảm khi chuyển sang nguồn ảnh khác? Tính Δ theo từng cơ quan từ tập nội bộ đến tập kiểm thử chéo.
- **E1 và E2:** Đối chiếu ảnh hưởng của cách chia dữ liệu và của Macenko. Mức cải thiện nhờ chuẩn hóa màu được đánh giá riêng theo mô hình và nguồn.
- **Phạm vi:** So sánh 15 lượt E1/E2 trên dữ liệu đóng băng 16/10/2026. Hiệu chỉnh MPP và thử nghiệm Phikon nằm ngoài kết quả chính.

### 1.5. Đóng góp chính của đề tài

- Ánh xạ năm nguồn ảnh về bảy lớp, tạo manifest có thể truy vết về ảnh nguồn và nhóm.
- Đối chiếu hai cách chia, hai kiến trúc và hai nhánh màu. Báo cáo hiệu năng ngoài miền theo từng cơ quan và minh họa trường hợp dự đoán đúng/sai bằng Grad-CAM.

---

## CHƯƠNG 2: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ KHOA HỌC (LITERATURE REVIEW)
### 2.1. Khảo sát các hướng tiếp cận học sâu trên ảnh mô bệnh học
- Các mô hình phân cấp tiên tiến: **Swin Transformer V2** (Shifted Windows, Continuous Position Bias).
- Các mạng gọn nhẹ có tích hợp cơ chế giải thích: **XLLC-Net** với kỹ thuật bản đồ nhiệt **Grad-CAM**.
- Các kỹ thuật kết hợp: **Feature Fusion** (VGG/GoogLeNet + Handcrafted LBP/GLCM) và **Ensemble Learning** (Multi-CNNs + Random Forest/SVM).
### 2.2. Phân tích lỗ hổng phương pháp luận trong các công bố quốc tế
- LC25000 có khoảng 1.250 ảnh gốc và các biến thể xoay, lật. Khi đọc một kết quả trên tập này, cần kiểm tra đơn vị chia tập và xem có đánh giá chéo nguồn hay không.
- Các kết quả từ y văn có thể khác nhau về tập lớp, đơn vị chia và cách đánh giá. Đối chiếu E1/E2 ở mục 4.3 dùng dữ liệu của đề tài.
### 2.3. Bảng so sánh tổng hợp các công trình tiêu biểu
[Bảng so sánh các công trình ở mục C9](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/docs/TONG_QUAN_TAI_LIEU_C9.md)
### 2.4. Cơ sở lý thuyết kỹ thuật bổ trợ
- **Mô hình vật lý quang học Macenko:** Định luật Beer-Lambert, không gian Mật độ quang học (Optical Density - OD), phép chiếu PCA và tìm vector phổ thuốc nhuộm Hematoxylin & Eosin.
- **Tỷ lệ phóng đại và độ phân giải vật lý (Microns Per Pixel - MPP):** MPP liên hệ kích thước pixel với trường nhìn vật lý. Việc quy đổi trường nhìn phụ thuộc vào độ tin cậy của MPP ở từng nguồn.
- **Kiến trúc mạng nơ-ron đối sánh:** ConvNeXt-Tiny (đại diện mạng tích chập hiện đại) và Swin-Tiny (đại diện Transformer phân cấp).

---

## CHƯƠNG 3: NGUYÊN LIỆU VÀ PHƯƠNG PHÁP NGHIÊN CỨU (MATERIALS & METHODS)
### 3.1. Tổng quan năm bộ dữ liệu

Nghiên cứu sử dụng năm bộ ảnh mô bệnh học nhuộm H&E của phổi, đại tràng và vú. LC25000 và BreakHis 40× cung cấp tập huấn luyện, tập xác thực và tập kiểm thử nội bộ. LungHist700, CRC-VAL-HE-7K và BACH được dành riêng cho kiểm thử chéo nguồn.

| Nguồn | Cơ quan và phạm vi sử dụng | Train | Val | Test nội bộ | Test chéo |
|---|---|---:|---:|---:|---:|
| LC25000 | Phổi và đại tràng | 17.464 | 3.742 | 3.743 | — |
| BreakHis | Vú, riêng mức 40× | 1.395 | 299 | 301 | — |
| LungHist700 | Phổi, patch cắt từ 691 ảnh nguồn | — | — | — | 14.557 |
| CRC-VAL-HE-7K | Đại tràng, hai nhóm NORM và TUM | — | — | — | 1.974 |
| BACH | Vú, patch cắt từ 400 ảnh microscopy | — | — | — | 13.581 |
| **Tổng mỗi nhánh tiền xử lý** | **57.056 mẫu đầu vào** | **18.859** | **4.041** | **4.044** | **30.112** |

Bảng đếm mẫu đầu vào ở cấp patch theo cột `split` của manifest E2.

[Bảng đối chiếu C5](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/outputs/eval/tables/dataset_summary.csv)

### 3.2. Ánh xạ bảy lớp

- **Phổi:** lành (0, `lung_benign`), ung thư biểu mô tuyến (1, `lung_aca`) và ung thư biểu mô tế bào vảy (2, `lung_scc`).
- **Đại tràng:** lành (3, `colon_benign`) và ung thư biểu mô tuyến (4, `colon_aca`). CRC chỉ dùng 741 patch NORM và 1.233 patch TUM.
- **Vú:** lành (5, `breast_benign`) và ác tính (6, `breast_malignant`). BACH gộp Normal và Benign vào lớp 5, InSitu và Invasive vào lớp 6.

[Bản đồ nhãn và ánh xạ từng nguồn](../splits/label_map.json)

### 3.3. Tái dựng nhóm và chia tập

- **LC25000:** tạo ứng viên bằng pHash và đặc trưng ảnh, sau đó kiểm chứng hình học và đối chiếu pixel trước khi nối nhóm. Dùng 24.949/25.000 ảnh. Giữ riêng 51 ảnh thuộc nhóm nhỏ chưa đủ bằng chứng gán họ ảnh.
- **BreakHis 40×:** gộp theo mã ca, gồm 70 nhóm sau khi gộp các hậu tố section của cùng mã.
- **Chia tập:** E2 phân tầng theo lớp và chia theo `group_id`, tỷ lệ mục tiêu 70/15/15, seed 42. Kiểm tra manifest cho thấy 0 nhóm giao nhau giữa train, val và test. E1 dùng cột chia theo ảnh để đối chiếu. Bản đóng băng ngày 16/10/2026 có fingerprint `f5c641abf5b155b1`.

[Manifest và checksum](../splits/FROZEN.json) · [Quyết định D3–D7](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/DECISIONS.md#dữ-liệu)

### 3.4. Tiền xử lý và chuẩn hóa màu

- **Kích thước đầu vào:** ảnh RGB 224 × 224 pixel. Quy đổi theo MPP của từng nguồn với mục tiêu 0,5 µm/pixel, tương ứng trường nhìn danh định 112 × 112 µm. MPP LC25000 và LungHist700 là ước lượng.
- **Tạo patch và lọc mô:** LC25000 và BreakHis dùng crop giữa. LungHist700 và BACH dùng lưới không chồng lấn, giữ patch có ít nhất 50% pixel mô theo ngưỡng RGB. Một pixel được tính là nền trắng nếu cả ba kênh đều lớn hơn 220.
- **Macenko:** chuẩn hóa H&E theo một ảnh tham chiếu từ LC25000 train. Hai nhánh `none` và `macenko` dùng chung tọa độ crop, nhãn, nhóm và split.

### 3.5. Thiết kế và thiết lập huấn luyện mô hình
- Cấu hình mạng: ConvNeXt-Tiny và Swin-Tiny, cùng khởi tạo từ trọng số ImageNet-1k. Chọn checkpoint có macro-F1 cao nhất trên tập xác thực nội bộ.
- Hàm mất mát có bù trừ mất cân bằng lớp (Inverse Frequency Class-weighted Cross-Entropy).
- Tối ưu hóa: AdamW, Learning Rate $10^{-4}$, Cosine Warmup, Weight Decay 0.05, Mixed Precision (bfloat16).

---

## CHƯƠNG 4: KẾT QUẢ VÀ BÀN LUẬN THỰC NGHIỆM (EXPERIMENTS & RESULTS)
### 4.1. Thiết kế ma trận thực nghiệm

- **E1:** ConvNeXt-Tiny, chia ngẫu nhiên theo ảnh, nhánh `none`, ba seed.
- **E2:** chia theo nhóm, hai kiến trúc × hai nhánh màu × ba seed, tổng 12 lượt. Đối chiếu ảnh hưởng của cách chia bằng E1 và cấu hình E2 ConvNeXt `none`.
- **Kiểm thử chéo:** đánh giá các checkpoint trên LungHist700, CRC-VAL-HE-7K và BACH. Đây là các tập đánh giá của E1/E2.

### 4.2. Thước đo

- Accuracy tính trên dự đoán từ cả bảy lớp. Báo thêm balanced accuracy, macro-F1 trên các lớp hiện diện trong tập, recall từng lớp và AUROC lành/ác theo cơ quan.
- Tỷ lệ nhầm cơ quan là tỷ lệ patch có cơ quan dự đoán khác cơ quan thật. Với accuracy trong cơ quan đúng, giới hạn argmax vào các lớp của cơ quan thật và giữ mẫu số là toàn bộ patch của tập.
- Tính Δ macro-F1 theo từng cơ quan bằng macro-F1 nội bộ trừ macro-F1 kiểm thử chéo tương ứng. Báo trung bình ± độ lệch chuẩn qua ba seed.

### 4.3. Phân tích kết quả

- **Ảnh hưởng của cách chia.** Với ConvNeXt-Tiny nhánh `none`, accuracy nội bộ của E1 là **99,74 ± 0,12%** và của E2 là **92,50 ± 1,23%**. Chênh lệch 7,24 điểm phần trăm đi cùng sự thay đổi cách chia. [Bảng so sánh C5](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/outputs/eval/tables/leakage_e1_vs_e2.csv)
- **Macenko có tác động khác nhau theo nguồn.** Macro-F1 trung bình tăng ở CRC và BACH trên cả hai kiến trúc. Trên LungHist700, macro-F1 của ConvNeXt giảm từ 0,370 xuống 0,079 và của Swin giảm từ 0,274 xuống 0,114. [Bảng kết quả C5](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/outputs/eval/tables/summary_by_config.csv)
- **So sánh theo cơ quan.** Ở nhánh `none`, ConvNeXt có Δ macro-F1 nhỏ hơn Swin trên phổi và đại tràng, còn Swin có Δ nhỏ hơn trên vú. Chênh lệch nội bộ–ngoài miền phụ thuộc cơ quan và cấu hình. Hai tỷ lệ nhầm cơ quan 97% ở CRC và 84% ở BACH thuộc lần chạy ConvNeXt seed 0 ngày 22/10. Nguyên nhân nhầm cơ quan vẫn chưa xác định. [Bảng Δ theo cơ quan](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/outputs/eval/tables/delta_by_config.csv) · [Lần chạy đầu, D9–D11](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/DECISIONS.md#lần-chạy-đầu-và-lỗi-tỷ-lệ)

### 4.4. Trực quan hóa và giải thích mô hình

Hai hình minh họa tám patch, mỗi patch gồm ảnh đầu vào, Grad-CAM của ConvNeXt-Tiny và Grad-CAM của Swin-Tiny. Trong từng tập kiểm thử, một patch được rút từ các trường hợp cả hai mô hình đoán đúng và một patch từ các trường hợp cả hai đoán sai. Quy tắc rút dùng seed 42, chọn đều theo nhóm trước rồi theo patch, với tám `group_id` khác nhau. Chọn mẫu dựa trên dự đoán C5 trước khi tính bản đồ nhiệt. Checkpoint E2 nhánh `none` của ConvNeXt ở epoch 7 và Swin ở epoch 3, cùng seed huấn luyện 0.

- **Hình 1. Bốn patch cả hai mô hình dự đoán đúng.** CAM-03 cho thấy hai bản đồ cùng nổi bật ở dải bên trái patch CRC.

  ![Grad-CAM của bốn patch cả hai mô hình đoán đúng](../outputs/gradcam_2026-11-13/gradcam_4_dung.png)

- **Hình 2. Bốn patch cả hai mô hình dự đoán sai.** Ở CAM-07, ConvNeXt nhầm lớp trong cùng cơ quan, còn Swin nhầm sang cơ quan khác. Ở CAM-08, cả hai mô hình dự đoán lớp thuộc phổi cho patch từ BACH.

  ![Grad-CAM của bốn patch cả hai mô hình đoán sai](../outputs/gradcam_2026-11-13/gradcam_4_sai.png)

Màu cam đậm hơn biểu thị giá trị Grad-CAM cao hơn trong cùng bản đồ. Grad-CAM lấy gradient logit của lớp dự đoán tại block cuối của ConvNeXt (`stages.3.blocks.2`) và lớp chuẩn hóa trước attention trong block cuối của Swin (`layers.3.blocks.1.norm1`). Tỷ lệ dưới mỗi bản đồ là softmax khi chạy lại bằng CPU FP32. Cả 16 nhãn dự đoán khớp với C5, còn giá trị xác suất có thể chênh do C5 dùng CUDA bf16. Bảng mẫu lưu đường dẫn patch, ảnh nguồn, nhãn, SHA-256, dự đoán và xác suất của cả hai lần chạy. [Bảng tám mẫu](../outputs/gradcam_2026-11-13/samples.csv) · [Provenance](../outputs/gradcam_2026-11-13/provenance.json)

Hai hình đọc từ thư mục kết quả cục bộ theo quy ước lưu ảnh của dự án. Mở báo cáo trong checkout có sẵn bộ Grad-CAM để xem các hình.

---

## CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (CONCLUSION)
### 5.1. Kết luận chính

- Cách chia theo ảnh cho accuracy nội bộ cao hơn cách chia theo nhóm trong đối chiếu ConvNeXt-Tiny. Kết quả kiểm thử chéo cho thấy mức suy giảm tùy cơ quan và cấu hình.
- Macenko có thể cải thiện kết quả ở một số nguồn. Hiệu quả quan sát được trên CRC và BACH đi kèm sự suy giảm trên LungHist700.

### 5.2. Hạn chế

1. **Tỷ lệ vật lý chưa được xác nhận ở mọi nguồn.** Giá trị MPP của LC25000 và LungHist700 là ước lượng. LC25000 còn có thể bị co giãn khác nhau theo hai trục do các phép biến đổi ảnh. Nhóm phát hiện dấu hiệu lệch tỷ lệ sau khi xem kết quả kiểm thử chéo của lần chạy đầu. Khảo sát bằng tế bào tham chiếu chưa có bộ đo đạt yêu cầu ở cả ba nguồn và chưa có kết quả rà độc lập để hoàn tất kiểm chứng. Theo quyết định D10 và D12, kết quả chính dùng bản đóng băng 16/10 với MPP LC25000 là 0,5 µm/pixel, trạng thái `estimated_unverified`. [Quyết định D10–D12](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/DECISIONS.md#lần-chạy-đầu-và-lỗi-tỷ-lệ)
2. **Chia theo nhóm có giới hạn về danh tính.** Nhóm LC25000 đại diện cho họ ảnh biến đổi được tái dựng. Mức độc lập theo bệnh nhân vẫn chưa xác định. Việc loại 51 ảnh có thể làm thay đổi phân bố mẫu nội bộ. BACH và CRC thiếu mã bệnh nhân đầy đủ trong dữ liệu sử dụng, nên lấy mẫu lại theo `group_id` vẫn có thể bỏ sót tương quan trong cùng bệnh nhân.
3. **Nhãn ở cấp patch có độ bất định.** Các patch cắt từ ảnh nguồn thừa hưởng nhãn ảnh. Một patch đạt ngưỡng mô có thể chỉ chứa vùng lành hoặc mô đệm trong ảnh mang nhãn ác tính. Các thước đo và Grad-CAM vì vậy cần được diễn giải ở cấp patch với nhãn hiện có.
4. **Màu nhuộm và sai lệch giữa nguồn.** Nhánh `none` giữ màu của ảnh đầu vào sau các bước xử lý hình học của nhóm. Lịch sử xử lý màu trước khi bộ dữ liệu được phát hành có thể khác nhau giữa các nguồn. Sai khác tỷ lệ, màu, thiết bị và thành phần mô có thể cùng xuất hiện, nên nguyên nhân nhầm cơ quan trên test chéo vẫn chưa được xác định.
5. **Grad-CAM là phân tích định tính.** Mỗi bản đồ thể hiện vùng đóng góp dương vào logit của lớp mô hình dự đoán. Bản đồ gốc có lưới 7 × 7 và được nội suy để chồng lên patch. Mức màu được chuẩn hóa riêng cho từng bản đồ, nên phép đối chiếu chủ yếu dựa trên vị trí tương đối của vùng nổi bật. Bộ tám ảnh được chọn theo kết quả đúng/sai của hai checkpoint seed 0, do đó chỉ minh họa các trường hợp cụ thể. Việc xác định mô u hoặc mức trùng khớp với vùng bệnh cần chú giải mô học độc lập. [Selvaraju và cộng sự, ICCV 2017](https://openaccess.thecvf.com/content_iccv_2017/html/Selvaraju_Grad-CAM_Visual_Explanations_ICCV_2017_paper.html)

### 5.3. Hướng nghiên cứu tiếp theo (Future Work)
- Ứng dụng các mô hình nền tảng chuyên biệt cho mô bệnh học (Pathology Foundation Models như Phikon, UNI, Prov-GigaPath).
- Mở rộng phân đoạn tiêu bản WSI toàn phần và tích hợp đa phương thức (Multimodal CPath).

---

# PHẦN 2: KHUNG SLIDE BÁO CÁO BẢO VỆ (PRESENTATION SLIDE DECK)
*Thời lượng thuyết trình: 10 – 15 phút (16 Slide chuẩn)*

```
[Slide 1: Bìa] ───> [Slide 2: Đặt vấn đề] ───> [Slide 3: Nguy cơ rò rỉ]
       │
[Slide 4: Câu hỏi NC] ───> [Slide 5: Đa nguồn Dữ liệu] ───> [Slide 6: Ánh xạ 7 lớp]
       │
[Slide 7: Chia theo nhóm] ───> [Slide 8: Tiền xử lý & Macenko] ───> [Slide 9: Kiến trúc Mạng]
       │
[Slide 10: Thiết kế Thực nghiệm] ───> [Slide 11: Kết quả E1 (Leakage)] ───> [Slide 12: Kết quả E2 (Stain)]
       │
[Slide 13: Kiểm thử chéo] ───> [Slide 14: Grad-CAM] ───> [Slide 15: Hạn chế]
       │
[Slide 16: Kết luận & Q&A]
```

### Slide 1: Trang tiêu đề (Title Slide)
- **Tiêu đề:** ĐÁNH GIÁ TÍNH TỔNG QUÁT HÓA CỦA MÔ HÌNH HỌC SÂU TRÊN ẢNH MÔ BỆNH HỌC ĐA TRUNG TÂM
- **Phụ đề:** Phân loại 7 lớp, ảnh hưởng của cách chia tập và sai lệch giữa các nguồn
- **Người thực hiện & Giảng viên hướng dẫn.**

### Slide 2: Bối cảnh & Tính cấp thiết (Context & Motivation)
- **Hình ảnh:** Tiêu bản kính hiển vi nhuộm H&E của các mô Phổi, Đại tràng, Tuyến vú.
- **Nội dung:**
  + Bài toán của đề tài là phân loại patch H&E ở phổi, đại tràng và vú.
  + Thách thức thực tế: Sự sai lệch màu sắc (Domain Shift) và thiết bị chụp giữa các bệnh viện.

### Slide 3: Nguy cơ rò rỉ trong LC25000

- Khoảng 1.250 ảnh gốc tạo thành 25.000 ảnh qua biến đổi hình học.
- Nếu chia theo ảnh, các biến thể cùng nguồn có thể rơi vào cả train và test. Trình bày cách đối chiếu E1 và E2 ở Slide 11.

### Slide 4: Câu hỏi nghiên cứu

- So sánh mức suy giảm ngoài miền của ConvNeXt-Tiny và Swin-Tiny theo từng cơ quan.
- Đối chiếu chia theo ảnh với chia theo nhóm và đo tác động của Macenko theo nguồn.

### Slide 5: Năm nguồn dữ liệu

- **Nội bộ:** LC25000 dùng 24.949 ảnh và BreakHis 40× dùng 1.995 ảnh. Sau khi chia theo nhóm có 18.859 mẫu train, 4.041 val và 4.044 test.
- **Kiểm thử chéo:** LungHist700 có 14.557 patch từ 691 ảnh nguồn, CRC có 1.974 patch NORM/TUM, BACH có 13.581 patch từ 400 ảnh microscopy.

### Slide 6: Hệ thống Ánh xạ 7 Lớp Thống nhất (Unified 7-Class Scheme)
- **Sơ đồ cấu trúc lớp:**
  + Phổi: Lành tính (0), Tuyến ác tính (1), Vảy ác tính (2).
  + Đại tràng: Lành tính (3), Tuyến ác tính (4).
  + Tuyến vú: Lành tính (5), Ác tính (6).
- **Ý nghĩa:** Chuẩn hóa không gian phân loại chung cho nhiều cơ quan lâm sàng.

### Slide 7: Chia theo nhóm để giảm rò rỉ

- Ảnh LC25000 → tạo ứng viên bằng đặc trưng ảnh và pHash → kiểm chứng hình học → tái dựng họ ảnh → chia train/val/test theo nhóm.
- Kiểm tra manifest cho thấy 0 nhóm giao nhau giữa các tập. Nhóm LC25000 đại diện cho họ ảnh biến đổi. Mức độc lập theo bệnh nhân vẫn chưa xác định.

### Slide 8: Tạo patch và chuẩn hóa màu

- Đầu vào RGB 224 × 224. Trường nhìn 112 × 112 µm là mục tiêu danh định theo MPP đã gán.
- Với LungHist700 và BACH, lọc patch dưới 50% mô bằng ngưỡng nền trắng RGB.
- Hai nhánh `none` và `macenko` dùng cùng crop. Ảnh tham chiếu Macenko lấy từ LC25000 train.

### Slide 9: Kiến trúc Mô hình (Model Architectures)
- **Đối sánh hai trường phái:**
  + **ConvNeXt-Tiny:** Đại diện mạng tích chập hiện đại (Modern CNN) với kernel depthwise $7 \times 7$ trong block.
  + **Swin-Tiny:** Đại diện Vision Transformer phân cấp với cơ chế Shifted Local Window Self-Attention.

### Slide 10: Thiết kế 15 lượt chạy

- E1 có ba lượt ConvNeXt chia theo ảnh, nhánh `none`. E2 có 12 lượt chia theo nhóm gồm hai kiến trúc, hai nhánh màu và ba seed.
- Đánh giá checkpoint nội bộ và trên ba tập kiểm thử chéo. Chọn checkpoint theo macro-F1 val.

### Slide 11: Đối chiếu cách chia

- Accuracy test nội bộ của ConvNeXt nhánh `none` là 99,74 ± 0,12% khi chia theo ảnh và 92,50 ± 1,23% khi chia theo nhóm. Độ lệch chuẩn tính qua ba seed.

### Slide 12: Ảnh hưởng của Macenko

- Macro-F1 trung bình tăng ở CRC và BACH, giảm ở LungHist700 trên cả hai kiến trúc. Dùng bảng C5 ở mục 4.3.

### Slide 13: Mức suy giảm khi kiểm thử chéo

- Dùng bảng Δ macro-F1 theo cơ quan ở mục 4.3. Trình bày kèm accuracy 7 lớp, tỷ lệ nhầm cơ quan và accuracy khi giới hạn argmax theo cơ quan thật.

### Slide 14: Grad-CAM

- Dùng hai hình ở mục 4.4. Giữ cùng một ảnh đầu vào giữa hai mô hình để so sánh vị trí vùng nổi bật. CAM-07 minh họa hai kiểu sai khác nhau.

### Slide 15: Hạn chế

- MPP LC25000 và LungHist700 là ước lượng. Nguyên nhân nhầm cơ quan trên tập kiểm thử chéo vẫn chưa xác định.
- Họ ảnh LC25000 được tái dựng, BACH và CRC thiếu mã bệnh nhân đầy đủ, và patch có thể mang nhãn thừa hưởng từ ảnh nguồn. Grad-CAM dùng để minh họa định tính.

### Slide 16: Tổng kết & Hỏi đáp (Conclusion & Q&A)
- **Tóm tắt 3 kết luận chính của đề tài.**
- Lời cảm ơn và mời Hội đồng / Giảng viên đặt câu hỏi.
