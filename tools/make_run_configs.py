"""Sinh 15 config cho E1/E2 từ configs/train_base.yaml vào configs/runs/.

Mỗi file chứa đủ tham số (R09) để một lần chạy tự đứng được, không phụ thuộc file base.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [0, 1, 2]


def runs():
    for seed in SEEDS:
        yield dict(experiment='e1', model='convnext', split='random', stain='none', seed=seed)
    for model in ('convnext', 'swin'):
        for stain in ('none', 'macenko'):
            for seed in SEEDS:
                yield dict(experiment='e2', model=model, split='group', stain=stain, seed=seed)


def main():
    base = yaml.safe_load((ROOT / 'configs/train_base.yaml').read_text(encoding='utf-8'))
    out = ROOT / 'configs/runs'
    out.mkdir(parents=True, exist_ok=True)
    for run in runs():
        name = '{experiment}_{model}_{split}_{stain}_s{seed}'.format(**run)
        cfg = {'run_name': name, **run, **base}
        (out / f'{name}.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding='utf-8')
        print(name)


if __name__ == '__main__':
    main()
