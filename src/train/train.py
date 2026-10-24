"""Fine-tune một cấu hình E1/E2 rồi xuất checkpoint + predictions.

    python -m src.train.train configs/runs/e2_convnext_group_none_s0.yaml
    python -m src.train.train configs/runs/e2_convnext_group_none_s0.yaml --smoke   # chạy thử vài phút

Ctrl+C an toàn: chạy lại cùng lệnh sẽ tiếp tục từ epoch cuối đã lưu.
Chọn checkpoint theo macro-F1 trên val nội bộ (R06); tập xtest chỉ dùng ở bước dự đoán cuối (R01).
"""
import argparse
import csv
import json
import math
import random
import time

import numpy as np
import torch
import yaml
from sklearn.metrics import balanced_accuracy_score, f1_score
from timm.optim import create_optimizer_v2
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.train.data import ROOT, ManifestDataset, class_weights, eval_sets, load_manifest
from src.train.models import build_model, norm_stats
from src.train.predict import predict_probs, write_predictions


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def smoke_subset(df, split_col, seed):
    """Vài chục ảnh mỗi lớp để kiểm tra pipeline từ đầu đến cuối, không dùng kết quả."""
    take = {'train': 32, 'val': 16, 'test': 16, 'xtest': 16}
    parts = [g.sample(min(len(g), take[s]), random_state=seed)
             for (s, _), g in df.groupby([split_col, 'label']) if s in take]
    return df.loc[sorted(np.concatenate([p.index for p in parts]))]


def evaluate(model, df, cfg, mean, std, criterion):
    probs = predict_probs(model, df, cfg, mean, std, 'val')
    y = df.label.values
    pred = probs.argmax(1)
    loss = criterion(torch.log(torch.from_numpy(probs).clamp_min(1e-12)), torch.tensor(y)).item()
    return {'val_loss': float(loss), 'val_macro_f1': float(f1_score(y, pred, average='macro')),
            'val_bal_acc': float(balanced_accuracy_score(y, pred))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--smoke', action='store_true', help='2 epoch trên vài trăm ảnh, ghi ra tên *_smoke')
    args = parser.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding='utf-8'))
    if args.smoke:
        cfg.update(run_name=cfg['run_name'] + '_smoke', epochs=2, warmup_epochs=1)
    run = cfg['run_name']
    ckpt_dir, log_dir = ROOT / 'outputs/checkpoints', ROOT / 'outputs/logs'
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    best_path, last_path, log_path = ckpt_dir / f'{run}.pt', ckpt_dir / f'{run}.last.pt', log_dir / f'{run}.csv'
    if (log_dir / f'{run}.json').exists():
        print(f'{run} đã chạy xong ({log_dir / f"{run}.json"}). Muốn dự đoán lại: python -m src.train.predict {args.config}')
        return
    if not last_path.exists():
        log_path.unlink(missing_ok=True)  # log của lần chạy dở chưa kịp lưu epoch nào

    seed_everything(cfg['seed'])
    torch.backends.cudnn.benchmark = True
    df, split_col = load_manifest(cfg)
    if args.smoke:
        df = smoke_subset(df, split_col, cfg['seed'])
    train_df, val_df = df[df[split_col] == 'train'], df[df[split_col] == 'val']
    print(f'{run}: train {len(train_df)}, val {len(val_df)} ảnh ({split_col}, stain={cfg["stain"]})')

    model = build_model(cfg['model'], cfg['num_classes']).cuda().to(memory_format=torch.channels_last)
    mean, std = norm_stats(model)
    gen = torch.Generator().manual_seed(cfg['seed'])
    loader = DataLoader(ManifestDataset(train_df, cfg, mean, std, train=True), batch_size=cfg['batch_size'],
                        shuffle=True, drop_last=True, num_workers=cfg['num_workers'], pin_memory=True,
                        persistent_workers=True, generator=gen)
    weights = class_weights(train_df.label, cfg['num_classes'])
    criterion = torch.nn.CrossEntropyLoss(weight=weights.cuda())
    eval_criterion = torch.nn.NLLLoss(weight=weights)
    optimizer = create_optimizer_v2(model, 'adamw', lr=cfg['lr'], weight_decay=cfg['weight_decay'])
    total, warmup = cfg['epochs'] * len(loader), cfg['warmup_epochs'] * len(loader)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda s: (s + 1) / warmup if s < warmup
                                                  else 0.5 * (1 + math.cos(math.pi * (s - warmup) / max(1, total - warmup))))
    amp = getattr(torch, cfg['amp_dtype'])

    state = {'epoch': 0, 'best_f1': -1.0, 'best_epoch': 0, 'bad_epochs': 0, 'finished': False, 'epoch_sec': []}
    if last_path.exists():
        last = torch.load(last_path, map_location='cpu', weights_only=False)
        model.load_state_dict(last['model'])
        optimizer.load_state_dict(last['optimizer'])
        scheduler.load_state_dict(last['scheduler'])
        state = last['state']
        print(f'Tiếp tục từ epoch {state["epoch"]} (best macro-F1 {state["best_f1"]:.4f} ở epoch {state["best_epoch"]})')

    while not state['finished'] and state['epoch'] < cfg['epochs']:
        epoch = state['epoch'] + 1
        model.train()
        t0, running = time.time(), 0.0
        bar = tqdm(loader, desc=f'epoch {epoch}/{cfg["epochs"]}')
        for step, (x, y) in enumerate(bar, 1):
            x = x.cuda(non_blocking=True).to(memory_format=torch.channels_last)
            y = y.cuda(non_blocking=True)
            with torch.autocast('cuda', dtype=amp):
                loss = criterion(model(x), y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            scheduler.step()
            running += loss.item()
            if step % 20 == 0:
                bar.set_postfix(loss=f'{running / step:.4f}', lr=f'{scheduler.get_last_lr()[0]:.2e}')
        train_sec = time.time() - t0
        metrics = evaluate(model, val_df, cfg, mean, std, eval_criterion)
        row = {'epoch': epoch, 'train_loss': running / len(loader), **metrics,
               'lr': scheduler.get_last_lr()[0], 'train_sec': round(train_sec, 1)}
        with log_path.open('a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=row.keys())
            if f.tell() == 0:
                w.writeheader()
            w.writerow(row)

        state['epoch'], state['epoch_sec'] = epoch, state['epoch_sec'] + [round(train_sec, 1)]
        if metrics['val_macro_f1'] > state['best_f1']:
            state.update(best_f1=metrics['val_macro_f1'], best_epoch=epoch, bad_epochs=0)
            torch.save({'model': model.state_dict(), 'config': cfg, 'epoch': epoch, 'val': metrics}, best_path)
            mark = ' (best)'
        else:
            state['bad_epochs'] += 1
            mark = ''
        print(f'epoch {epoch}: train_loss {row["train_loss"]:.4f}, val macro-F1 {metrics["val_macro_f1"]:.4f}, '
              f'bal_acc {metrics["val_bal_acc"]:.4f}, {train_sec:.0f}s{mark}')
        if state['bad_epochs'] >= cfg['patience']:
            print(f'Early stopping: {cfg["patience"]} epoch không cải thiện')
            state['finished'] = True
        state['finished'] |= state['epoch'] >= cfg['epochs']
        torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                    'scheduler': scheduler.state_dict(), 'state': state}, last_path)

    best = torch.load(best_path, map_location='cpu', weights_only=False)
    model.load_state_dict(best['model'])
    write_predictions(model, cfg, mean, std, eval_sets(df, split_col))
    summary = {'run_name': run, 'best_epoch': state['best_epoch'], 'best_val_macro_f1': state['best_f1'],
               'epochs_run': state['epoch'], 'mean_epoch_sec': float(np.mean(state['epoch_sec'])),
               'peak_vram_gb': round(torch.cuda.max_memory_allocated() / 2**30, 2),
               'n_train': len(train_df), 'n_val': len(val_df)}
    (log_dir / f'{run}.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    last_path.unlink()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
