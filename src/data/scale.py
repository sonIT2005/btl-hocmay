"""Scale metadata comes from configuration, including per-magnification status."""
import math


def scale_metadata(config, source, magnification=None):
    entry = config['scale'][source]
    status = entry['status']
    if source == 'LungHist700':
        if magnification not in (20, 40):
            raise ValueError('LungHist700 magnification must be 20 or 40')
        mpp = entry[f'mpp_{magnification}x']
        status = entry.get(f'status_{magnification}x', status)
    elif source == 'BreakHis':
        magnification = magnification or config['breakhis_magnification']
        values = entry['mpp_by_magnification']
        mpp = values.get(magnification, values.get(str(magnification)))
        if mpp is None:
            raise ValueError(f'Missing configured BreakHis MPP at {magnification}x')
    else:
        mpp = entry['mpp']
    mpp = float(mpp)
    if not math.isfinite(mpp) or mpp <= 0:
        raise ValueError(f'Invalid MPP for {source}: {mpp}')
    return mpp, status


def scale_limitations(config):
    limitations = []
    for source in config['scale']:
        for mag in ([20, 40] if source == 'LungHist700' else [None]):
            mpp, status = scale_metadata(config, source, mag)
            if status.startswith('estimated'):
                name = source + (f' {mag}x' if mag else '')
                limitations.append(f'{name}: {mpp:g} MPP, {status}; physical scale remains estimated, not calibrated.')
    return limitations
