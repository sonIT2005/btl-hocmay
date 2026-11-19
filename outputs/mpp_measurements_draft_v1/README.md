# Bộ đo C3 dự thảo — chưa review độc lập

Bản hiện hành: **draft_v3**. Mở [trang xem đối tượng](draft_v3/index.html), [bảng đo](draft_v3/draft_measurements.csv), [bảng loại](draft_v3/excluded_objects.csv) và trả [review_return.csv](draft_v3/review_return.csv).

| Nhân nghi lympho | Dòng đo dự thảo | Số ảnh | Thiếu tế bào / ảnh | Rút review |
|---|---:|---:|---|---:|
| CRC | 27 | 14 | 3 tế bào; ít nhất 1 ảnh khác | 6 |
| BACH | 19 | 16 | 11 tế bào; đã đủ số ảnh tối thiểu | 4 |
| BreakHis 40× | 0 | 0 | 30 tế bào / 15 ảnh | 0 |

RBC chưa có mẫu đạt tiêu chí ở cả ba nguồn. 36 đối tượng/vùng nghi ngờ được ghi riêng. Không trộn marker, không tính đối tượng chưa rõ vào cỡ mẫu. Chưa tính LOO; đây không phải kết luận phương pháp thất bại.

Mỗi đường biên được Codex đặt bằng mắt trên raw, polygon lồi 8 đỉnh; tính dây dài nhất và dây H/V bên trong polygon. Đây là ước lượng biên nhìn thấy, chưa phải số đo chính thức. Measurer ghi rõ Codex_visual_assist, người rà để trống. Các ROI có cặp ảnh nguyên pixel và ảnh đánh dấu; context giữ kích thước raw. Vàng=D, xanh lơ=H, cam=V, xanh lá=biên vẽ.

[Danh sách review](selected_review_cells.csv) rút ngẫu nhiên 6 CRC + 4 BACH bằng seed 43. Người rà xác nhận danh tính/vị trí các ứng viên và đo lại ít nhất các dòng được rút; loại/ghi lý do nếu không rõ. Không chỉ thay status hoặc điền tên C3 vào số đo AI. Bổ sung đủ mẫu theo cùng hàng đợi trước LOO. Bản v1/v2 chỉ giữ lịch sử tự QA; v3 loại thêm 3 đối tượng CRC do biên/hình dạng chưa rõ, không dựa vào LOO.

Chi tiết phạm vi khảo sát, kiểm chứng và việc phải xác nhận: [BAN_GIAO_INSTRUCT2.md](../../docs/BAN_GIAO_INSTRUCT2.md), mục 11. [final_verification.json](final_verification.json): 180 SHA raw, 82 ROI khớp pixel, 55 bộ D/H/V kiểm từ đầu mút; 36 file khóa không đổi; 53 tests đạt. Kit chính thức vẫn 0 dòng và thiếu review bị chặn.

Raw ở FrameView, không copy dataset. Không đổi nhãn/group/split/MPP/freeze, không regenerate hoặc chạy model. PNG bị ignore khỏi Git; phải gửi kèm thư mục output này nếu bàn giao cho máy khác. Mã tái xuất chuẩn là tools/draft_mpp.py; số đo đầu vào đầy đủ ở draft_v3/annotations_input.json. Các script trong provenance_scripts chỉ lưu đúng thao tác cục bộ đã thực hiện, có đường dẫn máy/thư mục tạm lịch sử; không phải entrypoint triển khai.
