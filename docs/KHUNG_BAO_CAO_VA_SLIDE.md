# KHUNG BÁO CÁO TOÀN VĂN VÀ SLIDE THUYẾT TRÌNH BÀI TẬP LỚN
**Dự án:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Học Sâu trên Ảnh Mô Bệnh Học Đa Trung Tâm  
**Học phần:** Học máy (Machine Learning)  
**Ngày cập nhật:** 14/11/2026

---

# PHẦN 1: KHUNG BÁO CÁO TOÀN VĂN (FULL REPORT STRUCTURE)
*Dung lượng đề xuất: 20 – 30 trang (Chuẩn báo cáo đồ án môn học)*

## BÌA VÀ MỞ ĐẦU
- **Trang bìa chính & phụ:** Trường/Viện, Bộ môn, Tên đề tài, Giảng viên hướng dẫn, Danh sách sinh viên thực hiện và phân công đóng góp.
- **Tóm tắt báo cáo (Abstract) - Tiếng Việt & Tiếng Anh:** Nêu RQ1 về khả năng tổng quát hóa của ConvNeXt-Tiny và Swin-Tiny, rủi ro rò rỉ khi chia ảnh LC25000, cách chia theo nhóm, so sánh Macenko và các kết quả chính.
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
- **Thách thức 2 – Rò rỉ dữ liệu:** Chia ngẫu nhiên theo từng tệp LC25000 có thể đưa các biến thể của cùng một ảnh gốc vào nhiều tập và làm tăng chỉ số test nội bộ.
### 1.4. Câu hỏi nghiên cứu và các so sánh bổ trợ
- **RQ1 (trọng tâm):** Với cùng tiền huấn luyện trên ImageNet, ConvNeXt-Tiny hay Swin-Tiny giữ hiệu năng tốt hơn khi kiểm thử chéo sang nguồn ảnh khác? So sánh mức giảm chỉ số từ test nội bộ sang test ngoài theo từng cơ quan.
- **So sánh bổ trợ:** Đo chênh lệch hiệu năng giữa chia ngẫu nhiên và chia theo nhóm, đồng thời kiểm tra tác động của việc áp thêm Macenko theo từng kiến trúc và từng nguồn ngoài.
### 1.5. Đóng góp chính của đề tài
- Tái dựng họ ảnh biến thể LC25000 để chia theo nhóm và đo chênh lệch so với chia ngẫu nhiên.
- Đối sánh ConvNeXt-Tiny và Swin-Tiny trên ba nguồn ngoài. Hai baseline theo D14 là dự đoán lớp đa số và hồi quy logistic trên đặc trưng ConvNeXt đóng băng.
- Đánh giá tác động của Macenko và dùng Grad-CAM để minh họa các dự đoán đúng, sai. [Phạm vi đã chốt](../DECISIONS.md)

---

## CHƯƠNG 2: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ KHOA HỌC (LITERATURE REVIEW)
### 2.1. Khảo sát các hướng tiếp cận học sâu trên ảnh mô bệnh học
- Kiến trúc ConvNeXt và Swin Transformer là cơ sở cho hai mô hình đối sánh. Bài Swin V2 thuộc phần tổng quan kiến trúc.
- Mạng gọn nhẹ **XLLC-Net** dùng **Grad-CAM** để minh họa vùng ảnh ảnh hưởng đến dự đoán.
- Các hướng dung hợp đặc trưng và kết hợp mô hình trong nghiên cứu của Al-Jabbar và Talukder.
### 2.2. Rủi ro khi chia tập và đánh giá trên cùng nguồn
- LC25000 có khoảng 1.250 ảnh gốc. Tác giả dùng phép xoay ngẫu nhiên sang trái hoặc phải tối đa 25° và lật ngang hoặc dọc để tạo 25.000 ảnh. [Bài gốc LC25000, mục 2.1–2.2](https://arxiv.org/pdf/1912.12142)
- Các biến thể có thể xuất hiện ở nhiều tập khi chia ngẫu nhiên theo ảnh. Đánh giá chéo giúp đo khả năng giữ hiệu năng trên nguồn độc lập.
### 2.3. Bảng so sánh tổng hợp các công trình tiêu biểu
[Bảng so sánh và DOI/đường dẫn bài gốc](TONG_QUAN_TAI_LIEU_C9.md#4-bảng-tổng-hợp-so-sánh-các-công-trình-nghiên-cứu-liên-quan).
### 2.4. Cơ sở lý thuyết kỹ thuật bổ trợ
- **Mô hình vật lý quang học Macenko:** Định luật Beer-Lambert, không gian Mật độ quang học (Optical Density - OD), phép chiếu PCA và tìm vector phổ thuốc nhuộm Hematoxylin & Eosin.
- **Độ phân giải vật lý (Microns Per Pixel, MPP):** Nêu cách MPP liên hệ kích thước pixel với trường nhìn (Field of View, FOV). Trình bày giới hạn của các ước lượng MPP ở mục 5.2.
- **Kiến trúc mạng nơ-ron đối sánh:** ConvNeXt-Tiny (đại diện mạng tích chập hiện đại) và Swin-Tiny (đại diện Transformer phân cấp).

---

## CHƯƠNG 3: NGUYÊN LIỆU VÀ PHƯƠNG PHÁP NGHIÊN CỨU (MATERIALS & METHODS)
### 3.1. Tổng quan 5 bộ dữ liệu tích hợp
1. **LC25000 (nội bộ, phổi và đại tràng):** 25.000 ảnh trong tập công bố ở kích thước $768 \times 768$ pixel. Dùng 24.949 ảnh sau khi cách ly 51 ảnh.
2. **LungHist700 (test ngoài, phổi):** 691 ảnh hiển vi $1200 \times 1600$ pixel ở 20× và 40×. [Diosdado và cộng sự, 2024](https://doi.org/10.1038/s41597-024-03944-3)
3. **CRC-VAL-HE-7K (test ngoài, đại tràng):** Dùng 1.974 patch thuộc hai lớp NORM/TUM trong tập công bố. [Hồ sơ bộ dữ liệu](https://doi.org/10.5281/zenodo.1214456)
4. **BACH (test ngoài, vú):** 400 ảnh hiển vi mô vú nhuộm H&E. [Aresta và cộng sự, 2019](https://doi.org/10.1016/j.media.2019.05.010)
5. **BreakHis 40× (nội bộ, vú):** 1.995 ảnh mô vú, dùng trong train/val/test nội bộ. [Spanhol và cộng sự, 2016](https://doi.org/10.1109/TBME.2015.2496264)
### 3.2. Hệ thống phân loại 7 lớp bệnh học thống nhất (Unified 7-Class Ontology)
- Chi tiết ánh xạ nhãn: `lung_benign` (0), `lung_aca` (1), `lung_scc` (2), `colon_benign` (3), `colon_aca` (4), `breast_benign` (5), `breast_malignant` (6). [Bản đồ nhãn](../splits/label_map.json)
### 3.3. Tái dựng họ ảnh và chia theo nhóm (Group Split)
- pHash ban đầu tạo 20.443 nhóm và không tái dựng được các họ biến thể ở mức cần thiết. Quy trình cuối tìm cặp ứng viên bằng đặc trưng CNN và kiểm chứng hình học bằng SIFT/RANSAC. Nhóm thu được 1.263 nhóm tái dựng và cách ly 51 ảnh thuộc nhóm có 1–4 ảnh. [Thống kê gom nhóm](../results/grouping_summary.json) · [D5](../DECISIONS.md)
- Chia train/val/test theo tỷ lệ mục tiêu 70/15/15, có cân bằng lớp theo nhóm. Mỗi `group_id` của LC25000 chỉ xuất hiện trong một tập. Các nhóm đại diện cho họ biến thể ước lượng từ ảnh; nguy cơ rò rỉ còn sót lại và sự tách biệt ở cấp bệnh nhân chưa thể kiểm chứng. Với BreakHis, chia theo mã ca đã gộp các hậu tố section. [D3, D5 và các giới hạn](../DECISIONS.md)
- Dùng phép chia theo ảnh ở E1 làm đối chứng cho phép chia theo nhóm.
### 3.4. Pipeline tiền xử lý và chuẩn hóa dữ liệu
- **Kích thước đầu vào:** $224 \times 224$ pixel. Cắt giữa với dữ liệu nội bộ. LungHist700 và BACH dùng lưới patch không chồng lấn.
- **Lọc vùng mô:** Chỉ áp dụng cho LungHist700 và BACH. Pixel có cả ba kênh RGB lớn hơn 220 được tính là nền trắng. Giữ patch có tỷ lệ mô ít nhất 50%. [Cấu hình](../configs/preparation.yaml) · [Mã tiền xử lý](../tools/prepare.py)
- **Chuẩn hóa màu Macenko:** Dùng một ảnh tham chiếu từ LC25000 train. Hai nhánh `none` và `macenko` dùng chung crop, nhãn và cách chia.
### 3.5. Thiết kế và thiết lập huấn luyện mô hình
- Cấu hình mạng: ConvNeXt-Tiny và Swin-Tiny.
- Hàm mất mát có bù trừ mất cân bằng lớp (Inverse Frequency Class-weighted Cross-Entropy).
- Tối ưu hóa: AdamW, Learning Rate $10^{-4}$, Cosine Warmup, Weight Decay 0.05, Mixed Precision (bfloat16).

---

## CHƯƠNG 4: KẾT QUẢ VÀ BÀN LUẬN THỰC NGHIỆM (EXPERIMENTS & RESULTS)
### 4.1. Thiết kế ma trận thực nghiệm
- **E1 (đối chứng cách chia):** ConvNeXt-Tiny, chia ngẫu nhiên theo ảnh, nhánh `none`, ba seed. Đối chiếu với ConvNeXt-Tiny chia theo nhóm ở E2.
- **E2 (đối sánh kiến trúc, Macenko và test chéo):** ConvNeXt-Tiny và Swin-Tiny, chia theo nhóm, mỗi kiến trúc có nhánh `none` và `macenko` với ba seed mỗi cấu hình. Đánh giá trên test nội bộ và test chéo trên LungHist700, CRC-VAL-HE-7K, BACH.
- **E3 (Grad-CAM):** Phân tích trực quan khoảng tám ảnh, gồm bốn dự đoán đúng và bốn dự đoán sai theo kế hoạch D14.
- **Baseline theo D14:** Dự đoán lớp đa số và hồi quy logistic trên đặc trưng ConvNeXt đóng băng. [Thiết kế thực nghiệm](../DECISIONS.md)
### 4.2. Thước đo đánh giá chuyên sâu
- Báo cáo macro-F1, balanced accuracy và mức giảm chỉ số từ test nội bộ sang test chéo theo từng cơ quan (Δ = nội bộ − test chéo). Tổng hợp trung bình ± độ lệch chuẩn qua ba seed cho mỗi cấu hình E1/E2.
- Với test chéo, dự đoán sang cơ quan khác tính là sai. Báo riêng tỷ lệ nhầm cơ quan và accuracy khi giới hạn lựa chọn vào các lớp của cơ quan thật.
### 4.3. Phân tích kết quả chi tiết
- **Ảnh hưởng của cách chia:** Với ConvNeXt-Tiny ở nhánh `none`, macro-F1 test nội bộ trung bình là 0,994 khi chia ngẫu nhiên và 0,827 khi chia theo nhóm. Accuracy nội bộ của cấu hình chia theo nhóm khoảng 92%. [Bảng E1/E2](../outputs/eval/tables/leakage_e1_vs_e2.csv)
- **Kiểm thử chéo E2:** Đối chiếu mức giảm theo cơ quan và theo cấu hình. Nguyên nhân nhầm cơ quan chưa xác định (D11). [Bảng độ giảm theo cấu hình](../outputs/eval/tables/delta_by_config.csv) · [D11](../DECISIONS.md)
- **Tác động của Macenko:** Kết quả thay đổi theo kiến trúc và nguồn test. Ví dụ với ConvNeXt-Tiny, accuracy trung bình tăng trên CRC-VAL-HE-7K và BACH nhưng giảm trên LungHist700 khi áp thêm Macenko. [Bảng kết quả theo cấu hình](../outputs/eval/tables/summary_by_config.csv)
### 4.4. Trực quan hóa và giải thích mô hình
- Đối chiếu ma trận nhầm lẫn giữa các kịch bản E1/E2.
- Dùng Grad-CAM trong E3 để minh họa vùng ảnh ảnh hưởng đến dự đoán ở các ví dụ đúng và sai.

---

## CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN (CONCLUSION)
### 5.1. Kết luận chính
- Tóm tắt chênh lệch macro-F1 giữa hai cách chia, kết quả đối sánh ConvNeXt-Tiny và Swin-Tiny theo từng cơ quan, và tác động của Macenko theo từng nguồn.
### 5.2. Các hạn chế tồn tại (Limitations)
- LC25000 thiếu mã bệnh nhân. Các nhóm tái dựng đại diện cho họ biến thể của ảnh và có thể còn bỏ sót quan hệ giữa các ảnh.
- MPP của LC25000 và LungHist700 là ước lượng chưa kiểm chứng. Nhóm dừng hiệu chỉnh và giữ dữ liệu đóng băng 16/10. Nguyên nhân nhầm cơ quan khi test chéo chưa xác định. [D10, D11 và D14](../DECISIONS.md)
### 5.3. Hướng nghiên cứu tiếp theo (Future Work)
- Ứng dụng các mô hình nền tảng chuyên biệt cho mô bệnh học (Pathology Foundation Models như Phikon, UNI, Prov-GigaPath).
- Mở rộng phân đoạn tiêu bản WSI toàn phần và tích hợp đa phương thức (Multimodal CPath).

---

# PHẦN 2: KHUNG SLIDE BÁO CÁO BẢO VỆ (PRESENTATION SLIDE DECK)
*Thời lượng thuyết trình: 10 – 15 phút (16 Slide chuẩn)*

```
[Slide 1: Bìa] ───> [Slide 2: Đặt vấn đề] ───> [Slide 3: Y văn và rủi ro chia tập]
       │
[Slide 4: Câu hỏi NC] ───> [Slide 5: Đa nguồn Dữ liệu] ───> [Slide 6: Ánh xạ 7 lớp]
       │
[Slide 7: Tái dựng họ ảnh] ───> [Slide 8: Tiền xử lý & Macenko] ───> [Slide 9: Kiến trúc Mạng]
       │
[Slide 10: Thiết kế Thực nghiệm] ───> [Slide 11: So sánh cách chia] ───> [Slide 12: E2 (Kiến trúc & Macenko)]
       │
[Slide 13: E2 (Test chéo)] ───> [Slide 14: Hạn chế (MPP)] ───> [Slide 15: E3 (Grad-CAM) & Thảo luận]
       │
[Slide 16: Kết luận & Q&A]
```

### Slide 1: Trang tiêu đề (Title Slide)
- **Tiêu đề:** ĐÁNH GIÁ TÍNH TỔNG QUÁT HÓA CỦA MÔ HÌNH HỌC SÂU TRÊN ẢNH MÔ BỆNH HỌC ĐA TRUNG TÂM
- **Phụ đề:** Phân loại 7 lớp, so sánh cách chia dữ liệu và đánh giá ngoài miền.
- **Người thực hiện & Giảng viên hướng dẫn.**

### Slide 2: Bối cảnh & Tính cấp thiết (Context & Motivation)
- **Hình ảnh:** Tiêu bản kính hiển vi nhuộm H&E của các mô Phổi, Đại tràng, Tuyến vú.
- **Nội dung:** 
  + AI trong giải phẫu bệnh số (CPath) hỗ trợ chẩn đoán ung thư sớm.
  + Thách thức thực tế: Sự sai lệch màu sắc (Domain Shift) và thiết bị chụp giữa các bệnh viện.

### Slide 3: Y văn và rủi ro khi chia tập
- Minh họa các kết quả trên LC25000 từ XLLC-Net, Talukder và Al-Jabbar. Ghi rõ dữ liệu và cách đánh giá đi kèm. [Bảng C9 và bài gốc](TONG_QUAN_TAI_LIEU_C9.md)
- Khoảng 1.250 ảnh gốc được mở rộng thành 25.000 ảnh bằng phép xoay ngẫu nhiên tối đa 25° và lật ngang hoặc dọc. Chia ngẫu nhiên theo tệp có thể đưa biến thể của cùng một ảnh gốc vào nhiều tập. [Bài gốc LC25000](https://arxiv.org/pdf/1912.12142)

### Slide 4: Câu hỏi nghiên cứu & Mục tiêu đề tài (Research Question & Objectives)
- **RQ1:** Với cùng tiền huấn luyện ImageNet, ConvNeXt-Tiny hay Swin-Tiny giữ hiệu năng tốt hơn khi kiểm thử chéo? Dùng mức giảm chỉ số từ test nội bộ sang test ngoài theo từng cơ quan.
- **So sánh bổ trợ:** Dùng E1/E2 để đo chênh lệch giữa hai cách chia và so sánh nhánh `none` với nhánh `macenko`.

### Slide 5: Hệ sinh thái 5 Bộ Dữ liệu (Multi-Center Datasets)
- **Nội bộ:** LC25000 cho phổi và đại tràng (24.949 ảnh dùng trong thí nghiệm), BreakHis 40× cho vú (1.995 ảnh).
- **Test ngoài:** LungHist700 (691 ảnh hiển vi 1200 × 1600 pixel), CRC-VAL-HE-7K (1.974 patch NORM/TUM) và BACH (400 ảnh hiển vi). [Nguồn dữ liệu](#31-tổng-quan-5-bộ-dữ-liệu-tích-hợp)
- **Hình ảnh minh họa:** Sự khác biệt rõ rệt về màu sắc và góc chụp giữa các bộ dữ liệu.

### Slide 6: Hệ thống Ánh xạ 7 Lớp Thống nhất (Unified 7-Class Scheme)
- **Sơ đồ cấu trúc lớp:**
  + Phổi: Lành tính (0), Tuyến ác tính (1), Vảy ác tính (2).
  + Đại tràng: Lành tính (3), Tuyến ác tính (4).
  + Tuyến vú: Lành tính (5), Ác tính (6).
- **Ý nghĩa:** Chuẩn hóa không gian phân loại chung cho nhiều cơ quan lâm sàng.

### Slide 7: Tái dựng họ ảnh và chia theo nhóm
- pHash ban đầu cho 20.443 nhóm. Quy trình cuối dùng CNN tìm ứng viên và SIFT/RANSAC kiểm chứng, thu được 1.263 nhóm và cách ly 51 ảnh.
- Mỗi nhóm tái dựng của LC25000 nằm trong một tập. Các nhóm biểu diễn họ biến thể ước lượng từ ảnh và chưa xác minh được sự tách biệt ở cấp bệnh nhân.

### Slide 8: Tiền xử lý: Lọc mô và chuẩn hóa Macenko
- Với LungHist700 và BACH, dùng ngưỡng trắng RGB 220 và chỉ giữ patch có tỷ lệ mô ≥50%.
- Hình minh họa hai nhánh `none` và `macenko` dùng chung crop 224 × 224 pixel. Macenko dùng một ảnh tham chiếu từ LC25000 train.

### Slide 9: Kiến trúc Mô hình (Model Architectures)
- **Đối sánh hai trường phái:**
  + **ConvNeXt-Tiny:** Đại diện mạng tích chập hiện đại (Modern CNN) với receptive field lớn ($7 \times 7$).
  + **Swin-Tiny:** Đại diện Vision Transformer phân cấp với cơ chế Shifted Local Window Self-Attention.

### Slide 10: Thiết kế Thực nghiệm (Experimental Setup)
- **E1:** ConvNeXt-Tiny, chia ngẫu nhiên theo ảnh, nhánh `none`, ba seed.
- **E2:** ConvNeXt-Tiny và Swin-Tiny, chia theo nhóm, nhánh `none` và `macenko`, ba seed mỗi cấu hình. Báo test nội bộ và test chéo trên ba nguồn ngoài.
- **E3:** Grad-CAM trên các ví dụ dự đoán đúng và sai.
- **Baseline theo D14:** Lớp đa số và hồi quy logistic trên đặc trưng ConvNeXt đóng băng. [Phạm vi đã chốt](../DECISIONS.md)

### Slide 11: E1/E2 – So sánh hai cách chia
- **Macro-F1 trên test nội bộ** của ConvNeXt-Tiny, nhánh `none`, trung bình ± độ lệch chuẩn qua ba seed.
  - Chia ngẫu nhiên (E1): **0,994 ± 0,002**.
  - Chia theo nhóm (cấu hình tương ứng trong E2): **0,827 ± 0,018**.
- Chênh lệch cho thấy lựa chọn cách chia ảnh hưởng đến kết quả đánh giá. [Bảng E1/E2](../outputs/eval/tables/leakage_e1_vs_e2.csv)

### Slide 12: E2 – Đối sánh kiến trúc và chuẩn hóa màu Macenko
- So sánh ConvNeXt-Tiny và Swin-Tiny trong cùng điều kiện chia theo nhóm, lần lượt với `none` và `macenko`. Trình bày macro-F1 và accuracy theo cấu hình, trung bình ± độ lệch chuẩn qua ba seed. Tác động của Macenko thay đổi theo kiến trúc và nguồn dữ liệu. [Bảng kết quả theo cấu hình](../outputs/eval/tables/summary_by_config.csv)

### Slide 13: E2 – Kết quả kiểm thử chéo ngoài miền
- Trình bày Δ macro-F1 theo cơ quan cho LungHist700, CRC-VAL-HE-7K và BACH. Báo riêng tỷ lệ nhầm cơ quan.
- Ví dụ với ConvNeXt-Tiny, chia theo nhóm, nhánh `none`: accuracy trung bình ba seed là 92,5% trên test nội bộ, 32,2% trên LungHist700, 12,7% trên CRC-VAL-HE-7K và 11,8% trên BACH. Đây là accuracy khi mô hình dự đoán trong cả bảy lớp. Nguyên nhân nhầm cơ quan chưa xác định (D11). [Bảng kết quả theo cấu hình](../outputs/eval/tables/summary_by_config.csv) · [Bảng độ giảm theo cấu hình](../outputs/eval/tables/delta_by_config.csv) · [D11](../DECISIONS.md)

### Slide 14: Hạn chế về độ phân giải vật lý (MPP)
- Nhóm dừng hiệu chỉnh MPP theo D10 và D14. Thí nghiệm dùng dữ liệu đóng băng 16/10. Mức 0,5 µm/pixel của LC25000 là ước lượng chưa kiểm chứng. MPP của LungHist700 cũng chưa được kiểm chứng. [D10 và D14](../DECISIONS.md)

### Slide 15: E3 – Grad-CAM và thảo luận
- Theo kế hoạch D14, minh họa khoảng tám ảnh bằng Grad-CAM, gồm bốn dự đoán đúng và bốn dự đoán sai.
- Đối chiếu bản đồ Grad-CAM với các dạng nhầm lẫn quan sát được. Trình bày các giới hạn khi diễn giải khác biệt giữa các nguồn ảnh.

### Slide 16: Tổng kết & Hỏi đáp (Conclusion & Q&A)
- **Tóm tắt 3 kết luận chính của đề tài.**
- Lời cảm ơn và mời Hội đồng / Giảng viên đặt câu hỏi.
