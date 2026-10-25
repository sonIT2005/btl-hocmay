"""Prepare raw-image measurement queues; validate annotations; estimate MPP without changing data.

No command edits preparation.yaml, images, splits, reference.json or FROZEN.json.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

KNOWN = {'CRC-VAL-HE-7K': .5, 'BACH': .42, 'BreakHis': .49}
MEASUREMENT_COLUMNS = ['measurement_id', 'candidate_id', 'cell_type', 'x1', 'y1', 'x2', 'y2',
                       'diameter_px', 'axis_h_px', 'axis_v_px', 'measurer', 'checked_by', 'review_status', 'note']


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with Path(path).open('x', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader(); w.writerows(rows)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stratum(row):
    if row['source'] == 'LC25000':
        return 'LC25000_' + row['organ']
    if row['source'] == 'LungHist700':
        return 'LungHist700_' + str(row['magnification']) + 'x'
    return row['source']


def prepare(splits, out, seed=42, per_stratum=60):
    splits, out = Path(splits).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError('Measurement kit already exists; never overwrite annotations')
    inventory = read_csv(splits / 'inventory.csv')
    raw = {r['source_image_path']: r for r in read_csv(splits / 'raw_checksums.csv')}
    pools = defaultdict(list)
    for row in inventory:
        if row['included'] != 'True':
            continue
        if row['source'] == 'LC25000' and row['split'] != 'train':
            continue
        pools[stratum(row)].append(row)
    rng = random.Random(seed)
    candidates = []
    for name, rows in sorted(pools.items()):
        rows = sorted(rows, key=lambda r: r['source_image_path'])
        rng.shuffle(rows)
        seen = set(); taken = 0
        for row in rows:
            if row['source'] == 'LC25000' and row['group_id'] in seen:
                continue
            seen.add(row['group_id'])
            path = row['source_image_path']
            item = {'candidate_id': hashlib.sha256(path.encode()).hexdigest()[:16],
                    'source': row['source'], 'image_path': path, 'group_id': row['group_id'],
                    'organ': row['organ'], 'magnification': row['magnification'], 'split': row['split'],
                    'stratum': name, 'queue_order': taken + 1, 'selection_seed': seed,
                    'raw_sha256': raw[path]['sha256'], 'width': raw[path]['width'], 'height': raw[path]['height']}
            candidates.append(item); taken += 1
            if taken == per_stratum:
                break
    if not candidates:
        raise ValueError('No eligible raw candidates')
    out.mkdir(parents=True)
    write_csv(out / 'candidates.csv', candidates, list(candidates[0]))
    write_csv(out / 'measurements.csv', [], MEASUREMENT_COLUMNS)
    reviews = [{'candidate_id': r['candidate_id'], 'decision': 'pending', 'note': ''} for r in candidates]
    write_csv(out / 'image_review.csv', reviews, ['candidate_id', 'decision', 'note'])
    protocol = {'schema': 1, 'selection_seed': seed, 'review_seed': 43, 'bootstrap_seed': 20261025,
                'bootstrap_repeats': 2000, 'min_cells': 30, 'expanded_min_cells': 60,
                'min_images': 15, 'max_cells_per_image': 3, 'min_lc_cells_per_organ': 15,
                'review_fraction': .20, 'max_loo_error': .15, 'known_mpp': KNOWN,
                'lc_organ_disagreement_threshold': .15,
                'cell_types_separate': ['rbc', 'lymph_nucleus'],
                'splits_dir_at_creation': str(splits), 'frozen_sha256': digest(splits / 'FROZEN.json'),
                'candidate_sha256': digest(out / 'candidates.csv'),
                'state': 'awaiting_manual_measurements',
                'failure_rule': 'One expansion to 60 cells/source; then keep estimated_unverified and existing MPP. No automatic config update.'}
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    (out / 'protocol.sha256').write_text(digest(out / 'protocol.json'), encoding='ascii')
    return {'status': protocol['state'], 'candidates': len(candidates),
            'by_stratum': dict(Counter(r['stratum'] for r in candidates)), 'kit': str(out)}


def load_measurements(kit, cell_type):
    kit = Path(kit)
    if digest(kit / 'protocol.json') != (kit / 'protocol.sha256').read_text(encoding='ascii').strip():
        raise ValueError('Protocol changed after preparation; create a new kit instead')
    protocol = json.loads((kit / 'protocol.json').read_text(encoding='utf-8'))
    if digest(kit / 'candidates.csv') != protocol['candidate_sha256']:
        raise ValueError('Candidate list changed after protocol was locked')
    candidates = {r['candidate_id']: r for r in read_csv(kit / 'candidates.csv')}
    image_reviews = {r['candidate_id']: r for r in read_csv(kit / 'image_review.csv')}
    rows = read_csv(kit / 'measurements.csv')
    seen = set(); accepted = []
    for row in rows:
        if row['cell_type'] not in protocol['cell_types_separate']:
            raise ValueError('Unknown cell type')
        if not row['measurement_id'] or row['measurement_id'] in seen:
            raise ValueError('Missing or duplicate measurement_id')
        seen.add(row['measurement_id'])
        if row['candidate_id'] not in candidates:
            raise ValueError('Unknown raw candidate')
        if row['cell_type'] != cell_type:
            continue
        candidate = candidates[row['candidate_id']]
        if row['review_status'] == 'rejected':
            if not row['checked_by'] or not row['note']:
                raise ValueError('Rejected measurement requires reviewer and reason')
            continue
        if row['review_status'] not in ('', 'checked'):
            raise ValueError('review_status must be empty, checked or rejected')
        if not row['measurer'].strip():
            raise ValueError('Human measurer must be recorded')
        if row['checked_by'] and row['checked_by'].strip().casefold() == row['measurer'].strip().casefold():
            raise ValueError('Independent checker must differ from measurer')
        if row['review_status'] == 'checked' and not row['checked_by'].strip():
            raise ValueError('Checked measurement requires checked_by')
        if image_reviews.get(row['candidate_id'], {}).get('decision') != 'eligible':
            raise ValueError('Measured image must be marked eligible in image_review.csv')
        x1, y1, x2, y2 = [float(row[k]) for k in ['x1', 'y1', 'x2', 'y2']]
        if not all(math.isfinite(v) for v in [x1, y1, x2, y2]):
            raise ValueError('Coordinates must be finite raw pixel coordinates')
        w, h = int(candidate['width']), int(candidate['height'])
        if not (0 <= x1 < w and 0 <= x2 < w and 0 <= y1 < h and 0 <= y2 < h):
            raise ValueError('Coordinates outside raw image')
        diameter = math.hypot(x2 - x1, y2 - y1)
        if diameter <= 0:
            raise ValueError('Zero length measurement')
        for axis in ['axis_h_px', 'axis_v_px']:
            if row[axis] and (not math.isfinite(float(row[axis])) or float(row[axis]) <= 0):
                raise ValueError('Optional axis measurement must be finite and positive')
        if row['diameter_px'] and not math.isclose(float(row['diameter_px']), diameter, abs_tol=.01):
            raise ValueError('diameter_px differs from coordinate distance')
        accepted.append({**candidate, **row, 'diameter': diameter})
    counts = Counter(r['candidate_id'] for r in accepted)
    if any(n > protocol['max_cells_per_image'] for n in counts.values()):
        raise ValueError('At most three cells per raw image for the selected cell type')
    return protocol, accepted


def image_medians(rows):
    images = defaultdict(list)
    for row in rows:
        images[row['candidate_id']].append(row['diameter'])
    return np.array([np.median(v) for _, v in sorted(images.items())], dtype=float)


def bootstrap(references, target_rows, repeats, seed):
    rng = np.random.default_rng(seed)
    ref = [image_medians(references[s]) for s in sorted(KNOWN)]
    # LC lung/colon strata retain their image counts; other targets have one stratum.
    strata = defaultdict(list)
    for row in target_rows:
        strata[row['organ']].append(row)
    targets = [image_medians(v) for _, v in sorted(strata.items())]
    mpps = [KNOWN[s] for s in sorted(KNOWN)]
    estimates = []
    for _ in range(repeats):
        donor_sizes = [np.median(rng.choice(values, len(values), replace=True)) * mpp
                       for values, mpp in zip(ref, mpps)]
        target = np.concatenate([rng.choice(values, len(values), replace=True) for values in targets])
        estimates.append(np.median(donor_sizes) / np.median(target))
    return list(map(float, np.percentile(estimates, [2.5, 97.5])))


def analyze(kit, cell_type='rbc', stage='initial'):
    protocol, rows = load_measurements(kit, cell_type)
    min_cells = protocol['min_cells'] if stage == 'initial' else protocol['expanded_min_cells']
    cohorts = defaultdict(list)
    for row in rows:
        key = 'LC25000' if row['source'] == 'LC25000' else row['stratum']
        cohorts[key].append(row)
    needed = []; review_ids = []; stats = {}
    for name in sorted(set(KNOWN) | set(cohorts)):
        group = cohorts[name]
        medians = image_medians(group)
        if len(group) < min_cells or len(medians) < protocol['min_images']:
            needed.append(name + ': insufficient cells/images')
        if name == 'LC25000':
            organ_counts = Counter(r['organ'] for r in group)
            if any(organ_counts[o] < protocol['min_lc_cells_per_organ'] for o in ['lung', 'colon']):
                needed.append(name + ': need at least 15 cells each from lung and colon')
            by_group = defaultdict(set)
            for r in group:
                by_group[r['group_id']].add(r['candidate_id'])
            if any(len(v) > 1 for v in by_group.values()):
                raise ValueError('LC25000 has multiple images from the same group')
        rng = random.Random(protocol['review_seed'])
        ordered = sorted(group, key=lambda r: r['measurement_id'])
        selected = rng.sample(ordered, math.ceil(len(ordered) * protocol['review_fraction']))
        for row in selected:
            if row['review_status'] != 'checked' or not row['checked_by']:
                review_ids.append(row['measurement_id'])
        stats[name] = {'n_cells': len(group), 'n_images': len(medians),
                       'median_px': float(np.median(medians)) if len(medians) else None,
                       'diameter_iqr_px': list(map(float, np.percentile([r['diameter'] for r in group], [25, 75]))) if group else None}
    report = {'status': 'incomplete', 'cell_type': cell_type, 'stage': stage,
              'counts': stats, 'needs': needed, 'review_measurement_ids': review_ids,
              'applies_config_changes': False, 'physical_calibration_claimed': False,
              'protocol_sha256': digest(Path(kit) / 'protocol.json'),
              'measurements_sha256': digest(Path(kit) / 'measurements.csv')}
    if needed or review_ids:
        return report
    donor_sizes = {s: stats[s]['median_px'] * KNOWN[s] for s in KNOWN}
    loo = {}
    for s in KNOWN:
        d = np.mean([value for name, value in donor_sizes.items() if name != s])
        mpp = float(d / stats[s]['median_px'])
        loo[s] = {**stats[s], 'reference_cell_um': donor_sizes[s], 'published_mpp': KNOWN[s],
                  'loo_mpp': mpp, 'relative_error': abs(mpp / KNOWN[s] - 1)}
    report['leave_one_out'] = loo
    if any(r['relative_error'] > protocol['max_loo_error'] for r in loo.values()):
        report['status'] = 'needs_one_expansion' if stage == 'initial' else 'method_rejected_keep_current_mpp'
        return report
    d_ref = float(np.median(list(donor_sizes.values())))
    report.update(status='reference_consistency_passed', reference_cell_um=d_ref, targets={})
    for index, name in enumerate(['LC25000', 'LungHist700_20x', 'LungHist700_40x']):
        if not cohorts[name]:
            report['targets'][name] = {'status': 'not_measured_keep_current_mpp'}
            continue
        mpp = d_ref / stats[name]['median_px']
        report['targets'][name] = {'status': 'proposal_requires_independent_and_group_review',
                                    'mpp_estimate': mpp, 'scale_status': 'estimated_reference_cell',
                                    'ci95_sampling_only': bootstrap(cohorts, cohorts[name], protocol['bootstrap_repeats'], protocol['bootstrap_seed'] + index)}
        if name == 'LC25000':
            estimates = {organ: d_ref / float(np.median(image_medians([r for r in cohorts[name] if r['organ'] == organ])))
                         for organ in ['lung', 'colon']}
            report['targets'][name]['organ_estimates'] = estimates
            discrepancy = abs(estimates['lung'] / estimates['colon'] - 1)
            report['targets'][name]['organ_relative_disagreement'] = discrepancy
            if discrepancy > protocol.get('lc_organ_disagreement_threshold', .15):
                report['targets'][name]['status'] = 'organ_disagreement_requires_investigation'
        else:
            old = .5 if name.endswith('20x') else .25
            report['targets'][name]['current_mpp'] = old
            report['targets'][name]['change_trigger_over15pct'] = abs(mpp / old - 1) > .15
    report['limitations'] = ['Source-to-source cell-size bias and cell identification error are not quantified by this CI.',
                            'Passing reference consistency does not prove LC25000 physical MPP within 15%.',
                            'Reference images include external evaluation sources; disclose post-evaluation preprocessing estimation.']
    return report


def render(kit, data_root, out, cell_type):
    from PIL import Image, ImageDraw
    _, rows = load_measurements(kit, cell_type)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    groups = defaultdict(list)
    for r in rows:
        groups[r['candidate_id']].append(r)
    for candidate, measurements in groups.items():
        path = Path(data_root) / measurements[0]['image_path']
        if digest(path) != measurements[0]['raw_sha256']:
            raise ValueError('Raw image checksum changed: ' + str(path))
        with Image.open(path) as im:
            im = im.convert('RGB')
        draw = ImageDraw.Draw(im)
        for r in measurements:
            box = tuple(float(r[k]) for k in ['x1', 'y1', 'x2', 'y2'])
            draw.line(box, fill='yellow', width=2)
            draw.text(box[:2], f"{r['measurement_id']} {r['diameter']:.2f}px", fill='yellow')
        im.save(out / (candidate + '.png'))
    return {'annotated_images': len(groups), 'native_pixel_coordinates': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--splits-dir', required=True); p.add_argument('--out', required=True)
    p.add_argument('--seed', type=int, default=42); p.add_argument('--per-stratum', type=int, default=60)
    a = sub.add_parser('analyze'); a.add_argument('--kit', required=True); a.add_argument('--out', required=True)
    a.add_argument('--cell-type', choices=['rbc', 'lymph_nucleus'], default='rbc')
    a.add_argument('--stage', choices=['initial', 'expanded'], default='initial')
    r = sub.add_parser('render'); r.add_argument('--kit', required=True); r.add_argument('--data-root', required=True)
    r.add_argument('--out', required=True); r.add_argument('--cell-type', choices=['rbc', 'lymph_nucleus'], default='rbc')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.splits_dir, args.out, args.seed, args.per_stratum)
    elif args.command == 'analyze':
        result = analyze(args.kit, args.cell_type, args.stage)
        with Path(args.out).open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        result = render(args.kit, args.data_root, args.out, args.cell_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
