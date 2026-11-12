"""C5: tính metric từ predictions và log, bám theo slide "Model assessment" của môn.

    python -m src.eval.metrics
    python -m src.eval.metrics --pred-dir outputs/precalibration/full_precision/predictions \
        --logs-dir outputs/precalibration/logs --out outputs/eval_precalibration

Chỉ đọc file, không chọn model hay ngưỡng nào theo kết quả test (slide 6–7).
Đầu ra (outputs/eval/):
- tables/per_run.csv          mỗi run × tập: accuracy, balanced accuracy, macro-F1, log-loss, nhầm cơ quan,
                              accuracy trong cơ quan đúng, AUROC lành/ác, CI 95% bootstrap theo group_id
- tables/per_class.csv        precision, recall, F1, support từng lớp (accuracy che lớp yếu, slide 12)
- tables/per_organ.csv        metric theo cơ quan, dùng để tính Δ nội bộ − test chéo
- tables/summary_by_config.csv, per_class_by_config.csv, delta_by_config.csv
                              gộp các seed: mean ± SD (độ phân tán giữa các lần train, không phải CI; slide 25)
- tables/leakage_e1_vs_e2.csv chia ngẫu nhiên (E1) so với chia theo nhóm (E2), slide 33
- tables/dataset_summary.csv  số ảnh, số nhóm theo nguồn × split × lớp (báo cáo auditable, slide 57)
- tables/efficiency.csv       thời gian/epoch, VRAM, số epoch (đánh giá ngoài độ chính xác, slide 8)
- confusion/*.csv             confusion matrix 7×7 của mọi run × tập
- figures/confusion, figures/reliability (seed 0), figures/training_curves (theo epoch)
"""
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
CLASS_NAMES = ['lung_benign', 'lung_aca', 'lung_scc', 'colon_benign', 'colon_aca', 'breast_benign', 'breast_malignant']
K = len(CLASS_NAMES)
ORGAN_OF = np.array([0, 0, 0, 1, 1, 2, 2])
ORGANS = ['lung', 'colon', 'breast']
ORGAN_CLASSES = {o: np.flatnonzero(ORGAN_OF == i) for i, o in enumerate(ORGANS)}
MALIGNANT = {'lung': [1, 2], 'colon': [4], 'breast': [6]}
XTEST_ORGAN = {'LungHist700': 'lung', 'CRC-VAL-HE-7K': 'colon', 'BACH': 'breast'}
SET_ORDER = ['test', 'LungHist700', 'CRC-VAL-HE-7K', 'BACH']
RUN_RE = re.compile(r'^(?P<experiment>e\d)_(?P<model>[a-z0-9]+)_(?P<split>group|random)_(?P<stain>none|macenko)_s(?P<seed>\d+)$')
CONFIG_KEYS = ['experiment', 'model', 'split', 'stain']
SCALAR_METRICS = ['accuracy', 'balanced_accuracy', 'macro_f1', 'log_loss', 'organ_confusion',
                  'within_organ_accuracy', 'auroc_lung', 'auroc_colon', 'auroc_breast']


# ---------------------------------------------------------------- metric từ confusion matrix

def confusion(y_true, y_pred):
    cm = np.zeros((K, K), dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    return cm


def cm_metrics(cm, labels):
    """Accuracy, balanced accuracy, macro-F1 từ confusion matrix.

    Macro lấy trung bình đều trên các lớp có trong nhãn thật (`labels`): tập test chéo chỉ chứa lớp của
    một cơ quan, nên không tính các lớp vắng mặt vào trung bình.
    """
    tp = np.diag(cm).astype(float)
    support, predicted = cm.sum(1), cm.sum(0)
    with np.errstate(invalid='ignore', divide='ignore'):
        recall = np.where(support > 0, tp / support, np.nan)
        precision = np.where(predicted > 0, tp / predicted, 0.0)
        f1 = np.where(support + predicted > 0, 2 * tp / (support + predicted), 0.0)
    return {'accuracy': tp.sum() / cm.sum(), 'balanced_accuracy': float(np.mean(recall[labels])),
            'macro_f1': float(np.mean(f1[labels])), 'precision': precision, 'recall': recall,
            'f1': f1, 'support': support}


def within_organ_predictions(probs, y_true):
    """Argmax chỉ trong các lớp của cơ quan thật (mẫu số vẫn là toàn bộ mẫu)."""
    mask = ORGAN_OF[None, :] == ORGAN_OF[y_true][:, None]
    return np.where(mask, probs, -np.inf).argmax(1)


def organ_auroc(probs, y_true, organ):
    """AUROC lành/ác trong một cơ quan: điểm = P(ác) / P(cơ quan đó). Trả NaN nếu thiếu một trong hai nhóm."""
    rows = ORGAN_OF[y_true] == ORGANS.index(organ)
    if not rows.any():
        return np.nan
    cls = ORGAN_CLASSES[organ]
    y = np.isin(y_true[rows], MALIGNANT[organ])
    if y.all() or not y.any():
        return np.nan
    p = probs[rows]
    score = p[:, MALIGNANT[organ]].sum(1) / np.clip(p[:, cls].sum(1), 1e-12, None)
    return float(roc_auc_score(y, score))


def group_bootstrap(y_true, y_pred, groups, labels, n_boot, seed):
    """CI 95% percentile, lấy mẫu lại theo group_id (slide 48–51: đơn vị lấy mẫu phải là nhóm).

    Lần lặp thiếu hẳn một lớp của `labels` thì không tính được macro-F1: bỏ qua và báo số lần bị bỏ.
    """
    codes, group_index = np.unique(groups, return_inverse=True)
    per_group = np.zeros((len(codes), K, K), dtype=np.int64)
    np.add.at(per_group, (group_index, y_true, y_pred), 1)
    rng = np.random.default_rng(seed)
    stats, invalid = [], 0
    for _ in range(n_boot):
        cm = per_group[rng.integers(0, len(codes), len(codes))].sum(0)
        if (cm.sum(1)[labels] == 0).any():
            invalid += 1
            continue
        m = cm_metrics(cm, labels)
        stats.append([m['accuracy'], m['balanced_accuracy'], m['macro_f1']])
    out = {'n_groups': len(codes), 'boot_B': n_boot, 'boot_invalid': invalid}
    if stats:
        lo, hi = np.percentile(np.array(stats), [2.5, 97.5], axis=0)
        for i, name in enumerate(['accuracy', 'balanced_accuracy', 'macro_f1']):
            out[f'{name}_ci_low'], out[f'{name}_ci_high'] = lo[i], hi[i]
    return out


# ---------------------------------------------------------------- đánh giá một file predictions

def evaluate(df, n_boot, seed):
    y_true = df.true_label.to_numpy()
    y_pred = df.pred_label.to_numpy()
    probs = df[[f'prob_{k}' for k in range(K)]].to_numpy(dtype=float)
    if not np.array_equal(probs.argmax(1), y_pred):
        raise ValueError('pred_label không khớp argmax của xác suất')
    labels = np.unique(y_true)
    cm = confusion(y_true, y_pred)
    m = cm_metrics(cm, labels)
    within = within_organ_predictions(probs, y_true)
    row = {'n': len(df), 'accuracy': m['accuracy'], 'balanced_accuracy': m['balanced_accuracy'],
           'macro_f1': m['macro_f1'],
           'log_loss': float(-np.mean(np.log(np.clip(probs[np.arange(len(df)), y_true], 1e-15, 1)))),
           'organ_confusion': float(np.mean(ORGAN_OF[y_pred] != ORGAN_OF[y_true])),
           'within_organ_accuracy': float(np.mean(within == y_true))}
    for organ in ORGANS:
        row[f'auroc_{organ}'] = organ_auroc(probs, y_true, organ)
    if n_boot:
        row.update(group_bootstrap(y_true, y_pred, df.group_id.to_numpy(), labels, n_boot, seed))
    per_class = pd.DataFrame({'class': CLASS_NAMES, 'precision': m['precision'], 'recall': m['recall'],
                              'f1': m['f1'], 'support': m['support']})
    per_class = per_class[per_class.support > 0]
    organs = []
    for organ in ORGANS:
        rows = ORGAN_OF[y_true] == ORGANS.index(organ)
        if rows.any():
            om = cm_metrics(confusion(y_true[rows], y_pred[rows]), np.unique(y_true[rows]))
            organs.append({'organ': organ, 'n': int(rows.sum()), 'accuracy': om['accuracy'],
                           'macro_f1': om['macro_f1'], 'within_organ_accuracy': float(np.mean(within[rows] == y_true[rows]))})
    return row, per_class, pd.DataFrame(organs), cm, (probs.max(1), y_pred == y_true)


# ---------------------------------------------------------------- hình

def plot_confusion(cm, title, path):
    rows = cm.sum(1) > 0
    norm = cm[rows] / cm[rows].sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(7.5, 0.6 * rows.sum() + 1.8))
    ax.imshow(norm, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(K), CLASS_NAMES, rotation=40, ha='right')
    ax.set_yticks(range(rows.sum()), np.array(CLASS_NAMES)[rows])
    for i, r in enumerate(np.flatnonzero(rows)):
        for j in range(K):
            if cm[r, j]:
                ax.text(j, i, f'{cm[r, j]}\n{norm[i, j]:.0%}', ha='center', va='center', fontsize=7,
                        color='white' if norm[i, j] > 0.5 else 'black')
    ax.set_xlabel('Dự đoán')
    ax.set_ylabel('Nhãn thật')
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_reliability(confidence, correct, title, path, bins=10):
    """Reliability diagram cho độ tin cậy top-1 (slide 39: phân biệt tốt vẫn có thể hiệu chuẩn kém)."""
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(confidence, edges) - 1, 0, bins - 1)
    centers, accs, counts = [], [], []
    for b in range(bins):
        sel = idx == b
        if sel.any():
            centers.append(confidence[sel].mean()); accs.append(correct[sel].mean()); counts.append(int(sel.sum()))
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.plot([0, 1], [0, 1], '--', color='gray', linewidth=1, label='Hiệu chuẩn hoàn hảo')
    ax.plot(centers, accs, 'o-', label='Mô hình')
    for c, a, n in zip(centers, accs, counts):
        ax.annotate(str(n), (c, a), textcoords='offset points', xytext=(0, 6), ha='center', fontsize=7)
    ax.set_xlabel('Độ tin cậy dự đoán (top-1)')
    ax.set_ylabel('Tỷ lệ đúng thực tế')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc='upper left')
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_training_curves(logs, config, path):
    """Đường huấn luyện theo epoch. Đây KHÔNG phải learning curve theo cỡ tập train ở slide 42–43."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for seed, log in sorted(logs.items()):
        axes[0].plot(log.epoch, log.train_loss, label=f'seed {seed}')
        axes[1].plot(log.epoch, log.val_loss, label=f'seed {seed}')
        axes[2].plot(log.epoch, log.val_macro_f1, label=f'seed {seed}')
    for ax, title in zip(axes, ['Train loss', 'Val loss', 'Val macro-F1']):
        ax.set_title(title); ax.set_xlabel('Epoch'); ax.grid(alpha=0.3)
    axes[0].set_yscale('log')
    axes[2].legend(fontsize=8)
    fig.suptitle(config, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- gộp seed

def mean_sd(df, keys, metrics):
    """Mean ± SD qua các seed. SD mô tả độ phân tán giữa các lần train, không phải khoảng tin cậy."""
    g = df.groupby(keys, sort=False)[metrics]
    out = g.mean().add_suffix('_mean').join(g.std(ddof=1).add_suffix('_sd'))
    out['n_seeds'] = df.groupby(keys, sort=False).size()
    return out.reset_index()


def config_name(row):
    return '{experiment}_{model}_{split}_{stain}'.format(**row)


def dataset_summary(splits_dir):
    df = pd.read_csv(splits_dir / 'splits_none.csv')
    df['class'] = df.label.map(dict(enumerate(CLASS_NAMES)))
    rows = []
    for split_col in ['split', 'split_random']:
        g = df.groupby(['source', split_col, 'class'])
        part = g.size().rename('n_images').to_frame().join(g.group_id.nunique().rename('n_groups')).reset_index()
        part = part.rename(columns={split_col: 'split_value'})
        part.insert(0, 'split_column', split_col)
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def efficiency(logs_dir):
    rows = []
    for path in sorted(logs_dir.glob('*.json')):
        if path.name.endswith('.provenance.json') or not RUN_RE.match(path.stem):
            continue
        s = json.loads(path.read_text(encoding='utf-8'))
        rows.append({'run': s['run_name'], **RUN_RE.match(path.stem).groupdict(),
                     **{k: s.get(k) for k in ['epochs_run', 'best_epoch', 'best_val_macro_f1', 'mean_epoch_sec', 'peak_vram_gb']}})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- chạy

def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--pred-dir', default='outputs/predictions')
    parser.add_argument('--logs-dir', default='outputs/logs')
    parser.add_argument('--splits-dir', default='splits')
    parser.add_argument('--out', default='outputs/eval')
    parser.add_argument('--bootstrap', type=int, default=1000, help='Số lần bootstrap theo group_id; 0 để tắt')
    parser.add_argument('--seed', type=int, default=20261031)
    args = parser.parse_args()
    pred_dir, logs_dir, out = (ROOT / p for p in (args.pred_dir, args.logs_dir, args.out))
    tables, conf_dir = out / 'tables', out / 'confusion'
    figs = {name: out / 'figures' / name for name in ['confusion', 'reliability', 'training_curves']}
    for d in [tables, conf_dir, *figs.values()]:
        d.mkdir(parents=True, exist_ok=True)

    per_run, per_class, per_organ = [], [], []
    files = sorted(pred_dir.glob('*__*.csv'))
    for path in files:
        run, test_set = path.stem.split('__', 1)
        match = RUN_RE.match(run)
        if not match or test_set not in SET_ORDER:
            continue
        meta = {'run': run, 'set': test_set, **match.groupdict()}
        row, pc, po, cm, (confidence, correct) = evaluate(pd.read_csv(path), args.bootstrap, args.seed)
        per_run.append({**meta, **row})
        per_class.append(pc.assign(**meta))
        per_organ.append(po.assign(**meta))
        pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES).to_csv(conf_dir / f'{run}__{test_set}.csv')
        if meta['seed'] == '0':
            plot_confusion(cm, f'{run} · {test_set}', figs['confusion'] / f'{run}__{test_set}.png')
            if test_set == 'test':
                plot_reliability(confidence, correct, f'{run} · test nội bộ', figs['reliability'] / f'{run}__test.png')
        print(f"{run:32s} {test_set:>14s}  acc {row['accuracy']:.4f}  macro-F1 {row['macro_f1']:.4f}  "
              f"nhầm cơ quan {row['organ_confusion']:.1%}")
    if not per_run:
        raise SystemExit(f'Không tìm thấy file predictions hợp lệ trong {pred_dir}')

    per_run = pd.DataFrame(per_run)
    per_class = pd.concat(per_class, ignore_index=True)
    per_organ = pd.concat(per_organ, ignore_index=True)
    per_run.to_csv(tables / 'per_run.csv', index=False)
    per_class.to_csv(tables / 'per_class.csv', index=False)
    per_organ.to_csv(tables / 'per_organ.csv', index=False)

    summary = mean_sd(per_run, CONFIG_KEYS + ['set'], SCALAR_METRICS)
    summary.to_csv(tables / 'summary_by_config.csv', index=False)
    mean_sd(per_class, CONFIG_KEYS + ['set', 'class'], ['precision', 'recall', 'f1']).to_csv(
        tables / 'per_class_by_config.csv', index=False)

    # Δ = metric nội bộ (cùng cơ quan) − metric test chéo, tính trong từng run rồi mới gộp seed
    internal = per_organ[per_organ.set == 'test'].set_index(['run', 'organ'])
    deltas = []
    for _, r in per_organ[per_organ.set.isin(XTEST_ORGAN)].iterrows():
        key = (r.run, XTEST_ORGAN[r.set])
        if key not in internal.index:
            continue
        i = internal.loc[key]
        deltas.append({**{k: r[k] for k in ['run', 'set', *CONFIG_KEYS, 'seed']}, 'organ': key[1],
                       **{f'delta_{m}': i[m] - r[m] for m in ['accuracy', 'macro_f1', 'within_organ_accuracy']}})
    if deltas:
        mean_sd(pd.DataFrame(deltas), CONFIG_KEYS + ['set', 'organ'],
                ['delta_accuracy', 'delta_macro_f1', 'delta_within_organ_accuracy']).to_csv(
            tables / 'delta_by_config.csv', index=False)

    test_summary = summary[summary.set == 'test']
    leak = test_summary[(test_summary.model == 'convnext') & (test_summary['stain'] == 'none')]
    if set(leak.split) == {'random', 'group'}:
        leak.to_csv(tables / 'leakage_e1_vs_e2.csv', index=False)

    dataset_summary(ROOT / args.splits_dir).to_csv(tables / 'dataset_summary.csv', index=False)
    eff = efficiency(logs_dir)
    if not eff.empty:
        eff.to_csv(tables / 'efficiency.csv', index=False)

    logs = {}
    for path in sorted(logs_dir.glob('*.csv')):
        match = RUN_RE.match(path.stem)
        if match:
            logs.setdefault(config_name(match.groupdict()), {})[match['seed']] = pd.read_csv(path)
    for config, by_seed in logs.items():
        plot_training_curves(by_seed, config, figs['training_curves'] / f'{config}.png')

    cols = ['experiment', 'model', 'split', 'stain', 'set', 'n_seeds', 'accuracy_mean', 'macro_f1_mean',
            'macro_f1_sd', 'organ_confusion_mean', 'within_organ_accuracy_mean']
    print('\n' + summary[cols].to_string(index=False, float_format=lambda v: f'{v:.4f}'))
    print(f'\nĐã ghi bảng và hình vào {out}/')


if __name__ == '__main__':
    main()
