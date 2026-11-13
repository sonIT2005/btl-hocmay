"""Render the E2 seed-0 comparison from the frozen split and the C5 predictions."""
import argparse
import json
import random
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import yaml
from PIL import Image, ImageDraw, ImageFont
from torch import Tensor

from src.train.data import ManifestDataset, eval_sets, load_manifest
from src.train.models import build_model, norm_stats
from src.train.provenance import make_provenance, require_same, sha256


class Run(NamedTuple):
    name: str
    architecture: str
    layer: str
    model: torch.nn.Module
    dataset: ManifestDataset
    predictions: pd.DataFrame


class Cam(NamedTuple):
    predicted: int
    probs: list[float]
    overlay: Image.Image
    grid: np.ndarray
    positive_max: float


def read_run(code: Path, repo: Path, data: Path, architecture: str, layer: str) -> Run:
    name = f'e2_{architecture}_group_none_s0'
    cfg = yaml.safe_load((code / 'configs/runs' / f'{name}.yaml').read_text(encoding='utf-8'))
    if (cfg['run_name'], cfg['model'], cfg['split'], cfg['stain'], cfg['seed']) != (
        name, architecture, 'group', 'none', 0
    ):
        raise ValueError(f'{name}: config does not describe the requested E2 run')
    cfg.update(data_root=str(data), splits_dir=str(repo / 'splits'))
    provenance = make_provenance(cfg, code)
    log = json.loads((code / 'outputs/logs' / f'{name}.json').read_text(encoding='utf-8'))
    checkpoint = torch.load(repo / f'{name}.pt', map_location='cpu', weights_only=True)
    require_same(provenance, log['provenance'], name + ' log')
    require_same(provenance, checkpoint['provenance'], name + ' checkpoint')
    if checkpoint['epoch'] != log['best_epoch']:
        raise ValueError(f'{name}: checkpoint epoch does not match the C5 log')
    model = build_model(architecture, cfg['num_classes'], pretrained=False)
    model.load_state_dict(checkpoint['model'], strict=True)
    model.eval().requires_grad_(False)
    manifest, split_col = load_manifest(cfg)
    frames = []
    for key, subset in eval_sets(manifest, split_col).items():
        path = code / 'outputs/predictions' / f'{name}__{key}.csv'
        pred = pd.read_csv(path).set_index('image_path', verify_integrity=True)
        expected = subset.set_index('image_path', verify_integrity=True)
        if set(pred.index) != set(expected.index):
            raise ValueError(f'{path}: rows differ from the frozen {key} split')
        pred = pred.loc[expected.index]
        if not (pred.true_label.eq(expected.label).all() and pred.group_id.eq(expected.group_id).all()
                and pred.test_set.eq(key).all() and pred.run_name.eq(name).all()):
            raise ValueError(f'{path}: labels, groups or run identity differ')
        frames.append(pred.assign(source=expected.source, dataset_row=expected.index.map(
            pd.Series(subset.index, index=subset.image_path))))
    predictions = pd.concat(frames, verify_integrity=True)
    mean, std = norm_stats(model)
    print(f'{name}: strict load, provenance and epoch {checkpoint["epoch"]} verified', flush=True)
    return Run(name, architecture, layer, model, ManifestDataset(manifest, cfg, mean, std, False), predictions)


def select_samples(conv: pd.DataFrame, swin: pd.DataFrame, seed: int) -> list[str]:
    rng = random.Random(seed)
    used_groups: set[str] = set()
    chosen: list[str] = []
    for correct in (True, False):
        for key in ('test', 'LungHist700', 'CRC-VAL-HE-7K', 'BACH'):
            eligible = conv.test_set.eq(key) & conv.pred_label.eq(conv.true_label).eq(correct)
            eligible &= swin.pred_label.eq(swin.true_label).eq(correct)
            pool = conv.loc[eligible & ~conv.group_id.isin(used_groups)]
            # Choose a group uniformly before choosing a patch so large images do not dominate.
            group = rng.choice(sorted(pool.group_id.unique()))
            path = rng.choice(sorted(pool.index[pool.group_id.eq(group)]))
            chosen.append(path)
            used_groups.add(group)
    return chosen


def compute_cam(run: Run, path: str, rgb: Image.Image) -> Cam:
    row = run.predictions.loc[path]
    x, label = run.dataset[int(row.dataset_row)]
    if label != row.true_label or tuple(x.shape) != (3, 224, 224):
        raise ValueError(f'{path}: unexpected loader label or shape')
    captured: list[Tensor] = []
    hook = run.model.get_submodule(run.layer).register_forward_hook(
        lambda module, inputs, output: captured.append(output))
    try:
        logits = run.model(x.unsqueeze(0).requires_grad_(True))
    finally:
        hook.remove()
    if len(captured) != 1 or tuple(logits.shape) != (1, 7) or not torch.isfinite(logits).all():
        raise ValueError(f'{run.name}: unexpected activation or logits for {path}')
    activation = captured[0]
    target = int(logits.argmax(dim=1).item())
    if target != row.pred_label:
        raise ValueError(f'{run.name}: FP32 argmax {target} differs from C5 {row.pred_label} for {path}')
    gradient, = torch.autograd.grad(logits[0, target], activation)
    if run.architecture == 'swin':
        activation = activation.permute(0, 3, 1, 2)
        gradient = gradient.permute(0, 3, 1, 2)
    if tuple(activation.shape) != (1, 768, 7, 7) or not torch.isfinite(gradient).all():
        raise ValueError(f'{run.name}: unexpected activation shape or gradient for {path}')
    raw = (gradient.mean(dim=(2, 3), keepdim=True) * activation.detach()).sum(1).relu()
    low, high = raw.min().item(), raw.max().item()
    if not np.isfinite(high) or high <= low:
        raise ValueError(f'{run.name}: constant or invalid Grad-CAM for {path}')
    grid = ((raw - low) / (high - low)).unsqueeze(1)
    mask = F.interpolate(grid, (224, 224), mode='bilinear', align_corners=False)[0, 0].numpy()
    # Use strength as opacity. Zero is transparent, high values are orange.
    weight = 0.68 * mask[..., None]
    overlay = Image.fromarray(np.round((1 - weight) * np.asarray(rgb)
                                      + weight * np.array([255, 108, 18])).astype(np.uint8))
    return Cam(target, logits.detach().softmax(1)[0].tolist(), overlay, grid[0, 0].numpy(), high)


def render_panel(sample_id: str, row: pd.Series, rgb: Image.Image, cams: list[Cam],
                 labels: dict[str, str]) -> Image.Image:
    panel = Image.new('RGB', (830, 345), '#f5f7fa')
    draw = ImageDraw.Draw(panel)
    heading = ImageFont.truetype('arialbd.ttf', 23)
    font = ImageFont.truetype('arial.ttf', 18)
    status = 'ĐÚNG' if cams[0].predicted == row.true_label else 'SAI'
    test_name = 'Nội bộ' if row.test_set == 'test' else 'Test chéo'
    draw.text((18, 12), f'{sample_id}  |  {row.source} · {test_name}  |  {status}',
              fill='#101827', font=heading)
    for x, title, im, details in zip((18, 292, 566), ('Ảnh đầu vào', 'ConvNeXt-Tiny', 'Swin-Tiny'),
                                     (rgb, *(cam.overlay for cam in cams)),
                                     (f'Nhãn: {labels[str(row.true_label)]}', *(
                                         f'{labels[str(c.predicted)]} ({c.probs[c.predicted]:.1%})' for c in cams)),
                                     strict=True):
        draw.text((x, 48), title, fill='#142038', font=heading)
        panel.paste(im, (x, 79))
        draw.text((x, 313), details, fill='#142038', font=font)
    return panel


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('repo', 'upstream-snapshot', 'data-root', 'out'):
        parser.add_argument(f'--{argument}', type=Path, required=True)
    parser.add_argument('--selection-seed', type=int, required=True)
    args = parser.parse_args()
    repo, code, data, out = (p.resolve() for p in
                             (args.repo, args.upstream_snapshot, args.data_root, args.out))
    torch.set_num_threads(4)
    runs = [read_run(code, repo, data, 'convnext', 'stages.3.blocks.2'),
            read_run(code, repo, data, 'swin', 'layers.3.blocks.1.norm1')]
    paths = select_samples(runs[0].predictions, runs[1].predictions, args.selection_seed)
    frozen = json.loads((repo / 'splits/FROZEN.json').read_text(encoding='utf-8'))
    checksums_path = repo / 'splits/processed_checksums.csv'
    if sha256(checksums_path) != frozen['sha256']['splits/processed_checksums.csv']:
        raise ValueError('Processed checksums differ from FROZEN')
    checksums = pd.read_csv(checksums_path).set_index('image_path', verify_integrity=True).sha256
    labels = json.loads((repo / 'splits/label_map.json').read_text(encoding='utf-8'))['classes']
    extended = pd.read_csv(repo / 'splits/splits.csv', usecols=['image_path', 'source_image_path'])
    extended = extended.set_index('image_path', verify_integrity=True)
    if sha256(repo / 'splits/splits.csv') != frozen['sha256']['splits/splits.csv']:
        raise ValueError('Extended manifest differs from FROZEN')

    records = []
    panels = []
    grids = {}
    for index, path in enumerate(paths, 1):
        row = runs[0].predictions.loc[path]
        digest = sha256(data / path)
        if digest != checksums[path]:
            raise ValueError(f'{path}: image checksum differs from frozen data')
        with Image.open(data / path) as source:
            rgb = source.convert('RGB')
        sample_id = f'CAM-{index:02}'
        cams = [compute_cam(run, path, rgb) for run in runs]
        panels.append(render_panel(sample_id, row, rgb, cams, labels))
        record = {'id': sample_id, 'eval_set': row.test_set, 'source': row.source,
                  'group_id': row.group_id, 'image_path': path, 'sha256': digest,
                  'source_image_path': extended.loc[path, 'source_image_path'],
                  'true_label': labels[str(row.true_label)], 'both_correct': cams[0].predicted == row.true_label}
        for run, cam in zip(runs, cams, strict=True):
            prefix = run.architecture
            published = run.predictions.loc[path]
            record[prefix + '_label'] = labels[str(cam.predicted)]
            record[prefix + '_p_fp32'] = cam.probs[cam.predicted]
            record[prefix + '_p_c5'] = published[f'prob_{cam.predicted}']
            record[prefix + '_max_prob_abs_diff'] = float(np.max(np.abs(
                np.array(cam.probs) - published[[f'prob_{k}' for k in range(7)]].to_numpy(dtype=float))))
            record[prefix + '_cam_positive_max'] = cam.positive_max
            grids[f'{sample_id}_{prefix}'] = cam.grid
        records.append(record)
        print(sample_id, row.test_set, record['true_label'], record['convnext_label'],
              record['swin_label'], flush=True)
    out.mkdir(parents=True, exist_ok=False)
    for record, panel in zip(records, panels, strict=True):
        panel.save(out / f'{record["id"]}.png', dpi=(200, 200))
    for filename, images in (('gradcam_4_dung.png', panels[:4]), ('gradcam_4_sai.png', panels[4:])):
        figure = Image.new('RGB', (1668, 698), '#dee4ec')
        for index, panel in enumerate(images):
            figure.paste(panel, ((index % 2) * 838, (index // 2) * 353))
        figure.save(out / filename, dpi=(200, 200))
    pd.DataFrame(records).to_csv(out / 'samples.csv', index=False)
    np.savez_compressed(out / 'cam_grids.npz', **grids)
    metadata = {'selection_seed': args.selection_seed, 'torch': torch.__version__,
                'manifest_sha256': sha256(repo / 'splits/splits_none.csv'),
                'frozen_sha256': sha256(repo / 'splits/FROZEN.json'),
                'runs': [{'name': run.name, 'layer': run.layer,
                          'checkpoint_sha256': sha256(repo / f'{run.name}.pt')} for run in runs]}
    (out / 'provenance.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
