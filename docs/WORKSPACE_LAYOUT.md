# Bố trí workspace sau hợp nhất — 25/10/2026

## Phân chia trách nhiệm thư mục

| Loại | Vị trí chính |
|---|---|
| Ảnh raw/processed, metadata đọc archive dataset | `C:\Users\Admin\Documents\FrameView\btl-histo\data` |
| Code, config, tests, manifests và FROZEN | `C:\Users\Admin\Documents\GitHub\btl-hocmay` |
| Tài liệu bàn giao đang dùng | [BAN_GIAO_INSTRUCT2.md](BAN_GIAO_INSTRUCT2.md) |
| Giấy phép, mô tả nguồn, bản dự án cũ | `docs/provenance/` |
| README/HANDOFF/PLAN cũ của FrameView | `docs/archive/frameview_root_2026-10-25/` |
| Mốc code/config/metadata C1–C3 frozen | `snapshots/2026-10-16/` |
| Khác biệt C3 không trùng snapshot | `snapshots/frameview_merge_conflicts_2026-10-25/` nếu có |
| Code/tài liệu trước thay đổi đường dẫn | `outputs/reorganization_2026-10-25/before_layout/` |
| MPP kit, pilot, review pack, bằng chứng bảo trì | `outputs/` trong repo; không còn trong FrameView |

Không có junction/symlink và không có bản copy dataset mới trong repo. Thư mục data bên FrameView giữ đường dẫn ảnh gốc; phần code đọc nó qua `src/data/paths.py`.

## Hợp nhất và giữ phiên bản

Đã xử lý **368 file** theo kế hoạch kiểm hash trước khi chuyển:

- **317 file di chuyển** vào repo.
- **40 file trùng** giữ bản đã có ở repo rồi bỏ bản dư tại FrameView sau khi SHA-256 khớp.
- **11 file C1–C3 khác code C4** đã có nguyên byte trong snapshot; giữ snapshot và bản C4 mới hơn, không ghi đè ngược code C4.

Toàn bộ snapshot 50 file được di chuyển nguyên trạng; không tạo thêm một bản copy ảnh. Hai script `process_db_stat.py` đi kèm BreakHis được giữ dưới `docs/provenance/upstream_tools/`, kèm ánh xạ vị trí raw cũ. Không dùng chúng trong loader hoặc coi chúng là ảnh bị loại.

Code đường dẫn đã được tích hợp để các tools prepare/validate/audit/download/grouping/diagnostics và loader train cùng tìm đúng data_root. Prepare/validate nhận thêm `--data-root`; CLI chỉ chọn nơi đọc dữ liệu, không đổi split/MPP và không bỏ guard regeneration.

Recipe 15 run, config MPP, các manifest, nhãn, group và FROZEN cũ giữ nguyên byte trong đợt hợp nhất. Cấu hình máy riêng nằm trong `configs/paths.local.json`, được ignore; ví dụ portable ở `configs/paths.example.json`.

## Kiểm chứng sau chuyển

- **41.180 raw + 114.112 processed khớp SHA-256**, 0 lỗi.
- **64 file được bảo vệ khớp bản gốc** qua vị trí mới hoặc snapshot giữ nguyên byte.
- **42/42 tests đạt**, không skip, gồm fixture ảnh thật và test resolver/ưu tiên đường dẫn.
- Preflight ConvNeXt/Swin kiểm mapping, toàn bộ đường dẫn và tensor/forward CPU; xem báo cáo trong `outputs/reorganization_2026-10-25`.
- Không huấn luyện, regenerate, regroup, thay đổi MPP, freeze lại, stage, commit hoặc push.

`FROZEN.json` vẫn mô tả freeze lịch sử 16/10. Hash source code trong đó không phải hash code mới tích hợp. Không được sửa FROZEN để làm như code mới đã sinh ra bộ ảnh cũ. Khi audit bản cũ, kiểm source/config qua snapshot; khi train mới, ghi code thực thi vào provenance mới.

## Đường dẫn trong bằng chứng lịch sử

Các JSON/CSV/protocol đã khóa có thể chứa đường dẫn FrameView tại thời điểm tạo. **Giữ nguyên byte các bằng chứng đó**, không sửa hashes hoặc protocol chỉ vì đổi thư mục. Tra:

```text
outputs/reorganization_2026-10-25/merge_plan.json
outputs/reorganization_2026-10-25/actions.jsonl
outputs/reorganization_2026-10-25/relocation_map.json
```

`target` là vị trí sau chuyển. Nếu file hoạt động cần cập nhật đường dẫn/nội dung, `preserved_copy` trỏ tới bản nguyên byte trước cập nhật. `historical_path()` dùng ánh xạ này để kiểm checksum lịch sử. Các script audit hoạt động đã được sửa để đọc dataset riêng và giữ báo cáo mới trong thư mục reorganization; các script trong staging/backup/snapshot là bản lịch sử, không dùng làm entrypoint hiện hành.

`SHA256SUMS.json` ở các đợt bàn giao trước chứng nhận phiên bản trước hợp nhất. Các tài liệu có cập nhật đường dẫn và code tích hợp có hash mới, được ghi riêng trong `code_changes.json`, `doc_changes.json` và `final_checks.json`; không diễn giải checksum lịch sử như checksum của mọi file hoạt động hiện tại.

## Chuyển sang máy khác

Chuyển repo và dataset theo hai phần; không cần copy ảnh vào repo. Giữ manifest/reference/provenance của dataset tương ứng. Tạo môi trường từ các file environment/lock; đặt `BTL_DATA_ROOT` hoặc `configs/paths.local.json`, kiểm resolver rồi chạy preflight. Không mang môi trường runtime/cache sang thay cho cài đặt môi trường.

MPP vẫn chưa được nghiệm thu. Việc gộp workspace không làm hoàn thành yêu cầu đo tế bào, review độc lập hay 15 run; xem file bàn giao chính để biết phần còn thiếu.
