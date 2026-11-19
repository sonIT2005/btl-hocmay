# Dữ liệu và hạn chế

## Dữ liệu

Nghiên cứu sử dụng năm bộ ảnh mô bệnh học nhuộm H&E của phổi, đại tràng và vú. LC25000 và BreakHis 40× cung cấp tập huấn luyện, tập xác thực và tập kiểm thử nội bộ. LungHist700, CRC-VAL-HE-7K và BACH được dành riêng cho kiểm thử chéo nguồn.

| Nguồn | Cơ quan và phạm vi sử dụng | Train | Val | Test nội bộ | Test chéo |
|---|---|---:|---:|---:|---:|
| LC25000 | Phổi và đại tràng | 17.464 | 3.742 | 3.743 | — |
| BreakHis | Vú, riêng mức 40× | 1.395 | 299 | 301 | — |
| LungHist700 | Phổi, patch cắt từ 691 ảnh nguồn | — | — | — | 14.557 |
| CRC-VAL-HE-7K | Đại tràng, hai nhóm NORM và TUM | — | — | — | 1.974 |
| BACH | Vú, patch cắt từ 400 ảnh microscopy | — | — | — | 13.581 |
| **Tổng mỗi nhánh tiền xử lý** | **57.056 mẫu đầu vào** | **18.859** | **4.041** | **4.044** | **30.112** |

Bảng đếm mẫu đầu vào ở cấp patch theo cột `split` của manifest E2. Bảy lớp lần lượt là phổi lành, ung thư biểu mô tuyến phổi, ung thư biểu mô tế bào vảy phổi, đại tràng lành, ung thư biểu mô tuyến đại tràng, vú lành và vú ác tính. Với BACH, hai nhãn Normal và Benign gộp vào vú lành, InSitu và Invasive gộp vào vú ác tính. Tập CRC giới hạn ở 741 patch NORM và 1.233 patch TUM.

LC25000 có 24.949/25.000 ảnh được đưa vào thí nghiệm. Nhóm tái dựng các họ ảnh biến đổi bằng đối chiếu hình học và giữ riêng 51 ảnh thuộc các nhóm nhỏ chưa đủ bằng chứng gán nhóm. BreakHis 40× được gộp theo mã ca, gồm 70 nhóm mã sau khi gộp các hậu tố section. E2 phân tầng theo lớp và chia theo nhóm với tỷ lệ mục tiêu 70/15/15 và seed 42. E1 dùng phép chia ngẫu nhiên theo ảnh để đối chiếu. Cả hai dùng bản dữ liệu đóng băng ngày 16/10/2026, fingerprint `f5c641abf5b155b1`.

Pipeline tạo ảnh RGB 224 × 224 pixel với mục tiêu 0,5 µm/pixel, tương ứng trường nhìn danh định 112 × 112 µm. Ảnh nội bộ dùng crop giữa, còn LungHist700 và BACH dùng lưới patch không chồng lấn và giữ vùng có tỷ lệ mô từ 50%. Hai nhánh `none` và `macenko` dùng chung tọa độ crop, nhãn và split. Macenko dùng một ảnh tham chiếu từ LC25000 train.

Nguồn đối chiếu gồm manifest đóng băng, bản đồ nhãn và bảng tổng hợp C5. [FROZEN.json](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/splits/FROZEN.json) · [label_map.json](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/splits/label_map.json) · [Bảng dữ liệu C5](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/outputs/eval/tables/dataset_summary.csv)

## Chú thích hình Grad-CAM

Hai hình minh họa tám patch, mỗi patch gồm ảnh đầu vào, Grad-CAM của ConvNeXt-Tiny và Grad-CAM của Swin-Tiny. Trong từng tập kiểm thử, một patch được rút từ các trường hợp cả hai mô hình đoán đúng và một patch từ các trường hợp cả hai đoán sai. Quy tắc rút dùng seed 42, chọn đều theo nhóm trước rồi theo patch, với tám `group_id` khác nhau. Chọn mẫu dựa trên dự đoán C5 trước khi tính bản đồ nhiệt. Checkpoint E2 nhánh `none` của ConvNeXt ở epoch 7 và Swin ở epoch 3, cùng seed huấn luyện 0.

- **Hình 1. Bốn patch cả hai mô hình dự đoán đúng.** CAM-03 cho thấy hai bản đồ cùng nổi bật ở dải bên trái patch CRC. [Hình 1](gradcam_4_dung.png)
- **Hình 2. Bốn patch cả hai mô hình dự đoán sai.** Ở CAM-07, ConvNeXt nhầm lớp trong cùng cơ quan, còn Swin nhầm sang cơ quan khác. Ở CAM-08, cả hai mô hình dự đoán lớp thuộc phổi cho patch từ BACH. [Hình 2](gradcam_4_sai.png)

Màu cam đậm hơn biểu thị giá trị Grad-CAM cao hơn trong cùng bản đồ. Grad-CAM lấy gradient logit của lớp dự đoán tại block cuối của ConvNeXt (`stages.3.blocks.2`) và lớp chuẩn hóa trước attention trong block cuối của Swin (`layers.3.blocks.1.norm1`). Tỷ lệ dưới mỗi bản đồ là softmax khi chạy lại bằng CPU FP32. Cả 16 nhãn dự đoán khớp với C5, còn giá trị xác suất có thể chênh do C5 dùng CUDA bf16. Bảng mẫu lưu đường dẫn patch, ảnh nguồn, nhãn, SHA-256, dự đoán và xác suất của cả hai lần chạy. [Bảng tám mẫu](samples.csv) · [Provenance](provenance.json)

## Hạn chế

1. **Tỷ lệ vật lý chưa được xác nhận ở mọi nguồn.** Giá trị MPP của LC25000 và LungHist700 là ước lượng. LC25000 còn có thể bị co giãn khác nhau theo hai trục do các phép biến đổi ảnh. Nhóm phát hiện dấu hiệu lệch tỷ lệ sau khi xem kết quả kiểm thử chéo của lần chạy đầu. Khảo sát bằng tế bào tham chiếu chưa có bộ đo đạt yêu cầu ở cả ba nguồn và chưa có kết quả rà độc lập để hoàn tất kiểm chứng. Theo quyết định D10 và D12, kết quả chính dùng bản đóng băng 16/10 với MPP LC25000 là 0,5 µm/pixel, trạng thái `estimated_unverified`. [Quyết định D10–D12](https://github.com/sonIT2005/btl-hocmay/blob/de68c188fcb902588522eb5b2042ed5a3c67cee2/DECISIONS.md#dữ-liệu)
2. **Chia theo nhóm có giới hạn về danh tính.** Nhóm LC25000 đại diện cho họ ảnh biến đổi được tái dựng. Mức độc lập theo bệnh nhân vẫn chưa xác định. Việc loại 51 ảnh có thể làm thay đổi phân bố mẫu nội bộ. BACH và CRC thiếu mã bệnh nhân đầy đủ trong dữ liệu sử dụng, nên lấy mẫu lại theo `group_id` vẫn có thể bỏ sót tương quan trong cùng bệnh nhân.
3. **Nhãn ở cấp patch có độ bất định.** Các patch cắt từ ảnh nguồn thừa hưởng nhãn ảnh. Một patch đạt ngưỡng mô có thể chỉ chứa vùng lành hoặc mô đệm trong ảnh mang nhãn ác tính. Các thước đo và Grad-CAM vì vậy cần được diễn giải ở cấp patch với nhãn hiện có.
4. **Màu nhuộm và sai lệch giữa nguồn.** Nhánh `none` giữ màu của ảnh đầu vào sau các bước xử lý hình học của nhóm. Lịch sử xử lý màu trước khi bộ dữ liệu được phát hành có thể khác nhau giữa các nguồn. Sai khác tỷ lệ, màu, thiết bị và thành phần mô có thể cùng xuất hiện, nên nguyên nhân nhầm cơ quan trên test chéo vẫn chưa được xác định.
5. **Grad-CAM là phân tích định tính.** Mỗi bản đồ thể hiện vùng đóng góp dương vào logit của lớp mô hình dự đoán. Bản đồ gốc có lưới 7 × 7 và được nội suy để chồng lên patch. Mức màu được chuẩn hóa riêng cho từng bản đồ, nên phép đối chiếu chủ yếu dựa trên vị trí tương đối của vùng nổi bật. Bộ tám ảnh được chọn theo kết quả đúng/sai của hai checkpoint seed 0, do đó chỉ minh họa các trường hợp cụ thể. Việc xác định mô u hoặc mức trùng khớp với vùng bệnh cần chú giải mô học độc lập. [Selvaraju và cộng sự, ICCV 2017](https://openaccess.thecvf.com/content_iccv_2017/html/Selvaraju_Grad-CAM_Visual_Explanations_ICCV_2017_paper.html)
