import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.data.paths import historical_path, resolve_data_root

ROOT = Path(__file__).resolve().parents[1]
TMP = Path(os.environ.get('BTL_TEST_TMP_ROOT', ROOT / 'outputs/test_tmp'))
TMP.mkdir(parents=True, exist_ok=True)


class DatasetLocationTests(unittest.TestCase):
    def test_separate_local_data_and_explicit_override(self):
        with tempfile.TemporaryDirectory(dir=TMP) as value, patch.dict(os.environ, {}, clear=True):
            root = Path(value)
            (root/'configs').mkdir()
            external = root.parent / 'image_store'
            (root/'configs/paths.local.json').write_text(json.dumps({'data_root': str(external)}))
            self.assertEqual(resolve_data_root(root, 'data'), external.resolve())
            self.assertEqual(resolve_data_root(root, 'other_data'), (root/'other_data').resolve())

    def test_environment_and_explicit_path_precedence(self):
        with tempfile.TemporaryDirectory(dir=TMP) as value:
            root = Path(value)
            with patch.dict(os.environ, {'BTL_DATA_ROOT': str(root/'environment_images')}):
                self.assertEqual(resolve_data_root(root), (root/'environment_images').resolve())
                self.assertEqual(resolve_data_root(root, root/'explicit_images'), (root/'explicit_images').resolve())

    def test_portable_default_does_not_create_data(self):
        with tempfile.TemporaryDirectory(dir=TMP) as value, patch.dict(os.environ, {}, clear=True):
            root = Path(value)
            self.assertEqual(resolve_data_root(root), root/'data')
            self.assertFalse((root/'data').exists())

    def test_invalid_local_config_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory(dir=TMP) as value, patch.dict(os.environ, {}, clear=True):
            root = Path(value)
            (root/'configs').mkdir()
            (root/'configs/paths.local.json').write_text('{"data_root": ""}')
            with self.assertRaises(ValueError): resolve_data_root(root)

    def test_old_audit_paths_use_retained_original_copy(self):
        with tempfile.TemporaryDirectory(dir=TMP) as value:
            root = Path(value)
            mapping = root/'outputs/reorganization_2026-10-25/relocation_map.json'
            mapping.parent.mkdir(parents=True)
            old = str(root/'old/file.csv')
            retained = str(root/'snapshots/file.csv')
            mapping.write_text(json.dumps({old: {'target': str(root/'current.csv'), 'preserved_copy': retained}}))
            self.assertEqual(historical_path(old, root), Path(retained))
            self.assertEqual(historical_path(root/'unmoved.csv', root), root/'unmoved.csv')
