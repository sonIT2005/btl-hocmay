"""Đọc manifest splits_{stain}.csv và nạp ảnh 224×224 đã xử lý sẵn ở C1–C3."""
from pathlib import Path
import random

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms.functional import pil_to_tensor

ROOT = Path(__file__).resolve().parents[2]
XTEST_SOURCES = ['LungHist700', 'CRC-VAL-HE-7K', 'BACH']


def load_manifest(cfg):
    df = pd.read_csv(ROOT / cfg['splits_dir'] / f"splits_{cfg['stain']}.csv")
    split_col = {'group': 'split', 'random': 'split_random'}[cfg['split']]
    return df, split_col


def eval_sets(df, split_col):
    """Tập test nội bộ + 3 tập test chéo, mỗi tập 1 file predictions."""
    sets = {'test': df[df[split_col] == 'test']}
    for source in XTEST_SOURCES:
        sets[source] = df[(df[split_col] == 'xtest') & (df.source == source)]
    return sets


def class_weights(labels, num_classes):
    counts = torch.bincount(torch.tensor(labels.to_numpy()), minlength=num_classes).float()
    return counts.sum() / (num_classes * counts)


class ManifestDataset(Dataset):
    """Chỉ dùng phép hình học (R05): xoay 90°, lật ngang, lật dọc."""

    def __init__(self, df, cfg, mean, std, train):
        self.paths = [ROOT / cfg['data_root'] / p for p in df.image_path]
        self.labels = df.label.tolist()
        self.aug = set(cfg['augmentation']) if train else set()
        self.mean = torch.tensor(mean).view(3, 1, 1)
        self.std = torch.tensor(std).view(3, 1, 1)

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        with Image.open(self.paths[i]) as im:
            x = pil_to_tensor(im.convert('RGB')).float().div_(255)
        if 'rot90' in self.aug:
            x = torch.rot90(x, random.randint(0, 3), dims=(1, 2))
        if 'hflip' in self.aug and random.random() < 0.5:
            x = x.flip(2)
        if 'vflip' in self.aug and random.random() < 0.5:
            x = x.flip(1)
        return (x - self.mean) / self.std, self.labels[i]
