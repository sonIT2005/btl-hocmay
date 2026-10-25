"""Separate project metadata/code from the existing image dataset, without links/copies."""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_data_root(project_root=PROJECT_ROOT, configured=None):
    """Explicit custom path > BTL_DATA_ROOT > ignored local config > project/data.

    The conventional config value 'data' means the default dataset location;
    use an absolute path when explicitly selecting project/data over a local override.
    """
    root = Path(project_root).resolve()
    value = None
    if configured is not None and str(configured).replace('\\', '/').rstrip('/') not in ('', 'data', './data'):
        value = str(configured)
    if value is None:
        value = os.environ.get('BTL_DATA_ROOT')
    local = root / 'configs/paths.local.json'
    if not value and local.exists():
        value = json.loads(local.read_text(encoding='utf-8-sig')).get('data_root')
        if not isinstance(value, str) or not value.strip():
            raise ValueError('paths.local.json must contain a non-empty data_root string')
    if not value:
        value = 'data'
    path = Path(value).expanduser()
    return (path if path.is_absolute() else root / path).resolve()


def historical_path(path, project_root=PROJECT_ROOT):
    """Locate retained original bytes named by an audit created before the move."""
    original = Path(path)
    mapping = Path(project_root) / 'outputs/reorganization_2026-10-25/relocation_map.json'
    if mapping.is_file():
        entries = json.loads(mapping.read_text(encoding='utf-8-sig'))
        key = str(original).replace('\\', '/').casefold()
        for name, entry in entries.items():
            if name.replace('\\', '/').casefold() == key:
                return Path(entry.get('preserved_copy', entry['target']))
    return original
