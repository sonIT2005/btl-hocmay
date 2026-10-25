"""Read-only contract, image, tensor and optional random-weight forward preflight."""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from src.train.provenance import add_path_arguments, apply_overrides, inspect_run, make_provenance, resolve_path


def check(cfg, tensor_check=False, forward=False, device='cpu'):
    import numpy as np
    import pandas as pd
    from PIL import Image
    from src.train.provenance import sha256
    provenance = make_provenance(cfg)
    splits = resolve_path(cfg['splits_dir'])
    df = pd.read_csv(splits / f"splits_{cfg['stain']}.csv")
    data = resolve_path(cfg['data_root'])
    if not data.is_dir():
        raise FileNotFoundError('Use --data-root to point to existing data: ' + str(data))
    required = {'image_path', 'label', 'organ', 'source', 'group_id', 'split', 'split_random'}
    if not required.issubset(df.columns):
        raise ValueError('Missing manifest columns')
    organs = np.array(['lung', 'lung', 'lung', 'colon', 'colon', 'breast', 'breast'])
    if not df.label.isin(range(7)).all() or not (df.organ.to_numpy() == organs[df.label.to_numpy()]).all():
        raise ValueError('Label/organ mapping is invalid')
    ext = df.source.isin(['CRC-VAL-HE-7K', 'BACH', 'LungHist700'])
    if not ((df.loc[ext, 'split'] == 'xtest') & (df.loc[ext, 'split_random'] == 'xtest')).all():
        raise ValueError('External source entered internal split')
    split_col = 'split' if cfg['split'] == 'group' else 'split_random'
    train = df[df[split_col] == 'train']
    if set(train.label) != set(range(7)) or (df[split_col] == 'val').sum() == 0:
        raise ValueError('Internal train/val coverage is incomplete')
    missing = [p for p in df.image_path if not (data / p).is_file()]
    if missing:
        raise FileNotFoundError(f'{len(missing)} images missing; first: {missing[0]}')
    with (splits / 'processed_checksums.csv').open(encoding='utf-8-sig', newline='') as stream:
        hashes = {r['image_path']: r['sha256'] for r in csv.DictReader(stream)}
    sample = df.groupby('source', sort=True).head(2).reset_index(drop=True)
    for row in sample.itertuples():
        path = data / row.image_path
        if sha256(path) != hashes.get(row.image_path):
            raise ValueError('Sample image checksum mismatch: ' + row.image_path)
        with Image.open(path) as im:
            im.load()
            if im.size != (224, 224) or im.mode != 'RGB':
                raise ValueError('Unexpected image dimensions/mode')
    report = {'provenance': provenance, 'manifest_rows': len(df), 'missing_images': 0,
              'sample_images_checked': len(sample), 'n_train': len(train),
              'n_val': int((df[split_col] == 'val').sum()), 'tensor_check': False,
              'forward_check': False, 'training_executed': False, 'pretrained_weights_downloaded': False}
    try:
        report['run_state'] = inspect_run(cfg, provenance)
    except ValueError as error:
        report['run_state'] = 'blocked_old_artifacts'
        report['run_state_reason'] = str(error)
    if tensor_check or forward:
        import torch
        from src.train.data import ManifestDataset
        from src.train.models import build_model, norm_stats
        torch.set_num_threads(4)
        model = build_model(cfg['model'], 7, pretrained=False).eval()
        mean, std = norm_stats(model)
        dataset = ManifestDataset(sample, cfg, mean, std, train=False)
        tensors = []
        for i, row in enumerate(sample.itertuples()):
            actual, label = dataset[i]
            with Image.open(data / row.image_path) as im:
                a = np.asarray(im.convert('RGB'), dtype=np.float32) / 255.
            manual = torch.from_numpy(a).permute(2, 0, 1)
            manual = (manual - torch.tensor(mean).view(3, 1, 1)) / torch.tensor(std).view(3, 1, 1)
            if label != row.label or not torch.equal(actual, manual):
                raise ValueError('Loader/manual tensor mismatch: ' + row.image_path)
            tensors.append(actual)
        report.update(tensor_check=True, torch_version=torch.__version__,
                      cuda_available=torch.cuda.is_available(), model=cfg['model'])
        if forward:
            if device == 'cuda' and not torch.cuda.is_available():
                raise RuntimeError('CUDA was requested but is unavailable')
            with torch.no_grad():
                result = model.to(device)(torch.stack(tensors[:2]).to(device)).float().cpu()
            if result.shape != (2, 7) or not torch.isfinite(result).all():
                raise ValueError('Model forward produced invalid logits')
            report.update(forward_check=True, device=device, logits_shape=list(result.shape))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config')
    add_path_arguments(parser)
    parser.add_argument('--tensor-check', action='store_true')
    parser.add_argument('--forward', action='store_true', help='Random weights, no optimizer or training')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    parser.add_argument('--report')
    args = parser.parse_args()
    cfg = apply_overrides(yaml.safe_load(Path(args.config).read_text(encoding='utf-8')), args)
    report = check(cfg, args.tensor_check, args.forward, args.device)
    content = json.dumps(report, indent=2)
    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as stream:
            stream.write(content)
    print(content)


if __name__ == '__main__':
    main()
