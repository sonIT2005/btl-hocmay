"""Render manually outlined raw objects and preview UNREVIEWED control measurements.

This module cannot publish target MPP or write to a formal measurement kit.
Polygons describe visible boundary estimates, not segmentation-mask diameters.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.paths import resolve_data_root

SOURCES = ('CRC-VAL-HE-7K', 'BACH', 'BreakHis')
MARKERS = ('rbc', 'lymph_nucleus')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, columns):
    with Path(path).open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def geometry(polygon, width, height):
    """Longest chord and maximum H/V chords of a manually drawn CONVEX polygon.

    Raw coordinates: x right, y down; integer coordinates denote pixel centres.
    A convex outline ensures every computed chord stays inside the outline.
    Chord maxima occur at vertex levels for a convex piecewise-linear boundary.
    """
    pts = [tuple(map(float, p)) for p in polygon]
    if len(pts) < 3 or any(len(p) != 2 for p in pts) or len(set(pts)) != len(pts):
        raise ValueError('Need at least three distinct 2D polygon vertices')
    if any(not math.isfinite(v) for p in pts for v in p):
        raise ValueError('Non-finite coordinate')
    if any(not (0 <= x <= width-1 and 0 <= y <= height-1) for x, y in pts):
        raise ValueError('Polygon outside raw image')
    # All other vertices must lie on the same side of every directed edge.
    # Unlike consecutive-turn checks, this also rejects self-crossing star polygons.
    orientations = []
    for i, (x, y) in enumerate(pts):
        u, v = pts[(i+1) % len(pts)]
        crosses = [(u-x)*(b-y)-(v-y)*(a-x) for a, b in pts]
        pos = any(t > 1e-8 for t in crosses)
        neg = any(t < -1e-8 for t in crosses)
        if pos and neg:
            raise ValueError('Outline must be simple and convex; redraw this object')
        orientations.append(1 if pos else -1 if neg else 0)
    signs = {v for v in orientations if v}
    if len(signs) != 1:
        raise ValueError('Degenerate or self-crossing outline')
    a, b = max(((a, b) for i, a in enumerate(pts) for b in pts[i+1:]),
               key=lambda pair: math.dist(*pair))
    result = {'longest': [a, b], 'diameter_px': math.dist(a, b)}
    for axis, label in ((1, 'h'), (0, 'v')):
        chords = []
        for level in sorted({p[axis] for p in pts}):
            hits = []
            for i, p in enumerate(pts):
                q = pts[(i+1) % len(pts)]
                if abs(p[axis]-q[axis]) < 1e-10:
                    if abs(level-p[axis]) < 1e-10:
                        hits += [p[1-axis], q[1-axis]]
                elif min(p[axis], q[axis]) <= level <= max(p[axis], q[axis]):
                    t = (level-p[axis])/(q[axis]-p[axis])
                    hits.append(p[1-axis]+t*(q[1-axis]-p[1-axis]))
            if hits:
                ends = [[min(hits), level], [max(hits), level]]
                if axis == 0:
                    ends = [p[::-1] for p in ends]
                chords.append(ends)
        ends = max(chords, key=lambda pair: math.dist(*pair))
        result[label] = ends
        result['axis_'+label+'_px'] = math.dist(*ends)
    return result


def preview(records, protocol):
    """Draft-only arithmetic. Review gates and release outputs do not exist here."""
    result = {'status': 'draft_only_unreviewed', 'formal_accepted_cells': 0,
              'physical_calibration_claimed': False, 'applies_config_changes': False,
              'approved_mpp': None, 'targets': {}, 'markers': {}}
    for marker in MARKERS:
        cohorts = {}
        all_complete = True
        for source in SOURCES:
            group = [r for r in records if r['source'] == source and r['cell_type'] == marker
                     and r['decision'] == 'draft_eligible']
            images = defaultdict(list)
            for r in group:
                images[r['candidate_id']].append(r['diameter_px'])
            if any(len(values) > protocol['max_cells_per_image'] for values in images.values()):
                raise ValueError('Too many eligible cells per image and marker')
            medians = {key: statistics.median(values) for key, values in sorted(images.items())}
            ids = sorted(r['measurement_id'] for r in group)
            selected = random.Random(protocol['review_seed']).sample(
                ids, math.ceil(len(ids)*protocol['review_fraction']))
            missing_cells = max(0, protocol['min_cells']-len(group))
            missing_images = max(0, protocol['min_images']-len(images))
            cohorts[source] = {'n_cells': len(group), 'n_images': len(images),
                               'missing_cells': missing_cells, 'missing_images': missing_images,
                               'image_medians_px': medians,
                               'median_of_image_medians_px': statistics.median(medians.values()) if medians else None,
                               'review_measurement_ids': selected}
            all_complete &= not (missing_cells or missing_images)
        item = {'counts': cohorts, 'leave_one_out': None,
                'reason': 'insufficient_comparable_cells_or_images', 'method_failed': False}
        if all_complete:
            sizes = {s: cohorts[s]['median_of_image_medians_px']*protocol['known_mpp'][s] for s in SOURCES}
            item['leave_one_out'] = {}
            for s in SOURCES:
                ref = statistics.mean(v for key, v in sizes.items() if key != s)
                estimate = ref/cohorts[s]['median_of_image_medians_px']
                item['leave_one_out'][s] = {'draft_loo_mpp': estimate,
                                            'relative_error': abs(estimate/protocol['known_mpp'][s]-1)}
            item['reason'] = 'arithmetic_preview_requires_independent_review'
        result['markers'][marker] = item
    return result


def draw_record(im, polygon, g, label, out, stem):
    from PIL import Image, ImageDraw
    outline = im.copy()
    pen = ImageDraw.Draw(outline)
    pen.line([tuple(p) for p in polygon]+[tuple(polygon[0])], fill='#00ff88', width=1)
    for key, color in (('longest', '#ffff00'), ('h', '#00ffff'), ('v', '#ff8800')):
        pair = [tuple(p) for p in g[key]]
        pen.line(pair, fill=color, width=1)
        for x, y in pair:
            pen.rectangle((x-1, y-1, x+1, y+1), outline=color)
    xs, ys = zip(*polygon)
    left, top = max(0, math.floor(min(xs))-14), max(0, math.floor(min(ys))-14)
    right, bottom = min(im.width, math.ceil(max(xs))+15), min(im.height, math.ceil(max(ys))+15)
    bounds = (left, top, right, bottom)
    # Full native-size context preserves the exact raw coordinate mapping.
    pen.rectangle(bounds, outline='red', width=1)
    outline.save(out/(stem+'_context.png'))
    scale = 10
    plain = im.crop(bounds).resize(((right-left)*scale, (bottom-top)*scale), Image.Resampling.NEAREST)
    marked = outline.crop(bounds).resize(plain.size, Image.Resampling.NEAREST)
    panel = Image.new('RGB', (plain.width*2, plain.height+72), 'white')
    panel.paste(plain, (0, 72)); panel.paste(marked, (plain.width, 72))
    p = ImageDraw.Draw(panel)
    p.text((5, 5), label, fill='black')
    p.text((5, 21), f'RAW crop x={left}..{right-1}, y={top}..{bottom-1}; nearest {scale}x', fill='black')
    p.text((5, 37), f'DRAFT: D={g["diameter_px"]:.2f}px  H={g["axis_h_px"]:.2f}px  V={g["axis_v_px"]:.2f}px', fill='black')
    p.text((5, 53), 'Yellow=longest; cyan=H; orange=V; green=manual outline', fill='black')
    panel.save(out/(stem+'_roi.png'))
    return list(bounds)


def draw_location(im, location, label, out, stem):
    """Unmeasured exclusion: point is a navigation cue, never a caliper."""
    from PIL import Image, ImageDraw
    x,y = location
    marked = im.copy(); pen = ImageDraw.Draw(marked)
    pen.line((x-5,y,x+5,y), fill='yellow'); pen.line((x,y-5,x,y+5), fill='yellow')
    marked.save(out/(stem+'_context.png'))
    bounds = (max(0,x-28),max(0,y-28),min(im.width,x+29),min(im.height,y+29))
    plain = im.crop(bounds).resize(((bounds[2]-bounds[0])*8,(bounds[3]-bounds[1])*8),Image.Resampling.NEAREST)
    panel = Image.new('RGB',(plain.width,plain.height+48),'white');panel.paste(plain,(0,48))
    p=ImageDraw.Draw(panel);p.text((5,5),label,fill='black')
    p.text((5,21),f'Unmeasured location ({x},{y}); identity/boundary unresolved',fill='black')
    panel.save(out/(stem+'_roi.png'))
    return list(bounds)


def build(kit, annotations, out, data_root=None, frozen=None):
    from PIL import Image
    kit, out = Path(kit).resolve(), Path(out).resolve()
    data = resolve_data_root(configured=data_root)
    # Protect the official kit, source dataset, and repository inputs from output misuse.
    for protected in (kit, data, ROOT/'splits', ROOT/'configs'):
        if out == protected or protected in out.parents:
            raise ValueError('Draft output must be separate from formal kit, data and frozen inputs')
    if out.exists():
        raise FileExistsError('Use a new versioned output; never overwrite a draft')
    protocol = json.loads((kit/'protocol.json').read_text(encoding='utf-8-sig'))
    if sha(kit/'protocol.json') != (kit/'protocol.sha256').read_text().strip().split()[0]:
        raise ValueError('Locked protocol hash changed')
    if sha(kit/'candidates.csv') != protocol['candidate_sha256']:
        raise ValueError('Locked candidate queue changed')
    frozen = Path(frozen) if frozen else ROOT/'splits/FROZEN.json'
    if sha(frozen) != protocol['frozen_sha256']:
        raise ValueError('Frozen manifest changed')
    candidates = {r['candidate_id']: r for r in load_csv(kit/'candidates.csv') if r['source'] in SOURCES}
    source_checks = []
    for r in candidates.values():
        path = (data/r['image_path']).resolve()
        if data not in path.parents:
            raise ValueError('Candidate path escapes data root')
        actual = sha(path)
        with Image.open(path) as im:
            size = im.size
        if actual != r['raw_sha256'] or size != (int(r['width']), int(r['height'])):
            raise ValueError('Raw source SHA or dimensions changed: '+r['candidate_id'])
        source_checks.append({'candidate_id': r['candidate_id'], 'sha256': actual, 'size': size})
    payload = json.loads(Path(annotations).read_text(encoding='utf-8-sig'))
    records = []
    seen = set()
    counts = Counter()
    for a in payload['objects']:
        ident = a['measurement_id']
        if not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in ident) or ident in seen:
            raise ValueError('Duplicate or unsafe measurement ID')
        seen.add(ident)
        r = candidates[a['candidate_id']]
        if a['cell_type'] not in MARKERS or a['decision'] not in ('draft_eligible', 'uncertain', 'rejected'):
            raise ValueError('Invalid draft marker/decision')
        if a.get('checked_by') or a.get('review_status', 'draft_unreviewed') != 'draft_unreviewed':
            raise ValueError('Draft tool cannot record independent approval')
        g = geometry(a['polygon'], int(r['width']), int(r['height'])) if a.get('polygon') else None
        if a['decision'] == 'draft_eligible' and g is None:
            raise ValueError('Eligible objects need a visible boundary outline')
        if not a.get('note'):
            raise ValueError('Document visible morphology or reason for exclusion')
        location=a.get('location')
        if location is not None and (len(location)!=2 or any(not isinstance(v,(float,int)) or not math.isfinite(v) for v in location)
                                    or not (0<=location[0]<=int(r['width'])-1 and 0<=location[1]<=int(r['height'])-1)):
            raise ValueError('Unmeasured location outside raw image')
        if g is None and location is None:
            raise ValueError('Excluded objects need a raw location to inspect')
        if a['decision'] == 'draft_eligible':
            counts[r['candidate_id']] += 1
            if counts[r['candidate_id']] > protocol['max_cells_per_image']:
                raise ValueError('Too many draft cells per image')
        record = {**a, 'source': r['source'], 'queue_order': int(r['queue_order']), 'image_path': r['image_path'],
                  'group_id': r.get('group_id', ''),
                  'raw_sha256': r['raw_sha256'], 'width': int(r['width']), 'height': int(r['height']),
                  'measurer': 'Codex_visual_assist', 'checked_by': '', 'review_status': 'draft_unreviewed',
                  'marking_method': 'visual_raw_convex_polygon_integer_pixel_centres',
                  'boundary_uncertainty_px': a.get('boundary_uncertainty_px', 1),
                  'geometry': g, 'diameter_px': g['diameter_px'] if g else None,
                  'axis_h_px': g['axis_h_px'] if g else None, 'axis_v_px': g['axis_v_px'] if g else None}
        records.append(record)
    report = preview(records, protocol)
    selected = {i for m in report['markers'].values() for c in m['counts'].values() for i in c['review_measurement_ids']}
    out.mkdir(parents=True)
    (out/'objects').mkdir()
    Path(out/'annotations_input.json').write_bytes(Path(annotations).read_bytes())
    rows = []; pages = []
    for r in records:
        g = r['geometry']; ident = r['measurement_id']
        row = {k: r[k] for k in ('measurement_id','candidate_id','source','queue_order','cell_type','decision','image_path','group_id','raw_sha256','width','height',
               'diameter_px','axis_h_px','axis_v_px','measurer','checked_by','review_status','marking_method','boundary_uncertainty_px','note')}
        for key, prefix in (('longest',''), ('h','h_'), ('v','v_')):
            for j in range(2):
                for axis, name in enumerate(('x','y')):
                    row[f'{prefix}{name}{j+1}'] = g[key][j][axis] if g else ''
        row['polygon_json'] = json.dumps(r.get('polygon', []))
        row['location_x'] = r.get('location', ['', ''])[0]
        row['location_y'] = r.get('location', ['', ''])[1]
        row['selected_for_review'] = ident in selected
        row['context_image'] = ''; row['roi_image'] = ''
        if g:
            with Image.open(data/r['image_path']) as im:
                r['roi_bounds'] = draw_record(im.convert('RGB'), r['polygon'], g, ident+' '+r['decision'], out/'objects', ident)
            # Recheck all chord endpoints lie inside the exported raw ROI.
            l,t,rr,bb = r['roi_bounds']
            assert all(l <= x < rr and t <= y < bb for key in ('longest','h','v') for x,y in g[key])
            row['context_image'] = 'objects/'+ident+'_context.png'
            row['roi_image'] = 'objects/'+ident+'_roi.png'
            badge=' / RANDOM REVIEW DRAW' if ident in selected else ''
            pages.append(f'<article id="{ident}"><h3>{html.escape(ident)} / {r["decision"]}{badge}</h3><p>{html.escape(r["note"])}</p>'
                         f'<a href="{row["context_image"]}">Native raw context</a><br><img loading="lazy" src="{row["roi_image"]}"></article>')
        else:
            with Image.open(data/r['image_path']) as im:
                r['roi_bounds']=draw_location(im.convert('RGB'),r['location'],ident+' '+r['decision'],out/'objects',ident)
            row['context_image']='objects/'+ident+'_context.png';row['roi_image']='objects/'+ident+'_roi.png'
            pages.append(f'<article id="{ident}"><h3>{html.escape(ident)} / UNMEASURED exclusion</h3><p>{html.escape(r["note"])}</p>'
                         f'<a href="{row["context_image"]}">Native context</a><br><img loading="lazy" src="{row["roi_image"]}"></article>')
        rows.append(row)
    columns = list(rows[0]) if rows else ['measurement_id','review_status']
    save_csv(out/'draft_measurements.csv', [r for r in rows if r['decision']=='draft_eligible'], columns)
    save_csv(out/'excluded_objects.csv', [r for r in rows if r['decision']!='draft_eligible'], columns)
    review_cols = ['measurement_id','candidate_id','source','cell_type','selected_for_review','checked_by','review_date','review_status',
                   'identity_confirmed','boundary_confirmed','redrawn_x1','redrawn_y1','redrawn_x2','redrawn_y2',
                   'redrawn_diameter_px','redrawn_h_px','redrawn_v_px','review_note']
    review = [{k: r.get(k, '') for k in review_cols} for r in rows if r['decision']=='draft_eligible']
    save_csv(out/'review_return.csv', review, review_cols)
    image_groups=defaultdict(list)
    for r in records:
        if r['decision']=='draft_eligible':
            image_groups[(r['source'],r['cell_type'],r['candidate_id'])].append(r)
    image_rows=[]
    for (source,marker,candidate),group in sorted(image_groups.items()):
        image_rows.append({'source':source,'cell_type':marker,'candidate_id':candidate,
                           'image_path':group[0]['image_path'],'n_cells':len(group),
                           'median_longest_px':statistics.median(v['diameter_px'] for v in group),
                           'median_h_px':statistics.median(v['axis_h_px'] for v in group),
                           'median_v_px':statistics.median(v['axis_v_px'] for v in group),
                           'review_status':'draft_unreviewed'})
    image_cols=['source','cell_type','candidate_id','image_path','n_cells','median_longest_px','median_h_px','median_v_px','review_status']
    save_csv(out/'image_medians.csv',image_rows,image_cols)
    cohort_rows=[]
    for marker,item in report['markers'].items():
        for source,c in item['counts'].items():
            cohort_rows.append({'source':source,'cell_type':marker,'n_cells':c['n_cells'],'n_images':c['n_images'],
                                'median_of_image_medians_px':c['median_of_image_medians_px'],
                                'missing_cells':c['missing_cells'],'missing_images':c['missing_images'],
                                'n_review_selected':len(c['review_measurement_ids']),'review_status':'draft_unreviewed'})
    save_csv(out/'cohort_summary.csv',cohort_rows,list(cohort_rows[0]))
    (out/'locked_protocol.json').write_bytes((kit/'protocol.json').read_bytes())
    (out/'locked_candidates.csv').write_bytes((kit/'candidates.csv').read_bytes())
    (out/'draft_preview.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    (out/'measurements_geometry.json').write_text(json.dumps(records, indent=2), encoding='utf8')
    review_links=' '.join(f'<a href="#{ident}">{ident}</a>' for ident in sorted(selected))
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Unreviewed raw-cell measurements</title>'
        '<style>body{font:16px sans-serif;max-width:1300px;margin:auto}article{border-top:1px solid #aaa;padding:12px}img{max-width:100%}</style>'
        '<h1>DRAFT ONLY - independent review pending</h1><p>Yellow longest; cyan horizontal; orange vertical; green manual boundary. '
        'Integer raw pixel centres; no subpixel precision or approved MPP. See excluded_objects.csv separately.</p>'
        '<h2>Locked random review draw</h2><p>'+review_links+'</p><p><a href="review_return.csv">Return review CSV</a> | '
        '<a href="cohort_summary.csv">Counts and deficits</a></p>'+''.join(pages), encoding='utf8')
    evidence = {'protocol_sha256': sha(kit/'protocol.json'), 'candidate_sha256': sha(kit/'candidates.csv'),
                'frozen_sha256': sha(frozen), 'formal_measurements_sha256': sha(kit/'measurements.csv'),
                'annotations_sha256': sha(annotations), 'source_checks': source_checks,
                'raw_sources_verified': len(source_checks), 'geometry_rows': sum(bool(r['geometry']) for r in records),
                'coordinate_bounds_passed': True, 'roi_endpoint_mapping_passed': True,
                'longest_lengths_recomputed': True, 'max3_eligible_per_image_marker_passed': True,
                'max3_eligible_per_image_total_passed': True,
                'formal_review_gate_modified': False, 'release_mpp_emitted': False}
    (out/'verification.json').write_text(json.dumps(evidence, indent=2), encoding='utf8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', required=True); parser.add_argument('--annotations', required=True)
    parser.add_argument('--out', required=True); parser.add_argument('--data-root'); parser.add_argument('--frozen')
    args = parser.parse_args()
    report = build(args.kit, args.annotations, args.out, args.data_root, args.frozen)
    print(json.dumps({m:{s:{k:c[k] for k in ('n_cells','n_images','missing_cells','missing_images')} for s,c in v['counts'].items()}
                      for m,v in report['markers'].items()}, indent=2))


if __name__ == '__main__':
    main()
