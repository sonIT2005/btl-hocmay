import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from src.eval.metrics import (K, cm_metrics, confusion, group_bootstrap, mean_sd, organ_auroc,
                              within_organ_predictions)


class MetricsTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(0)
        self.y_true = rng.integers(0, K, 500)
        self.y_pred = np.where(rng.random(500) < 0.7, self.y_true, rng.integers(0, K, 500))

    def test_confusion_metrics_match_sklearn(self):
        labels = np.unique(self.y_true)
        m = cm_metrics(confusion(self.y_true, self.y_pred), labels)
        self.assertAlmostEqual(m['accuracy'], accuracy_score(self.y_true, self.y_pred))
        self.assertAlmostEqual(m['balanced_accuracy'], balanced_accuracy_score(self.y_true, self.y_pred))
        self.assertAlmostEqual(m['macro_f1'], f1_score(self.y_true, self.y_pred, labels=labels, average='macro'))

    def test_macro_only_over_classes_present_in_truth(self):
        # Tập test chéo đại tràng: chỉ có lớp 3, 4; dự đoán sang lớp vú vẫn tính là sai.
        y_true, y_pred = np.array([3, 3, 4, 4]), np.array([3, 6, 4, 4])
        m = cm_metrics(confusion(y_true, y_pred), np.array([3, 4]))
        self.assertAlmostEqual(m['macro_f1'], f1_score(y_true, y_pred, labels=[3, 4], average='macro'))

    def test_within_organ_argmax_ignores_other_organs(self):
        probs = np.zeros((2, K))
        probs[0, [6, 3, 4]] = [0.8, 0.05, 0.15]  # mô đại tràng, argmax 7 lớp rơi vào vú
        probs[1, [0, 1]] = [0.4, 0.6]
        within = within_organ_predictions(probs, np.array([4, 0]))
        np.testing.assert_array_equal(within, [4, 1])

    def test_organ_auroc_uses_malignant_share(self):
        probs = np.zeros((4, K))
        probs[:, 3] = [0.9, 0.8, 0.2, 0.1]
        probs[:, 4] = 1 - probs[:, 3]
        self.assertAlmostEqual(organ_auroc(probs, np.array([3, 3, 4, 4]), 'colon'), 1.0)
        self.assertTrue(np.isnan(organ_auroc(probs, np.array([3, 3, 3, 3]), 'colon')))

    def test_group_bootstrap_reports_invalid_resamples(self):
        y_true = np.array([0] * 10 + [5])
        y_pred = y_true.copy()
        groups = np.array(['a'] * 10 + ['b'])
        out = group_bootstrap(y_true, y_pred, groups, np.array([0, 5]), 200, seed=1)
        self.assertEqual(out['n_groups'], 2)
        self.assertGreater(out['boot_invalid'], 0)  # nhiều lần lấy mẫu chỉ được nhóm 'a', thiếu lớp 5
        self.assertEqual(out['macro_f1_ci_low'], 1.0)

    def test_mean_sd_over_seeds(self):
        df = pd.DataFrame({'model': ['m'] * 3, 'acc': [0.8, 0.9, 1.0]})
        out = mean_sd(df, ['model'], ['acc'])
        self.assertAlmostEqual(out.acc_mean[0], 0.9)
        self.assertAlmostEqual(out.acc_sd[0], 0.1)
        self.assertEqual(out.n_seeds[0], 3)


if __name__ == '__main__':
    unittest.main()
