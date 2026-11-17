# BÁO CÁO C9: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ KHOA HỌC CỦA ĐỀ TÀI
**Học phần:** Bài tập lớn Học máy (Machine Learning Project)  
**Chủ đề:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Học Sâu trên Ảnh Mô Bệnh Học Đa Trung Tâm  
**Hạn nộp:** 02/11/2026  
**Độ dài:** ~1,5 trang A4 tiêu chuẩn (Học thuật & Thực nghiệm)

---

## 1. BỐI CẢNH VÀ CÁC HƯỚNG TIẾP CẬN CHÍNH TRONG Y VĂN

Trong giải phẫu bệnh số (Computational Pathology, CPath), mô hình học sâu có thể được đánh giá trên cả tập kiểm thử nội bộ và nguồn ảnh độc lập. Hai cách đánh giá trả lời các câu hỏi khác nhau về hiệu năng và khả năng tổng quát hóa.

### 1.1. Kiến trúc ConvNeXt và Swin Transformer
ConvNeXt của Z. Liu và cộng sự (CVPR 2022) là kiến trúc tích chập hiện đại. Swin Transformer của Ze Liu và cộng sự (ICCV 2021) dùng cơ chế tự chú ý trong các cửa sổ dịch chuyển. Bài Swin Transformer V2 (CVPR 2022) trình bày cách mở rộng dung lượng mô hình và độ phân giải đầu vào trên các bộ chuẩn thị giác như ImageNet, COCO, ADE20K và Kinetics-400. Đề tài dùng ConvNeXt-Tiny và Swin-Tiny (Swin phiên bản gốc), đều tiền huấn luyện trên ImageNet. [ConvNeXt](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_A_ConvNet_for_the_2020s_CVPR_2022_paper.html) · [Swin](https://openaccess.thecvf.com/content/ICCV2021/html/Liu_Swin_Transformer_Hierarchical_Vision_Transformer_Using_Shifted_Windows_ICCV_2021_paper.html) · [Swin V2](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_Swin_Transformer_V2_Scaling_Up_Capacity_and_Resolution_CVPR_2022_paper.html) · [Cấu hình mô hình](../src/train/models.py)

### 1.2. Mạng CNN gọn nhẹ tích hợp khả năng giải thích
XLLC-Net của Jim và cộng sự dùng bốn khối tích chập với khoảng 3 triệu tham số. Trên ba lớp phổi của LC25000, tác giả báo cáo accuracy 99,62% và F1-score 99,70%, đồng thời dùng Grad-CAM và bản đồ độ nổi bật để trực quan hóa vùng ảnh có ảnh hưởng đến dự đoán. [Jim và cộng sự, 2025](https://doi.org/10.1371/journal.pone.0322488)

### 1.3. Dung hợp đặc trưng và kết hợp mô hình
* Talukder và cộng sự kết hợp đặc trưng học sâu với bộ phân loại ensemble trên LC25000. Accuracy công bố là 99,05% cho phổi, 100% cho đại tràng và 99,30% khi kết hợp cả hai cơ quan. [Talukder và cộng sự, 2022](https://doi.org/10.1016/j.eswa.2022.117695)
* Al-Jabbar và cộng sự báo cáo accuracy 99,64% với mạng ANN dùng đặc trưng VGG-19 kết hợp các đặc trưng thủ công như LBP, GLCM và DWT. [Al-Jabbar và cộng sự, 2023](https://doi.org/10.3390/bioengineering10030383)

### 1.4. Nguồn dữ liệu dùng để đánh giá ngoài miền
Kather và cộng sự huấn luyện VGG19 trên NCT-CRC-HE-100K và đánh giá phân loại chín loại mô trên 7.180 patch độc lập của CRC-VAL-HE-7K. Bài báo ghi nhận accuracy gần 99% ở tập kiểm thử nội bộ và 94,3% ở tập ngoài. Các patch CRC-VAL-HE-7K có độ phân giải 0,5 µm/pixel. [Kather và cộng sự, 2019](https://doi.org/10.1371/journal.pmed.1002730) · [Hồ sơ dữ liệu CRC](https://doi.org/10.5281/zenodo.1214456)

Diosdado, Gilabert, Seguí và Borrego công bố LungHist700 gồm 691 ảnh hiển vi mô phổi kích thước 1200 × 1600 pixel từ 45 bệnh nhân, ở độ phóng đại 20× và 40×. Ảnh ghi lại các trường nhìn qua kính hiển vi. Các mô hình cơ sở của bài báo đạt accuracy 81–92% khi phân loại ba nhóm mô phổi trên LungHist700, tùy phương pháp và độ phóng đại. [Diosdado và cộng sự, 2024](https://doi.org/10.1038/s41597-024-03944-3)

---

## 2. RỦI RO RÒ RỈ DỮ LIỆU VÀ KẾT QUẢ KIỂM THỬ CHÉO

### 2.1. Rủi ro khi chia ngẫu nhiên trên LC25000
LC25000 gồm khoảng 1.250 ảnh gốc, với 250 ảnh mỗi lớp. Tác giả dùng Augmentor để xoay ngẫu nhiên sang trái hoặc phải tối đa 25° và lật ngang hoặc dọc, tạo tập 25.000 ảnh. Chia ngẫu nhiên theo từng tệp có thể đưa các biến thể từ cùng một ảnh gốc vào nhiều tập. Chỉ số nội bộ cao tự nó chưa cho biết mô hình sẽ hoạt động ra sao trên nguồn ảnh khác. [Borkowski và cộng sự, 2019, mục 2.1–2.2](https://arxiv.org/pdf/1912.12142)

pHash ban đầu cho 20.443 nhóm và không tái dựng được các họ ảnh ở mức cần thiết. Quy trình cuối dùng đặc trưng CNN để tìm cặp ảnh ứng viên, sau đó kiểm chứng hình học bằng SIFT/RANSAC. Kết quả là 1.263 nhóm tái dựng. Nhóm cách ly 51 ảnh thuộc các nhóm có 1–4 ảnh, còn 24.949 ảnh LC25000 tham gia thí nghiệm. Mỗi `group_id` được xếp vào đúng một tập trong phép chia theo nhóm. Đây là các họ biến thể ước lượng từ ảnh, nên vẫn có thể có rò rỉ còn sót lại và chưa thể kiểm chứng sự tách biệt ở cấp bệnh nhân. [D5 và các giới hạn](../DECISIONS.md) · [Thống kê gom nhóm](../results/grouping_summary.json) · [Mã gom nhóm](../tools/group_lc.py)

### 2.2. Suy giảm hiệu năng ngoài miền
Trong kết quả chính E1/E2, ConvNeXt-Tiny ở nhánh `none` đạt macro-F1 test nội bộ trung bình 0,994 khi chia ngẫu nhiên và 0,827 khi chia theo nhóm (ba seed mỗi cấu hình). Accuracy nội bộ của cấu hình chia theo nhóm khoảng 92%. Trong E2, cấu hình này đạt accuracy trung bình 32,2% trên LungHist700, 12,7% trên CRC-VAL-HE-7K và 11,8% trên BACH khi dự đoán trong cả bảy lớp. Tỷ lệ nhầm cơ quan được báo cáo riêng. Nguyên nhân nhầm cơ quan chưa xác định (D11). [Bảng E1/E2](../outputs/eval/tables/leakage_e1_vs_e2.csv) · [Bảng kết quả theo cấu hình](../outputs/eval/tables/summary_by_config.csv) · [D11](../DECISIONS.md)

---

## 3. LÝ DO CHỌN ĐỀ TÀI VÀ ĐÓNG GÓP

1. **So sánh cách chia dữ liệu.** Dùng E1 với chia ngẫu nhiên theo ảnh làm đối chứng cho cấu hình tương ứng của E2 với chia theo nhóm. Tập nội bộ gồm LC25000 cho phổi và đại tràng, cùng BreakHis 40× cho vú.
2. **Đánh giá khả năng tổng quát hóa (RQ1).** Với cùng tiền huấn luyện ImageNet, ConvNeXt-Tiny hay Swin-Tiny giữ hiệu năng tốt hơn khi chuyển sang nguồn ảnh khác? E2 so sánh mức giảm chỉ số từ test nội bộ sang test chéo theo từng cơ quan. Kiểm thử ngoài miền dùng LungHist700 (phổi), CRC-VAL-HE-7K với hai lớp NORM/TUM (đại tràng) và BACH (vú). Hai baseline theo D14 là dự đoán lớp đa số và hồi quy logistic trên đặc trưng ConvNeXt đóng băng.
3. **Đánh giá Macenko và trực quan hóa dự đoán.** E2 so sánh `none` và `macenko` trên cùng cách chia theo nhóm. E3 dự kiến dùng Grad-CAM để minh họa các dự đoán đúng và sai. [D1, D2 và D14](../DECISIONS.md)

**Giới hạn về MPP.** Thí nghiệm dùng dữ liệu đóng băng ngày 16/10. Nhóm giữ mức 0,5 µm/pixel cho LC25000 ở trạng thái `estimated_unverified` sau khi dừng hiệu chỉnh theo D10 và D14. MPP của LungHist700 cũng là ước lượng chưa kiểm chứng. [D10 và D14](../DECISIONS.md)

---

## 4. BẢNG TỔNG HỢP SO SÁNH CÁC CÔNG TRÌNH NGHIÊN CỨU LIÊN QUAN

| STT | Công trình | Mô hình / phương pháp | Dữ liệu và cách đánh giá | Kết quả được báo cáo |
|:---:|:---|:---|:---|:---|
| 1 | [Ze Liu và cộng sự (2022)](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_Swin_Transformer_V2_Scaling_Up_Capacity_and_Resolution_CVPR_2022_paper.html) | Swin Transformer V2 | Các bộ chuẩn thị giác như ImageNet, COCO, ADE20K và Kinetics-400 | Bài gốc về kiến trúc Swin V2. |
| 2 | [Jim và cộng sự (2025)](https://doi.org/10.1371/journal.pone.0322488) | XLLC-Net + Grad-CAM | Ba lớp phổi LC25000, chia train/val/test 80/10/10 | Accuracy 99,62%, F1-score 99,70%. |
| 3 | [Talukder và cộng sự (2022)](https://doi.org/10.1016/j.eswa.2022.117695) | Đặc trưng học sâu + ensemble | LC25000, quy trình có kiểm định chéo 10 fold trong cùng nguồn | Accuracy phổi 99,05%, đại tràng 100%, gộp 99,30%. |
| 4 | [Al-Jabbar và cộng sự (2023)](https://doi.org/10.3390/bioengineering10030383) | ANN với đặc trưng VGG-19 và đặc trưng thủ công | LC25000, dành 20% cho test theo mô tả của tác giả | Accuracy 99,64%. |
| 5 | [Diosdado và cộng sự (2024)](https://doi.org/10.1038/s41597-024-03944-3) | ResNet50 và học đa thể hiện (MIL) | LungHist700, phân loại ba nhóm mô, chia theo bệnh nhân | Accuracy 81–92% tùy phương pháp và độ phóng đại. |
| 6 | [Kather và cộng sự (2019)](https://doi.org/10.1371/journal.pmed.1002730) | VGG19 | Huấn luyện trên NCT-CRC-HE-100K, test ngoài trên CRC-VAL-HE-7K | Accuracy chín lớp gần 99% nội bộ và 94,3% trên test ngoài. |
| 7 | Đề tài nhóm | ConvNeXt-Tiny và Swin-Tiny, với và không áp thêm Macenko | Nội bộ: LC25000 và BreakHis 40×. Test chéo E2: LungHist700, CRC-VAL-HE-7K và BACH. | ConvNeXt-Tiny, `none`: macro-F1 test nội bộ 0,994 khi chia ngẫu nhiên và 0,827 khi chia theo nhóm. [Bảng E1/E2](../outputs/eval/tables/leakage_e1_vs_e2.csv) |

Các kết quả trong bảng dùng bộ nhãn, cách chia và thước đo khác nhau. So sánh giữa hai cách chia của đề tài dựa trên cùng kiến trúc ConvNeXt-Tiny và cùng nhánh `none`.

---

## 5. TÀI LIỆU THAM KHẢO CHÍNH (KEY REFERENCES)

1. Borkowski, A. A., và cộng sự (2019). *Lung and Colon Cancer Histopathological Image Dataset (LC25000)*. [arXiv:1912.12142](https://arxiv.org/abs/1912.12142).
2. Liu, Ze, và cộng sự (2021, 2022). [Swin Transformer, ICCV 2021](https://openaccess.thecvf.com/content/ICCV2021/html/Liu_Swin_Transformer_Hierarchical_Vision_Transformer_Using_Shifted_Windows_ICCV_2021_paper.html) và [Swin Transformer V2, CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_Swin_Transformer_V2_Scaling_Up_Capacity_and_Resolution_CVPR_2022_paper.html).
3. Liu, Zhuang, và cộng sự (2022). *A ConvNet for the 2020s*. [CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Liu_A_ConvNet_for_the_2020s_CVPR_2022_paper.html).
4. Jim, J. R., Rayed, M. E., Mridha, M., & Nur, K. (2025). *XLLC-Net*. PLOS ONE, 20(5), e0322488. [DOI](https://doi.org/10.1371/journal.pone.0322488).
5. Talukder, M. A., và cộng sự (2022). *Machine learning-based lung and colon cancer detection using deep feature extraction and ensemble learning*. Expert Systems with Applications, 205, 117695. [DOI](https://doi.org/10.1016/j.eswa.2022.117695).
6. Al-Jabbar, M., và cộng sự (2023). *Histopathological Analysis for Detecting Lung and Colon Cancer Malignancies Using Hybrid Systems with Fused Features*. Bioengineering, 10(3), 383. [DOI](https://doi.org/10.3390/bioengineering10030383).
7. Kather, J. N., và cộng sự (2019). *Predicting survival from colorectal cancer histology slides using deep learning: A retrospective multicenter study*. PLOS Medicine, 16(1), e1002730. [DOI](https://doi.org/10.1371/journal.pmed.1002730) · [Bộ dữ liệu CRC](https://doi.org/10.5281/zenodo.1214456).
8. Diosdado, J., Gilabert, P., Seguí, S., & Borrego, H. (2024). *LungHist700: A dataset of histological images for deep learning in pulmonary pathology*. Scientific Data, 11, 1088. [DOI](https://doi.org/10.1038/s41597-024-03944-3).
9. Selvaraju, R. R., và cộng sự (2017). *Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization*. ICCV. [Bản của tác giả](https://arxiv.org/abs/1610.02391).
10. Macenko, M., và cộng sự (2009). *A method for normalizing histology slides for quantitative analysis*. ISBI. [DOI](https://doi.org/10.1109/ISBI.2009.5193250).
11. Aresta, G., và cộng sự (2019). *BACH: Grand challenge on breast cancer histology images*. Medical Image Analysis, 56, 122–139. [DOI](https://doi.org/10.1016/j.media.2019.05.010).
12. Spanhol, F. A., Oliveira, L. S., Petitjean, C., & Heutte, L. (2016). *A Dataset for Breast Cancer Histopathological Image Classification*. IEEE Transactions on Biomedical Engineering, 63(7), 1455–1462. [DOI](https://doi.org/10.1109/TBME.2015.2496264).
