"""Xuất predictions.csv (mục 4.3) từ checkpoint tốt nhất của một lần chạy.

Dùng lại khi cần dự đoán lại mà không train:
    python -m src.train.predict configs/runs/e2_swin_group_macenko_s1.yaml
"""
import argparse

import numpy as np
import pandas as pd
import torch
import yaml
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.train.data import ROOT, ManifestDataset, eval_sets, load_manifest
from src.train.models import build_model, norm_stats


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


def write_predictions(model, cfg, mean, std, sets):
    out_dir = ROOT / 'outputs/predictions'
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in sets.items():
        probs = predict_probs(model, df, cfg, mean, std, f'predict {name}')
        pred = pd.DataFrame({'image_path': df.image_path.values, 'group_id': df.group_id.values,
                             'true_label': df.label.values, 'pred_label': probs.argmax(1)})
        for k in range(probs.shape[1]):
            pred[f'prob_{k}'] = np.round(probs[:, k], 6)
        pred['run_name'] = cfg['run_name']
        pred['test_set'] = name
        path = out_dir / f"{cfg['run_name']}__{name}.csv"
        pred.to_csv(path, index=False)
        acc = (pred.pred_label == pred.true_label).mean()
        print(f'{name:>14}: {len(pred):6d} ảnh, accuracy {acc:.4f} -> {path.relative_to(ROOT)}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding='utf-8'))
    ckpt = torch.load(ROOT / 'outputs/checkpoints' / f"{cfg['run_name']}.pt", map_location='cpu')
    model = build_model(cfg['model'], cfg['num_classes'], pretrained=False)
    model.load_state_dict(ckpt['model'])
    model = model.cuda().to(memory_format=torch.channels_last)
    mean, std = norm_stats(model)
    df, split_col = load_manifest(cfg)
    write_predictions(model, cfg, mean, std, eval_sets(df, split_col))


if __name__ == '__main__':
    main()
