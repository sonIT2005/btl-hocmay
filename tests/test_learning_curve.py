import unittest

import pandas as pd

from src.eval.learning_curve import subsample_train


class LearningCurveSubsetTests(unittest.TestCase):
    def setUp(self):
        rows = [{'label': label, 'group_id': f'g{label}_{g}', 'split': 'train'}
                for label in range(3) for g in range(20) for _ in range(3)]
        rows += [{'label': 0, 'group_id': 'v0', 'split': 'val'}, {'label': 1, 'group_id': 't0', 'split': 'test'}]
        self.df = pd.DataFrame(rows)

    def train_groups(self, fraction):
        out = subsample_train(self.df, 'split', fraction)
        return set(out[out.split == 'train'].group_id)

    def test_keeps_fraction_of_groups_per_class_and_other_splits(self):
        out = subsample_train(self.df, 'split', 0.25)
        per_class = out[out.split == 'train'].groupby('label').group_id.nunique()
        self.assertEqual(per_class.tolist(), [5, 5, 5])
        self.assertEqual(len(out[out.split != 'train']), 2)  # val/test không bị cắt

    def test_subsets_are_nested(self):
        self.assertLess(self.train_groups(0.1), self.train_groups(0.25))
        self.assertLess(self.train_groups(0.25), self.train_groups(0.5))

    def test_whole_groups_only(self):
        out = subsample_train(self.df, 'split', 0.1)
        sizes = out[out.split == 'train'].groupby('group_id').size()
        self.assertTrue((sizes == 3).all())

    def test_full_fraction_returns_everything(self):
        self.assertEqual(len(subsample_train(self.df, 'split', 1.0)), len(self.df))


if __name__ == '__main__':
    unittest.main()
