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
import importlib.metadata
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
from src.train.provenance import (add_path_arguments, apply_overrides, inspect_run,
                                 make_provenance, output_root, require_same)


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def save_checkpoint(value,path):
    temp=path.with_suffix(path.suffix+'.tmp')
    torch.save(value,temp)
    temp.replace(path)


def smoke_subset(df, split_col, seed):
    """Vài chục ảnh mỗi lớp để kiểm tra pipeline từ đầu đến cuối, không dùng kết quả."""
    take = {'train': 32, 'val': 16}  # Technical smoke must not evaluate xtest.
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
    add_path_arguments(parser)
    args = parser.parse_args()
    cfg = apply_overrides(yaml.safe_load(open(args.config, encoding='utf-8')), args)
    if args.smoke:
        cfg.update(run_name=cfg['run_name'] + '_smoke', epochs=2, warmup_epochs=1, technical_smoke=True)
        cfg.setdefault('_output_root', 'outputs/trials')
    run = cfg['run_name']
    provenance = make_provenance(cfg)
    run_state = inspect_run(cfg, provenance)
    if run_state == 'complete':
        print(f'{run}: complete, same frozen data and recipe; no training repeated')
        return
    if not torch.cuda.is_available():
        raise RuntimeError('Training requires CUDA. Run tools/check_training.py --tensor-check --forward --device cpu for a CPU preflight.')
    if cfg['amp_dtype'] == 'bfloat16' and not torch.cuda.is_bf16_supported():
        raise RuntimeError('GPU does not support the configured bfloat16 recipe')
    ckpt_dir, log_dir = output_root(cfg) / 'checkpoints', output_root(cfg) / 'logs'
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    best_path, last_path, log_path = ckpt_dir / f'{run}.pt', ckpt_dir / f'{run}.last.pt', log_dir / f'{run}.csv'

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
                        persistent_workers=cfg['num_workers'] > 0, generator=gen)
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
        require_same(provenance, last.get('provenance'), 'Last checkpoint')
        model.load_state_dict(last['model'])
        optimizer.load_state_dict(last['optimizer'])
        scheduler.load_state_dict(last['scheduler'])
        state = last['state']
        print(f'Tiếp tục từ epoch {state["epoch"]} (best macro-F1 {state["best_f1"]:.4f} ở epoch {state["best_epoch"]})')

    (log_dir / f'{run}.provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')

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
            save_checkpoint({'model': model.state_dict(), 'config': cfg, 'epoch': epoch, 'val': metrics,
                        'provenance': provenance}, best_path)
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
        save_checkpoint({'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                    'scheduler': scheduler.state_dict(), 'state': state,
                    'provenance': provenance}, last_path)

    best = torch.load(best_path, map_location='cpu', weights_only=False)
    require_same(provenance, best.get('provenance'), 'Best checkpoint')
    model.load_state_dict(best['model'])
    sets = {'val_smoke': val_df} if args.smoke else eval_sets(df, split_col)
    write_predictions(model, cfg, mean, std, sets, provenance=provenance)
    summary = {'run_name': run, 'best_epoch': state['best_epoch'], 'best_val_macro_f1': state['best_f1'],
               'epochs_run': state['epoch'], 'mean_epoch_sec': float(np.mean(state['epoch_sec'])),
               'peak_vram_gb': round(torch.cuda.max_memory_allocated() / 2**30, 2),
               'n_train': len(train_df), 'n_val': len(val_df), 'provenance': provenance,
               'technical_smoke': bool(args.smoke),
               'runtime': {'torch': torch.__version__, 'cuda': torch.version.cuda,
                           'timm': importlib.metadata.version('timm'),
                           'gpu': torch.cuda.get_device_name(0)}}
    (log_dir / f'{run}.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    last_path.unlink()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
