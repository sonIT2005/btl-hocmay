"""Coordinates transcribed by visual inspection of raw 8x nearest-neighbour grids.
No mask geometry or published/target cell diameter is used for these outlines.
"""
import json
from pathlib import Path
ROOT=Path(r'C:\Users\Admin\Documents\GitHub\btl-hocmay')
OUT=ROOT/'outputs/mpp_measurements_draft_v1'
targets=json.loads((OUT/'navigation/grid_targets.json').read_text())
objects=[]
def add(source,q,n,points,decision='draft_eligible',cell_type='lymph_nucleus',note=None,grid=None):
 target=next(t for t in targets if t['source']==source and t['q']==q and t['id'].endswith('_'+str(grid or min(n,3))))
 polygon=[list(map(int,p.split(','))) for p in points.split()] if points else []
 ident=f'D1_{"CRC" if source.startswith("CRC") else source}_q{q:02d}_{n}'
 objects.append(dict(measurement_id=ident,candidate_id=target['candidate_id'],cell_type=cell_type,
                     decision=decision,polygon=polygon,location=[target['cx'],target['cy']],
                     evidence_grid_target=target['id'],boundary_uncertainty_px=1 if source!='BACH' else 2,
                     note=note or 'Visually small round/oval densely dark nucleus, separated from gland epithelium; identity and boundary remain unreviewed.'))
C='CRC-VAL-HE-7K'
add(C,3,1,'204,103 210,103 215,107 214,112 210,116 203,116 199,112 199,108')
add(C,3,2,'28,30 32,30 35,33 35,36 32,38 28,38 25,35 25,32')
add(C,3,3,'195,93 199,93 202,96 202,99 199,102 194,102 191,99 191,96',grid=1)
add(C,6,1,'70,145 75,145 79,148 80,152 76,156 70,156 66,153 66,149')
add(C,6,2,'46,160 50,160 54,163 53,167 49,170 45,169 43,166 43,163')
add(C,7,1,'187,67 192,67 195,70 195,75 192,79 188,78 185,74 184,70')
add(C,16,1,'124,99 128,99 130,102 130,105 128,108 124,108 122,105 122,102',grid=2)
add(C,16,2,'130,35 134,35 137,38 137,42 134,44 130,44 128,41 128,38',grid=3)
add(C,16,3,'125,45 129,45 132,48 131,51 128,53 124,52 122,49 123,47',grid=3)
add(C,18,1,'151,34 155,34 159,37 162,41 159,44 154,45 150,42 148,38',grid=2)
add(C,20,1,'66,45 70,45 73,48 73,51 70,54 66,54 63,51 63,48')
add(C,20,2,'138,27 142,27 144,30 144,33 141,36 137,35 135,32 135,29')
add(C,20,3,'180,140 184,140 187,143 187,147 185,150 180,150 176,147 176,143')
add(C,21,1,'76,157 80,157 84,160 84,164 81,168 76,168 73,165 73,161')
add(C,21,2,'131,137 134,138 136,141 136,144 133,147 130,146 128,143 128,140')
add(C,24,1,'66,61 69,61 72,64 72,67 69,69 66,69 63,66 63,63')
add(C,24,2,'172,133 176,133 179,136 178,139 175,141 171,139 169,136 170,134',grid=3)
add(C,28,1,'203,76 207,77 210,80 210,83 207,86 203,85 200,82 199,79',grid=2)
add(C,28,2,'95,9 99,9 102,12 101,16 98,18 94,17 92,14 92,11',grid=3)
add(C,28,3,'169,43 172,43 176,46 175,49 172,51 168,50 166,47 167,44',grid=1)
add(C,33,1,'31,193 35,194 38,198 37,202 34,205 30,204 27,201 27,196')
add(C,33,2,'140,200 144,200 147,202 147,205 144,207 140,206 138,204 138,202',grid=3)
add(C,33,3,'43,180 47,180 50,183 50,186 47,189 43,189 40,186 40,183',grid=1)
add(C,36,1,'95,181 98,181 101,184 101,188 98,191 94,190 92,187 92,184',grid=2)
add(C,39,1,'110,131 113,131 116,134 116,137 113,141 109,140 107,137 107,134')
add(C,47,1,'79,171 83,171 86,175 85,179 82,181 78,180 76,177 76,174')
add(C,48,1,'91,61 95,61 98,64 98,68 95,71 91,70 88,67 88,64')
add(C,60,1,'160,71 164,72 167,75 167,79 164,82 159,81 156,78 156,74')
add(C,60,2,'194,112 199,113 202,117 201,121 198,125 192,125 189,121 189,116')
add(C,60,3,'146,147 149,147 151,150 151,153 148,155 144,154 142,151 143,148')

B='BACH'
add(B,9,1,'1677,34 1683,34 1687,38 1687,44 1684,49 1679,50 1675,46 1674,40')
add(B,15,1,'1010,598 1017,598 1022,601 1023,605 1020,610 1013,611 1005,608 1004,603')
add(B,16,1,'1494,558 1501,558 1508,563 1509,570 1505,576 1497,578 1490,573 1489,565')
add(B,16,2,'530,1208 534,1209 537,1213 537,1219 534,1224 529,1224 525,1220 525,1214')
add(B,20,1,'1124,610 1129,610 1133,614 1133,618 1129,621 1123,621 1120,618 1120,614')
add(B,23,1,'263,1499 267,1499 271,1503 271,1508 268,1511 262,1511 259,1507 260,1502')
add(B,26,1,'777,208 783,208 787,211 788,217 784,222 778,222 774,219 773,213',note='Whole dark rounded nucleus at (781,215), not the tiny locator dot at (787,226); visible boundary drawn on raw grid.')
add(B,27,1,'990,126 997,126 1001,130 1001,135 997,139 990,139 986,135 986,130')
add(B,27,2,'2018,348 2025,348 2029,352 2028,357 2024,360 2018,359 2014,355 2014,351')
add(B,29,1,'1940,957 1947,957 1952,962 1952,968 1948,973 1941,974 1937,970 1937,962')
add(B,30,1,'577,824 583,824 589,828 592,834 588,840 581,840 575,836 573,829')
add(B,32,1,'440,1314 447,1314 454,1320 454,1325 448,1332 439,1333 434,1328 434,1320')
add(B,36,1,'562,862 568,862 573,866 575,872 571,879 565,880 560,875 558,868',grid=2)
add(B,47,1,'1962,1060 1967,1061 1972,1065 1973,1071 1969,1076 1965,1076 1960,1071 1959,1065')
add(B,50,1,'850,290 861,290 867,293 867,299 862,303 852,304 845,301 843,295')
add(B,50,2,'1390,746 1398,746 1403,750 1403,757 1399,762 1390,762 1384,759 1383,752')
add(B,52,1,'881,1105 889,1107 894,1113 895,1123 892,1131 883,1132 875,1126 872,1116')
add(B,53,1,'1382,44 1386,44 1390,48 1389,55 1386,62 1379,62 1377,58 1378,50')
add(B,56,1,'1661,410 1667,410 1673,414 1674,420 1670,425 1660,425 1654,421 1653,415')

# Uncertain identity or boundary never contributes to draft sample size or LOO.
for source,q,n,grid,note in [
 (C,16,9,1,'Locator at (150,51) may connect to another dark nucleus above; boundary not separable.'),
 (C,18,9,1,'Adjacent dark objects overlap; no reliable single-nucleus outline.'),
 (C,24,9,2,'Dark centre with lower extension; whole-nucleus boundary uncertain.'),
 (C,28,9,1,'Target (162,36) has pale/heterogeneous chromatin; identity uncertain. A different separated object in this ROI was measured.'),
 (C,33,9,2,'Overlapping pale nuclei; identity and boundary unsuitable.'),
 (C,36,9,1,'Pale-centred dark outline; lymphocyte identity uncertain.'),
 (C,36,10,3,'Elongated nucleus; lymphocyte identity uncertain.'),
 (C,47,9,2,'Angular dark object among elongated stromal nuclei; identity uncertain.'),
 (C,47,10,3,'Irregular pale/overlapping nuclei, not a separate uniformly dark round nucleus.'),
 (C,48,9,2,'Elongated dark object and nearby dark neighbour; boundary/identity uncertain.'),
 (B,25,9,1,'Magenta object with blue lower focus: cannot identify as RBC or lymphocyte.'),
 (B,29,9,2,'Pale internal area/eccentric chromatin; possible non-lymphocyte nucleus.'),
 (B,32,9,2,'Large pale nucleus in a cluster; possible epithelial nucleus.'),
 (B,35,9,1,'Clustered dark nuclei at duct epithelium; identity not established.'),
 (B,35,10,2,'Clustered dark nucleus; cannot exclude epithelial identity.'),
 (B,36,9,1,'Locator target does not contain a separate round nucleus; nearby object elongated.'),
 (B,57,9,1,'Low-contrast nucleus: boundary not stable to 1-2 pixels.'),
 (B,58,9,1,'Raw grid target contains pale background, not a nucleus. Locator false positive.'),
 ('BreakHis',4,9,1,'Dark region in epithelium; cannot identify a whole lymphocyte nucleus.'),
 ('BreakHis',21,9,1,'Blurred brown/purple object and adjacent stain; identity and boundary uncertain.'),
 ('BreakHis',21,10,2,'Small dark dot amid blurred staining; cannot establish whole-nucleus boundary.'),
 ('BreakHis',36,9,1,'Two touching purple objects; cannot isolate one whole round nucleus.'),
 ('BreakHis',42,9,1,'Black object detached in gland lumen; debris/artefact cannot be excluded.'),
 ('BreakHis',43,9,1,'Low-resolution dark object; identity and true nuclear boundary uncertain.'),
 ]:
 add(source,q,n,'',decision='uncertain',note=note,grid=grid)
add(B,2,9,'1985,421 1992,421 1997,426 1996,433 1992,438 1985,440 1978,435 1978,428',decision='uncertain',cell_type='rbc',grid=1,note='Anucleate-looking magenta body in a lumen; solitary object, RBC identity not established. Not counted.')
add(B,49,9,'221,1377 226,1379 230,1384 230,1390 226,1395 220,1395 216,1391 215,1383',decision='uncertain',cell_type='rbc',grid=1,note='Round magenta body adjacent to a second smaller body; RBC versus other eosinophilic structure unresolved. Not counted.')

# Final visual QA before any review draw or LOO: criteria are unchanged.
for o in objects:
 if o['measurement_id']=='D1_CRC_q18_1':
  o.update(decision='uncertain',note='Final overlay QA: angular nucleus with dark continuation below; round identity and independent lower boundary not secure. Excluded before LOO.')
 if o['measurement_id']=='D1_CRC_q33_2':
  o.update(decision='uncertain',note='Final overlay QA: pale blurred nuclear boundary and a dark internal focus; whole-boundary estimate insufficient. Excluded before LOO.')
 if o['measurement_id']=='D1_CRC_q60_3':
  o.update(decision='uncertain',note='Final overlay QA: blurred small dark object touches surrounding staining; identity/boundary uncertain. Excluded before LOO.')

H='BreakHis'
add(H,13,11,'259,54 264,54 267,58 266,65 263,70 258,71 255,67 255,61',decision='uncertain',grid=1,note='Native full-image survey found an elongated low-contrast purple object. Approximate extent only, not an identified lymphocyte nucleus.')
add(H,22,11,'281,319 284,319 287,324 287,330 284,335 277,335 273,332 273,326',decision='uncertain',grid=1,note='Solitary stromal purple object, but boundary diffuse and nucleus not uniformly dark. Approximate visible outline only; excluded.')
add(H,29,11,'171,167 177,167 182,170 182,174 178,177 171,177 166,174 166,170',decision='uncertain',grid=1,note='Dark grey oval object lacks clear hematoxylin nuclear appearance; artefact cannot be excluded. Outline only for review.')
add(H,37,11,'541,125 546,125 549,129 549,134 545,138 540,137 537,133 537,129',decision='uncertain',grid=1,note='Low-contrast stromal object with blurry edge; not enough evidence of a whole lymphocyte nucleus.')
for q,n,grid,note in [(10,11,1,'Pink/red vessel region, but individual anucleate cell boundaries cannot be separated.'),
                       (50,11,1,'Blood-coloured region with merged red staining; no single clear RBC boundary.'),
                       (50,12,2,'Second vessel region; red objects merge and individual RBC identity/boundary is unresolved.')]:
 add(H,q,n,'',decision='uncertain',cell_type='rbc',grid=grid,note=note)
for o in objects:
 if o['candidate_id'] in {t['candidate_id'] for t in targets if t['source']=='BreakHis'}:
  o['boundary_uncertainty_px']=2

payload=dict(schema=1,status='draft_unreviewed',coordinate_system='raw pixel centres; zero-based x right / y down',
             outline_origin='Codex visual transcription of raw-grid images; no mask-size reuse',
             marker_choice='RBC preferred; control overview survey insufficient; lymph nuclei surveyed separately across all sources before any LOO.',
             objects=objects)
Path(r'C:\Users\Admin\AppData\Local\Temp\btl_mpp_draft_20261025_v1\annotations_v2.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
print({s:sum(o['decision']=='draft_eligible' and next(t['source'] for t in targets if t['candidate_id']==o['candidate_id'])==s for o in objects) for s in (C,B,'BreakHis')})
