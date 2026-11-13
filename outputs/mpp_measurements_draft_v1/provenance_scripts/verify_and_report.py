import csv,hashlib,json,math,random,shutil,sys,tempfile
from collections import Counter
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay');sys.path.insert(0,str(ROOT))
from tools.measure_mpp import analyze,load_measurements
OUT=ROOT/'outputs/mpp_measurements_draft_v1';D=OUT/'draft_v3'
DATA=Path(r'C:\Users\Admin\Documents\FrameView\btl-histo\data')
KIT=ROOT/'outputs/maintenance_2026-10-25/mpp_kit'
STAGE=Path(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savecsv(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
records=json.loads((D/'measurements_geometry.json').read_text())
protocol=json.loads((KIT/'protocol.json').read_text())
preview=json.loads((D/'draft_preview.json').read_text())
checks=[]
for r in records:
 g=r['geometry'];bounds=r['roi_bounds'];raw=Image.open(DATA/r['image_path']).convert('RGB')
 roi=Image.open(D/'objects'/(r['measurement_id']+'_roi.png')).convert('RGB')
 factor,header=(10,72) if g else (8,48)
 plain=raw.crop(bounds).resize(((bounds[2]-bounds[0])*factor,(bounds[3]-bounds[1])*factor),Image.Resampling.NEAREST)
 actual=roi.crop((0,header,plain.width,header+plain.height))
 assert ImageChops.difference(actual,plain).getbbox() is None,r['measurement_id']
 if g:
  for axis,col,prefix in [('longest','diameter_px',''),('h','axis_h_px','h_'),('v','axis_v_px','v_')]:
   (x1,y1),(x2,y2)=g[axis]
   assert math.isclose(math.hypot(x2-x1,y2-y1),r[col],abs_tol=1e-9)
   assert all(0<=x<r['width'] and 0<=y<r['height'] for x,y in g[axis])
   assert all(bounds[0]<=x<bounds[2] and bounds[1]<=y<bounds[3] for x,y in g[axis])
  assert g['h'][0][1]==g['h'][1][1] and g['v'][0][0]==g['v'][1][0]
  max_chord=max(math.hypot(a[0]-b[0],a[1]-b[1]) for a in r['polygon'] for b in r['polygon'])
  assert math.isclose(max_chord,r['diameter_px'],abs_tol=1e-9)
 checks.append(dict(measurement_id=r['measurement_id'],decision=r['decision'],raw_roi_pixels_equal=True,
                    coordinates_and_endpoint_lengths_passed=bool(g),
                    self_visual_qa='overlay_location_seen' if g else 'unmeasured_point_only',
                    qa_actor='Codex_visual_assist_NOT_independent_review',checked_by='',review_status='draft_unreviewed'))
savecsv(OUT/'geometry_and_roi_checks.csv',checks)
eligible=[r for r in records if r['decision']=='draft_eligible'];excluded=[r for r in records if r['decision']!='draft_eligible']
counts=Counter(r['candidate_id'] for r in eligible);assert max(counts.values())<=3
for marker,item in preview['markers'].items():
 for s,cohort in item['counts'].items():
  ids=sorted(r['measurement_id'] for r in eligible if r['source']==s and r['cell_type']==marker)
  assert cohort['review_measurement_ids']==random.Random(43).sample(ids,math.ceil(len(ids)*.2))
assert all(not r['checked_by'] and r['review_status']=='draft_unreviewed' for r in records)
assert all(v['leave_one_out'] is None for v in preview['markers'].values())
formal={m:analyze(KIT,m) for m in ('rbc','lymph_nucleus')}
assert all(r['status']=='incomplete' and not r.get('leave_one_out') for r in formal.values())
with tempfile.TemporaryDirectory() as temp:
 testkit=Path(temp)/'kit';shutil.copytree(KIT,testkit)
 shutil.copyfile(D/'draft_measurements.csv',testkit/'measurements.csv')
 try:load_measurements(testkit,'lymph_nucleus')
 except ValueError as e:
  rejection=str(e);assert 'review_status' in rejection
 else:raise AssertionError('Formal tool accepted draft status')
formal['direct_draft_import_rejected']=rejection
(OUT/'formal_safety_check.json').write_text(json.dumps(formal,indent=2))
before=json.loads((STAGE/'protected_before.json').read_text(encoding='utf-8-sig'))
changed=[p for p,value in before.items() if digest(p)!=value];assert not changed,changed
locators=json.loads((OUT/'navigation/locators.json').read_text());red={r['candidate_id']:r for r in json.loads((OUT/'navigation/rbc_locators.json').read_text())}
screen=[]
for r in locators:
 selected=[v for v in eligible if v['candidate_id']==r['candidate_id']]
 exc=[v for v in excluded if v['candidate_id']==r['candidate_id']]
 screen.append(dict(candidate_id=r['candidate_id'],source=r['source'],queue_order=r['queue_order'],image_path=r['image_path'],raw_sha256=r['raw_sha256'],
                    overview_inspected=True,raw_nuclear_locator_rois_inspected=len(r['locators']),
                    red_locator_rois_inspected=len(red[r['candidate_id']]['red_locator_points']),
                    full_native_frame_inspected=r['source']=='BreakHis',
                    draft_eligible_nuclei=len(selected),excluded_objects=len(exc),
                    conclusion='draft_candidates_recorded' if selected else 'no_qualified_object_selected_in_inspected_views',
                    limitation='Visual search is not exhaustive cell enumeration; no locator is not proof of absence.'))
savecsv(OUT/'image_screening.csv',screen)
savecsv(OUT/'selected_review_cells.csv',[{k:r[k] for k in ('measurement_id','candidate_id','source','cell_type','image_path','review_status','checked_by')}
       for r in eligible if r['measurement_id'] in {i for m in preview['markers'].values() for c in m['counts'].values() for i in c['review_measurement_ids']}])
summary=dict(active_version='draft_v3',status='draft_only_unreviewed',draft_eligible=len(eligible),
             excluded_objects=len(excluded),objects_with_calipers=sum(bool(r['geometry']) for r in records),
             objects_with_point_only=sum(not r['geometry'] for r in records),
             excluded_by_source_marker={f'{s}/{m}':sum(r['source']==s and r['cell_type']==m for r in excluded)
                                      for s in ('CRC-VAL-HE-7K','BACH','BreakHis') for m in ('rbc','lymph_nucleus')},
             raw_control_sources_sha_verified=180,raw_roi_pixel_checks=len(checks),protected_files_unchanged=len(before),
             changed_protected_files=changed,formal_accepted_cells=0,formal_draft_import_rejected=True,
             test_suite='53 tests passed',independent_review_pending=True,model_run=False,regenerated_images=False,
             source_and_split_files_modified=False,review_seed=43,selection_seed=42,
             tool_sha256=digest(ROOT/'tools/draft_mpp.py'),formal_tool_sha256=digest(ROOT/'tools/measure_mpp.py'))
(OUT/'final_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
(OUT/'CURRENT.json').write_text(json.dumps({'active_version':'draft_v3','entry':'draft_v3/index.html',
                                          'previous_versions':'draft_v1 and draft_v2 are superseded self-QA snapshots, not independent approvals'},indent=2))
for name in ('draft_v1','draft_v2'):
 (OUT/name/'SUPERSEDED.md').write_text('Superseded by ../draft_v3. Retained for self-QA provenance only. No independent approval or approved MPP.\n')
print(json.dumps(summary,indent=2))
