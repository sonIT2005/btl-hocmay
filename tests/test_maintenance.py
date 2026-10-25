import copy
import csv
import hashlib
import io
import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import yaml

from src.data.catalog import collect
from src.data.scale import scale_metadata, scale_limitations
from src.train.provenance import inspect_run, make_provenance
from src.train.predict import prediction_frame
from src.train.train import save_checkpoint, smoke_subset
from tools.measure_mpp import KNOWN, MEASUREMENT_COLUMNS, analyze, write_csv
from tools.prepare import preserve_existing_splits, processing_signature, require_regeneration_opt_in

ROOT = Path(__file__).resolve().parents[1]
TEST_TMP=Path(os.environ.get('BTL_TEST_TMP_ROOT',ROOT/'outputs/test_tmp'))
TEST_TMP.mkdir(parents=True,exist_ok=True)


class ScaleRegressionTests(unittest.TestCase):
    def setUp(self):
        self.cfg = yaml.safe_load((ROOT / 'configs/preparation.yaml').read_text(encoding='utf-8'))

    def test_collect_uses_lc_mpp_and_status(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            path = Path(folder) / 'raw/LC25000/colon_image_sets/colon_aca/a.jpeg'
            path.parent.mkdir(parents=True); path.touch()
            self.cfg['scale']['LC25000'].update(mpp=.31, status='estimated_reference_cell')
            row = collect(folder, self.cfg)[0]
            self.assertEqual(row['native_mpp'], .31)
            self.assertEqual(row['scale_status'], 'estimated_reference_cell')

    def test_all_breakhis_magnifications_from_config(self):
        for mag, expected in [(40, .49), (100, .2), (200, .1), (400, .05)]:
            self.assertEqual(scale_metadata(self.cfg, 'BreakHis', mag)[0], expected)
        self.cfg['scale']['BreakHis']['mpp_by_magnification'][100] = .21
        self.assertEqual(scale_metadata(self.cfg, 'BreakHis', 100)[0], .21)

    def test_lunghist_status_per_magnification_and_estimated_limitations(self):
        self.cfg['scale']['LungHist700']['status_20x'] = 'estimated_reference_cell'
        self.assertEqual(scale_metadata(self.cfg, 'LungHist700', 20)[1], 'estimated_reference_cell')
        self.assertEqual(scale_metadata(self.cfg, 'LungHist700', 40)[1], 'estimated_unverified')
        self.assertTrue(any('estimated_reference_cell' in s for s in scale_limitations(self.cfg)))

    def test_invalid_mpp_is_rejected(self):
        self.cfg['scale']['LC25000']['mpp'] = 0
        with self.assertRaises(ValueError): scale_metadata(self.cfg, 'LC25000')

    def test_prepare_blocked_without_opt_in(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            path = Path(folder) / 'splits/FROZEN.json'
            path.parent.mkdir(); path.write_text('{}')
            with self.assertRaises(RuntimeError): require_regeneration_opt_in(folder, False)
            require_regeneration_opt_in(folder, True)

    def test_catalog_change_changes_processing_signature(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            for name in ['src/data/stain.py', 'src/data/catalog.py', 'src/data/scale.py', 'tools/prepare.py']:
                path = Path(folder) / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('old')
            before = processing_signature(folder, {}, 'ref')
            (Path(folder) / 'src/data/catalog.py').write_text('new')
            self.assertNotEqual(before, processing_signature(folder, {}, 'ref'))

    def test_existing_splits_preserved_and_missing_sources_rejected(self):
        row = dict(source_image_path='a', label=0, organ='lung', source='LC25000', group_id='g')
        prior = {**row, 'split': 'train', 'split_random': 'test'}
        rows = [dict(row)]; preserve_existing_splits(rows, [prior])
        self.assertEqual(rows[0]['split_random'], 'test')
        with self.assertRaises(ValueError): preserve_existing_splits([], [prior])
        with self.assertRaises(ValueError): preserve_existing_splits([{**row, 'group_id': 'changed'}], [prior])


class RunGuardTests(unittest.TestCase):
    def fixture(self, root):
        split = root / 'splits'; split.mkdir()
        manifest = split / 'splits_none.csv'
        manifest.write_text('image_path,label,organ,source,group_id,split,split_random\nprocessed/abc/none/a.png,0,lung,LC25000,g,train,train\n')
        labels = split / 'label_map.json'; labels.write_text('{}')
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        (split / 'FROZEN.json').write_text(json.dumps({'sha256': {'splits/splits_none.csv': sha(manifest), 'splits/label_map.json': sha(labels)}}))
        return dict(run_name='probe', splits_dir='splits', data_root='data', stain='none', model='convnext', seed=0)

    def test_modified_manifest_fails_before_run(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root = Path(folder); cfg = self.fixture(root)
            make_provenance(cfg, root)
            with (root / 'splits/splits_none.csv').open('a') as f: f.write('\n')
            with self.assertRaises(ValueError): make_provenance(cfg, root)

    def test_legacy_complete_run_cannot_be_skipped(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root = Path(folder); cfg = self.fixture(root); p = make_provenance(cfg, root)
            log = root / 'outputs/logs/probe.json'; log.parent.mkdir(parents=True); log.write_text('{}')
            with self.assertRaises(ValueError): inspect_run(cfg, p, root)
            self.assertEqual(log.read_text(), '{}')

    def test_complete_run_requires_same_recipe_and_checkpoint(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root = Path(folder); cfg = self.fixture(root); p = make_provenance(cfg, root)
            log = root / 'outputs/logs/probe.json'; log.parent.mkdir(parents=True); log.write_text(json.dumps({'provenance': p}))
            ckpt = root / 'outputs/checkpoints/probe.pt'; ckpt.parent.mkdir(parents=True); ckpt.touch()
            preds=root/'outputs/predictions';preds.mkdir()
            for name in ['test','LungHist700','CRC-VAL-HE-7K','BACH']:
                (preds/f'probe__{name}.csv').write_text('header\n')
            self.assertEqual(inspect_run(cfg, p, root), 'complete')
            changed = make_provenance({**cfg, 'seed': 2}, root)
            with self.assertRaises(ValueError): inspect_run(cfg, changed, root)

    def test_resume_requires_matching_sidecar(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root = Path(folder); cfg = self.fixture(root); p = make_provenance(cfg, root)
            checkpoints = root / 'outputs/checkpoints'; checkpoints.mkdir(parents=True)
            (checkpoints / 'probe.last.pt').touch(); (checkpoints / 'probe.pt').touch()
            with self.assertRaises(ValueError): inspect_run(cfg, p, root)
            sidecar = root / 'outputs/logs/probe.provenance.json'; sidecar.parent.mkdir(parents=True)
            sidecar.write_text(json.dumps(p))
            self.assertEqual(inspect_run(cfg, p, root), 'resume')

    def test_probability_export_preserves_tiny_class_ordering(self):
        probs = np.array([[.01, .01, .01, 1.1e-7, 1.4e-7, .01, .96 - 2.5e-7]], dtype=np.float32)
        df = pd.DataFrame({'image_path': ['a'], 'group_id': ['g'], 'label': [4]})
        pred = prediction_frame(probs, df, {'num_classes': 7, 'run_name': 'probe'}, 'test')
        stream = io.StringIO(); pred.to_csv(stream, index=False, float_format='%.17g'); stream.seek(0)
        saved = pd.read_csv(stream)
        self.assertGreater(saved.prob_4.iloc[0], saved.prob_3.iloc[0])

    def test_technical_smoke_contains_only_internal_train_val(self):
        df=pd.DataFrame([{'split':s,'label':k} for s in ['train','val','test','xtest'] for k in range(7)])
        subset=smoke_subset(df,'split',0)
        self.assertEqual(set(subset.split),{'train','val'})

    def test_interrupted_checkpoint_write_preserves_previous_checkpoint(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            path=Path(folder)/'old.pt';path.write_bytes(b'previous checkpoint')
            def fail(value,temp):
                temp.write_bytes(b'partial')
                raise OSError('simulated interrupted write')
            with patch('src.train.train.torch.save',side_effect=fail):
                with self.assertRaises(OSError):save_checkpoint({},path)
            self.assertEqual(path.read_bytes(),b'previous checkpoint')


class MeasurementTests(unittest.TestCase):
    def kit(self, root, images=16, cells=2, distort=False, ref_variation=False):
        candidates = []; measurements = []
        for source in [*KNOWN, 'LC25000']:
            mpp = KNOWN.get(source, .25)
            for image in range(images):
                cid = source + str(image)
                organ = 'lung' if source == 'LC25000' and image < images // 2 else 'colon'
                candidates.append(dict(candidate_id=cid, source=source, image_path=cid+'.png', group_id=cid,
                                       organ=organ, magnification='', stratum=source, width=100, height=100))
                diameter = 7 / mpp
                if distort and source == 'BACH': diameter *= 1.7
                if ref_variation and source in KNOWN: diameter *= 1 + .04 * np.sin(image)
                for cell in range(cells):
                    measurements.append(dict(zip(MEASUREMENT_COLUMNS, [cid+str(cell), cid, 'rbc', 5, 5, 5+diameter, 5,
                                          diameter, '', '', 'person_a', 'person_b', 'checked', 'synthetic test fixture'])))
        write_csv(root/'candidates.csv', candidates, list(candidates[0]))
        write_csv(root/'measurements.csv', measurements, MEASUREMENT_COLUMNS)
        write_csv(root/'image_review.csv', [dict(candidate_id=r['candidate_id'], decision='eligible', note='synthetic') for r in candidates], ['candidate_id','decision','note'])
        protocol = dict(candidate_sha256=hashlib.sha256((root/'candidates.csv').read_bytes()).hexdigest(),
                        cell_types_separate=['rbc','lymph_nucleus'], max_cells_per_image=3, review_seed=43,
                        review_fraction=.2, min_cells=30, expanded_min_cells=60, min_images=15,
                        min_lc_cells_per_organ=15, max_loo_error=.15, bootstrap_repeats=80, bootstrap_seed=42)
        (root/'protocol.json').write_text(json.dumps(protocol))
        (root/'protocol.sha256').write_text(hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest())

    def test_reference_recovery_is_not_automatic_calibration(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root); report=analyze(root)
            self.assertEqual(report['status'], 'reference_consistency_passed')
            self.assertAlmostEqual(report['targets']['LC25000']['mpp_estimate'], .25)
            self.assertFalse(report['applies_config_changes'])

    def test_reference_uncertainty_is_in_bootstrap(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root, ref_variation=True); report=analyze(root)
            lo,hi=report['targets']['LC25000']['ci95_sampling_only']
            self.assertGreater(hi,lo)

    def test_failed_method_expands_once_then_stops(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root, images=20, cells=3, distort=True)
            self.assertEqual(analyze(root)['status'], 'needs_one_expansion')
            self.assertEqual(analyze(root,stage='expanded')['status'], 'method_rejected_keep_current_mpp')

    def test_cell_types_are_not_pooled(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root)
            self.assertEqual(analyze(root,cell_type='lymph_nucleus')['status'], 'incomplete')

    def test_no_independent_review_blocks_estimation(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root)
            text=(root/'measurements.csv').read_text(encoding='utf-8-sig').replace('person_b,checked', ',')
            (root/'measurements.csv').write_text(text,encoding='utf-8-sig')
            result=analyze(root)
            self.assertEqual(result['status'],'incomplete'); self.assertTrue(result['review_measurement_ids'])

    def test_locked_protocol_cannot_be_edited_to_force_pass(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root)
            (root/'protocol.json').write_text('{}')
            with self.assertRaises(ValueError): analyze(root)

    def test_same_person_and_out_of_bounds_coordinates_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as folder:
            root=Path(folder); self.kit(root)
            text=(root/'measurements.csv').read_text(encoding='utf-8-sig')
            (root/'measurements.csv').write_text(text.replace('person_b','PERSON_A'),encoding='utf-8-sig')
            with self.assertRaises(ValueError): analyze(root)
            (root/'measurements.csv').write_text(text.replace(',5,5,',',-1,5,',1),encoding='utf-8-sig')
            with self.assertRaises(ValueError): analyze(root)


if __name__ == '__main__':
    unittest.main()
