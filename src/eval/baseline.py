"""Baseline (D14): mốc so sánh đơn giản cho ConvNeXt-T và Swin-T đã fine-tune.

    python -m src.eval.baseline                 # nhánh none
    python -m src.eval.baseline --smoke         # chạy thử vài phút trên ít ảnh, ghi vào outputs/trials/

Hai baseline, dùng cùng dữ liệu đóng băng và cùng cách chia theo nhóm với E2:
- b0_majority: luôn đoán lớp nhiều ảnh nhất trong train; xác suất = tỷ lệ lớp trong train.
  Cho biết mức "không học gì" (slide 12: accuracy có thể cao mà mô hình vô dụng).
- b1_logreg: ConvNeXt-T pretrain ImageNet **đóng băng** (không fine-tune) trích vector 768 chiều cho mỗi ảnh,
  rồi StandardScaler + Logistic Regression. Cho biết fine-tune toàn bộ mạng có đáng hay không.

Quy trình chọn mô hình theo slide 27–32: scaler chỉ fit trên train (không rò rỉ qua tiền xử lý),
C chọn theo macro-F1 trên val, test và test chéo chỉ dùng một lần ở cuối.
Predictions ghi đúng định dạng của các run, nên `python -m src.eval.metrics` tự đọc và đưa vào bảng.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.eval.metrics import K, cm_metrics, confusion
from src.train.data import ROOT, ManifestDataset, eval_sets, load_manifest
from src.train.models import MODELS, build_model, norm_stats

# Lần 1 chọn C=0,01 nằm ở biên lưới, nên mở rộng về phía C nhỏ. Chỉ dựa trên val, không xem test.
# Hòa điểm thì chọn C nhỏ hơn (mô hình đơn giản hơn).
C_GRID = [0.001, 0.003, 0.01, 0.1, 1.0, 10.0]


@torch.no_grad()
def extract_features(df, cfg, batch_size):
    """Vector 768 chiều sau global pooling của ConvNeXt-T ImageNet, không có lớp phân loại."""
    model = build_model('convnext', num_classes=0).cuda().eval().to(memory_format=torch.channels_last)
    mean, std = norm_stats(model)
    loader = DataLoader(ManifestDataset(df, cfg, mean, std, train=False), batch_size=batch_size,
                        num_workers=cfg['num_workers'], pin_memory=True)
    out = []
    for x, _ in tqdm(loader, desc='trích đặc trưng'):
        with torch.autocast('cuda', dtype=torch.bfloat16):
            out.append(model(x.cuda(non_blocking=True).to(memory_format=torch.channels_last)).float().cpu())
    return torch.cat(out).numpy()


def cached_features(df, cfg, cache, batch_size):
    """Trích một lần rồi lưu lại; lần sau đọc từ cache nếu đúng danh sách ảnh."""
    if cache.exists():
        saved = np.load(cache, allow_pickle=False)
        if np.array_equal(saved['image_path'], df.image_path.to_numpy(dtype=str)):
            print(f'Đọc đặc trưng từ {cache.relative_to(ROOT)}')
            return saved['features']
    feats = extract_features(df, cfg, batch_size)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, features=feats, image_path=df.image_path.to_numpy(dtype=str))
    return feats


def macro_f1(y_true, y_pred):
    return cm_metrics(confusion(y_true, y_pred), np.unique(y_true))['macro_f1']


def write_predictions(probs, df, run, name, out_dir, force):
    path = out_dir / f'{run}__{name}.csv'
    if path.exists() and not force:
        raise FileExistsError(f'{path} đã có; thêm --force nếu muốn ghi đè')
    pred = pd.DataFrame({'image_path': df.image_path.values, 'group_id': df.group_id.values,
                         'true_label': df.label.values, 'pred_label': probs.argmax(1)})
    for k in range(K):
        pred[f'prob_{k}'] = probs[:, k]
    pred['run_name'], pred['test_set'] = run, name
    pred.to_csv(path, index=False, float_format='%.17g')
    acc = (pred.pred_label == pred.true_label).mean()
    print(f'  {run:28s} {name:>14s}: accuracy {acc:.4f}, macro-F1 {macro_f1(df.label.values, pred.pred_label.values):.4f}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--stain', choices=['none', 'macenko'], default='none')
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--smoke', action='store_true', help='Chạy thử trên vài trăm ảnh, ghi vào outputs/trials/')
    parser.add_argument('--force', action='store_true', help='Cho phép ghi đè predictions đã có')
    args = parser.parse_args()

    cfg = yaml.safe_load((ROOT / 'configs/train_base.yaml').read_text(encoding='utf-8'))
    cfg.update(stain=args.stain, split='group')
    df, split_col = load_manifest(cfg)
    if args.smoke:
        df = df.groupby([split_col, 'label'], group_keys=False).sample(n=20, random_state=0, replace=True).drop_duplicates()
    out_root = ROOT / ('outputs/trials' if args.smoke else 'outputs')
    pred_dir = out_root / 'predictions'
    pred_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    feats = cached_features(df, cfg, out_root / 'features' / f'convnext_in1k_{args.stain}{"_smoke" if args.smoke else ""}.npz',
                            args.batch_size)
    idx = {name: np.flatnonzero((df[split_col] == name).to_numpy()) for name in ['train', 'val']}
    y_train, y_val = df.label.values[idx['train']], df.label.values[idx['val']]
    print(f'Đặc trưng {feats.shape}, train {len(y_train)}, val {len(y_val)} ảnh ({time.time() - t0:.0f}s)')

    # b0: lớp đa số
    prior = np.bincount(y_train, minlength=K) / len(y_train)
    majority = f'b0_majority_group_{args.stain}_s0'
    print(f'\n{majority}: luôn đoán lớp {prior.argmax()} (tỷ lệ {prior.max():.1%} trong train)')

    # b1: chọn C trên val
    selection = []
    for c in C_GRID:
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=c, class_weight='balanced', max_iter=3000))
        clf.fit(feats[idx['train']], y_train)
        selection.append({'C': c, 'val_macro_f1': macro_f1(y_val, clf.predict(feats[idx['val']])),
                          'train_macro_f1': macro_f1(y_train, clf.predict(feats[idx['train']])), 'model': clf})
        print(f'  C={c:<5g} train macro-F1 {selection[-1]["train_macro_f1"]:.4f}  val macro-F1 {selection[-1]["val_macro_f1"]:.4f}')
    best = max(selection, key=lambda s: (round(s['val_macro_f1'], 4), -s['C']))
    logreg = f'b1_logreg_group_{args.stain}_s0'
    print(f'{logreg}: chọn C={best["C"]} theo val macro-F1')

    print('\nDự đoán (chỉ một lần, sau khi đã chốt C):')
    for name, part in eval_sets(df, split_col).items():
        if part.empty:
            continue
        rows = df.index.get_indexer(part.index)
        write_predictions(np.tile(prior, (len(part), 1)), part, majority, name, pred_dir, args.force)
        write_predictions(best['model'].predict_proba(feats[rows]), part, logreg, name, pred_dir, args.force)

    record = {'feature_extractor': MODELS['convnext'], 'frozen': True, 'stain': args.stain, 'C_grid': C_GRID,
              'selected_C': best['C'], 'selection': [{k: v for k, v in s.items() if k != 'model'} for s in selection],
              'majority_class': int(prior.argmax()), 'train_prior': prior.round(6).tolist(),
              'n_train': int(len(y_train)), 'n_val': int(len(y_val)), 'seconds': round(time.time() - t0, 1)}
    (out_root / 'logs').mkdir(parents=True, exist_ok=True)
    (out_root / 'logs' / f'baseline_{args.stain}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(f'\nXong sau {time.time() - t0:.0f}s. Chạy `python -m src.eval.metrics` để cập nhật bảng.')


if __name__ == '__main__':
    main()
