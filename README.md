# Bài tập lớn học máy — histopathology

Repo này là nơi làm việc chính cho **code, config, manifests/split, báo cáo và tài liệu**. Ảnh/dataset nằm riêng tại `C:\Users\Admin\Documents\FrameView\btl-histo\data`; không copy dataset vào Git, không dùng junction.

Tài liệu cần đọc:

- [Bàn giao và đối chiếu instruct2](docs/BAN_GIAO_INSTRUCT2.md): phần đã làm, bằng chứng, các đầu vào còn thiếu và người phụ trách.
- [Bố trí thư mục và kết quả hợp nhất](docs/WORKSPACE_LAYOUT.md): đường dẫn, bản cũ giữ ở đâu, cách kiểm chứng sau chuyển.
- [Đo MPP và kiểm hạ tầng model](docs/MPP_AND_SMOKE.md).
- [Yêu cầu phản hồi gốc](instruct2.md), [quyết định nghiên cứu](results/C1_DECISIONS.md).

## Bố trí hiện tại

```text
FrameView/
  btl-histo/
    data/
      raw/                       # 41.180 ảnh nguồn
      processed/                 # 114.112 ảnh hai nhánh + reference
      downloads/                 # metadata tải/kiểm archive của dataset

btl-hocmay/
  src/  tools/  tests/            # code đang dùng
  configs/                       # recipe, reference, đường dẫn local
  splits/                        # manifest và FROZEN.json cũ giữ nguyên byte
  results/                       # kết quả/báo cáo
  docs/                          # bàn giao, provenance, tài liệu lịch sử
  outputs/                       # log/predictions, MPP kit và QA local
  snapshots/                     # code/config/metadata lịch sử, không chứa bản copy dataset
```

FrameView chỉ là kho ảnh/dataset. Mọi lệnh dưới đây chạy từ thư mục repo `btl-hocmay`.

## Cấu hình đường dẫn dữ liệu

Máy hiện tại đã có file local **không đưa lên Git** `configs/paths.local.json`:

```json
{
  "data_root": "C:/Users/Admin/Documents/FrameView/btl-histo/data"
}
```

Trên máy khác, sửa file local hoặc đặt biến môi trường:

```powershell
$env:BTL_DATA_ROOT = 'D:\Datasets\histo\data'
```

Ưu tiên: đường dẫn custom tường minh trong config/CLI → `BTL_DATA_ROOT` → file local → `data/` dưới repo. Giá trị recipe mặc định `data` dùng vị trí dataset đã cấu hình. Dùng đường dẫn tuyệt đối nếu muốn override một vị trí cụ thể. `splits/` và `outputs/` mặc định luôn thuộc repo.

Kiểm đường dẫn mà code thực sự dùng:

```powershell
python -c "from src.data.paths import resolve_data_root; print(resolve_data_root())"
```

## Môi trường và kiểm tra

Tạo môi trường data/CPU theo cấu hình đã giữ; lệnh `python` phải chạy trong môi trường đã kích hoạt:

```powershell
conda env create -f environment.yml
conda activate btl-histo-data
python -m unittest discover -s tests -v
```

Sau hợp nhất: **42/42 tests đạt**, không skip; gồm fixture grouping trên ảnh thật và 5 test đường dẫn tách dataset. Chi tiết: `outputs/reorganization_2026-10-25/tests.txt`.

Preflight không train và không tải pretrained weights:

```powershell
python tools/check_training.py configs/runs/e2_convnext_group_none_s0.yaml --tensor-check --forward --device cpu
python tools/check_training.py configs/runs/e2_swin_group_none_s0.yaml --tensor-check --forward --device cpu
```

Hai model phải đọc ảnh thật tại FrameView, metadata tại repo. Run cũ có thể báo `blocked_old_artifacts`: guard bảo vệ provenance, không phải quyền chạy đè.

## Dữ liệu và MPP

Mốc dữ liệu vẫn là **16/10/2026**, fingerprint `f5c641abf5b155b1`, 57.056 dòng mỗi manifest nhánh `none`/`macenko`. 51 ảnh LC25000 cách ly vẫn nằm ngoài thí nghiệm. Không đổi nhãn, cơ quan, group hoặc split trong đợt chuyển thư mục.

MPP LC25000/LungHist700 vẫn là `estimated_unverified`; pilot chưa đủ tế bào tham chiếu xác nhận và review độc lập. Bộ đo ở `outputs/maintenance_2026-10-25/mpp_kit`; gói rà 180 ảnh đối chứng ở `outputs/handoff_2026-10-25/review_pack`. Xem file bàn giao để tiếp tục đúng quy trình.

Không chạy lại grouping hay regenerate chỉ để sửa đường dẫn. `prepare.py` được chặn trên dữ liệu frozen nếu không có `--allow-regenerate`. Cờ này chỉ dùng khi bằng chứng MPP/snapshot đã được duyệt; việc chuyển thư mục không làm thay đổi MPP.

Code hiện tại có thể khác hash code ghi trong freeze lịch sử. Snapshot `snapshots/2026-10-16` giữ đầy đủ các byte cũ; không ghi đè FROZEN cũ để che khác biệt. Contract dữ liệu/manifest giữ nguyên và code thực thi được ghi provenance riêng cho run mới.

## Model và kết quả cũ

`environment-gpu.yml` dành cho môi trường train; phải kiểm CUDA thực tế trước khi dùng. Kết quả CPU/preflight không chứng minh đã train được trên GPU. Các run nghiên cứu vẫn chờ nghiệm thu MPP/quyết định nhánh không đạt. Smoke kỹ thuật, khi cần, dùng output riêng theo `docs/MPP_AND_SMOKE.md`.

Log/predictions run đầu được giữ trong `outputs/`. C4 cần checkpoint gốc/scores đủ precision để chốt restricted accuracy và tái chạy diagnostics; checkpoint đó hiện chưa có trên máy local. Không ghi đè kết quả cũ hoặc dùng test chéo để chọn MPP.

Ảnh, QA chứa ảnh, snapshots và cấu hình đường dẫn local được ignore khỏi Git. Code/tài liệu mới chưa được stage/commit/push trong đợt hợp nhất này.
