import csv,json,sys
from pathlib import Path
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay');sys.path.insert(0,str(ROOT))
from tools.draft_mpp import geometry
OUT=ROOT/'outputs/mpp_measurements_followup_2026-10-26'
BASE=ROOT/'outputs/mpp_measurements_draft_v1/draft_v3'
payload=json.loads((BASE/'annotations_input.json').read_text())
rows=list(csv.DictReader((BASE/'locked_candidates.csv').open(encoding='utf-8-sig')))
targets={r['id']:r for r in json.loads((OUT/'navigation/grid_targets.json').read_text())}
def add(source,q,n,points,decision='draft_eligible',note=None,location=None):
 r=next(r for r in rows if r['source']==source and int(r['queue_order'])==q)
 ident=f'D2_{"CRC" if source.startswith("CRC") else source}_q{q:02d}_{n}'
 target=targets.get(ident)
 polygon=[list(map(int,v.split(','))) for v in points.split()] if points else []
 if polygon:geometry(polygon,int(r['width']),int(r['height']))
 if location is None:location=[target['cx'],target['cy']]
 payload['objects'].append(dict(measurement_id=ident,candidate_id=r['candidate_id'],cell_type='lymph_nucleus',
     decision=decision,polygon=polygon,location=location,evidence_grid_target=ident,
     boundary_uncertainty_px=1 if source.startswith('CRC') else 2,
     note=note or 'Additional raw visual inspection: separate small rounded/oval densely stained nucleus outside gland epithelium; draft identity and whole-boundary estimate remain unreviewed.'))
C='CRC-VAL-HE-7K';B='BACH'
add(C,18,1,'170,89 174,89 178,92 180,96 178,99 172,100 168,97 168,93')
add(C,44,1,'134,60 138,60 141,63 143,66 140,70 135,70 132,67 131,63')
add(C,36,1,'103,205 107,205 110,208 109,213 106,216 102,215 100,212 100,208',location=[104,210],
    note='Separate rounded/oval dark nucleus at (104,210) selected visually within the grid centred on (112,201). No threshold-mask boundary used; independent identity/boundary review pending.')
add(B,9,1,'1055,710 1059,711 1062,715 1061,720 1057,723 1052,722 1049,719 1050,715')
add(B,9,2,'555,208 559,208 563,212 563,217 559,222 554,222 550,218 550,212')
add(B,16,1,'1979,1378 1985,1379 1989,1383 1988,1390 1984,1395 1978,1395 1973,1391 1973,1384')
add(B,20,1,'480,1469 486,1469 491,1473 491,1480 487,1486 481,1486 476,1482 476,1475')
add(B,24,2,'1287,323 1292,324 1297,328 1298,334 1294,339 1288,341 1283,337 1282,329')
add(B,24,3,'773,155 780,155 785,158 786,165 782,172 776,174 769,170 767,163')
add(B,25,1,'1040,240 1047,240 1052,244 1052,250 1048,255 1041,255 1036,249 1037,243')
add(B,25,2,'1092,1145 1097,1146 1101,1150 1100,1156 1096,1161 1091,1162 1087,1158 1087,1151')
add(B,25,3,'103,887 109,888 114,892 114,898 110,903 103,904 98,899 98,892')
add(B,47,1,'80,1290 84,1290 88,1293 88,1297 85,1300 80,1300 77,1297 77,1293')
add(B,47,2,'835,472 840,472 844,476 843,480 840,483 834,482 831,479 831,475')
add(C,18,2,'',decision='uncertain',note='New raw grid: elongated dark nucleus/continuation, not a separate small round nucleus; excluded, no caliper.')
add(B,20,2,'',decision='uncertain',note='New raw grid: low-contrast/pale internal nuclear area; identity and complete boundary not secure; no caliper.')
add(B,24,1,'',decision='uncertain',note='New raw grid: pale internal area and asymmetric chromatin; lymphocyte identity uncertain; no caliper.')
for q,location,note in [(35,[9,303],'Round black object outside tissue: stain/debris cannot be excluded.'),
                         (49,[522,306],'Isolated black focus near epithelial tissue; cannot establish lymphocyte identity and whole-nucleus boundary.'),
                         (56,[618,93],'Brown/dark rounded focus with adjacent tissue; marker identity unclear.'),
                         (60,[602,67],'Black object in pale/empty background, artefact/debris cannot be excluded.')]:
 add('BreakHis',q,1,'',decision='uncertain',note='Additional 60-image navigation pass: '+note,location=location)
payload.update(status='draft_unreviewed',parent_annotations=str(BASE/'annotations_input.json'),
               additional_survey='Locked queue unchanged. Relative-contrast locator supplies navigation only; no expected diameter or LOO used to select cells.',
               new_measurement_ids=[r['measurement_id'] for r in payload['objects'] if r['measurement_id'].startswith('D2_')])
(OUT/'annotations_extended.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
print('Added',len(payload['new_measurement_ids']),'objects; old annotation objects retained unchanged.')
