# KHUNG BÁO CÁO TOÀN VĂN VÀ SLIDE THUYẾT TRÌNH BÀI TẬP LỚN
**Dự án:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Học Sâu trên Ảnh Mô Bệnh Học Đa Trung Tâm  
**Học phần:** Học máy (Machine Learning)  
**Ngày cập nhật:** 31/10/2026

---

# PHẦN 1: KHUNG BÁO CÁO TOÀN VĂN (FULL REPORT STRUCTURE)
*Dung lượng đề xuất: 20 – 30 trang (Chuẩn báo cáo đồ án môn học)*

## BÌA VÀ MỞ ĐẦU
- **Trang bìa chính & phụ:** Trường/Viện, Bộ môn, Tên đề tài, Giảng viên hướng dẫn, Danh sách sinh viên thực hiện và phân công đóng góp.
- **Tóm tắt báo cáo (Abstract) - Tiếng Việt & Tiếng Anh:** Nêu bối cảnh, bài toán rò rỉ dữ liệu của LC25000, phương pháp đề xuất (Group-based Split, Macenko Normalization, MPP Harmonization), kết quả chính và ý nghĩa học thuật.
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
- **Thách thức 2 - Rò rỉ dữ liệu ảo (Data Leakage):** Nhiều tập dữ liệu công khai (tiêu biểu là LC25000) được nhân bản từ một lượng nhỏ tiêu bản gốc. Việc chia ngẫu nhiên dẫn đến hiệu năng ảo (99–100%) nhưng mô hình sụp đổ khi thử nghiệm ngoài thực tế.
### 1.4. Câu hỏi nghiên cứu (Research Questions) & Giả thuyết thực nghiệm
- **Câu hỏi mở:** *"Liệu việc kết hợp chuẩn hóa quang phổ màu Macenko cùng chiến lược phân chia không rò rỉ dữ liệu có giúp mô hình học sâu khắc phục hiện tượng sai lệch miền và đạt được tính tổng quát hóa cao khi kiểm thử ngoại miền (OOD) hay không?"*
- **3 Giả thuyết khoa học:**
  - *H1 (Về rò rỉ dữ liệu ở LC25000):* Chia ngẫu nhiên tạo độ chính xác ảo >99%; chia theo cụm (Group Split) phản ánh đúng năng lực thật của mô hình.
  - *H2 (Về vai trò chuẩn hóa Macenko):* Giảm thiểu khoảng cách phân phối đặc trưng giữa các trung tâm, cải thiện F1-score trên dữ liệu kiểm thử chéo.
  - *H3 (Về tính tin cậy & độ hiệu chuẩn tỷ lệ vật lý - MPP):* Đồng bộ trường nhìn và tỷ lệ phóng đại tế bào là tiền đề bắt buộc trước khi xử lý màu sắc.
### 1.5. Đóng góp chính của đề tài

---

## CHƯƠNG 2: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ KHOA HỌC (LITERATURE REVIEW)
### 2.1. Khảo sát các hướng tiếp cận học sâu trên ảnh mô bệnh học
- Các mô hình phân cấp tiên tiến: **Swin Transformer V2** (Shifted Windows, Continuous Position Bias).
- Các mạng gọn nhẹ có tích hợp cơ chế giải thích: **XLLC-Net** với kỹ thuật bản đồ nhiệt **Grad-CAM**.
- Các kỹ thuật kết hợp: **Feature Fusion** (VGG/GoogLeNet + Handcrafted LBP/GLCM) và **Ensemble Learning** (Multi-CNNs + Random Forest/SVM).
### 2.2. Phân tích lỗ hổng phương pháp luận trong các công bố quốc tế
- Bản chất bộ dữ liệu LC25000: Sinh từ ~1.250 ảnh gốc qua phép xoay/lật đối xứng $D_4$.
- Lỗi phân chia ngẫu nhiên (Random Train/Test Split) gây rò rỉ dữ liệu nghiêm trọng, dẫn đến báo cáo tràn lan chỉ số ảo 99–100%.
- Tình trạng thiếu vắng các kiểm nghiệm chéo ngoài miền (Cross-dataset Validation).
### 2.3. Bảng so sánh tổng hợp các công trình tiêu biểu
*(Bảng so sánh 8 công trình đã xây dựng ở mục C9).*
### 2.4. Cơ sở lý thuyết kỹ thuật bổ trợ
- **Mô hình vật lý quang học Macenko:** Định luật Beer-Lambert, không gian Mật độ quang học (Optical Density - OD), phép chiếu PCA và tìm vector phổ thuốc nhuộm Hematoxylin & Eosin.
- **Tỷ lệ phóng đại và độ phân giải vật lý (Microns Per Pixel - MPP):** Vai trò của kích thước nhân tế bào và hồng cầu chuẩn (7,5 µm) trong việc chuẩn hóa trường quan sát (Field of View - FOV).
- **Kiến trúc mạng nơ-ron đối sánh:** ConvNeXt-Tiny (đại diện mạng tích chập hiện đại) và Swin-Tiny (đại diện Transformer phân cấp).

---

## CHƯƠNG 3: NGUYÊN LIỆU VÀ PHƯƠNG PHÁP NGHIÊN CỨU (MATERIALS & METHODS)
### 3.1. Tổng quan 5 bộ dữ liệu tích hợp
1. **LC25000 (In-Domain Training & Testing):** 25.000 ảnh kích thước $768 \times 768$ (Phổi & Đại tràng).
2. **LungHist700 (Out-of-Domain Pulmonary Test):** 691 tiêu bản WSI $1200 \times 1600$, độ phóng đại 20x và 40x (Nature Sci Data 2024).
3. **CRC-VAL-HE-7K (Out-of-Domain Colorectal Test):** Tập kiểm định 1.974 patch đại tràng độc lập từ 50 bệnh nhân (Kather et al., 2019).
4. **BACH (BreAst Cancer Histology - OOD Test):** 400 ảnh vi thể nhuộm H&E ung thư vú.
5. **BreakHis 40x (Breast Tumor Histology - OOD Test):** 1.995 ảnh mô học tuyến vú chụp tại độ phóng đại 40x (MPP ~0,49 µm).
### 3.2. Hệ thống phân loại 7 lớp bệnh học thống nhất (Unified 7-Class Ontology)
- Chi tiết ánh xạ nhãn: `lung_normal` (0), `lung_aca` (1), `lung_scc` (2), `colon_normal` (3), `colon_aca` (4), `breast_benign` (5), `breast_malignant` (6).
### 3.3. Thuật toán phát hiện ảnh trùng và phân chia chống rò rỉ (Group Split)
- Kỹ thuật băm tri giác bất biến hình học (**Rotation-Invariant pHash**): gom 25.000 ảnh LC25000 về các cụm mô gốc (`cluster_id`).
- Quy trình phân chia Stratified Group Split (70% Train, 15% Val, 15% Test): đảm bảo toàn bộ biến thể của cùng một cụm nằm trọn vẹn trong một tập, triệt tiêu 100% rò rỉ dữ liệu.
- Thiết lập tập đối chứng chia ngẫu nhiên (Random Split) để kiểm chứng giả thuyết H1.
### 3.4. Pipeline tiền xử lý và chuẩn hóa dữ liệu
- **Đồng bộ trường nhìn (FOV Harmonization):** Đưa toàn bộ các nguồn dữ liệu về chuẩn vật lý 112 µm và kích thước đầu vào $224 \times 224$.
- **Lọc vùng mô (Tissue Segmentation):** Ngưỡng Otsu trong không gian màu HSV nhằm loại bỏ các patch nền trắng/kính rỗng (>50% background).
- **Chuẩn hóa màu Macenko:** Tách và chuẩn hóa phổ màu H&E theo ảnh mẫu tham chiếu chuẩn duy nhất từ tập huấn luyện.
### 3.5. Thiết kế và thiết lập huấn luyện mô hình
- Cấu hình mạng: ConvNeXt-Tiny và Swin-Tiny.
- Hàm mất mát có bù trừ mất cân bằng lớp (Inverse Frequency Class-weighted Cross-Entropy).
- Tối ưu hóa: AdamW, Learning Rate $10^{-4}$, Cosine Warmup, Weight Decay 0.05, Mixed Precision (bfloat16).

---

## CHƯƠNG 4: KẾT QUẢ VÀ BÀN LUẬN THỰC NGHIỆM (EXPERIMENTS & RESULTS)
### 4.1. Thiết kế ma trận thực nghiệm
- **Thực nghiệm E1 (Chứng minh Data Leakage):** So sánh hiệu năng mô hình khi chia Random Split vs. Group Split trên LC25000.
- **Thực nghiệm E2 (Đánh giá Stain Normalization & Model Architectures):** So sánh `None` vs. `Macenko` trên ConvNeXt-Tiny và Swin-Tiny qua 3 seeds ngẫu nhiên.
- **Thực nghiệm E3 (Kiểm định chéo ngoài miền - Out-of-Domain Generalization):** Đánh giá độ suy giảm hiệu năng khi kiểm thử trên LungHist700, CRC-VAL-HE-7K và BACH.
### 4.2. Thước đo đánh giá chuyên sâu
- Macro-averaged F1-Score, Balanced Accuracy, Cross-Domain F1 Drop ($\Delta F1$).
- Tỷ lệ nhầm lẫn cơ quan (Organ Confusion Rate) và độ chính xác nội bộ cơ quan (Within-Organ Accuracy).
### 4.3. Phân tích kết quả chi tiết
- **Bằng chứng về rò rỉ dữ liệu:** Sự sụt giảm của Accuracy từ mức giả tạo >99% (Random) về mức thực chất ~92% (Group Split).
- **Hiện tượng suy giảm ngoài miền:** Nguyên nhân khiến 97% mẫu CRC và 84% mẫu BACH bị đoán nhầm sang cơ quan khác khi chưa đồng bộ MPP.
- **Tác động của Macenko:** Cải thiện độ ổn định và giảm thiểu biến thiên màu giữa các nguồn.
### 4.4. Trực quan hóa và giải thích mô hình
- Đối chiếu ma trận nhầm lẫn (Confusion Matrix) giữa các kịch bản.
- Phân tích Grad-CAM trên các trường hợp đoán đúng và đoán sai đặc trưng bệnh lý.

---

## CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (CONCLUSION)
### 5.1. Kết luận chính
- Khẳng định tính cấp thiết của việc chia tập chống rò rỉ dữ liệu và kiểm định chéo trong AI y tế.
- Khái quát hóa bài học kinh nghiệm về việc đồng bộ tỷ lệ vật lý và quang phổ màu sắc.
### 5.2. Các hạn chế tồn tại (Limitations)
- Bộ dữ liệu LC25000 chưa có thông tin giải phẫu bệnh chi tiết từng bệnh nhân (Patient ID).
- Việc ước lượng MPP dựa trên thước đo sinh học (hồng cầu) đòi hỏi kiểm tra độc lập thủ công.
### 5.3. Hướng nghiên cứu tiếp theo (Future Work)
- Ứng dụng các mô hình nền tảng chuyên biệt cho mô bệnh học (Pathology Foundation Models như Phikon, UNI, Prov-GigaPath).
- Mở rộng phân đoạn tiêu bản WSI toàn phần và tích hợp đa phương thức (Multimodal CPath).

---

# PHẦN 2: KHUNG SLIDE BÁO CÁO BẢO VỆ (PRESENTATION SLIDE DECK)
*Thời lượng thuyết trình: 10 – 15 phút (16 Slide chuẩn)*

```
[Slide 1: Bìa] ───> [Slide 2: Đặt vấn đề] ───> [Slide 3: Nghịch lý Y văn]
       │
[Slide 4: Câu hỏi NC] ───> [Slide 5: Đa nguồn Dữ liệu] ───> [Slide 6: Ánh xạ 7 lớp]
       │
[Slide 7: Gom cụm Chống Leak] ───> [Slide 8: Tiền xử lý & Macenko] ───> [Slide 9: Kiến trúc Mạng]
       │
[Slide 10: Thiết kế Thực nghiệm] ───> [Slide 11: Kết quả E1 (Leakage)] ───> [Slide 12: Kết quả E2 (Stain)]
       │
[Slide 13: Kết quả E3 (Cross-domain)] ───> [Slide 14: Thước đo Tế bào MPP] ───> [Slide 15: Thảo luận]
       │
[Slide 16: Kết luận & Q&A]
```

### Slide 1: Trang tiêu đề (Title Slide)
- **Tiêu đề:** ĐÁNH GIÁ TÍNH TỔNG QUÁT HÓA CỦA MÔ HÌNH HỌC SÂU TRÊN ẢNH MÔ BỆNH HỌC ĐA TRUNG TÂM
- **Phụ đề:** Bài toán Phân loại 7 Lớp, Khắc phục Rò rỉ Dữ liệu và Sai lệch Miền (Domain Shift)
- **Người thực hiện & Giảng viên hướng dẫn.**

### Slide 2: Bối cảnh & Tính cấp thiết (Context & Motivation)
- **Hình ảnh:** Tiêu bản kính hiển vi nhuộm H&E của các mô Phổi, Đại tràng, Tuyến vú.
- **Nội dung:** 
  + AI trong giải phẫu bệnh số (CPath) hỗ trợ chẩn đoán ung thư sớm.
  + Thách thức thực tế: Sự sai lệch màu sắc (Domain Shift) và thiết bị chụp giữa các bệnh viện.

### Slide 3: Nghịch lý trong Y văn (Literature Paradox: 99% vs. Reality)
- **Biểu đồ/Bảng minh họa:** Danh sách các bài báo cáo 99% - 100% trên LC25000 (Swin Transformer V2, XLLC-Net, Ensembles).
- **Điểm nhấn cốt lõi:**
  + LC25000 chỉ có ~1.250 ảnh gốc, 25.000 ảnh là kết quả của phép xoay/lật.
  + Việc chia ngẫu nhiên (Random Split) làm rò rỉ dữ liệu -> Mô hình "học vẹt", độ chính xác 99% là ảo!
  + Hầu như không có bài kiểm thử chéo sang bệnh viện khác.

### Slide 4: Câu hỏi nghiên cứu & Mục tiêu đề tài (Research Question & Objectives)
- **Câu hỏi mở:** Liệu phân chia chống rò rỉ kết hợp chuẩn hóa Macenko có giúp mô hình tổng quát hóa ngoại miền?
- **3 Mục tiêu cụ thể:**
  1. Loại bỏ rò rỉ dữ liệu bằng Group Split.
  2. Kiểm định chéo trên các tập dữ liệu ngoài miền (LungHist700, CRC-VAL, BACH, BreakHis).
  3. Đánh giá vai trò của chuẩn hóa màu Macenko và đồng bộ tỷ lệ vật lý tế bào (MPP).

### Slide 5: Hệ sinh thái 5 Bộ Dữ liệu (Multi-Center Datasets)
- **Bảng trực quan:** 
  + Nội miền: LC25000 (25.000 ảnh).
  + Ngoại miền: LungHist700 (691 WSI), CRC-VAL-HE-7K (1.974 patch), BACH (400 ảnh), BreakHis 40x (1.995 ảnh).
- **Hình ảnh minh họa:** Sự khác biệt rõ rệt về màu sắc và góc chụp giữa các bộ dữ liệu.

### Slide 6: Hệ thống Ánh xạ 7 Lớp Thống nhất (Unified 7-Class Scheme)
- **Sơ đồ cấu trúc lớp:**
  + Phổi: Lành tính (0), Tuyến ác tính (1), Vảy ác tính (2).
  + Đại tràng: Lành tính (3), Tuyến ác tính (4).
  + Tuyến vú: Lành tính (5), Ác tính (6).
- **Ý nghĩa:** Chuẩn hóa không gian phân loại chung cho nhiều cơ quan lâm sàng.

### Slide 7: Giải pháp Chống rò rỉ Dữ liệu (Leak-Free Group Clustering)
- **Sơ đồ thuật toán:**
  $$\text{Ảnh LC25000} \longrightarrow \text{Rotation-Invariant pHash} \longrightarrow \text{Gom cụm} \longrightarrow \text{Stratified Group Split}$$
- **Khẳng định:** 100% các biến thể của cùng một lát cắt nằm trọn trong 1 tập; 0% rò rỉ dữ liệu.

### Slide 8: Tiền xử lý: Lọc mô, Đồng bộ FOV & Chuẩn hóa Macenko
- **Quy trình:**
  + Lọc mô bằng Otsu thresholding (loại bỏ phông nền rỗng).
  + Chuyển đổi Optical Density (Beer-Lambert Law) và trích xuất vector màu H&E.
  + Chuẩn hóa về một ảnh mốc tham chiếu duy nhất.

### Slide 9: Kiến trúc Mô hình (Model Architectures)
- **Đối sánh hai trường phái:**
  + **ConvNeXt-Tiny:** Đại diện mạng tích chập hiện đại (Modern CNN) với receptive field lớn ($7 \times 7$).
  + **Swin-Tiny:** Đại diện Vision Transformer phân cấp với cơ chế Shifted Local Window Self-Attention.

### Slide 10: Thiết kế Thực nghiệm (Experimental Setup)
- **Khung thực nghiệm:**
  + E1: So sánh Random Split (đối chứng) vs. Group Split (chống rò rỉ).
  + E2: So sánh Không chuẩn hóa màu (`None`) vs. `Macenko` qua 3 seeds ngẫu nhiên.
  + E3: Kiểm thử chéo ngoại vi (Out-of-Distribution Testing).
- Cấu hình huấn luyện: Class-weighting, AdamW, Mixed Precision.

### Slide 11: Kết quả Thực nghiệm E1: Bóc trần "Hiệu năng Ảo" (Data Leakage Exposed)
- **Biểu đồ so sánh:**
  + Random Split: Accuracy đạt **>99%** (tái lập lại các kết quả trong y văn).
  + Group Split: Accuracy thực chất ở mức **~92%**.
- **Kết luận:** Chứng minh thành công Giả thuyết H1 về sự tồn tại của rò rỉ dữ liệu.

### Slide 12: Kết quả Thực nghiệm E2: Vai trò của Chuẩn hóa Màu Macenko
- **Bảng số liệu:** F1-score và Accuracy giữa `None` và `Macenko` trên ConvNeXt và Swin.
- **Quan sát:** Macenko giúp làm mịn không gian đặc trưng và cải thiện tính ổn định giữa các lần chạy.

### Slide 13: Kết quả Thực nghiệm E3: Thử thách Kiểm thử Chéo Ngoài miền (Cross-Dataset Drop)
- **Số liệu gây sốc:**
  + LungHist700: Accuracy tụt xuống ~38,4% (ngay cả cùng cơ quan phổi cũng chỉ đạt ~48,9%).
  + CRC-VAL: 97% mẫu bị đoán nhầm sang cơ quan khác.
- **Phân tích:** Minh chứng hùng hồn cho thấy mô hình học sâu rất dễ thất bại khi gặp Domain Shift.

### Slide 14: Phát hiện then chốt về Tỷ lệ Phóng đại Vật lý (Physical Scale / MPP)
- **Hình ảnh đo đạc tế bào:** Thước đo kích thước nhân tế bào và hồng cầu (7,5 µm).
- **Phát hiện:** Nhân tế bào LC25000 bị phóng đại gấp ~1,5 - 2 lần so với CRC, dẫn đến hiện tượng mô hình nhận nhầm đặc trưng cơ quan. Việc đồng bộ MPP là điều kiện tiên quyết.

### Slide 15: Thảo luận & Ý nghĩa Lâm sàng (Discussion & Clinical Impact)
- AI y tế không thể chỉ dựa vào một bộ dữ liệu nội bộ duy nhất.
- Kiểm thử chéo ngoại miền và kiểm soát rò rỉ dữ liệu là tiêu chuẩn đạo đức và an toàn bắt buộc trước khi đưa vào bệnh viện.

### Slide 16: Tổng kết & Hỏi đáp (Conclusion & Q&A)
- **Tóm tắt 3 kết luận chính của đề tài.**
- Lời cảm ơn và mời Hội đồng / Giảng viên đặt câu hỏi.
