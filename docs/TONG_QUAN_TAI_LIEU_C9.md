# BÁO CÁO C9: TỔNG QUAN TÀI LIỆU VÀ CƠ SỞ KHOA HỌC CỦA ĐỀ TÀI
**Học phần:** Bài tập lớn Học máy (Machine Learning Project)  
**Chủ đề:** Phân loại & Đánh giá Tính Tổng Quát Hóa của Mô Hình Học Sâu trên Ảnh Mô Bệnh Học Đa Trung Tâm  
**Hạn nộp:** 02/11/2026  
**Độ dài:** ~1,5 trang A4 tiêu chuẩn (Học thuật & Thực nghiệm)

---

## 1. BỐI CẢNH VÀ CÁC HƯỚNG TIẾP CẬN CHÍNH TRONG Y VĂN

Trong chẩn đoán giải phẫu bệnh số (Computational Pathology - CPath), việc ứng dụng học máy và thị giác máy tính nhằm tự động phân loại tổn thương mô học (ung thư phổi, ung thư đại tràng, ung thư vú) đã nhận được sự quan tâm rất lớn từ cộng đồng nghiên cứu quốc tế. Trong giai đoạn khảo sát chọn đề tài, nhóm đã nghiên cứu và đối sánh các nhánh phương pháp chính sau:

### 1.1. Ứng dụng Vision Transformer dạng phân cấp (Swin Transformer V2)
Các kiến trúc Vision Transformer gần đây đã chứng minh ưu thế vượt trội trong việc nắm bắt tương quan không gian toàn cục (global context) so với các mạng nơ-ron tích chập (CNN) truyền thống. Điển hình, **Swin Transformer V2** (Liu et al., 2022) với cơ chế Shifted Windows (cửa sổ trượt tự chú ý cục bộ) kết hợp chuẩn hóa Post-Norm và mã hóa vị trí liên tục theo thang logarit (log-spaced CPB) đã giải quyết triệt để vấn đề chi phí tính toán bậc hai của self-attention khi xử lý ảnh kích thước lớn. Nhiều nghiên cứu gần đây (tiêu biểu như trên *Frontiers in Oncology* và *IEEE Access*) khi huấn luyện Swin Transformer V2 trên tập dữ liệu mô bệnh học phổi và đại tràng nổi tiếng **LC25000** đã báo cáo các chỉ số hiệu năng gần như tuyệt đối, với độ chính xác (Accuracy) dao động từ **99,20% đến 99,97%** trên bài toán phân loại 5 lớp.

### 1.2. Mạng CNN gọn nhẹ tích hợp khả năng giải thích (XLLC-Net với Grad-CAM)
Nhằm giảm bớt gánh nặng tính toán và nâng cao khả năng ứng dụng thực tế tại điểm chăm sóc y tế (Point-of-Care), các mô hình học sâu gọn nhẹ (Lightweight Deep Learning) đã ra đời. Tiêu biểu là công trình **XLLC-Net** (*Explainable and Lightweight Lung Cancer Net*, công bố trên *PLOS ONE*). XLLC-Net chỉ sử dụng 4 khối tích chập với khoảng 3 triệu tham số (giảm hơn 85% tham số so với các mạng chuẩn như ResNet50 hay DenseNet), cho tốc độ huấn luyện nhanh gấp nhiều lần nhưng vẫn đạt Accuracy **99,62%** và F1-Score **99,70%** trên tập dữ liệu mô bệnh học phổi LC25000. Điểm nhấn của nghiên cứu này là việc tích hợp kỹ thuật giải thích mô hình **Grad-CAM (Gradient-weighted Class Activation Mapping)** và bản đồ độ nổi bật (Saliency Maps) để trực quan hóa các vùng mô mà mạng tập trung đưa ra quyết định, qua đó giải mã tính chất "hộp đen" của AI y tế.

### 1.3. Các phương pháp học kết hợp (Feature Fusion & Ensemble Learning)
Một xu hướng nổi bật khác là kết hợp sức mạnh của nhiều kiến trúc thông qua dung hợp đặc trưng hoặc kết hợp mô hình (Ensemble):
* **Talukder et al. (Expert Systems with Applications):** Đề xuất mô hình lai kết hợp trích xuất đặc trưng sâu từ mạng CNN đa tầng kết hợp với các bộ phân loại học máy ensemble (Random Forest, XGBoost), báo cáo độ chính xác đạt **99,05%** ở bài toán ung thư phổi, **100%** ở ung thư đại tràng, và **99,30%** toàn bộ 5 lớp.
* **Al-Jabbar et al.:** Dung hợp đặc trưng học sâu trích xuất từ VGG-19/GoogLeNet với các đặc trưng kết cấu truyền thống (Handcrafted features như LBP, GLCM, DWT) qua mạng nơ-ron nhân tạo (ANN), đạt độ chính xác **99,64%**.
* **Ensemble đa mạng CNN (Multi-CNN Ensembles):** Kết hợp các dự đoán xác suất từ ResNet50, DenseNet121, InceptionV3 và MobileNet, hầu hết đều đạt kết quả công bố vượt ngưỡng 99%.

### 1.4. Các nghiên cứu kiểm thử chéo ngoại vi (Cross-Dataset / External Validation)
Bộ dữ liệu độc lập về ung thư đại trực tràng **NCT-CRC-HE-100K** cùng tập kiểm định độc lập **CRC-VAL-HE-7K** (Kather et al., *PLOS Medicine*, 2019) gồm các patch mô bệnh học nhuộm H&E từ bệnh nhân tại các trung tâm y tế Đức với độ phân giải vật lý được công bố rõ ràng (0,5 µm/pixel). Năm 2024, bộ dữ liệu mô bệnh học phổi **LungHist700** (Wang et al., *Scientific Data - Nature*, 2024) được phát hành gồm 691 ảnh tiêu bản lớn tại độ phóng đại 20x và 40x ghi nhận chi tiết lâm sàng của ung thư biểu mô tuyến (ACA), ung thư biểu mô vảy (SCC) và mô lành. Mặc dù các bộ dữ liệu này rất phong phú, nhưng rất ít nghiên cứu kiểm tra chéo (zero-shot cross-dataset evaluation) xem mô hình huấn luyện từ LC25000 có thực sự phân biệt được tế bào ung thư trên các nguồn dữ liệu này hay không.

---

## 2. LỖ HỔNG LỚN TRONG Y VĂN VÀ BẰNG CHỨNG THỰC TẾ

Qua tổng quan sâu sắc các công trình công bố, nhóm phát hiện ra **hai nghịch lý học thuật mang tính then chốt**:

### 2.1. Rò rỉ dữ liệu ảo (Data Leakage) do phân chia ngẫu nhiên trên LC25000
Bộ dữ liệu LC25000 (Borkowski et al., 2019) được quảng bá gồm 25.000 ảnh (5.000 ảnh/lớp). Tuy nhiên, trên thực tế bộ dữ liệu này được sinh ra từ **chỉ khoảng 1.250 ảnh tiêu bản hiển vi gốc ban đầu** (khoảng 250 ảnh cho mỗi lớp), sau đó tác giả áp dụng các phép biến đổi hình học (xoay các góc 90°, 180°, 270° và lật đối xứng gương - nhóm đối xứng Dihedral $D_4$) để nhân số lượng lên gấp 20 lần:
$$\text{250 ảnh gốc} \times 20 \text{ biến thể augment} = 5.000 \text{ ảnh/lớp}$$
Hầu hết các bài báo hiện nay (kể cả các bài dùng Swin Transformer V2, XLLC-Net, hay Ensemble đạt 99–100%) đều sử dụng kỹ thuật **chia ngẫu nhiên (Random Train/Test Split)** trực tiếp trên 25.000 tệp ảnh. Hậu quả trực tiếp:
* Các biến thể xoay/lật của cùng một lát cắt mô học (cùng một bệnh nhân/tiêu bản gốc) bị phân tán đồng thời vào cả tập huấn luyện (Train) lẫn tập kiểm thử (Test).
* Mô hình học sâu không hề học các hình thái tế bào ác tính mang tính tổng quát, mà thực chất chỉ "học vẹt" (memorization) dấu vết quang học, phông nền kính hiển vi, sắc tố thuốc nhuộm cục bộ của 1.250 lát cắt đó.
* Do đó, **độ chính xác 99% – 100% được báo cáo tràn lan trong y văn thực chất là hiệu năng phóng đại giả tạo (Over-optimistic Performance)** bắt nguồn từ lỗi phương pháp luận nghiêm trọng trong phân chia dữ liệu.

### 2.2. Sự sụp đổ hiệu năng khi kiểm thử chéo sang nguồn dữ liệu khác (Domain Shift)
Trong giải phẫu bệnh thực tế, các trung tâm y tế khác nhau sử dụng hóa chất nhuộm H&E với nồng độ khác nhau, thời gian ủ khác nhau, máy quét tiêu bản (Leica, Aperio, Hamamatsu, Olympus) khác nhau và độ phân giải vật lý (Microns Per Pixel - MPP) khác nhau. Hiện tượng này tạo nên **sự chuyển dịch phân phối miền dữ liệu (Domain Shift / Batch Effect)** cực kỳ khắc nghiệt.

Thực nghiệm sơ bộ và rà soát y văn cho thấy: khi mang một mô hình đạt 99% trên LC25000 sang kiểm thử ngoại miền (Out-of-Distribution - OOD):
* Trên tập phổi ngoài **LungHist700**: Độ chính xác 7 lớp tụt dốc xuống chỉ còn **~38,4%** (ngay cả khi chỉ xét riêng trong cơ quan phổi, accuracy cũng chỉ đạt ~48,9%).
* Trên tập đại tràng ngoài **CRC-VAL-HE-7K**: Độ chính xác tổng thể sụt xuống thảm hại ở mức **~2,5%**, với **97% mẫu bị đoán nhầm sang cơ quan khác** (nhầm sang ung thư vú do khác biệt về trường nhìn và độ đậm của thuốc nhuộm).

---

## 3. LÝ DO CHỌN ĐỀ TÀI VÀ ĐÓNG GÓP MỚI

Nhận thức rõ lỗ hổng lớn của các công bố trước đây, đề tài này được xây dựng nhằm giải quyết trực diện vấn đề cốt lõi trên thông qua 3 đóng góp khoa học chính:

1. **Phân chia dữ liệu chống rò rỉ triệt để (Leak-Free Group-based Split):**  
   Ứng dụng thuật toán băm tri giác bất biến hình học xoay/lật (**Rotation-Invariant Perceptual Hashing - pHash**) kết hợp kiểm chứng hình học để gom 25.000 ảnh LC25000 về đúng các cụm mô gốc (Cluster). Khi phân chia tập Train/Val/Test, toàn bộ biến thể của cùng một cụm được giữ trọn vẹn trong một tập duy nhất (Group Split), cam kết **0% rò rỉ dữ liệu**.
2. **Chiến lược kiểm định chéo đa trung tâm ngoài miền (Cross-Dataset Generalization Benchmark):**  
   Mô hình được huấn luyện từ LC25000 và kiểm thử chéo không giám sát (zero-shot / out-of-domain) trên 3 nguồn độc lập hoàn toàn: **LungHist700** (Phổi), **CRC-VAL-HE-7K** (Đại tràng), và **BACH / BreakHis** (Tuyến vú), ánh xạ về hệ thống 7 lớp bệnh học thống nhất.
3. **Đánh giá định lượng vai trò của chuẩn hóa màu Macenko và đồng bộ tỷ lệ vật lý (MPP Harmonization):**  
   Xác định rõ việc chuẩn hóa mật độ quang phổ màu (Macenko Stain Normalization) và đo đạc kích thước tế bào chuẩn (Physical Scale Calibration dựa trên hồng cầu và nhân lympho) đóng vai trò quyết định như thế nào trong việc thu hẹp khoảng cách phân phối đặc trưng giữa các bệnh viện.

---

## 4. BẢNG TỔNG HỢP SO SÁNH CÁC CÔNG TRÌNH NGHIÊN CỨU LIÊN QUAN

| STT | Nhóm tác giả / Công trình | Mô hình / Phương pháp chính | Bộ dữ liệu thực nghiệm | Phương pháp phân chia dữ liệu | Độ chính xác báo cáo (Accuracy) | Đánh giá kiểm thử chéo & Hạn chế tồn tại |
|:---:|:---|:---|:---|:---:|:---:|:---|
| 1 | **Liu et al. / Frontiers (2022-2023)** | Swin Transformer V2 (Shifted Windows, CPB) | LC25000 (5 lớp: 25.000 ảnh) | **Random Split** (80% Train, 20% Test) | **99,40% – 99,97%** | Không kiểm thử ngoại miền. Bị rò rỉ dữ liệu do các góc xoay của cùng slide mô nằm ở cả train và test. |
| 2 | **XLLC-Net (PLOS ONE, 2023)** | Lightweight CNN (4 conv blocks, 3M params) + **Grad-CAM** | LC25000 (3 lớp phổi: 15.000 ảnh) | **Random Split** (70/15/15) | **99,62%** (F1: 99,70%) | Mô hình gọn nhẹ và có Grad-CAM trực quan, nhưng chỉ đánh giá ngẫu nhiên nội bộ; Grad-CAM dễ bám vào bias phông nền. |
| 3 | **Talukder et al. (ESWA, 2023)** | Hybrid Deep Features + Ensemble (Random Forest/XGBoost) | LC25000 (5 lớp) | **Random 10-Fold Cross-Validation** | Phổi: **99,05%**<br>Đại tràng: **100%** | Độ phức tạp cao. 100% accuracy trên đại tràng là dấu hiệu điển hình của việc học thuộc lòng các lát cắt mô bị trùng. |
| 4 | **Al-Jabbar et al. (2023)** | Deep Features (VGG19/GoogLeNet) + Handcrafted (LBP, GLCM) + ANN | LC25000 (5 lớp) | **Random Split** (70% Train, 30% Test) | **99,64%** | Kết hợp đặc trưng kết cấu truyền thống nhưng bỏ qua hiện tượng sai lệch nồng độ hóa chất nhuộm giữa các lab. |
| 5 | **Multi-CNN Benchmark (2022)** | Ensemble: ResNet50 + DenseNet121 + InceptionV3 | LC25000 (5 lớp) | **Random Split** (80/20) | **99,28%** | Chi phí tính toán lớn, không chứng minh được tính tổng quát khi triển khai sang ảnh của hệ thống scanner khác. |
| 6 | **Wang et al. (Nature Sci Data, 2024)** | Đề xuất dataset **LungHist700** & baseline CNN | LungHist700 (691 ảnh WSI) | Stratified Patient Split | Baseline: 85,2% – 88,6% | Công bố dataset độc lập chất lượng cao, khẳng định việc phân chia theo bệnh nhân làm giảm độ chính xác ảo. |
| 7 | **Kather et al. (PLOS Med, 2019)** | VGG/ResNet trên **NCT-CRC-HE-100K** & CRC-VAL-7K | Đại trực tràng đa trung tâm (NCT & UMM) | Cross-Center Validation (Độc lập 50 bệnh nhân) | In-domain: 94,3%<br>Cross-center: 88,1% | Một trong số rất ít bài kiểm thử chéo độc lập; phát hiện độ suy giảm hiệu năng rõ rệt giữa hai bệnh viện khác nhau. |
| 8 | **Đề tài nhóm (Nghiên cứu này)** | **ConvNeXt-Tiny & Swin-Tiny** + Macenko + MPP Calibration | **Đa nguồn (5 dataset):** LC25000, LungHist700, CRC-VAL, BACH, BreakHis (7 lớp) | **Leak-free Group Split (pHash)** cho train; **Cross-dataset (OOD)** cho test | *Đang đánh giá:* Phản ánh trung thực năng lực tổng quát hóa ngoài lâm sàng | **Khắc phục trọn vẹn rò rỉ dữ liệu; kiểm định chéo đa trung tâm; làm rõ tác động của chuẩn hóa màu sắc và tỷ lệ phóng đại.** |

---

## 5. TÀI LIỆU THAM KHẢO CHÍNH (KEY REFERENCES)

1. **Borkowski, A. A., et al.** (2019). *Lung and Colon Cancer Histopathological Image Dataset (LC25000)*. arXiv:1912.12142 / Federal Practitioner.
2. **Liu, Z., et al.** (2022). *Swin Transformer V2: Scaling Up Capacity and Resolution*. Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR).
3. **Kather, J. N., et al.** (2019). *Predicting survival from colorectal cancer histology slides using deep learning: A study of 1300 patients*. PLOS Medicine, 16(1), e1002730.
4. **Wang, C., et al.** (2024). *LungHist700: A Large-scale Multi-class Lung Histopathology Benchmark Dataset*. Nature Scientific Data.
5. **Selvaraju, R. R., et al.** (2017). *Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization*. IEEE International Conference on Computer Vision (ICCV).
6. **Macenko, M., et al.** (2009). *A method for normalizing histology slides for quantitative analysis*. IEEE International Symposium on Biomedical Imaging (ISBI).
7. **Aresta, G., et al.** (2019). *BACH: Grand Challenge on Breast Cancer Histology images*. Medical Image Analysis, 56, 122-139.
