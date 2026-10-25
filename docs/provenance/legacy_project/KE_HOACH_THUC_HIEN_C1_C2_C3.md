# KẾ HOẠCH TRIỂN KHAI CHI TIẾT: MODULE C1 - C2 - C3
**Dự án:** Phân loại & Phân tích Ảnh Mô Bệnh Học Đa Trung Tâm  
**Phụ trách:** Đông / Huy  
**Ngày lập:** 16/10/2026  

---

## 📌 TỔNG QUAN NHIỆM VỤ

| Mã CV | Tên công việc | Trọng tâm kỹ thuật | Kết quả đầu ra (Deliverables) |
| :--- | :--- | :--- | :--- |
| **C1** | Quản lý 5 dataset, ánh xạ nhãn về 7 lớp, chốt câu hỏi mở | Khảo sát dữ liệu, chuẩn hóa phân loại giải phẫu bệnh, định hình bài toán | Bảng ánh xạ nhãn chuẩn (`mapping.json`), văn bản câu hỏi mở & giả thuyết |
| **C2** | Gom nhóm ảnh trùng LC25000, chia tập, xuất `splits.csv` | Thuật toán băm tri giác (pHash/SSIM), gom cụm, phân chia dữ liệu chống rò rỉ (Leak-free) | Script lọc trùng, file phân chia tập dữ liệu `splits.csv` |
| **C3** | Cắt patch LungHist700 & BACH, Macenko stain normalization | Tissue segmentation (Otsu threshold), Patch extraction, Chuẩn hóa màu quang học H&E (Beer-Lambert law) | Pipeline cắt patch, module Macenko Normalization, tập ảnh đã chuẩn hóa |

---

## 🔬 CHI TIẾT TỪNG MODULE

### 1. MODULE C1: TỔ HỢP 5 DATASET, ÁNH XẠ 7 LỚP & CÂU HỎI MỞ

#### 1.1. Khảo sát & Quản lý 5 Bộ Dữ liệu
Dự án tích hợp 5 tập dữ liệu mô bệnh học đa cơ quan (Phổi, Đại tràng, Tuyến vú):
1. **LC25000** (Borkowski et al.): 25,000 ảnh kích thước $768 \times 768$ (5 lớp: Phổi lành tính, Ung thư biểu mô tuyến phổi, Ung thư biểu mô tế bào vảy phổi; Đại tràng lành tính, Ung thư biểu mô tuyến đại tràng).
2. **LungHist700**: Bộ ảnh mô bệnh học phổi kích thước lớn / độ phân giải cao.
3. **BACH (BreAst Cancer Histology)**: Ảnh mô bệnh học ung thư vú nhuộm H&E (Benign, In situ, Invasive, Normal).
4. **Dataset bổ sung 4**: (Dataset kiểm chứng ngoại vi / ngoài miền - Out-of-Distribution).
5. **Dataset bổ sung 5**: (Dataset kiểm chứng ngoại vi).

#### 1.2. Ánh xạ Nhãn về 7 Lớp Chuẩn (Unified 7-Class Ontology)
Để thống nhất các nguồn dữ liệu vào một không gian phân loại chung:

| ID Lớp | Tên lớp chuẩn | Mô tả y khoa | Nguồn Dataset chính |
| :---: | :--- | :--- | :--- |
| **0** | `lung_normal` | Mô phổi lành tính / bình thường | LC25000 (`lung_n`), LungHist700 |
| **1** | `lung_aca` | Ung thư biểu mô tuyến phổi (Adenocarcinoma) | LC25000 (`lung_aca`), LungHist700 |
| **2** | `lung_scc` | Ung thư biểu mô tế bào vảy phổi (Squamous Cell Carcinoma) | LC25000 (`lung_scc`), LungHist700 |
| **3** | `colon_normal` | Niêm mạc đại tràng lành tính | LC25000 (`colon_n`) |
| **4** | `colon_aca` | Ung thư biểu mô tuyến đại tràng (Adenocarcinoma) | LC25000 (`colon_aca`) |
| **5** | `breast_benign` | Mô vú lành tính / bình thường | BACH (`Benign`, `Normal`) |
| **6** | `breast_malignant` | Mô vú ác tính (Xâm lấn / Tại chỗ) | BACH (`Invasive`, `InSitu`) |

#### 1.3. Định hình Câu hỏi Mở & Giả thuyết Nghiên cứu
- **Câu hỏi mở (Research Question):**
  > *"Liệu việc kết hợp chuẩn hóa quang phổ màu Macenko (Stain Normalization) cùng chiến lược phân chia không rò rỉ (Leak-free Cross-Dataset Validation) có giúp mô hình Deep Learning giảm thiểu hiệu ứng sai lệch thiết bị nhuộm/chụp (Domain Shift) và duy trì độ chính xác cao trên các tập dữ liệu ngoại miền (Out-of-Distribution - OOD) hay không?"*
- **Các giả thuyết cần chứng minh trong phần thực nghiệm:**
  - *H1:* Lọc trùng LC25000 sẽ làm giảm độ chính xác ảo (over-optimistic performance) trên tập Test nội bộ nhưng phản ánh chính xác năng lực mô hình.
  - *H2:* Macenko Normalization cải thiện F1-score đáng kể trên các dataset kiểm thử đến từ bệnh viện/phòng thí nghiệm khác.

---

### 2. MODULE C2: XỬ LÝ TRÙNG LẶP LC25000, CHIA TẬP & XUẤT `splits.csv`

#### 2.1. Vấn đề Trùng lặp của LC25000 (Data Leakage Issue)
Bộ dữ liệu LC25000 được sinh ra bằng cách cắt và biến đổi hình học (xoay, lật) từ một số lượng tiêu bản kính hiển vi (WSI) gốc hạn chế. Nếu chia ngẫu nhiên (Random Split), ảnh cùng nguồn sẽ lọt vào cả Train và Test, dẫn đến hiện tượng **Data Leakage nghiêm trọng**.

#### 2.2. Quy trình Gom cụm & Lọc trùng
1. **Tính Fingerprint ảnh:**
   - Sử dụng **Perceptual Hash (pHash)**: Chuyển ảnh về grayscale $32 \times 32$, tính Discrete Cosine Transform (DCT), lấy top low-frequency tạo hash 64-bit.
   - Hoặc trích xuất đặc trưng sâu (feature embeddings) bằng ResNet-50 tiền huấn luyện.
2. **Xác định ngưỡng tương đồng:**
   - Khoảng cách Hamming $\le 4$ hoặc Cosine Similarity $> 0.95$.
3. **Gom nhóm vào các `cluster_id`:**
   - Các ảnh biến thể của cùng một vùng mô được gán chung một `cluster_id`.

#### 2.3. Chiến lược Chia tập (Group Stratified Split)
- **Tỷ lệ:** 70% Train, 15% Validation, 15% Test.
- **Ràng buộc tuyệt đối:** Toàn bộ ảnh thuộc cùng một `cluster_id` chỉ được nằm hoàn toàn trong MỘT tập (Train, Val hoặc Test).
- **Cân bằng lớp:** Phân bổ đều các lớp chẩn đoán qua Stratified Group K-Fold.

#### 2.4. Cấu trúc File `splits.csv`
File đầu ra được chuẩn hóa với các trường thông tin:
```csv
image_id,filepath,dataset,original_label,label_7class,cluster_id,split
img_00001.jpeg,dataset/lc25000/lung_aca/lungaca1.jpeg,LC25000,lung_aca,1,cluster_102,train
img_00002.jpeg,dataset/lc25000/lung_aca/lungaca2.jpeg,LC25000,lung_aca,1,cluster_102,train
img_00003.jpeg,dataset/lc25000/colon_n/colonn5.jpeg,LC25000,colon_n,3,cluster_540,test
...
```

---

### 3. MODULE C3: CẮT PATCH & CHUẨN HÓA MÀU MACENKO

#### 3.1. Pipeline Cắt Patch (LungHist700 & BACH)
Do LungHist700 và BACH chứa các ảnh có kích thước lớn, cần phân rã thành các patch phù hợp với mạng nơ-ron:
- **Kích thước patch:** $224 \times 224$ (hoặc $256 \times 256$, $512 \times 512$ tùy theo cấu hình mô hình).
- **Stride / Overlap:** Stride = 224 (không overlap khi tạo test) hoặc Stride = 112 (overlap 50% khi augment train).
- **Bộ lọc mô (Tissue Filtering):**
  - Chuyển không gian màu sang HSV hoặc Grayscale.
  - Áp dụng thuật toán Otsu thresholding để tính tỷ lệ mô (Tissue Ratio).
  - Loại bỏ các patch có $> 60\%$ là nền trắng trống, vệt kính hoặc bọt khí.

#### 3.2. Thuật toán Chuẩn hóa màu Macenko (Stain Normalization)
Kỹ thuật nhuộm H&E (Hematoxylin - tím nhân tế bào, Eosin - hồng bào tương) có sự sai lệch màu giữa các phòng xét nghiệm. Macenko giải quyết điều này bằng mô hình vật lý quang học:
1. **Chuyển đổi sang Mật độ Quang học (Optical Density - OD):**
   $$OD = -\log_{10}\left(\frac{I}{I_0}\right)$$
   với $I_0 = 255$ (cường độ ánh sáng truyền qua không có mẫu).
2. **Lọc ngưỡng nền:** Loại bỏ các pixel có $OD < \beta$ (vùng nền).
3. **Phân tích thành phần chính (PCA) trong không gian OD:** Chiếu các điểm ảnh lên mặt phẳng tạo bởi 2 eigenvector lớn nhất.
4. **Xác định Stain Vector:** Tìm góc cực biên (percentile $1\%$ và $99\%$) để tách biệt vector nhuộm Hematoxylin và Eosin ($V \in \mathbb{R}^{2 \times 3}$).
5. **Ước lượng ma trận nồng độ màu (Concentration):** $C = V^+ \cdot OD$.
6. **Tái tạo ảnh theo bảng màu chuẩn (Reference Template):** Áp dụng nồng độ $C$ của ảnh nguồn lên vector màu $V_{\text{target}}$ của ảnh mẫu chuẩn tham chiếu đã được chọn trước.

---

## 📂 CẤU TRÚC THƯ MỤC DỰ ÁN ĐỀ XUẤT

```text
duanhocmay/
├── KE_HOACH_THUC_HIEN_C1_C2_C3.md    # Tài liệu kế hoạch chi tiết (File này)
├── download_data.py                  # Script tải và đồng bộ dữ liệu
├── configs/
│   ├── mapping_7class.json           # Quy tắc ánh xạ 7 lớp
│   └── patch_config.yaml             # Cấu hình kích thước patch, ngưỡng lọc mô
├── dataset/
│   ├── raw/                          # Dữ liệu gốc tải về
│   │   ├── lc25000/
│   │   ├── lunghist700/
│   │   └── bach/
│   ├── patches/                      # Các patch đã được cắt từ LungHist700, BACH
│   └── normalized/                   # Các ảnh sau khi qua Macenko Normalization
├── src/
│   ├── c1_mapping/
│   │   └── dataset_indexer.py        # Quét dataset & ánh xạ nhãn
│   ├── c2_clustering/
│   │   ├── perceptual_hash.py        # Tính pHash & gom cụm ảnh trùng
│   │   └── split_generator.py        # Phân chia Train/Val/Test & xuất splits.csv
│   └── c3_preprocessing/
│       ├── patch_extractor.py        # Cắt patch & lọc background (Otsu)
│       └── macenko_normalizer.py     # Chuẩn hóa màu Macenko
└── outputs/
    ├── splits.csv                    # File quản lý phân chia dữ liệu toàn diện
    ├── cluster_summary.json          # Thống kê các nhóm ảnh trùng lặp
    └── macenko_reference.png         # Ảnh chuẩn dùng làm mốc màu
```

---

## 🚀 CÁC BƯỚC THỰC THI TIẾP THEO (ACTION ITEMS)

- [ ] **Bước 1:** Đồng bộ toàn bộ 25,000 ảnh LC25000 từ cache máy vào `d:\duanhocmay\dataset\raw\lc25000`.
- [ ] **Bước 2:** Định vị / đưa dữ liệu LungHist700 và BACH vào thư mục dự án.
- [ ] **Bước 3:** Viết module `perceptual_hash.py` để quét và gom cụm ảnh trùng trong LC25000.
- [ ] **Bước 4:** Viết module `split_generator.py` để xuất file `outputs/splits.csv`.
- [ ] **Bước 5:** Viết module `patch_extractor.py` và `macenko_normalizer.py` để xử lý LungHist700 và BACH.
