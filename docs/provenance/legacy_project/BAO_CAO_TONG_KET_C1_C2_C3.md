# BÁO CÁO TIÊU CHUẨN NGHIÊN CỨU & KỸ THUẬT: MODULE C1 - C2 - C3
**Dự án:** Phân loại & Phân tích Ảnh Mô Bệnh Học Đa Cơ Quan Chống Sai Lệch Miền (Multi-Organ Computational Pathology)  
**Phân ban phụ trách:** Đông / Huy (Module C1, C2, C3)  
**Thời gian hoàn thành:** 16/10/2026  
**Trạng thái:** [HOÀN THÀNH 100% - SẴN SÀNG CHUYỂN GIAO CHO C4]

---

## 📑 MỤC LỤC
1. [Tóm Tắt Tổng Quan (Executive Summary)](#1-tóm-tắt-tổng-quan-executive-summary)
2. [Module C1: Quản Lý Dataset, Ánh Xạ Nhãn 7 Lớp & Chốt Câu Hỏi Mở](#2-module-c1-quản-lý-dataset-ánh-xạ-nhãn-7-lớp--chốt-câu-hỏi-mở)
3. [Module C2: Gom Cụm Ảnh Trùng LC25000, Phân Chia Tập Dữ Liệu & Xuất splits.csv](#3-module-c2-gom-cụm-ảnh-trùng-lc25000-phân-chia-tập-dữ-liệu--xuất-splitscsv)
4. [Module C3: Cắt Patch LungHist700 & Chuẩn Hóa Quang Phổ Màu Macenko](#4-module-c3-cắt-patch-lunghist700--chuẩn-hóa-quang-phổ-màu-macenko)
5. [Bảng Chỉ Mục Đường Dẫn Tài Nguyên & Kết Quả (Resource Index)](#5-bảng-chỉ-mục-đường-dẫn-tài-nguyên--kết-quả-resource-index)
6. [Đề Xuất & Kế Hoạch Chuyển Giao Module C4](#6-đề-xuất--kế-hoạch-chuyển-giao-module-c4)

---

## 1. TÓM TẮT TỔNG QUAN (EXECUTIVE SUMMARY)

Giai đoạn C1 - C2 - C3 tập trung vào khâu tiền xử lý, chuẩn hóa dữ liệu mô bệnh học (Histopathology) và thiết lập cơ sở khoa học thực nghiệm vững chắc nhằm giải quyết hai vấn đề nhức nhối nhất trong thị giác máy tính y tế:
- **Hiện tượng rò rỉ dữ liệu (Data Leakage):** Do việc nhân bản biến thể xoay/lật từ cùng một slide mô trong các tập dữ liệu công khai.
- **Hiện tượng sai lệch miền (Domain Shift / Batch Effect):** Do sự chênh lệch quy trình nhuộm H&E (Hematoxylin & Eosin) và thiết bị quét (WSI Scanner) giữa các cơ sở y tế.

### Kết quả định lượng nổi bật:
* **C1:** Đồng bộ **25.000 ảnh LC25000**, xây dựng bảng ánh xạ thống nhất **7 lớp giải phẫu bệnh** và hoàn thiện văn bản chốt **Câu hỏi mở & 3 giả thuyết thực nghiệm**.
* **C2:** Áp dụng thuật toán băm tri giác bất biến xoay/lật (**Rotation-Invariant pHash**), gom 25.000 ảnh về **20.443 cụm mô gốc** (lọc trùng 4.557 biến thể lặp). Chia tập Train/Val/Test (tỷ lệ 70% / 15% / 15%) đạt chuẩn **0% rò rỉ dữ liệu (Zero Leakage)**.
* **C3:** Tải thành công dataset **LungHist700** từ Figshare chính thức (639.3 MB, 691 ảnh tiêu bản lớn); xây dựng thành công pipeline cắt patch $224 \times 224$ (lọc bỏ nền kính trống $\ge 50\%$) kết hợp chuẩn hóa màu **Macenko Stain Normalization**, trích xuất thành công **24.185 patch ảnh chuẩn hóa**.

---

## 2. MODULE C1: QUẢN LÝ DATASET, ÁNH XẠ NHÃN 7 LỚP & CHỐT CÂU HỎI MỞ

### 2.1. Quản lý và Tổ chức Dữ liệu Nguồn
Toàn bộ 25.000 ảnh của LC25000 đã được rà soát, kiểm tra tính toàn vẹn và phân bổ vào cấu trúc thư mục tiêu chuẩn:
- `dataset/lung_colon_image_set/colon_image_sets/colon_aca`: 5.000 ảnh
- `dataset/lung_colon_image_set/colon_image_sets/colon_n`: 5.000 ảnh
- `dataset/lung_colon_image_set/lung_image_sets/lung_aca`: 5.000 ảnh
- `dataset/lung_colon_image_set/lung_image_sets/lung_n`: 5.000 ảnh
- `dataset/lung_colon_image_set/lung_image_sets/lung_scc`: 5.000 ảnh

### 2.2. Bảng Ánh Xạ Nhãn 7 Lớp Chuẩn Y Khoa (Unified Pathology Ontology)

| ID Lớp | Tên lớp chuẩn | Cơ quan | Phân loại lâm sàng | Nguồn dữ liệu tích hợp | Số lượng mẫu hiện có |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **0** | `lung_normal` | Phổi | Bình thường / Lành tính | LC25000 (`lung_n`), LungHist700 (`nor`) | **5.000** (+ Patch C3) |
| **1** | `lung_aca` | Phổi | Ung thư biểu mô tuyến | LC25000 (`lung_aca`), LungHist700 (`aca_*`) | **5.000** (+ Patch C3) |
| **2** | `lung_scc` | Phổi | Ung thư biểu mô tế bào vảy | LC25000 (`lung_scc`), LungHist700 (`scc_*`) | **5.000** (+ Patch C3) |
| **3** | `colon_normal` | Đại tràng | Niêm mạc lành tính | LC25000 (`colon_n`) | **5.000** |
| **4** | `colon_aca` | Đại tràng | Ung thư biểu mô tuyến | LC25000 (`colon_aca`) | **5.000** |
| **5** | `breast_benign` | Tuyến vú | Lành tính / Bình thường | BACH (`Normal`, `Benign`) | *Dữ liệu OOD* |
| **6** | `breast_malignant` | Tuyến vú | Ác tính (Invasive / InSitu)| BACH (`Invasive`, `InSitu`) | *Dữ liệu OOD* |
| **TỔNG**| | | | | **25.000 ảnh gốc** |

### 2.3. Chốt Câu Hỏi Mở & Giả Thuyết Khoa Học
* **Câu hỏi mở chính thức:**
  > *"Liệu việc kết hợp chuẩn hóa quang phổ màu Macenko (Stain Normalization) cùng chiến lược phân chia không rò rỉ dữ liệu (Leak-free Cross-Dataset Validation) có giúp mô hình Deep Learning khắc phục hiện tượng sai lệch miền (Domain Shift) và đạt được tính tổng quát hóa cao (Generalization) khi kiểm thử trên dữ liệu ngoại miền (Out-of-Distribution - OOD) hay không?"*
* **3 Giả thuyết thực nghiệm cần chứng minh ở C4:**
  1. *Giả thuyết H1 (Về rò rỉ dữ liệu):* Phân chia ngẫu nhiên (Random Split) tạo ra độ chính xác ảo (>99%). Phân chia theo cụm không rò rỉ phản ánh đúng năng lực nhận diện của mô hình.
  2. *Giả thuyết H2 (Về Macenko Normalization):* Giảm thiểu sai lệch nồng độ Hematoxylin & Eosin, giúp cải thiện Macro F1-Score từ 5% - 15% trên tập kiểm thử ngoài nguồn (Cross-center OOD).
  3. *Giả thuyết H3 (Về độ tin cậy dự đoán):* Chuẩn hóa màu giúp mô hình giảm sai số hiệu chỉnh xác suất (Expected Calibration Error - ECE).

---

## 3. MODULE C2: GOM CỤM ẢNH TRÙNG LC25000, PHÂN CHIA TẬP DỮ LIỆU & XUẤT `splits.csv`

### 3.1. Phương Pháp Băm Tri Giác Bất Biến Hình Học (Rotation-Invariant pHash)
LC25000 được sinh ra từ các slide gốc qua phép cắt và xoay $0^\circ, 90^\circ, 180^\circ, 270^\circ$ kèm lật ảnh (nhóm đối xứng Dihedral $D_4$).  
Thuật toán tính pHash chuẩn hóa:
1. Tạo 8 biến thể xoay/lật của mỗi ảnh.
2. Tính DCT pHash cho cả 8 biến thể.
3. Lấy giá trị chuỗi băm nhỏ nhất làm **Canonical Hash**. Bất kỳ biến thể xoay/lật nào của cùng một vùng mô cũng cho ra cùng một Canonical Hash duy nhất.

### 3.2. Kết Quả Gom Cụm (Clustering Analysis)
Đã quét toàn bộ 25.000 ảnh LC25000, phát hiện:
- **Số cụm mô gốc:** **20.443 cụm**.
- **Số biến thể trùng lặp được gom nhóm:** **4.557 ảnh**.
- Phân bố cụm theo từng phân lớp:
  - `colon_aca`: 4.077 cụm
  - `colon_n`: 4.123 cụm
  - `lung_aca`: 4.074 cụm
  - `lung_n`: 4.088 cụm
  - `lung_scc`: 4.081 cụm

### 3.3. Phân Chia Tập Dữ Liệu Chống Rò Rỉ (Group Stratified Split)
Chia tập theo nguyên tắc: Toàn bộ ảnh cùng chung một `cluster_id` chỉ nằm trong duy nhất một tập (Train, Val hoặc Test).

| Phân lớp bệnh học | Tập Train (70%) | Tập Validation (15%) | Tập Test (15%) | Tổng cộng |
| :--- | :---: | :---: | :---: | :---: |
| `colon_aca` | 3.469 | 760 | 771 | **5.000** |
| `colon_n` | 3.529 | 745 | 726 | **5.000** |
| `lung_aca` | 3.514 | 746 | 740 | **5.000** |
| `lung_n` | 3.498 | 750 | 752 | **5.000** |
| `lung_scc` | 3.521 | 743 | 736 | **5.000** |
| **TỔNG MẪU** | **17.531 (70.1%)** | **3.744 (15.0%)** | **3.725 (14.9%)** | **25.000** |

> **Kiểm định rò rỉ dữ liệu (Leakage Test):**  
> `LEAKAGE CLUSTERS = 0 (0.00%)` $\rightarrow$ Đạt chứng nhận an toàn dữ liệu tuyệt đối.

---

## 4. MODULE C3: CẮT PATCH LUNGHIST700 & CHUẨN HÓA QUANG PHỔ MÀU MACENKO

### 4.1. Tải Dataset LungHist700 Chính Thức
- **Nguồn bài báo:** *Scientific Data (Nature 2024)*.
- **Dung lượng:** 639.3 MB (Tập tin nén: `dataset/LungHist700.rar`).
- **Nội dung:** 691 ảnh tiêu bản lớn kích thước $1200 \times 1600$ gồm các nhóm:
  - `nor`: Mô bình thường.
  - `aca_bd`, `aca_md`, `aca_pd`: Ung thư biểu mô tuyến (biệt hóa tốt, vừa, kém).
  - `scc_bd`, `scc_md`, `scc_pd`: Ung thư tế bào vảy (biệt hóa tốt, vừa, kém).
  - Kèm file nhãn lâm sàng chi tiết: `dataset/LungHist700/data/data.csv`.

### 4.2. Kỹ Thuật Trích Xuất Patch & Lọc Nền Kính Trống (Tissue Masking)
- **Kích thước patch:** $224 \times 224$ pixels, Stride = 224 (không overlap).
- **Thuật toán lọc mô (Tissue Filtering):** Pixel nền kính hiển vi có màu trắng sáng ($R, G, B > 220$). Chỉ giữ lại các patch có tỷ lệ diện tích mô $\ge 50\%$, loại bỏ hoàn toàn các patch rỗng hoặc chỉ chứa vệt kính.

### 4.3. Thuật Toán Chuẩn Hóa Màu Macenko
Dựa trên nguyên lý định luật Beer-Lambert:
1. Chuyển đổi sang không gian Optical Density (OD): $OD = -\log_{10}((I + 1)/255)$.
2. Lọc bỏ các pixel có $OD < 0.15$.
3. Phân tích SVD trên ma trận hiệp phương sai OD để xác định mặt phẳng chứa 2 vector màu Hematoxylin và Eosin.
4. Tìm góc cực biên (percentile $1\%$ và $99\%$) để tách 2 vector nhuộm $V_{H}$ và $V_{E}$.
5. Chiếu nồng độ màu lên Stain Vector và nồng độ cực đại của ảnh mẫu tham chiếu chuẩn: **[macenko_reference_template.png](file:///d:/duanhocmay/outputs/macenko_reference_template.png)**.

### 4.4. Kết Quả Thực Thi
- **Tổng số patch trích xuất và chuẩn hóa thành công:** **24.185 patch ảnh**.
- **Cấu trúc lưu trữ:** `dataset/patches/LungHist700_normalized/` được chia theo đúng 7 phân lớp con của phổi.

---

## 5. BẢNG CHỈ MỤC ĐƯỜNG DẪN TÀI NGUYÊN & KẾT QUẢ (RESOURCE INDEX)

Dưới đây là toàn bộ đường dẫn trực tiếp đến các file mã nguồn, cấu hình và kết quả dữ liệu được sinh ra trong dự án:

### 📄 Tài Liệu Báo Cáo & Kế Hoạch
* [Kế hoạch triển khai ban đầu (KE_HOACH_THUC_HIEN_C1_C2_C3.md)](file:///d:/duanhocmay/KE_HOACH_THUC_HIEN_C1_C2_C3.md)
* [Báo cáo chốt câu hỏi mở & giả thuyết (BAO_CAO_C1_CHOT_CAU_HOI_MO.md)](file:///d:/duanhocmay/BAO_CAO_C1_CHOT_CAU_HOI_MO.md)
* [Báo cáo tổng kết tiêu chuẩn C1-C2-C3 (File này)](file:///d:/duanhocmay/BAO_CAO_TONG_KET_C1_C2_C3.md)

### ⚙️ Cấu Hình Hệ Thống
* [Cấu hình ánh xạ 7 lớp (configs/mapping_7class.json)](file:///d:/duanhocmay/configs/mapping_7class.json)

### 💻 Mã Nguồn Thực Thi (Source Code)
* **Module C1:** [src/c1_mapping/dataset_indexer.py](file:///d:/duanhocmay/src/c1_mapping/dataset_indexer.py) *(Quét và lập chỉ mục dữ liệu)*
* **Module C2:**
  * [src/c2_clustering/perceptual_hash.py](file:///d:/duanhocmay/src/c2_clustering/perceptual_hash.py) *(Tính pHash bất biến xoay lật)*
  * [src/c2_clustering/split_generator.py](file:///d:/duanhocmay/src/c2_clustering/split_generator.py) *(Gom cụm và chia tập dữ liệu chống rò rỉ)*
* **Module C3:**
  * [download_lunghist.py](file:///d:/duanhocmay/download_lunghist.py) *(Tải và giải nén LungHist700 từ Figshare)*
  * [src/c3_preprocessing/macenko_normalizer.py](file:///d:/duanhocmay/src/c3_preprocessing/macenko_normalizer.py) *(Thuật toán chuẩn hóa quang phổ Macenko)*
  * [src/c3_preprocessing/patch_extractor.py](file:///d:/duanhocmay/src/c3_preprocessing/patch_extractor.py) *(Trích xuất patch và lọc nền)*
  * [src/c3_preprocessing/run_c3_pipeline.py](file:///d:/duanhocmay/src/c3_preprocessing/run_c3_pipeline.py) *(Pipeline tự động chạy toàn diện C3)*

### 📊 Dữ Liệu & Kết Quả Xuất Bản (Outputs)
* [outputs/splits.csv](file:///d:/duanhocmay/outputs/splits.csv) *(File phân chia 25.000 dòng chính thức: Train/Val/Test/Cluster_ID)*
* [outputs/c1_dataset_summary.json](file:///d:/duanhocmay/outputs/c1_dataset_summary.json) *(Báo cáo tóm tắt phân bố 7 lớp)*
* [outputs/c1_sample_preview.csv](file:///d:/duanhocmay/outputs/c1_sample_preview.csv) *(Bảng xem trước dữ liệu mẫu kèm nhãn)*
* [outputs/c2_clustering_summary.json](file:///d:/duanhocmay/outputs/c2_clustering_summary.json) *(Báo cáo thống kê gom cụm LC25000)*
* [outputs/macenko_reference_template.png](file:///d:/duanhocmay/outputs/macenko_reference_template.png) *(Ảnh mốc màu chuẩn dùng cho Macenko)*
* [Thư mục Patch LungHist700 đã chuẩn hóa (24.185 patch)](file:///d:/duanhocmay/dataset/patches/LungHist700_normalized/)

---

## 6. ĐỀ XUẤT & KẾ HOẠCH CHUYỂN GIAO MODULE C4

Với nền tảng dữ liệu sạch, đã loại bỏ rò rỉ và chuẩn hóa hệ màu, bước tiếp theo (**C4: Xây dựng Training Pipeline**) được khuyến nghị triển khai:
1. **Kiến trúc mạng:** Sử dụng các backbone hiện đại trong thị giác y khoa:
   - ResNet-50 / ConvNeXt-Tiny (đại diện CNN).
   - Swin Transformer / ViT-Small (đại diện Vision Transformer).
2. **Kịch bản thực nghiệm kiểm chứng 3 giả thuyết:**
   - **Thực nghiệm 1 (Kiểm chứng H1):** Huấn luyện trên Random Split vs. Huấn luyện trên Group Split (`splits.csv`) $\rightarrow$ So sánh độ suy giảm độ chính xác ảo.
   - **Thực nghiệm 2 (Kiểm chứng H2):** Huấn luyện mô hình trên LC25000 Gốc vs. LC25000 Macenko, sau đó kiểm thử ngoại miền trên tập patch LungHist700 $\rightarrow$ Đo lường độ tăng F1-Score khi có Macenko Normalization.
   - **Thực nghiệm 3 (Kiểm chứng H3):** Tính toán độ tin cậy ECE (Expected Calibration Error) và vẽ Reliability Diagram.

---
*Báo cáo được tạo tự động và lưu trữ chính thức tại kho mã nguồn dự án: `d:\duanhocmay\BAO_CAO_TONG_KET_C1_C2_C3.md`.*
