"""Xuất predictions.csv (mục 4.3) từ checkpoint tốt nhất của một lần chạy.

Dùng lại khi cần dự đoán lại mà không train:
    python -m src.train.predict configs/runs/e2_swin_group_macenko_s1.yaml
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.train.data import ROOT, ManifestDataset, eval_sets, load_manifest
from src.train.models import build_model, norm_stats
from src.train.provenance import add_path_arguments, apply_overrides, make_provenance, output_root, require_same


@torch.no_grad()
def predict_probs(model, df, cfg, mean, std, desc):
    loader = DataLoader(ManifestDataset(df, cfg, mean, std, train=False), batch_size=cfg['eval_batch_size'],
                        num_workers=cfg['num_workers'], pin_memory=True)
    model.eval()
    out = []
    for x, _ in tqdm(loader, desc=desc, leave=False):
        with torch.autocast('cuda', dtype=getattr(torch, cfg['amp_dtype'])):
            logits = model(x.cuda(non_blocking=True).to(memory_format=torch.channels_last))
        out.append(logits.float().softmax(1).cpu())
    return torch.cat(out).numpy()


def prediction_frame(probs, df, cfg, name):
    if probs.shape != (len(df), cfg['num_classes']) or not np.isfinite(probs).all():
        raise ValueError('Invalid probability shape or non-finite values')
    pred = pd.DataFrame({'image_path': df.image_path.values, 'group_id': df.group_id.values,
                         'true_label': df.label.values, 'pred_label': probs.argmax(1)})
    for k in range(probs.shape[1]):
        pred[f'prob_{k}'] = probs[:, k]  # Keep model precision; do not quantize small probabilities.
    pred['run_name'] = cfg['run_name']
    pred['test_set'] = name
    return pred


def write_predictions(model, cfg, mean, std, sets, provenance=None):
    out_dir = output_root(cfg) / 'predictions'
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in sets.items():
        path = out_dir / f"{cfg['run_name']}__{name}.csv"
        if path.exists():
            raise FileExistsError(f'Refuse to overwrite predictions: {path}')
        probs = predict_probs(model, df, cfg, mean, std, f'predict {name}')
        pred = prediction_frame(probs, df, cfg, name)
        pred.to_csv(path, index=False, float_format='%.17g')
        acc = (pred.pred_label == pred.true_label).mean()
        print(f'{name:>14}: {len(pred):6d} ảnh, accuracy {acc:.4f} -> {path}')
    if provenance is not None:
        (out_dir / f"{cfg['run_name']}__provenance.json").write_text(json.dumps(provenance, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--checkpoint', help='Checkpoint to export; defaults to run output checkpoint')
    parser.add_argument('--allow-legacy-checkpoint', action='store_true', help='Explicitly export an old checkpoint without provenance to a NEW output root')
    add_path_arguments(parser)
    args = parser.parse_args()
    cfg = apply_overrides(yaml.safe_load(open(args.config, encoding='utf-8')), args)
    provenance = make_provenance(cfg)
    path = Path(args.checkpoint) if args.checkpoint else output_root(cfg) / 'checkpoints' / f"{cfg['run_name']}.pt"
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    if ckpt.get('provenance') is None and args.allow_legacy_checkpoint:
        if not args.output_root or (output_root(cfg) / 'predictions').exists():
            raise ValueError('Legacy export requires --output-root with no existing predictions directory')
        provenance = {**provenance, 'checkpoint_identity': 'legacy_unverified', 'checkpoint_path': str(path)}
    else:
        require_same(provenance, ckpt.get('provenance'), 'Prediction checkpoint')
    if not torch.cuda.is_available():
        raise RuntimeError('Prediction currently requires CUDA; no checkpoint inference has been run')
    model = build_model(cfg['model'], cfg['num_classes'], pretrained=False)
    model.load_state_dict(ckpt['model'])
    model = model.cuda().to(memory_format=torch.channels_last)
    mean, std = norm_stats(model)
    df, split_col = load_manifest(cfg)
    write_predictions(model, cfg, mean, std, eval_sets(df, split_col), provenance=provenance)


if __name__ == '__main__':
    main()
