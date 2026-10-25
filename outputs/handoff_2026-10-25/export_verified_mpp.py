"""Export instruct2 fields and H/V summaries from an actually completed measurement kit.

Only writes a NEW output directory. Never fills human names, changes pixels/config,
or promotes the exploratory mask measurements to biological references.
"""
import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).resolve().parents[2] / 'tools/measure_mpp.py'


def axis_summary(rows):
    buckets = {}
    for row in rows:
        name = row['stratum']
        buckets.setdefault(name, []).append(float(row['axis_h_px']) / float(row['axis_v_px']))
    return {name: {'n_cells': len(v), 'min': float(min(v)), 'p05': float(np.percentile(v, 5)),
                   'q25': float(np.percentile(v, 25)), 'median': float(np.median(v)),
                   'q75': float(np.percentile(v, 75)), 'p95': float(np.percentile(v, 95)),
                   'max': float(max(v))} for name, v in buckets.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--cell-type', choices=['rbc', 'lymph_nucleus'], required=True)
    parser.add_argument('--stage', choices=['initial', 'expanded'], default='initial')
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise FileExistsError('Use a NEW output folder, never overwrite a prior conclusion.')
    spec = importlib.util.spec_from_file_location('measurement_engine', MODULE_PATH)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    _, rows = engine.load_measurements(args.kit, args.cell_type)
    report = engine.analyze(args.kit, args.cell_type, args.stage)
    missing_axes = [r['measurement_id'] for r in rows if not r['axis_h_px'] or not r['axis_v_px']]
    report['export_wrapper'] = {'requires_h_v_axes': True, 'measurements_missing_axes': missing_axes,
                                'engine_path': str(MODULE_PATH), 'engine_sha256': engine.digest(MODULE_PATH),
                                'does_not_approve_group_or_human_identity': True}
    if missing_axes:
        report['engine_status_before_axis_requirement'] = report['status']
        report['status'] = 'incomplete'
        report.setdefault('needs', []).append('instruct2 H/V axis fields must be measured before export')
    out.mkdir(parents=True, exist_ok=False)
    if report['status'] != 'incomplete':
        columns = ['source', 'image_path', 'group_id', 'cell_type', 'x1', 'y1', 'x2', 'y2',
                   'diameter_px', 'axis_h_px', 'axis_v_px', 'measurer', 'checked_by', 'note']
        with (out / 'scale_calibration.csv').open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows({**{k: r[k] for k in columns}, 'diameter_px': r['diameter']} for r in rows)
        (out / 'axis_ratio_summary.json').write_text(json.dumps(axis_summary(rows), indent=2), encoding='utf-8')
        report['export_wrapper']['calibration_table_exported'] = True
    else:
        report['export_wrapper']['calibration_table_exported'] = False
    (out / 'analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'rows_available': len(rows),
                      'table_exported': report['export_wrapper']['calibration_table_exported']}, indent=2))


if __name__ == '__main__':
    main()
