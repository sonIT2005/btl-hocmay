"""Version model runs by their actual data contract and recipe, without importing torch."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve_path(value, root=ROOT):
    return (Path(root) / value).resolve()


def make_provenance(cfg, root=ROOT):
    root = Path(root)
    split_dir = resolve_path(cfg['splits_dir'], root)
    frozen_path = split_dir / 'FROZEN.json'
    frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
    manifest_path = split_dir / f"splits_{cfg['stain']}.csv"
    manifest_sha = sha256(manifest_path)
    expected = frozen['sha256'].get('splits/' + manifest_path.name)
    if expected != manifest_sha:
        raise ValueError('Manifest differs from FROZEN: ' + str(manifest_path))
    label_map = split_dir / 'label_map.json'
    label_sha = sha256(label_map)
    if frozen['sha256'].get('splits/label_map.json') != label_sha:
        raise ValueError('label_map.json differs from FROZEN')
    with manifest_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not rows or len({r['image_path'] for r in rows}) != len(rows):
        raise ValueError('Empty manifest or duplicate image paths')
    fingerprints = set()
    for row in rows:
        path = Path(row['image_path'])
        if path.is_absolute() or '..' in path.parts or len(path.parts) < 4 or path.parts[0] != 'processed':
            raise ValueError('Unexpected image path: ' + str(path))
        if path.parts[2] != cfg['stain']:
            raise ValueError('Image branch does not match stain')
        fingerprints.add(path.parts[1])
    if len(fingerprints) != 1:
        raise ValueError('A run must use exactly one processing fingerprint')
    # Paths and execution resources may differ between machines; sample/recipe identity may not.
    recipe = {k: v for k, v in cfg.items() if k not in
              {'data_root', 'splits_dir', '_output_root', 'num_workers', 'eval_batch_size'}}
    recipe_sha = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    code = {}
    for name in ['data.py', 'models.py', 'train.py', 'predict.py', 'provenance.py']:
        path = root / 'src/train' / name
        if path.exists():
            code[name] = hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()
    paths_module = root / 'src/data/paths.py'
    if paths_module.is_file():
        code['data_paths.py'] = sha256(paths_module)
    return {'schema': 1, 'data_fingerprint': next(iter(fingerprints)),
            'frozen_sha256': sha256(frozen_path), 'manifest_sha256': manifest_sha,
            'label_map_sha256': label_sha, 'recipe_sha256': recipe_sha,
            'training_code_sha256': code}


def require_same(expected, actual, context):
    if actual != expected:
        raise ValueError(f'{context}: provenance missing or changed. Archive old outputs or use a new run name/output root; do not resume or overwrite them.')


def output_root(cfg, root=ROOT):
    return resolve_path(cfg.get('_output_root', 'outputs'), root)


def inspect_run(cfg, provenance, root=ROOT):
    base = output_root(cfg, root)
    run = cfg['run_name']
    summary_path = base / 'logs' / f'{run}.json'
    sidecar = base / 'logs' / f'{run}.provenance.json'
    best = base / 'checkpoints' / f'{run}.pt'
    last = base / 'checkpoints' / f'{run}.last.pt'
    csv_log = base / 'logs' / f'{run}.csv'
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding='utf-8'))
        require_same(provenance, summary.get('provenance'), 'Completed run')
        if not best.exists():
            raise ValueError('Completed run is missing its checkpoint; refuse to skip silently')
        sets = ['val_smoke'] if cfg.get('technical_smoke') else ['test', 'LungHist700', 'CRC-VAL-HE-7K', 'BACH']
        for name in sets:
            path = base / 'predictions' / f'{run}__{name}.csv'
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError('Completed run has missing predictions; export into a new output root')
        return 'complete'
    if last.exists():
        if not sidecar.exists() or not best.exists():
            raise ValueError('Resume requires provenance sidecar and best checkpoint')
        require_same(provenance, json.loads(sidecar.read_text(encoding='utf-8')), 'Resume')
        return 'resume'
    if best.exists() or csv_log.exists() or sidecar.exists() or any((base / 'predictions').glob(f'{run}__*')):
        raise ValueError('Unfinished/legacy artifacts already exist; archive them or use a new run name/output root')
    return 'new'


def apply_overrides(cfg, args):
    cfg = dict(cfg)
    for attr in ['data_root', 'splits_dir', 'num_workers']:
        value = getattr(args, attr, None)
        if value is not None:
            cfg[attr] = value
    if getattr(args, 'output_root', None):
        cfg['_output_root'] = args.output_root
    if getattr(args, 'run_suffix', None):
        suffix = args.run_suffix
        if not suffix.replace('_', '').replace('-', '').isalnum():
            raise ValueError('run suffix must contain letters, digits, underscores or hyphens')
        cfg['run_name'] += '_' + suffix
    return cfg


def add_path_arguments(parser):
    parser.add_argument('--data-root', help='Existing raw/processed data directory; no copy or junction needed')
    parser.add_argument('--splits-dir', help='Directory containing frozen manifests')
    parser.add_argument('--output-root', help='Separate directory for new outputs')
    parser.add_argument('--num-workers', type=int)
    parser.add_argument('--run-suffix')
