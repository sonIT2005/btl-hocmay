"""Validate the actual handoff and both image branches, then optionally freeze."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime,timezone
import numpy as np
import yaml
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.paths import resolve_data_root
DATA_ROOT = resolve_data_root(ROOT)
from src.data.scale import scale_limitations

def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    global DATA_ROOT
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--data-root', help='Existing raw/processed image directory');args=parser.parse_args()
    DATA_ROOT=resolve_data_root(ROOT,args.data_root)
    rows=read_csv(ROOT/'splits/splits.csv');inventory=read_csv(ROOT/'splits/inventory.csv')
    cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text(encoding='utf-8'))
    errors=[];warnings=[]
    required={'image_path','label','organ','source','group_id','split','split_random'}
    if not required.issubset(rows[0]):errors.append('Required columns missing')
    if len({r['image_path'] for r in rows})!=len(rows):errors.append('Duplicate sample paths')
    if set(r['label'] for r in rows)!=set(map(str,range(7))):errors.append('Missing target classes')
    groups=defaultdict(set);patients=defaultdict(set)
    for row in rows:
        if row['split'] not in {'train','val','test','xtest'}:errors.append('Bad split')
        if row['label'] not in map(str,range(7)):errors.append('Bad label')
        else:
            organ=['lung','lung','lung','colon','colon','breast','breast'][int(row['label'])]
            if row['organ']!=organ:errors.append('Label/organ mismatch')
        groups[row['group_id']].add(row['split'])
        if row['patient_id']:patients[(row['source'],row['patient_id'])].add(row['split'])
        if row['source'] in {'LungHist700','CRC-VAL-HE-7K','BACH'} and row['split']!='xtest':errors.append('External data entered internal split')
    if any(len(v)>1 for v in groups.values()):errors.append('Family crosses grouped splits')
    if any(len(v)>1 for v in patients.values()):errors.append('Patient crosses grouped splits')
    ext_sources={r['source_image_path'] for r in inventory if r['included']=='True'}
    with_samples={r['source_image_path'] for r in rows}
    missing_sources=sorted(ext_sources-with_samples)
    if missing_sources:warnings.append({'source_images_without_accepted_patches':missing_sources})
    reference=json.loads((ROOT/'configs/reference.json').read_text())
    if reference['split']!='train' or not any(r['source_image_path']==reference['source_image_path'] and r['split']=='train' for r in rows):
        errors.append('Reference not in internal training split')
    none=read_csv(ROOT/'splits/splits_none.csv');mac=read_csv(ROOT/'splits/splits_macenko.csv')
    if len(none)!=len(rows) or len(mac)!=len(rows):errors.append('Unpaired branches')
    for a,b in zip(none,mac):
        if any(a[k]!=b[k] for k in required-{'image_path'}):errors.append('Branches differ in labels/splits')
    for label in map(str,range(7)):
        if {r['split'] for r in rows if r['label']==label and r['source'] in {'LC25000','BreakHis'}}!={'train','val','test'}:
            errors.append(f'Internal class {label} missing a split')
    audit_path=ROOT/'results/raw_audit.json'
    if not audit_path.exists() or json.loads(audit_path.read_text())['status']!='passed':
        errors.append('Full raw-data audit is missing or failed')
    targets=[(DATA_ROOT/r['image_path'], 'none') for r in rows]+[(DATA_ROOT/r['image_path_macenko'],'macenko') for r in rows]
    def inspect(item):
        path,branch=item
        try:
            with Image.open(path) as im:
                im.load()
                if im.size!=(224,224) or im.mode!='RGB':return {'path':str(path),'error':'Wrong dimensions/mode'}
                a=np.asarray(im)
                return branch,float(np.mean(np.all(a<10,axis=2))),float(np.mean(np.all(a>245,axis=2))),sha(path),path.relative_to(DATA_ROOT).as_posix()
        except Exception as e:return {'path':str(path),'error':repr(e)}
    stats=defaultdict(Counter);image_checksums=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,value in enumerate(pool.map(inspect,targets),1):
            if isinstance(value,dict):errors.append(value)
            else:
                branch,black,white,digest,relative_path=value
                image_checksums.append({'image_path':relative_path,'branch':branch,'sha256':digest})
                stats[branch]['images']+=1
                stats[branch]['near_black_gt95pct']+=int(black>.95)
                stats[branch]['near_white_gt95pct']+=int(white>.95)
            if i%10000==0:print('VALIDATE_IMAGES',i,len(targets),flush=True)
    if stats['macenko']['near_black_gt95pct']>stats['none']['near_black_gt95pct']:
        errors.append('Normalization introduced nearly all-black samples')
    with (ROOT/'splits/processed_checksums.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['image_path','branch','sha256']);writer.writeheader();writer.writerows(image_checksums)
    quarantine=[r for r in inventory if r['exclusion_reason']=='family_assignment_requires_review']
    quarantine_paths={r['source_image_path'] for r in quarantine}
    if quarantine_paths&with_samples:errors.append('Quarantined sources entered model manifests')
    result={'sample_rows':len(rows),'image_files_decoded':len(targets),'group_overlap_count':sum(len(v)>1 for v in groups.values()),
        'patient_overlap_count':sum(len(v)>1 for v in patients.values()),'branch_statistics':dict(stats),
        'by_source':dict(Counter(r['source'] for r in rows)),'by_label_split':dict(Counter(r['label']+':'+r['split'] for r in rows)),
        'lc_images_pending_family_review':len(quarantine),
        'errors':errors,'warnings':warnings,'status':'passed_with_identity_and_scale_limitations' if not errors else 'failed',
        'limitations':scale_limitations(cfg)+['LC25000 groups reconstruct augmentation families, not patient identities.',
                       'CRC/BACH published patch/image identifiers do not guarantee patient-independent bootstrap.',
                       f'{len(quarantine)} LC25000 images are retained separately pending reliable family assignment.']}
    (ROOT/'results/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('VALIDATION_DONE',json.dumps(result),flush=True)
    if errors:raise SystemExit(1)
    if args.freeze:
        names=['splits/splits.csv','splits/splits_none.csv','splits/splits_macenko.csv','splits/lc_groups.csv',
               'splits/label_map.json','splits/raw_checksums.csv','splits/inventory.csv',
               'splits/grouping_review_required.csv','results/source_metadata.json',
               'splits/processed_checksums.csv',
               'configs/preparation.yaml','configs/reference.json','results/grouping_summary.json']
        names+=['src/data/stain.py','src/data/catalog.py','src/data/scale.py','tools/prepare.py','tools/group_lc.py']
        frozen={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'status':result['status'],
                'sha256':{n:sha(ROOT/n) for n in names},'sample_rows':len(rows),'limitations':result['limitations']}
        (ROOT/'splits/FROZEN.json').write_text(json.dumps(frozen,indent=2),encoding='utf-8')

if __name__=='__main__':main()
