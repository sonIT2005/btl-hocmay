"""Reproducible C1-C3 handoff, with paired preprocessing and strict validation."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from PIL import Image,ImageOps
from threadpoolctl import threadpool_limits
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.catalog import collect,CLASS_NAMES,MAPPINGS
from src.data.stain import MacenkoNormalizer,StainError

def write_csv(path,rows,columns=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        fieldnames=columns or list(dict.fromkeys(k for row in rows for k in row))
        writer=csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader();writer.writerows(rows)

def assign_splits(rows,seed,balance_trials=2048):
    groups=defaultdict(list)
    for row in rows:
        if row['included'] and row['source'] in {'LC25000','BreakHis'}:
            if not row['group_id']:raise ValueError('Missing internal group')
            groups[(row['label'],row['source'])].append(row)
    for key,records in sorted(groups.items()):
        ids=sorted({x['group_id'] for x in records})
        rng=np.random.default_rng(seed+int(key[0]))
        # Largest-remainder quotas avoid floor/floor/remainder bias for small
        # patient strata. Choose a seeded assignment balancing sample counts too.
        targets=np.array([.70,.15,.15])*len(ids)
        quota=np.floor(targets).astype(int)
        for j in np.argsort(-(targets-quota),kind='stable')[:len(ids)-quota.sum()]:quota[j]+=1
        if min(quota)<1:raise ValueError(f'Too few independent groups for {key}')
        weights=Counter(r['group_id'] for r in records)
        values=np.array([weights[g] for g in ids]);sample_targets=np.array([.70,.15,.15])*len(records)
        a=int(quota[0]);b=a+int(quota[1]);best=None;best_score=float('inf')
        for _ in range(balance_trials):
            order=rng.permutation(len(ids));w=values[order]
            sizes=np.array([w[:a].sum(),w[a:b].sum(),w[b:].sum()])
            score=float(np.abs(sizes-sample_targets).sum())
            if score<best_score:best,best_score=order.copy(),score
            if score<=2:break
        ordered=[ids[j] for j in best]
        decisions={g:'train' if i<a else 'val' if i<b else 'test' for i,g in enumerate(ordered)}
        for row in records:row['split']=decisions[row['group_id']]
        # E1's intentional image-random control is distinct from the grouped split.
        order=sorted(records,key=lambda x:x['source_image_path'])
        rng=np.random.default_rng(seed+100+int(key[0]));perm=rng.permutation(len(order))
        a=int(len(order)*.70);b=a+int(len(order)*.15)
        for i,j in enumerate(perm):order[j]['split_random']='train' if i<a else 'val' if i<b else 'test'
    for row in rows:
        row.setdefault('split_random','')
        if row['split']=='xtest':row['split_random']='xtest'

def scaled_image(row,cfg):
    with Image.open(ROOT/'data'/row['source_image_path']) as im:im=im.convert('RGB')
    factor=float(row['native_mpp'])/cfg['target_mpp']
    if abs(factor-1)>1e-6:
        im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
    return im

def windows(im,external,size,stride):
    if im.width<size or im.height<size:raise ValueError('Image smaller than target field of view')
    if external:
        for y in range(0,im.height-size+1,stride):
            for x in range(0,im.width-size+1,stride):yield (x,y,x+size,y+size)
    else:
        x=(im.width-size)//2;y=(im.height-size)//2
        yield (x,y,x+size,y+size)

def choose_reference(rows,cfg):
    # Stable candidate order; only internal training data can be considered.
    candidates=sorted((r for r in rows if r['source']=='LC25000' and r['split']=='train'),
                      key=lambda r:r['source_image_path'])
    for row in candidates:
        im=scaled_image(row,cfg);box=next(windows(im,False,cfg['image_size'],cfg['patch_stride']))
        crop=np.array(im.crop(box))
        if np.mean(~np.all(crop>cfg['white_threshold'],axis=2))<.70:continue
        normalizer=MacenkoNormalizer(**{k:cfg['normalization'][k] for k in ['alpha','beta','max_condition_number']})
        try:normalizer.fit(np.asarray(im))
        except StainError:continue
        reference_pixels=np.asarray(im)
        reference_id=hashlib.sha256(reference_pixels.tobytes()).hexdigest()[:16]
        path=ROOT/f'data/processed/references/{reference_id}.png';path.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(reference_pixels).save(path)
        record={'source_image_path':row['source_image_path'],'group_id':row['group_id'],
            'split':row['split'],'crop_bbox_scaled':[0,0,im.width,im.height],'reference_image':path.relative_to(ROOT/'data').as_posix(),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'basis_condition_number':float(np.linalg.cond(normalizer.target_basis)),
            'beta_used':normalizer.target_beta_used,
            'target_basis':normalizer.target_basis.tolist(),'target_concentrations':normalizer.target_concentrations.tolist()}
        (ROOT/'configs/reference.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        return normalizer,record
    raise RuntimeError('No numerical-quality training reference')

def process_source(row,cfg,normalizer):
    im=scaled_image(row,cfg)
    source_profile=normalizer.profile(np.asarray(im))
    external=row['source'] in {'LungHist700','BACH'}
    samples=[];rejected=0
    for box in windows(im,external,cfg['image_size'],cfg['patch_stride']):
        x,y,_,_=box;crop=np.array(im.crop(box))
        tissue=float(np.mean(~np.all(crop>cfg['white_threshold'],axis=2)))
        if external and tissue<cfg['min_tissue_ratio']:
            rejected+=1;continue
        rel=Path(row['source'])/Path(row['source_image_path']).parent.name/(Path(row['source_image_path']).stem+f'__x{x}_y{y}.png')
        pnone=Path('processed')/cfg['processing_signature']/'none'/rel
        pmac=Path('processed')/cfg['processing_signature']/'macenko'/rel
        none=ROOT/'data'/pnone;mac=ROOT/'data'/pmac
        if not (none.exists() and mac.exists()):
            normalized=normalizer.transform(crop,source_profile=source_profile)
            for dest,array in [(none,crop),(mac,normalized)]:
                dest.parent.mkdir(parents=True,exist_ok=True)
                tmp=dest.with_suffix('.part.png');Image.fromarray(array).save(tmp,compress_level=1);tmp.replace(dest)
        sample={'image_path':pnone.as_posix(),'label':row['label'],'organ':row['organ'],'source':row['source'],
            'group_id':row['group_id'],'split':row['split'],'split_random':row['split_random'],
            'image_path_macenko':pmac.as_posix(),'source_image_path':row['source_image_path'],
            'patient_id':row['patient_id'],'magnification':row['magnification'],'native_mpp':row['native_mpp'],
            'scale_status':row['scale_status'],'target_mpp':cfg['target_mpp'],
            'normalization_beta_used':source_profile['beta_used'],
            'normalization_sampling_stride':source_profile['sampling_stride'],
            'x_scaled':x,'y_scaled':y,'crop_size_scaled':cfg['image_size'],'tissue_ratio':round(tissue,6)}
        samples.append(sample)
    return samples,rejected

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--catalog-only',action='store_true');args=parser.parse_args()
    cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text())
    rows=collect(ROOT/'data',cfg)
    count=Counter(r['source'] for r in rows)
    for source,n in {'LC25000':25000,'BreakHis':7909,'LungHist700':691,'CRC-VAL-HE-7K':7180,'BACH':400}.items():
        if count[source]!=n:raise ValueError(f'{source}: expected {n}, found {count[source]}')
    (ROOT/'splits/label_map.json').write_text(json.dumps({'classes':dict(enumerate(CLASS_NAMES)),
        'dataset_mappings':MAPPINGS},indent=2),encoding='utf-8')
    if args.catalog_only:
        write_csv(ROOT/'splits/inventory.csv',rows)
        print('CATALOG_DONE',json.dumps(dict(count)),flush=True)
        return
    with (ROOT/'splits/lc_groups.csv').open(encoding='utf-8',newline='') as f:
        lc={r['source_image_path']:r for r in csv.DictReader(f)}
    quarantine=[]
    for row in rows:
        if row['source']=='LC25000':
            group=lc[row['source_image_path']];row['group_id']=group['group_id']
            if int(group['group_size'])<cfg['min_verified_lc_family_size']:
                row['included']=False;row['exclusion_reason']='family_assignment_requires_review'
                quarantine.append({**row,'group_size':group['group_size']})
    write_csv(ROOT/'splits/grouping_review_required.csv',quarantine or [],
              columns=list(quarantine[0]) if quarantine else ['source_image_path','group_id','group_size'])
    assign_splits(rows,cfg['seed'],cfg['split_balance_trials'])
    write_csv(ROOT/'splits/inventory.csv',rows)
    normalizer,reference=choose_reference(rows,cfg)
    signature_input=json.dumps(cfg,sort_keys=True)+reference['sha256']
    signature_input+=(ROOT/'src/data/stain.py').read_text()+(ROOT/'tools/prepare.py').read_text()
    cfg['processing_signature']=hashlib.sha256(signature_input.encode()).hexdigest()[:16]
    included=[r for r in rows if r['included']]
    all_samples=[];errors=[];rejected=0;start=time.time()
    def task(row):
        try:return process_source(row,cfg,normalizer),None
        except Exception as e:return None,{'source_image_path':row['source_image_path'],'error':repr(e)}
    with threadpool_limits(limits=1),ThreadPoolExecutor(max_workers=cfg['workers']) as pool:
        for i,(result,error) in enumerate(pool.map(task,included),1):
            if error:errors.append(error)
            else:
                samples,nreject=result;all_samples.extend(samples);rejected+=nreject
            if i%1000==0 or i==len(included):print('PREPROCESS',i,len(included),'SAMPLES',len(all_samples),'ERRORS',len(errors),f'{time.time()-start:.0f}s',flush=True)
    (ROOT/'results/preprocessing_errors.json').write_text(json.dumps(errors,indent=2),encoding='utf-8')
    if errors:raise RuntimeError(f'{len(errors)} sources failed. See results/preprocessing_errors.json; handoff not written.')
    all_samples.sort(key=lambda r:r['image_path'])
    write_csv(ROOT/'splits/splits.csv',all_samples)
    # Explicit two-branch manifests keep the required seven-column interface.
    columns=['image_path','label','organ','source','group_id','split','split_random']
    write_csv(ROOT/'splits/splits_none.csv',[{k:r[k] for k in columns} for r in all_samples],columns)
    write_csv(ROOT/'splits/splits_macenko.csv',[{k:r['image_path_macenko'] if k=='image_path' else r[k] for k in columns} for r in all_samples],columns)
    summary={'raw_counts':dict(count),'included_source_images':dict(Counter(r['source'] for r in included)),
        'model_samples':len(all_samples),'samples_by_source':dict(Counter(r['source'] for r in all_samples)),
        'samples_by_split':dict(Counter(r['split'] for r in all_samples)),
        'samples_by_label':dict(Counter(r['label'] for r in all_samples)),
        'tissue_rejected_patches':rejected,'reference':reference,'processing_signature':cfg['processing_signature'],
        'lc_images_pending_family_review':len(quarantine),
        'scale_limitation':'LC25000 and LungHist700 MPP are unverified estimates. Do not claim exact physical-scale matching.'}
    (ROOT/'results/preparation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('PREPARATION_DONE',json.dumps(summary),flush=True)

if __name__=='__main__':main()
