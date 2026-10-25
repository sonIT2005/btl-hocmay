"""Read-only input audit for instruct2 handoff; all new reports stay in this folder."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
import sys
sys.path.insert(0, str(ROOT))
from src.data.paths import resolve_data_root, historical_path
DATA_ROOT = resolve_data_root(ROOT)
REPO = Path('C:/Users/Admin/Documents/GitHub/btl-hocmay')
MAINT = ROOT / 'outputs/maintenance_2026-10-25'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def organ(label):
    return 'lung' if label < 3 else 'colon' if label < 5 else 'breast'


def main():
    manifest = read(ROOT / 'splits/splits_none.csv')
    full = {r['image_path']: r for r in read(ROOT / 'splits/splits.csv')}
    by_path = {r['image_path']: r for r in manifest}
    label_map = json.loads((ROOT / 'splits/label_map.json').read_text())['dataset_mappings']
    tables = {}
    inputs = {}
    for name in ['test', 'LungHist700', 'CRC-VAL-HE-7K', 'BACH']:
        path = REPO / f'outputs/predictions/e2_convnext_group_none_s0__{name}.csv'
        rows = read(path)
        inputs[str(path)] = sha(path)
        expected = {r['image_path'] for r in manifest if (r['split'] == 'test' if name == 'test' else r['split'] == 'xtest' and r['source'] == name)}
        paths = [r['image_path'] for r in rows]
        errors = []
        for r in rows:
            m = by_path.get(r['image_path'])
            if m is None:
                errors.append('not_in_manifest:' + r['image_path'])
                continue
            if int(m['label']) != int(r['true_label']) or m['group_id'] != r['group_id']:
                errors.append('label_or_group_mismatch:' + r['image_path'])
            raw = Path(full[r['image_path']]['source_image_path'])
            if m['source'] == 'CRC-VAL-HE-7K':
                raw_class = raw.parent.name
            elif m['source'] == 'BACH':
                raw_class = raw.parent.name
            elif m['source'] == 'LungHist700':
                raw_class = raw.stem.rsplit('_', 2)[0]
            elif m['source'] == 'LC25000':
                raw_class = raw.parent.name
            elif m['source'] == 'BreakHis':
                raw_class = raw.name.split('_')[1]
            else:
                raise ValueError(m['source'])
            if label_map[m['source']][raw_class] != int(r['true_label']):
                errors.append('raw_label_map_mismatch:' + r['image_path'])
        truth = np.array([int(r['true_label']) for r in rows])
        pred = np.array([int(r['pred_label']) for r in rows])
        probs = np.array([[float(r[f'prob_{k}']) for k in range(7)] for r in rows])
        assert np.isfinite(probs).all() and (probs >= 0).all() and (probs <= 1).all()
        restricted = []
        guaranteed = []
        possible = []
        ambiguous = 0
        for t, p in zip(truth, probs):
            allowed = list(range(3)) if t < 3 else [3, 4] if t < 5 else [5, 6]
            competitors = [k for k in allowed if k != t]
            restricted.append(allowed[int(np.argmax(p[allowed]))] == t)
            # Conservative bounds given export rounding to six decimal places.
            eps = .5e-6
            guaranteed.append(max(0, p[t]-eps) > max(min(1, p[k]+eps) for k in competitors))
            possible.append(min(1, p[t]+eps) >= max(max(0, p[k]-eps) for k in competitors))
            top = sorted(p[allowed], reverse=True)
            ambiguous += top[0] - top[1] <= 1e-6 + 1e-15
        tables[name] = {
            'n': len(rows), 'unique_raw_images': len({full[r['image_path']]['source_image_path'] for r in rows}),
            'correct_7class': int((truth == pred).sum()), 'accuracy_7class': float((truth == pred).mean()),
            'organ_confusion_count': sum(organ(t) != organ(p) for t, p in zip(truth, pred)),
            'organ_confusion_rate': sum(organ(t) != organ(p) for t, p in zip(truth, pred)) / len(rows),
            'predict_breast_rate': float((pred >= 5).mean()),
            'predicted_organ_counts': dict(Counter(organ(p) for p in pred)),
            'within_true_organ_accuracy_from_rounded_csv': float(np.mean(restricted)),
            'within_true_organ_correct_from_rounded_csv': int(sum(restricted)),
            'within_true_organ_accuracy_conservative_rounding_bounds': [float(np.mean(guaranteed)), float(np.mean(possible))],
            'restricted_top2_margin_le_1e_minus6': int(ambiguous),
            'probability_argmax_disagrees_with_pred_label': int((np.argmax(probs, axis=1) != pred).sum()),
            'max_probability_sum_error': float(abs(probs.sum(axis=1)-1).max()),
            'manifest_missing_predictions': len(expected-set(paths)),
            'unexpected_predictions': len(set(paths)-expected), 'duplicate_predictions': len(paths)-len(set(paths)),
            'label_group_raw_mapping_errors': errors,
            'true_label_counts': dict(Counter(map(int, truth))),
        }
        assert not errors and set(paths) == expected and len(paths) == len(set(paths))

    protected = json.loads((MAINT / 'protected_before.json').read_text())
    changed = [p for p, h in protected.items() if sha(historical_path(p, ROOT)) != h]
    applied = json.loads((MAINT / 'applied_changes.json').read_text())
    applied_drift = [r['path'] for r in applied if sha(REPO / r['path']) != r['sha256']]
    frozen = json.loads((ROOT / 'splits/FROZEN.json').read_text())
    frozen_drift = [p for p, h in frozen['sha256'].items() if sha(ROOT / 'snapshots/2026-10-16' / p) != h]
    result = {'predictions': tables, 'input_sha256': inputs,
              'protected_files_checked': len(protected), 'protected_files_changed': changed,
              'patched_files_checked': len(applied), 'patched_files_changed_since_pre_layout_test': applied_drift,
              'canonical_frozen_files_checked': len(frozen['sha256']), 'canonical_frozen_files_drifted': frozen_drift,
              'legacy_checkpoint_available': (REPO / 'outputs/checkpoints/e2_convnext_group_none_s0.pt').exists(),
              'limitations': ['Restricted argmax on rounded probabilities is not exact original-score verification.',
                              'No old checkpoint forward or diagnostic perturbation experiments rerun.',
                              'Image aggregation and patient-level statistics remain C5 decisions.']}
    (ROOT / 'outputs/reorganization_2026-10-25/legacy_metric_verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert not changed and not frozen_drift
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
