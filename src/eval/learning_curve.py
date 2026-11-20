"""Learning curve theo cỡ tập train (slide 42–43 của môn): sai số train và val khi tăng dần số ảnh train.

    python -m src.eval.learning_curve run        # train 9 run (10/25/50% × 3 seed), đo lại train/val, vẽ hình
    python -m src.eval.learning_curve report     # chỉ tổng hợp lại bảng và hình từ kết quả đã có
    python -m src.eval.learning_curve run --fractions 0.1 --seeds 0 --smoke   # chạy thử vài phút

Cấu hình giống hệt `e2_convnext_group_none` (ConvNeXt-T, chia theo nhóm, nhánh none). Mức 100% dùng lại 3 run E2
đã có. Tập con lấy **theo nhóm**, giữ tỷ lệ lớp và **lồng nhau** (10% ⊂ 25% ⊂ 50%), cố định qua các seed, nên độ
dao động giữa seed chỉ đến từ quá trình train. Val, test và test chéo giữ nguyên.

Không sửa `src/train/`: script gọi lại đúng `src.train.train.main`, chỉ thay hàm đọc manifest bằng bản có cắt bớt
tập train. Nhờ vậy code train của 15 run và provenance của chúng không đổi; `train_fraction` nằm trong config nên
recipe của run learning curve có provenance riêng.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml

import src.train.train as train_module
from src.eval.metrics import cm_metrics, confusion
from src.train.data import ROOT
from src.train.models import build_model, norm_stats
from src.train.predict import predict_probs

FRACTIONS = [0.1, 0.25, 0.5]
SEEDS = [0, 1, 2]
SUBSET_SEED = 42  # cố định, khác seed train
BASE = 'e2_convnext_group_none_s{seed}'
_original_load_manifest = train_module.load_manifest


def subsample_train(df, split_col, fraction, seed=SUBSET_SEED):
    """Giữ ceil(fraction × số nhóm) nhóm train của mỗi lớp (tối thiểu 1). Các tập khác giữ nguyên."""
    if fraction >= 1:
        return df
    train = df[df[split_col] == 'train']
    keep = []
    for label, part in train.groupby('label'):
        groups = np.array(sorted(part.group_id.unique()))
        order = np.random.default_rng([seed, int(label)]).permutation(groups)  # cùng thứ tự cho mọi fraction
        keep.extend(order[:max(1, math.ceil(fraction * len(groups)))])
    return df[(df[split_col] != 'train') | df.group_id.isin(set(keep))]


def load_manifest_subset(cfg):
    df, split_col = _original_load_manifest(cfg)
    return subsample_train(df, split_col, cfg.get('train_fraction', 1.0)), split_col


def run_name(fraction, seed):
    return BASE.format(seed=seed) if fraction >= 1 else f'l{round(fraction * 100)}_convnext_group_none_s{seed}'


def write_config(fraction, seed):
    cfg = yaml.safe_load((ROOT / 'configs/runs' / f'{BASE.format(seed=seed)}.yaml').read_text(encoding='utf-8'))
    cfg.update(run_name=run_name(fraction, seed), experiment=f'l{round(fraction * 100)}', train_fraction=fraction)
    path = ROOT / 'configs/learning_curve' / f"{cfg['run_name']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding='utf-8')
    return path


def train_run(config_path, smoke):
    """Gọi đúng hàm main của src/train/train.py, như khi chạy `python -m src.train.train <config>`."""
    train_module.load_manifest = load_manifest_subset
    argv = sys.argv
    sys.argv = ['src.train.train', str(config_path)] + (['--smoke'] if smoke else [])
    try:
        train_module.main()
    finally:
        sys.argv = argv
        train_module.load_manifest = _original_load_manifest


def evaluate_train_val(run, out_root):
    """Macro-F1 của checkpoint tốt nhất trên chính tập train đã dùng (không augmentation) và trên val."""
    cache = out_root / 'logs' / f'{run}.train_eval.json'
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8'))
    ckpt = torch.load(out_root / 'checkpoints' / f'{run}.pt', map_location='cpu', weights_only=False)
    cfg = ckpt['config']
    model = build_model(cfg['model'], cfg['num_classes'], pretrained=False)
    model.load_state_dict(ckpt['model'])
    model = model.cuda().to(memory_format=torch.channels_last)
    mean, std = norm_stats(model)
    df, split_col = load_manifest_subset(cfg)
    if cfg.get('technical_smoke'):
        df = train_module.smoke_subset(df, split_col, cfg['seed'])
    result = {'run': run, 'fraction': cfg.get('train_fraction', 1.0), 'seed': cfg['seed'], 'best_epoch': ckpt['epoch']}
    for split in ['train', 'val']:
        part = df[df[split_col] == split]
        y = part.label.to_numpy()
        pred = predict_probs(model, part, cfg, mean, std, f'{run} {split}').argmax(1)
        m = cm_metrics(confusion(y, pred), np.unique(y))
        result.update({f'n_{split}': len(part), f'{split}_macro_f1': m['macro_f1'], f'{split}_accuracy': m['accuracy']})
    cache.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"{run}: train macro-F1 {result['train_macro_f1']:.4f}, val {result['val_macro_f1']:.4f} ({result['n_train']} ảnh train)")
    return result


def test_macro_f1(run, out_root):
    path = out_root / 'predictions' / f'{run}__test.csv'
    if not path.exists():
        return np.nan
    p = pd.read_csv(path, usecols=['true_label', 'pred_label'])
    return cm_metrics(confusion(p.true_label.to_numpy(), p.pred_label.to_numpy()), np.unique(p.true_label))['macro_f1']


def report(rows, out_root):
    df = pd.DataFrame(rows)
    df['test_macro_f1'] = [test_macro_f1(r, out_root) for r in df.run]
    for split in ['train', 'val', 'test']:
        df[f'{split}_error'] = 1 - df[f'{split}_macro_f1']
    g = df.groupby('fraction')
    table = g[['n_train', 'train_error', 'val_error', 'test_error']].agg(['mean', 'std'])
    table.columns = [f'{a}_{b}' for a, b in table.columns]
    table['n_seeds'] = g.size()
    table = table.reset_index()
    tables, figs = out_root / 'eval/tables', out_root / 'eval/figures'
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    df.to_csv(tables / 'learning_curve_runs.csv', index=False)
    table.to_csv(tables / 'learning_curve.csv', index=False)

    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    x = table.n_train_mean
    for split, style, label in [('train', 'o-', 'Train'), ('val', 's-', 'Validation'), ('test', '^--', 'Test nội bộ')]:
        mean, sd = table[f'{split}_error_mean'], table[f'{split}_error_std'].fillna(0)
        ax.plot(x, mean, style, label=label)
        ax.fill_between(x, mean - sd, mean + sd, alpha=0.15)
    ax.set_xscale('log')
    ax.set_xticks(x, [f'{n:.0f}\n({f:.0%})' for n, f in zip(x, table.fraction)])
    ax.minorticks_off()
    ax.set_xlabel('Số ảnh train (tỷ lệ tập train)')
    ax.set_ylabel('Sai số = 1 − macro-F1')
    ax.set_title('Learning curve, ConvNeXt-T chia theo nhóm (mean ± SD, 3 seed)', fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figs / 'learning_curve.png', dpi=150)
    plt.close(fig)
    print('\n' + table.round(4).to_string(index=False))
    print(f"\nĐã ghi {tables / 'learning_curve.csv'} và {figs / 'learning_curve.png'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('command', choices=['run', 'report'])
    parser.add_argument('--fractions', type=float, nargs='+', default=FRACTIONS)
    parser.add_argument('--seeds', type=int, nargs='+', default=SEEDS)
    parser.add_argument('--smoke', action='store_true', help='2 epoch trên vài trăm ảnh, ghi vào outputs/trials/')
    args = parser.parse_args()
    out_root = ROOT / ('outputs/trials' if args.smoke else 'outputs')
    suffix = '_smoke' if args.smoke else ''

    if args.command == 'run':
        for seed in args.seeds:
            for fraction in args.fractions:
                print(f'\n=== {run_name(fraction, seed)}{suffix}: {fraction:.0%} tập train ===')
                train_run(write_config(fraction, seed), args.smoke)

    fractions = sorted(set(args.fractions) | ({1.0} if not args.smoke else set()))
    rows = [evaluate_train_val(run_name(f, s) + suffix, out_root) for f in fractions for s in args.seeds
            if (out_root / 'checkpoints' / f'{run_name(f, s)}{suffix}.pt').exists()]
    if rows:
        report(rows, out_root)


if __name__ == '__main__':
    main()
