# BÁO CÁO C1: CHỐT CÂU HỎI MỞ & GIẢ THUYẾT NGHIÊN CỨU
**Dự án:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Deep Learning trên Ảnh Mô Bệnh Học Đa Trung Tâm  
**Thành viên phụ trách:** Đông / Huy  
**Mục tiêu:** Hoàn thiện nội dung C1 - Thống nhất bảng ánh xạ 7 lớp và chốt câu hỏi mở cho đề tài.

---

## 1. BỐI CẢNH VÀ TÍNH CẤP THIẾT CỦA BÀI TOÁN

Trong chẩn đoán giải phẫu bệnh học số (Computational Pathology):
1. **Sự đa dạng cơ quan và phân lớp:** Việc phân loại đồng thời các tổn thương lành tính và ác tính trên nhiều cơ quan (Phổi, Đại tràng, Tuyến vú) giúp xây dựng các mô hình trợ giúp chẩn đoán đa năng (Multi-organ pathology AI).
2. **Thách thức sai lệch miền (Domain Shift / Batch Effect):** Mỗi bệnh viện/phòng thí nghiệm sử dụng hóa chất nhuộm H&E (Hematoxylin & Eosin) với nồng độ khác nhau, thời gian ủ khác nhau và máy quét tiêu bản (WSI Scanner) từ các hãng khác nhau (Leica, Aperio, Hamamatsu). Điều này tạo ra sự sai khác rất lớn về màu sắc và độ tương phản giữa các tập dữ liệu.
3. **Hiện tượng rò rỉ dữ liệu ảo (Over-optimistic Performance):** Nhiều bộ dữ liệu công khai (tiêu biểu như LC25000) được tạo ra bằng cách cắt và xoay/lật ảnh từ cùng một slide mô. Nếu không gom cụm và phân chia cẩn thận, mô hình sẽ "học vẹt" đặc trưng của bệnh nhân thay vì đặc trưng bệnh lý.

---

## 2. CÂU HỎI MỞ CHÍNH THỨC (OPEN RESEARCH QUESTION)

> **"Liệu việc kết hợp chuẩn hóa quang phổ màu Macenko (Stain Normalization) cùng chiến lược phân chia không rò rỉ dữ liệu (Leak-free Cross-Dataset Validation) có giúp mô hình Deep Learning khắc phục hiện tượng sai lệch miền (Domain Shift) và đạt được tính tổng quát hóa cao (Generalization) khi kiểm thử trên dữ liệu ngoại miền (Out-of-Distribution - OOD) hay không?"**

---

## 3. CÁC GIẢ THUYẾT KHOA HỌC (HYPOTHESES)

Để trả lời câu hỏi mở trên, nhóm thiết lập 3 giả thuyết thực nghiệm:

* **Giả thuyết H1 (Về rò rỉ dữ liệu ở LC25000):**  
  *Khi chia tập ngẫu nhiên thông thường (Random Split), mô hình sẽ đạt độ chính xác giả tạo (>99%). Khi áp dụng thuật toán gom cụm ảnh trùng (pHash Clustering) và chia tập theo cụm (Group-based Split), độ chính xác sẽ giảm nhẹ nhưng phản ánh trung thực năng lực nhận diện của mô hình.*

* **Giả thuyết H2 (Về vai trò của Macenko Stain Normalization):**  
  *Chuẩn hóa màu Macenko về một tiêu bản tham chiếu (Reference Slide) sẽ làm giảm khoảng cách phân phối đặc trưng (Feature Distribution Distance) giữa các trung tâm y tế, từ đó cải thiện Macro F1-score từ 5% - 15% khi đánh giá trên tập kiểm thử ngoại miền (Cross-center/Cross-dataset).*

* **Giả thuyết H3 (Về tính tin cậy và độ hiệu chỉnh của mô hình - Calibration):**  
  *Mô hình được huấn luyện trên dữ liệu đã chuẩn hóa màu sẽ có mức độ tự tin (Confidence score) tương thích tốt hơn với xác suất thực tế, giảm thiểu sai số hiệu chỉnh (Expected Calibration Error - ECE) đối với các trường hợp bệnh lý phức tạp.*

---

## 4. BẢNG ÁNH XẠ NHÃN THỐNG NHẤT (7 LỚP)

Tất cả các mẫu ảnh từ 5 bộ dữ liệu được ánh xạ đồng nhất về hệ thống phân loại 7 lớp sau:

| Mã lớp | Tên lớp chuẩn | Cơ quan | Phân loại y khoa | Nguồn dữ liệu |
| :---: | :--- | :---: | :---: | :--- |
| **0** | `lung_normal` | Phổi | Lành tính / Bình thường | LC25000 (`lung_n`), LungHist700 |
| **1** | `lung_aca` | Phổi | Ác tính (Biểu mô tuyến) | LC25000 (`lung_aca`), LungHist700 |
| **2** | `lung_scc` | Phổi | Ác tính (Biểu mô tế bào vảy) | LC25000 (`lung_scc`), LungHist700 |
| **3** | `colon_normal` | Đại tràng | Lành tính / Bình thường | LC25000 (`colon_n`) |
| **4** | `colon_aca` | Đại tràng | Ác tính (Biểu mô tuyến) | LC25000 (`colon_aca`) |
| **5** | `breast_benign` | Tuyến vú | Lành tính / Bình thường | BACH (`Normal`, `Benign`) |
| **6** | `breast_malignant` | Tuyến vú | Ác tính (Xâm lấn / Tại chỗ) | BACH (`Invasive`, `InSitu`) |

---

## 5. THƯỚC ĐO THỰC NGHIỆM ĐÁNH GIÁ (EVALUATION METRICS)

1. **Macro-averaged F1-Score:** Đảm bảo đánh giá công bằng giữa các lớp bất kể mất cân bằng số lượng mẫu.
2. **Balanced Accuracy:** Tránh đánh giá sai lệch khi số lượng mẫu giữa các cơ quan chênh lệch.
3. **Cross-Domain F1 Drop ($\Delta F1$):** Chênh lệch hiệu năng giữa tập kiểm thử nội miền (In-Domain Test) và ngoại miền (Out-of-Domain Test). Mục tiêu là $\Delta F1$ càng nhỏ càng tốt khi bật Macenko.
4. **Expected Calibration Error (ECE):** Đánh giá độ tin cậy của xác suất dự đoán (phục vụ tính an toàn trong ứng dụng lâm sàng).

---

## 6. KẾ HOẠCH BÁO CÁO VỚI GIẢNG VIÊN / HỘI ĐỒNG
- Phần C1 cung cấp cơ sở lý thuyết vững chắc, câu hỏi mở mang tính học thuật cao (giải quyết trực diện bài toán Domain Adaptation & Data Leakage trong ảnh y tế).
- Bảng ánh xạ 7 lớp đảm bảo tính logic sinh học và phân loại bệnh học chuẩn quốc tế.
