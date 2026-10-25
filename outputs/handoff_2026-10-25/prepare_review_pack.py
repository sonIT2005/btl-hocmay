"""Prepare the locked 60-image control queues and blank human measurement forms."""
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
import sys
sys.path.insert(0, str(ROOT))
from src.data.paths import resolve_data_root, historical_path
DATA_ROOT = resolve_data_root(ROOT)
KIT = ROOT / 'outputs/maintenance_2026-10-25/mpp_kit'
OUT = HERE / 'review_pack'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def csv_write(path, rows, columns):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(exist_ok=False)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    with (KIT / 'candidates.csv').open(encoding='utf-8-sig', newline='') as stream:
        all_rows = list(csv.DictReader(stream))
    rows = [r for r in all_rows if r['source'] in ['BACH', 'BreakHis', 'CRC-VAL-HE-7K']]
    csv_write(OUT / 'control_queue.csv', rows, list(rows[0]))
    forms = [{'candidate_id': r['candidate_id'], 'source': r['source'], 'queue_order': r['queue_order'],
              'image_path': r['image_path'], 'screening_decision': 'pending_human_cell_identity',
              'reviewer': '', 'note': ''} for r in rows]
    csv_write(OUT / 'image_review_return.csv', forms, list(forms[0]))
    columns = ['measurement_id', 'candidate_id', 'source', 'image_path', 'group_id', 'cell_type',
               'x1', 'y1', 'x2', 'y2', 'diameter_px', 'axis_h_px', 'axis_v_px',
               'measurer', 'checked_by', 'review_status', 'note']
    csv_write(OUT / 'scale_calibration_TEMPLATE.csv', [], columns)
    errors = []
    pages = []
    for source in ['CRC-VAL-HE-7K', 'BACH', 'BreakHis']:
        queue = sorted([r for r in rows if r['source'] == source], key=lambda r: int(r['queue_order']))
        for offset in range(0, len(queue), 10):
            sheet = Image.new('RGB', (1900, 650), 'white')
            for i, r in enumerate(queue[offset:offset+10]):
                raw = DATA_ROOT / r['image_path']
                if sha(raw) != r['raw_sha256']:
                    errors.append(r['image_path'])
                with Image.open(raw) as im:
                    im = im.convert('RGB')
                    assert im.size == (int(r['width']), int(r['height']))
                    thumb = ImageOps.contain(im, (374, 275), Image.Resampling.LANCZOS)
                    x, y = (i % 5) * 380, (i // 5) * 325
                    sheet.paste(thumb, (x + 3, y + 48))
                    d = ImageDraw.Draw(sheet)
                    name = Path(r['image_path']).name
                    d.text((x+3, y+2), f"{source} #{r['queue_order']} | {r['candidate_id'][:8]}", font=font, fill='black')
                    d.text((x+3, y+23), name[:43], font=font, fill='black')
            filename = f'{source}_{offset+1:02d}_{offset+10:02d}.png'
            sheet.save(OUT / filename)
            pages.append({'source': source, 'queue_start': offset+1, 'queue_end': offset+10, 'page': filename})
    pilot = json.loads((ROOT / 'outputs/mpp_pilot_2026-10-25/pilot_boundary_measurements.json').read_text())
    pending = []
    for r in pilot:
        if r['status'] == 'needs_review':
            pending.append({'pilot_object_id': r['measurement_id'], 'candidate_id': r['candidate_id'],
                            'source': r['source'], 'image_path': r['image_path'],
                            'marker_hypothesis': r['intended_marker'],
                            'raw_roi_center_x': (r['x1']+r['x2'])/2, 'raw_roi_center_y': (r['y1']+r['y2'])/2,
                            'requested_action': 'Confirm/reject identity and REDRAW longest whole-cell/nuclear boundary chord plus H/V axes. Mask chord is not a confirmed measurement.',
                            'reviewer': '', 'decision': '', 'note': ''})
    csv_write(OUT / 'pilot_identity_requests.csv', pending, list(pending[0]))
    result = {'control_images': len(rows), 'raw_sha256_checked': len(rows), 'raw_sha256_errors': errors,
              'contact_sheet_pages': pages, 'pilot_objects_for_identity_check': len(pending),
              'formal_measurements_added': 0, 'human_review_completed': False,
              'reviewer_qualification': 'Independent team member able to recognize the stipulated marker; a pathologist is not mandatory under instruct2, absence must be disclosed.',
              'scope': 'Expanded navigation and identity-review preparation, NOT a completed 30/60-cell metrology experiment. Thumbnails may not be measured.'}
    (OUT / 'pack_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert not errors and len(rows) == 180 and len(pages) == 18
    print(json.dumps({k:v for k,v in result.items() if k != 'contact_sheet_pages'}, indent=2))


if __name__ == '__main__':
    main()
