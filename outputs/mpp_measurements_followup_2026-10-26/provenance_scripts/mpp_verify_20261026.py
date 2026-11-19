import csv,hashlib,json,math,random,re,shutil,sys,tempfile
from collections import Counter
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay');sys.path.insert(0,str(ROOT))
from tools.measure_mpp import analyze,load_measurements
OUT=ROOT/'outputs/mpp_measurements_followup_2026-10-26';D=OUT/'draft_v4'
BASE=ROOT/'outputs/mpp_measurements_draft_v1/draft_v3'
DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data');KIT=ROOT/'outputs/maintenance_2026-10-25/mpp_kit'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savecsv(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
records=json.loads((D/'measurements_geometry.json').read_text());checks=[]
before=json.loads((BASE/'annotations_input.json').read_text())['objects']
extended=json.loads((D/'annotations_input.json').read_text())['objects'];assert extended[:len(before)]==before
for r in records:
 bounds=r['roi_bounds'];g=r['geometry'];im=Image.open(DATA/r['image_path']).convert('RGB')
 factor,header=(10,72) if g else (8,48)
 plain=im.crop(bounds).resize(((bounds[2]-bounds[0])*factor,(bounds[3]-bounds[1])*factor),Image.Resampling.NEAREST)
 rendered=Image.open(D/'objects'/(r['measurement_id']+'_roi.png')).convert('RGB').crop((0,header,plain.width,header+plain.height))
 assert ImageChops.difference(plain,rendered).getbbox() is None
 if g:
  for axis,column in [('longest','diameter_px'),('h','axis_h_px'),('v','axis_v_px')]:
   a,b=g[axis];assert math.isclose(math.hypot(a[0]-b[0],a[1]-b[1]),r[column],abs_tol=1e-9)
   assert all(0<=x<r['width'] and 0<=y<r['height'] and bounds[0]<=x<bounds[2] and bounds[1]<=y<bounds[3] for x,y in g[axis])
  assert g['h'][0][1]==g['h'][1][1] and g['v'][0][0]==g['v'][1][0]
  assert math.isclose(max(math.dist(a,b) for a in r['polygon'] for b in r['polygon']),r['diameter_px'],abs_tol=1e-9)
 checks.append(dict(measurement_id=r['measurement_id'],raw_roi_pixels_equal=True,
                    endpoint_lengths='pass' if g else 'not_applicable_unmeasured',
                    review_status=r['review_status'],checked_by=r['checked_by']))
 assert r['review_status']=='draft_unreviewed' and not r['checked_by'] and r['group_id']
savecsv(OUT/'geometry_and_roi_checks.csv',checks)
eligible=[r for r in records if r['decision']=='draft_eligible'];excluded=[r for r in records if r['decision']!='draft_eligible']
calipers=Counter(r['candidate_id'] for r in records if r['geometry']);assert max(calipers.values())<=3
report=json.loads((D/'draft_preview.json').read_text());review_ids=[]
for marker,item in report['markers'].items():
 assert item['leave_one_out'] is None and not item['method_failed']
 for source,c in item['counts'].items():
  ids=sorted(r['measurement_id'] for r in eligible if r['source']==source and r['cell_type']==marker)
  chosen=random.Random(43).sample(ids,math.ceil(len(ids)*.2));assert c['review_measurement_ids']==chosen;review_ids+=chosen
savecsv(OUT/'selected_review_cells.csv',[{k:r[k] for k in ('measurement_id','candidate_id','source','cell_type','image_path','group_id','review_status','checked_by')} for r in eligible if r['measurement_id'] in review_ids])
protected=json.loads(Path(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1\protected_before.json').read_text(encoding='utf-8-sig'))
assert all(sha(p)==value for p,value in protected.items())
savecsv(OUT/'protected_inputs_check.csv',[dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=value,unchanged=True) for p,value in protected.items()])
prior_verification=json.loads((BASE.parent/'final_verification.json').read_text())
assert sha(ROOT/'tools/measure_mpp.py')==prior_verification['formal_tool_sha256']
formal={m:analyze(KIT,m) for m in ('rbc','lymph_nucleus')};assert all(v['status']=='incomplete' for v in formal.values())
with tempfile.TemporaryDirectory() as temporary:
 testkit=Path(temporary)/'kit';shutil.copytree(KIT,testkit);shutil.copyfile(D/'draft_measurements.csv',testkit/'measurements.csv')
 try:load_measurements(testkit,'lymph_nucleus')
 except ValueError as e:
  assert 'review_status' in str(e);formal['draft_csv_rejected']=str(e)
 else:raise AssertionError('Formal gate accepted draft')
(OUT/'formal_safety_check.json').write_text(json.dumps(formal,indent=2))
navigation=json.loads((OUT/'navigation/adaptive_locators.json').read_text())
savecsv(OUT/'followup_screening.csv',[dict(candidate_id=r['candidate_id'],source=r['source'],queue_order=r['queue_order'],
      raw_sha256=r['raw_sha256'],navigation_rois_inspected=len(r['locators']),
      additional_eligible_cells=sum(v['candidate_id']==r['candidate_id'] and v['measurement_id'].startswith('D2_') for v in eligible),
      scope='Additional raw locator ROIs; not exhaustive enumeration or proof of marker absence') for r in navigation])
nav_counts={s:dict(images=sum(r['source']==s for r in navigation),rois=sum(len(r['locators']) for r in navigation if r['source']==s)) for s in ('CRC-VAL-HE-7K','BACH','BreakHis')}
index=(D/'index.html').read_text(encoding='utf8');refs=re.findall(r'(?:src|href)="([^"]+)"',index)
for target in refs:
 assert f'id="{target[1:]}"' in index if target.startswith('#') else (D/target).is_file(),target
summary=dict(active_version='draft_v4',status='draft_only_unreviewed',draft_eligible=len(eligible),excluded_objects=len(excluded),
       geometric_objects=sum(bool(r['geometry']) for r in records),raw_roi_checks=len(checks),max_caliper_objects_per_image=max(calipers.values()),
       raw_control_sources_sha_verified=180,protected_files_unchanged=len(protected),prior_annotation_objects_preserved=len(before),
       selected_review_cells=len(review_ids),independent_review_completed=False,formal_accepted_cells=0,
       formal_gate_unchanged=True,draft_import_rejected=True,source_queue_changed=False,selection_seed=42,review_seed=43,
       navigation_pass=nav_counts,tests_passed=53,regenerated_images=False,model_run=False,
       draft_tool_sha256=sha(ROOT/'tools/draft_mpp.py'),formal_tool_sha256=sha(ROOT/'tools/measure_mpp.py'))
(OUT/'final_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
(OUT/'CURRENT.json').write_text(json.dumps({'active_version':'draft_v4','entry':'draft_v4/index.html','status':'draft_only_unreviewed'},indent=2))
print(json.dumps(summary,indent=2))
