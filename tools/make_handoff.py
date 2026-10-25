"""Build a factual handoff from completed machine-readable checks."""
from pathlib import Path
from collections import Counter
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))

def main():
 raw=load('results/raw_audit.json');groups=load('results/grouping_summary.json')
 prep=load('results/preparation_summary.json');validation=load('results/validation.json')
 frozen=load('splits/FROZEN.json')
 test=(ROOT/'results/test_results.txt').read_text(encoding='utf-8-sig')
 count=re.search(r'Ran (\d+) tests?',test)
 if validation['errors'] or raw['errors'] or not test.rstrip().endswith('OK'):
  raise RuntimeError('Checks have not passed; refusing a success handoff')
 source_rows=[]
 for name,n in raw['source_counts'].items():
  source_rows.append(f"| {name} | {n:,} | {raw['selected_counts'][name]:,} | {prep['samples_by_source'].get(name,0):,} |")
 with (ROOT/'splits/inventory.csv').open(encoding='utf-8',newline='') as f:
  inventory=list(csv.DictReader(f))
 active={name:{r['group_id'] for r in inventory if r['source']=='LC25000' and r['original_label']==name and r['included']=='True'} for name in groups['groups_per_class']}
 active_count=sum(len(v) for v in active.values())
 classes='\n'.join(f"| {name} | {n:,} | {len(active[name]):,} |" for name,n in groups['groups_per_class'].items())
 internal=Counter()
 with (ROOT/'splits/splits.csv').open(encoding='utf-8',newline='') as f:
  for row in csv.DictReader(f):
   if row['split']!='xtest':internal[(row['label'],row['split'])]+=1
 class_names=load('splits/label_map.json')['classes']
 distribution='\n'.join(f"| {label} {class_names[str(label)]} | {internal[(str(label),'train')]:,} | {internal[(str(label),'val')]:,} | {internal[(str(label),'test')]:,} |" for label in range(7))
 reference=prep['reference']
 text=f'''# Bàn giao C1–C3 — scope 6 tuần

Trạng thái kiểm tra: **{validation['status']}**. Đã chuẩn bị dữ liệu và file bàn
giao local; kết quả này không phải kết quả huấn luyện/đánh giá các model E1–E4.
Code/metadata nằm trong `btl-hocmay`; cả 5 dataset nằm tại data_root cấu hình riêng. Xem README.md và docs/WORKSPACE_LAYOUT.md.
LC25000/LungHist700 được di chuyển từ bản cũ, không sao chép thêm tài nguyên.
File nén đã giải nén, cache trung gian, môi trường cục bộ và bản xử lý cũ đã
được dọn theo yêu cầu. Giữ ảnh gốc để truy vết và hai nhánh none/Macenko cho
thí nghiệm so sánh. Xem `cleanup_summary.json`, `delivery_integrity.json` và
`../README.md` để chuyển máy, kiểm tra và tạo lại môi trường.
Mã/tài liệu/metadata cũ được giữ gọn ở
`../data/downloads/provenance/legacy_project/` để truy vết baseline.

## Dữ liệu thực tế

| Dataset | Ảnh raw kiểm tra đủ | Ảnh nguồn chọn theo scope | Mẫu model / mỗi nhánh |
|---|---:|---:|---:|
{chr(10).join(source_rows)}

- Giải mã và SHA-256 **{raw['raw_images']:,} ảnh raw**, lỗi: {len(raw['errors'])}.
- Giải mã **{validation['image_files_decoded']:,} ảnh model** thuộc hai nhánh,
  kiểm tra kích thước 224×224/RGB, đường dẫn và ghép cặp none/Macenko.
- CRC-VAL-HE-7K dùng riêng NORM/TUM; BreakHis dùng riêng 40×. Các ảnh khác
  vẫn giữ trong raw và inventory có lý do loại, không lẫn vào train.
- BACH đủ 100 ảnh/lớp, đối chiếu ground truth; không lấy WSI vào pipeline.
- BreakHis có 74 ảnh raw cao 456 px thay vì 460 px; không tự loại các ảnh này.
- **{prep.get('lc_images_pending_family_review',0)} ảnh LC25000 trong nhóm 1–4 ảnh**
  được giữ riêng ở `splits/grouping_review_required.csv`, chưa đưa vào cả E1/E2.
  Đây là chưa đủ bằng chứng về họ hàng ảnh, không phải ảnh hỏng hay sai nhãn.

## Nhóm ảnh và chia tập

Baseline pHash cũ: **{groups['legacy_phash_groups']:,} nhóm**. Kết quả mới:
**{groups['verified_groups']:,} nhóm được tái dựng**, {groups['accepted_edges']:,}
cạnh nối đã qua kiểm chứng pixel/hình học. **{active_count:,} nhóm LC25000**
được dùng trong thí nghiệm sau khi giữ riêng các nhóm 1–4 ảnh. Không ép số nhóm về 1.250.

| Lớp nguồn LC25000 | Nhóm tái dựng | Nhóm vào thí nghiệm |
|---|---:|---:|
{classes}

Group ID là hash tên thành viên. BreakHis giữ mã gốc nhưng gộp các hậu tố section
của cùng mã ca số: 70 nhóm bảo thủ, không diễn giải là xác minh 70 bệnh nhân.
Chia theo lớp và nhóm với seed 42; quota nhóm 70/15/15 dùng largest remainder,
thử các hoán vị có seed để cân bằng số ảnh, không sử dụng kết quả mô hình.

| Nhãn nội bộ | Train | Val | Test |
|---|---:|---:|---:|
{distribution}

- Nhóm xuất hiện ở nhiều split: **{validation['group_overlap_count']}**.
- Mã bệnh nhân được cung cấp xuất hiện ở nhiều split: **{validation['patient_overlap_count']}**.
- Ba nguồn test chéo chỉ có `xtest`; không dùng làm train/val hay chọn tham chiếu.
- `split_random` là đối chứng chia theo ảnh cho E1, cùng danh sách mẫu.

## Tiền xử lý và kiểm chứng

FOV mục tiêu 112×112 µm tại 0,5 µm/pixel, đầu vào 224×224. Nội bộ dùng center
crop; LungHist700/BACH dùng lưới không overlap sau quy đổi scale. Loại
**{prep['tissue_rejected_patches']:,} patch ngoài miền** có mô <50%.
Hai nhánh dùng cùng crop, label, group và split; fingerprint:
`{prep['processing_signature']}`.

Macenko đã sửa lỗi góc qua biên -pi/pi, dùng covariance đã trừ trung bình và
kiểm tra basis suy biến. Profile nguồn lấy mẫu đều từ toàn ảnh để dùng chung
cho các patch; beta transparency thực dùng được ghi vào metadata. Có kiểm
chứng độc lập với torchstain và regression test tương phản cấu trúc. Mọi lỗi
số học được báo rõ, không âm thầm trả ảnh gốc như kết quả chuẩn hóa thành công.

Tham chiếu duy nhất: `{reference['source_image_path']}`, split **train**,
group `{reference['group_id']}`; condition number
**{reference['basis_condition_number']:.3f}**. Crop và SHA-256 nằm trong
`configs/reference.json`. Không chọn tham chiếu từ test hoặc theo cơ quan.

Đã pass **{count.group(1) if count else 'unknown'} tests** về mapping, giữ section
cùng ca, split tái lập/không cắt nhóm, xoay góc lẻ/co giãn hai trục, trường hợp
ảnh xanh sáng và Macenko. Xem `test_results.txt`, `raw_audit.json`,
`validation.json`; ảnh đối chiếu tại `../outputs/qa/`.

## Dùng cho C4/C8

Đọc `splits/splits_none.csv` hoặc `splits/splits_macenko.csv` theo config stain.
Cả hai có đúng 7 cột `image_path,label,organ,source,group_id,split,split_random`.
Đường dẫn tính từ thư mục `data/`. Bản `splits/splits.csv` có metadata mở rộng
để truy ngược về ảnh nguồn và tọa độ crop. Nhãn và source map nằm trong
`splits/label_map.json`, nguyên liệu kiểm kê trong `splits/inventory.csv`.

Đóng băng: `{frozen['frozen_at_utc']}`; checksum ở `splits/FROZEN.json`.
Không chỉnh split sau khi xem kết quả model. Nếu phát hiện vấn đề sau đó,
ghi rõ ảnh hưởng/giới hạn và trao đổi với cả nhóm theo scope.

## Giới hạn phải đưa vào báo cáo

1. **MPP LC25000 và LungHist700 là ước lượng, chưa hiệu chuẩn.** Affine do
   augmentation LC25000 còn có thể làm thay đổi scale theo từng trục. Không
   tuyên bố đã khớp chính xác tỷ lệ vật lý của tất cả nguồn.
2. LC25000 không cung cấp patient/source IDs đầy đủ; các nhóm khôi phục bằng
   hình học không chứng minh độc lập theo bệnh nhân hoặc không còn rò rỉ tuyệt đối.
   51 ảnh cần rà soát không vào thí nghiệm; phải báo mẫu số 24.949/25.000 và
   khả năng việc loại các biến thể khó này làm thay đổi phân bố ảnh nội bộ.
3. BACH/CRC thiếu patient IDs đầy đủ; bootstrap theo image/patch group có thể
   chưa phản ánh hết tương quan giữa mẫu cùng bệnh nhân.
4. Nhãn ảnh truyền xuống patch là weak label; đủ mô không đồng nghĩa có tế bào u.
5. `none` là không áp dụng thêm Macenko của nhóm; không mặc định nguồn chưa
   từng xử lý màu. Phải nêu giới hạn upstream stain khi diễn giải CRC.
6. Dữ liệu/ảnh biến đổi không đưa lên Git. BACH CC BY-NC-ND 4.0 và điều kiện
   phi thương mại của Phikon được lưu trong `C1_DECISIONS.md` và provenance.
7. Bàn giao repo `btl-hocmay` và dataset tại data_root riêng. Đặt BTL_DATA_ROOT
   hoặc configs/paths.local.json; không cần junction hay copy thêm dataset. Môi trường
   Python phải tạo lại từ các file cấu hình đã giữ, cache sẽ sinh lại khi cần.
'''
 (ROOT/'results/HANDOFF.md').write_text(text,encoding='utf-8')
 print('HANDOFF_WRITTEN',ROOT/'results/HANDOFF.md')

if __name__=='__main__':main()
