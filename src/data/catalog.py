"""Source-specific labels and identities. All paths are relative to data/."""
from __future__ import annotations
from pathlib import Path
import csv
import re
from src.data.scale import scale_metadata

CLASS_NAMES=['lung_benign','lung_aca','lung_scc','colon_benign','colon_aca','breast_benign','breast_malignant']
ORGANS=['lung','lung','lung','colon','colon','breast','breast']
MAPPINGS={
 'LC25000':{'lung_n':0,'lung_aca':1,'lung_scc':2,'colon_n':3,'colon_aca':4},
 'LungHist700':{'nor':0,'aca_bd':1,'aca_md':1,'aca_pd':1,'scc_bd':2,'scc_md':2,'scc_pd':2},
 'CRC-VAL-HE-7K':{'NORM':3,'TUM':4},
 'BACH':{'Normal':5,'Benign':5,'InSitu':6,'Invasive':6},
 'BreakHis':{'B':5,'M':6},
}
BREAKHIS_RE=re.compile(r'SOB_([BM])_([A-Z]+)-(\d{2})-([^-]+)-(40|100|200|400)-(\d+)\.png$',re.I)

def parse_breakhis(name):
    match=BREAKHIS_RE.fullmatch(name)
    if not match:raise ValueError(f'Unknown BreakHis filename: {name}')
    cls,subtype,year,slide,mag,seq=match.groups()
    number=re.match(r'\d+',slide)
    if number is None:raise ValueError(name)
    # AB/CD section suffixes must not create separate patient groups.
    return {'original_label':cls.upper(),'subtype':subtype,'patient_id':f'{year}-{slide}',
            'case_group_id':f'{year}-{number.group()}',
            'slide_id':f'{year}-{slide}','magnification':int(mag),
            'grouping_status':'conservative_numeric_case_sections_collapsed'}

def collect(data,config):
    data=Path(data);rows=[]
    for path in sorted((data/'raw/LC25000').rglob('*.jpeg')):
        label=MAPPINGS['LC25000'][path.parent.name]
        rows.append(make_record(data,path,'LC25000',path.parent.name,label,config))
    for path in sorted((data/'raw/BreakHis').rglob('*.png')):
        if not path.name.startswith('SOB_'):continue
        meta=parse_breakhis(path.name)
        label=MAPPINGS['BreakHis'][meta['original_label']]
        row=make_record(data,path,'BreakHis',meta['original_label'],label,config,meta['magnification'])
        row.update(meta);row['group_id']='BreakHis:'+meta['case_group_id']
        row['included']=meta['magnification']==config['breakhis_magnification']
        row['exclusion_reason']='' if row['included'] else 'unselected_magnification'
        rows.append(row)
    base=data/'raw/LungHist700'
    if (base/'data.csv').exists():
        with (base/'data.csv').open(encoding='utf-8-sig',newline='') as f:
            for meta in csv.DictReader(f):
                label_name=meta['superclass']+('_'+meta['subclass'] if meta['subclass'] else '')
                stem=f"{label_name}_{meta['resolution']}_{meta['image_id']}"
                path=base/'images'/label_name/(stem+'.jpg')
                if not path.exists():raise FileNotFoundError(path)
                row=make_record(data,path,'LungHist700',label_name,MAPPINGS['LungHist700'][label_name],config,int(meta['resolution'][:-1]))
                row.update(patient_id=meta['patient_id'],magnification=int(meta['resolution'][:-1]),
                           group_id='LungHist700:'+stem,split='xtest')
                rows.append(row)
    for path in sorted((data/'raw/CRC-VAL-HE-7K').rglob('*.tif')):
        name=path.parent.name;label=MAPPINGS['CRC-VAL-HE-7K'].get(name)
        row=make_record(data,path,'CRC-VAL-HE-7K',name,label,config)
        row.update(group_id='CRC-VAL-HE-7K:'+path.stem,split='xtest',
                   included=label is not None,exclusion_reason='' if label is not None else 'out_of_scope_tissue')
        rows.append(row)
    bach_truth={}
    truth_files=list((data/'raw/BACH').rglob('microscopy_ground_truth.csv'))
    if truth_files:
        if len(truth_files)!=1:raise ValueError('Multiple BACH ground-truth files')
        with truth_files[0].open(encoding='utf-8-sig',newline='') as f:
            bach_truth={name.strip():label.strip() for name,label in csv.reader(f)}
    for path in sorted((data/'raw/BACH').rglob('*.tif')):
        name=path.parent.name
        if name not in MAPPINGS['BACH']:raise ValueError(f'Unknown BACH label: {name}')
        if bach_truth and bach_truth.get(path.name)!=name:
            raise ValueError(f'BACH folder/ground-truth mismatch: {path.name}')
        row=make_record(data,path,'BACH',name,MAPPINGS['BACH'][name],config)
        row.update(group_id='BACH:'+path.stem,split='xtest')
        rows.append(row)
    return rows

def make_record(data,path,source,original_label,label,config,magnification=None):
    mpp,status=scale_metadata(config,source,magnification)
    return {'source_image_path':path.relative_to(data).as_posix(),'source':source,
        'original_label':original_label,'label':label if label is not None else '',
        'organ':ORGANS[label] if label is not None else 'colon',
        'group_id':'','patient_id':'','case_group_id':'','grouping_status':'','subtype':'',
        'slide_id':'','magnification':'','split':'',
        'included':True,'exclusion_reason':'','native_mpp':mpp,'scale_status':status}

