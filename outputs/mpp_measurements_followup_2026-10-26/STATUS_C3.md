# C3: đã bổ sung mẫu, phần còn thiếu và cách tiếp tục

Cập nhật ngày **26/10/2026**. Phiên hiện hành: `outputs/mpp_measurements_followup_2026-10-26/draft_v4`. Đây là **bộ đo dự thảo chưa review độc lập**, không phải nghiệm thu MPP. Các số liệu v3 trong mục 11 của bàn giao là mốc trước đợt bổ sung này.

## Đã hoàn thiện trong đợt bổ sung

| Nhân nghi lympho | Đối tượng tính trong dự thảo | Ảnh | Còn thiếu về số lượng | Rút review seed 43 |
|---|---:|---:|---|---:|
| CRC | 30 | 16 | Đủ mức tối thiểu trong dự thảo | 6 |
| BACH | 30 | 18 | Đủ mức tối thiểu trong dự thảo | 6 |
| BreakHis 40× | 0 | 0 | 30 tế bào từ ít nhất 15 ảnh | 0 |

- Bổ sung 3 CRC và 11 BACH từ các ảnh raw trong hàng đợi đã khóa. Không thay đổi 82 bản ghi trước, seed, tiêu chí hình thái hoặc MPP. Ba ứng viên mới chưa rõ và bốn vùng BreakHis được ghi riêng, không bù quota.
- Tổng hiện tại: **60 dòng dự thảo**, **43 bản ghi bị tách riêng**; 103 ROI, trong đó 69 đối tượng có đường vẽ (60 dự thảo + 9 không tính mẫu), 34 vị trí chưa thể đo. Tất cả vẫn `draft_unreviewed`, người rà trống; chính thức được chấp nhận: **0**.
- Đã xem thêm 360 ROI trên đủ 60 ảnh BACH và 360 ROI trên đủ 60 ảnh BreakHis; thêm 48 ROI trên 8 ảnh CRC và một ROI CRC chọn trực tiếp từ ảnh đã có mẫu. Bộ chỉ điểm dùng tương phản tương đối để tìm vùng trên ảnh nhạt; đây là công cụ điều hướng, không thay tiêu chí nhận diện hay lấy đường kính blob làm số đo. Đây vẫn là khảo sát có giới hạn, không chứng minh nguồn không có marker.
- Khảo sát RBC trước đó chưa có bộ tham chiếu đủ ba nguồn. Nhân lympho được đo riêng; không pool RBC/nhân, không chọn marker theo LOO. Cả hai nhánh chưa đủ ba đối chứng nên **LOO vẫn để trống**, không kết luận phương pháp thất bại.
- Bổ sung `group_id`, kích thước raw vào CSV; thêm ô trống ghi tọa độ/H/V đo lại và ngày review. Trang ảnh có liên kết nhảy thẳng tới 12 mẫu ngẫu nhiên. Không tự ghi kết quả review hoặc tên người.
- **53/53 test đạt**, không skip. Kiểm SHA 180 raw, đối chiếu pixel 103 ROI, tính lại D/H/V từ đầu mút cho 69 đối tượng có đường vẽ. Mỗi ảnh có tối đa 3 đối tượng có caliper, kể cả đối tượng tách riêng. 36 file split/config/kit giữ nguyên SHA. Công cụ chính thức không đổi; thử nhập draft vào bản sao kit vẫn bị chặn.

## Mở gì để rà

1. Mở [trang ảnh](draft_v4/index.html). Nhấp tên ở mục **Locked random review draw** để tới đúng mẫu; bên trái là pixel raw, bên phải là đường vẽ. Link context giữ kích thước raw.
2. Xem [bảng đo 60 dòng](draft_v4/draft_measurements.csv), [43 bản ghi tách riêng](draft_v4/excluded_objects.csv), [danh sách 12 mẫu ngẫu nhiên](selected_review_cells.csv).
3. Trả [review_return.csv](draft_v4/review_return.csv): nhận diện, biên, tọa độ D và H/V đo lại nếu cần, người rà thật, ngày và ghi chú. Giữ nguyên ID để nối lại nguồn. Không chỉ đổi status hoặc điền tên C3 vào số đo hỗ trợ khi chưa xác nhận/đo lại.
4. Chiều dài D/H/V là xấp xỉ từ đường biên lồi đặt bằng mắt trên raw. Số thập phân là kết quả tính từ tọa độ, không phải độ chính xác dưới pixel. Rà cả biên ngoài nhân, tránh đo riêng lõi nhuộm đậm/nucleolus.

## Còn thiếu để tiếp tục C3

1. **BreakHis:** nhận diện và đo được 30 tế bào đạt cùng tiêu chí trên ít nhất 15 ảnh trong hàng đợi. Nhờ người nhận diện được marker rà các vùng đã lưu và raw; không cần phải là bác sĩ theo instruct2, nhưng không nhận diện chắc thì tiếp tục ghi chưa rõ. Không tự đổi sang độ phóng đại, nguồn khác, loại nhân khác hoặc seed khác để qua ngưỡng. Nếu không tìm được, trạng thái là **thiếu đầu vào/chưa kiểm chứng**, không phải đã thất bại kiểm định LOO. Có thể tìm metadata calibration/thước chuẩn đáng tin cậy để nhóm xem xét nhánh thay thế có ghi quyết định; không tự gán MPP.
2. **Review độc lập:** người khác người đo/C3 rà tối thiểu 6 CRC + 6 BACH được rút hiện tại. Khi thêm đủ 30 BreakHis sẽ có thêm 6 đối tượng BreakHis cần rút/rà bằng cùng seed; nếu bộ mẫu thay đổi thì lưu phiên bản và rút lại đúng quy tắc. Loại mẫu không rõ rồi bổ sung theo cùng tiêu chí.
3. **Kiểm chứng ba nguồn:** sau khi đủ mẫu cùng marker, chạy LOO dự thảo để kiểm số học; kết luận chính thức chỉ sau khi có dữ liệu/review thật trong kit. Ngưỡng ≤15% cho từng nguồn. Chỉ mở rộng một lần lên 60 tế bào/nguồn nếu có LOO đủ mẫu mà không đạt; 60 ảnh ứng viên không phải 60 tế bào đã đo.

Nếu không thể có marker đối chứng hoặc calibration đáng tin cậy, không thể hoàn tất trung thực nhánh “ước lượng MPP mới” chỉ bằng thêm code/GPU. Cần ghi rõ thiếu hụt và quyết định của nhóm; không ký nghiệm thu hoặc đổi trạng thái thành `estimated_reference_cell` khi chưa có chứng cứ.

## Các bước sau, chưa được thực hiện

- Chỉ khi ba đối chứng qua kiểm chứng mới đo LC25000 train: ít nhất 15 tế bào phổi + 15 đại tràng, mỗi group tối đa 1 ảnh; bootstrap theo ảnh, IQR và H/V. LungHist700 20×/40× đo riêng nếu thực hiện.
- Nhóm chốt MPP/quyết định nghiên cứu rồi mới sửa config, sinh output fingerprint mới, so bất biến và freeze mới. Dữ liệu hiện tại giữ nguyên.
- Bằng chứng run đầu còn cần C4 cung cấp logits/probabilities đầy đủ hoặc checkpoint gốc để chốt restricted accuracy/tái lập diagnostics; checkpoint đó chưa có ở `outputs/checkpoints` tại máy này.
- GPU chỉ cần ở bước smoke CUDA/train tương ứng. Giai đoạn đo/review này chạy CPU; **không chạy model hoặc regenerate trong đợt bổ sung**.

## Nội dung có thể gửi cho người rà

> Nhờ bạn rà độc lập bộ đo C3 dự thảo v4: xác nhận loại nhân và biên ở 6 mẫu CRC + 6 mẫu BACH đã rút seed 43, đo lại D/H/V trên raw nếu cần, điền người rà/ngày/kết quả vào review_return.csv. CRC và BACH hiện mỗi nguồn 30 đối tượng dự thảo; chưa có số đo chính thức. BreakHis đã khảo sát đủ 60 ảnh, gồm lượt xem thêm 360 ROI nhưng chưa chọn được nhân lympho đủ rõ: nhờ bạn kiểm tra khả năng nhận diện và bổ sung 30 tế bào từ ≥15 ảnh nếu có, tối đa 3 tế bào/ảnh, giữ nguyên hàng đợi/tiêu chí. Nếu không xác định được thì trả đúng lý do, không ký đạt hoặc suy MPP. Chưa chạy LOO/đổi MPP/sinh ảnh/model.

Các PNG nằm ngoài Git theo cấu hình repo; dùng gói ZIP local cùng thư mục này khi chuyển cho người rà. Gói phục vụ rà nội bộ; không tự gửi hoặc phát hành. Bản gốc raw vẫn ở FrameView, code và artifacts ở `btl-hocmay`.
