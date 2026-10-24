"""Decode and checksum the actual five source datasets, including excluded data."""
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.catalog import collect
from tools.prepare import write_csv

def main():
 cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text());rows=collect(ROOT/'data',cfg)
 counts=Counter(r['source'] for r in rows)
 expected={'LC25000':25000,'BreakHis':7909,'LungHist700':691,'CRC-VAL-HE-7K':7180,'BACH':400}
 if counts!=expected:raise ValueError(dict(counts))
 errors=[];checksums=[];dimensions=defaultdict(Counter)
 def one(row):
  p=ROOT/'data'/row['source_image_path']
  try:
   with Image.open(p) as im:
    im.load();w,h=im.size;mode=im.mode
   with p.open('rb') as f:checksum=hashlib.file_digest(f,'sha256').hexdigest()
   return {**{k:row[k] for k in ['source_image_path','source']},'sha256':checksum,
           'width':w,'height':h,'mode':mode,'bytes':p.stat().st_size},None
  except Exception as e:return None,{'source_image_path':row['source_image_path'],'error':repr(e)}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for i,(record,error) in enumerate(pool.map(one,rows),1):
   if error:errors.append(error)
   else:
    checksums.append(record);dimensions[record['source']][f"{record['width']}x{record['height']}:{record['mode']}"]+=1
   if i%5000==0:print('RAW_AUDIT',i,len(rows),flush=True)
 write_csv(ROOT/'splits/raw_checksums.csv',checksums)
 summary={'raw_images':len(rows),'source_counts':dict(counts),'dimensions':dict(dimensions),
   'selected_counts':dict(Counter(r['source'] for r in rows if r['included'])),
   'excluded_reasons':dict(Counter(r['source']+':'+r['exclusion_reason'] for r in rows if not r['included'])),
   'errors':errors,'status':'passed' if not errors else 'failed'}
 (ROOT/'results/raw_audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print('RAW_AUDIT_DONE',json.dumps(summary),flush=True)
 if errors:raise SystemExit(1)

if __name__=='__main__':main()
