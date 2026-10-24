from pathlib import Path
import unittest

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_runs():
    return [yaml.safe_load(p.read_text(encoding='utf-8')) for p in sorted((ROOT / 'configs/runs').glob('*.yaml'))]


class TrainConfigTests(unittest.TestCase):
    def test_fifteen_runs_with_shared_recipe(self):
        runs = load_runs()
        self.assertEqual(len(runs), 15)
        self.assertEqual(sum(r['experiment'] == 'e1' for r in runs), 3)
        base = yaml.safe_load((ROOT / 'configs/train_base.yaml').read_text(encoding='utf-8'))
        for r in runs:
            self.assertEqual(r['run_name'], '{experiment}_{model}_{split}_{stain}_s{seed}'.format(**r))
            self.assertEqual({k: r[k] for k in base}, base)  # R04: cùng công thức cho mọi lần chạy

    def test_stain_manifests_differ_only_in_image_path(self):
        none = pd.read_csv(ROOT / 'splits/splits_none.csv')
        macenko = pd.read_csv(ROOT / 'splits/splits_macenko.csv')
        cols = ['label', 'organ', 'source', 'group_id', 'split', 'split_random']
        self.assertTrue(none[cols].equals(macenko[cols]))
        self.assertTrue((none.image_path.str.replace('/none/', '/macenko/', n=1) == macenko.image_path).all())


if __name__ == '__main__':
    unittest.main()
