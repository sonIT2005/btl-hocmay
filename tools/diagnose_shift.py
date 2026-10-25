"""Chẩn đoán lỗi nhầm cơ quan của một checkpoint bằng cách đổi từng yếu tố trên ảnh NỘI BỘ.

Chỉ dùng ảnh train/val (LC25000, BreakHis), không đọc ảnh xtest (R01). Mỗi phép thử đổi đúng
một yếu tố (tỷ lệ, độ bão hòa, nén JPEG, màu) rồi đo tỷ lệ đoán sang cơ quan khác.

    python tools/diagnose_shift.py configs/runs/e2_convnext_group_none_s0.yaml
"""
import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.paths import resolve_data_root
DATA_ROOT = resolve_data_root(ROOT)
from src.train.models import build_model, norm_stats  # noqa: E402

ORGAN = np.array([0, 0, 0, 1, 1, 2, 2])
BREAST = 2


def center_crop(im, factor, size=224):
    im = im.resize((round(im.width * factor), round(im.height * factor)), Image.Resampling.LANCZOS)
    x, y = (im.width - size) // 2, (im.height - size) // 2
    return im.crop((x, y, x + size, y + size))


def jpeg(im, quality):
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


def summary(pred, y):
    return {'organ_confusion': float(np.mean(ORGAN[pred] != ORGAN[y])),
            'pred_breast': float(np.mean(ORGAN[pred] == BREAST)), 'acc7': float(np.mean(pred == y))}


def main():
    global DATA_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--per-class', type=int, default=100, help='số ảnh val LC25000 mỗi lớp')
    args = parser.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding='utf-8'))
    DATA_ROOT = resolve_data_root(ROOT, cfg.get('data_root'))
    ckpt = torch.load(ROOT / 'outputs/checkpoints' / f"{cfg['run_name']}.pt", map_location='cpu', weights_only=False)
    model = build_model(cfg['model'], cfg['num_classes'], pretrained=False)
    model.load_state_dict(ckpt['model'])
    model = model.cuda().eval()
    mean, std = [torch.tensor(v).view(3, 1, 1) for v in norm_stats(model)]

    @torch.no_grad()
    def predict(arrays):
        x = torch.stack([(torch.from_numpy(np.asarray(a, dtype=np.float32) / 255).permute(2, 0, 1) - mean) / std
                         for a in arrays])
        with torch.autocast('cuda', dtype=getattr(torch, cfg['amp_dtype'])):
            return torch.cat([model(x[i:i + 100].cuda()).float().argmax(1).cpu() for i in range(0, len(x), 100)]).numpy()

    full = pd.read_csv(ROOT / 'splits/splits.csv', low_memory=False)
    manifest = pd.read_csv(ROOT / cfg['splits_dir'] / f"splits_{cfg['stain']}.csv")
    lc = full[(full.source == 'LC25000') & (full.split == 'val')]
    lc = pd.concat([lc[lc.label == k].sample(args.per_class, random_state=0) for k in range(5)])
    bh = full[(full.source == 'BreakHis') & (full.split == 'val')]
    lc_raw = [Image.open(DATA_ROOT / p).convert('RGB') for p in lc.source_image_path]
    bh_raw = [Image.open(DATA_ROOT / p).convert('RGB') for p in bh.source_image_path]
    lc_mpp, bh_mpp = lc.native_mpp.iloc[0] / cfg.get('target_mpp', 0.5), bh.native_mpp.iloc[0] / cfg.get('target_mpp', 0.5)
    out = {'run_name': cfg['run_name'], 'n_lc_val': len(lc), 'n_breakhis_val': len(bh), 'tests': {}}

    def record(name, value, pred, y):
        out['tests'].setdefault(name, []).append({'value': value, **summary(pred, y)})
        print(f'{name:28s} {str(value):>6}: {summary(pred, y)}')

    for f in [1.0, 0.85, 0.75, 0.66, 0.5]:
        record('lc_val_scale', f, predict([center_crop(im, lc_mpp * f) for im in lc_raw]), lc.label.values)
    for f in [1.0, 1.5, 2.0, 3.0]:
        record('breakhis_val_scale', f, predict([center_crop(im, bh_mpp * f) for im in bh_raw]), bh.label.values)
    for s in [1.0, 0.6, 0.3, 0.0]:
        record('lc_val_saturation', s, predict([ImageEnhance.Color(center_crop(im, lc_mpp)).enhance(s) for im in lc_raw]),
               lc.label.values)
    bh_proc = [Image.open(DATA_ROOT / p).convert('RGB') for p in manifest.loc[bh.index, 'image_path']]
    for q in [None, 95, 75, 50]:
        record('breakhis_val_jpeg', q, predict(bh_proc if q is None else [jpeg(im, q) for im in bh_proc]), bh.label.values)

    # Chuyển màu: khớp mean/std từng kênh RGB của LC25000 val sang thống kê ảnh TRAIN BreakHis.
    def stats(paths):
        a = np.stack([np.asarray(Image.open(DATA_ROOT / p).convert('RGB'), dtype=np.float32) for p in paths])
        return a.mean((0, 1, 2)), a.std((0, 1, 2))
    train = manifest[manifest.split == 'train']
    lc_stats = stats(train[train.source == 'LC25000'].sample(300, random_state=0).image_path)
    lc_val = [np.asarray(Image.open(DATA_ROOT / p).convert('RGB'), dtype=np.float32) for p in manifest.loc[lc.index, 'image_path']]
    for name, label in [('breakhis_benign', 5), ('breakhis_malignant', 6)]:
        dst = stats(train[(train.source == 'BreakHis') & (train.label == label)].sample(300, random_state=0).image_path)
        moved = [np.clip((a - lc_stats[0]) / lc_stats[1] * dst[1] + dst[0], 0, 255) for a in lc_val]
        record('lc_val_color_to', name, predict(moved), lc.label.values)

    path = ROOT / 'results' / f"diagnostics_{cfg['run_name']}.json"
    path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('->', path.relative_to(ROOT))


if __name__ == '__main__':
    main()
