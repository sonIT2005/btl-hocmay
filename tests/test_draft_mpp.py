import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image
from tools.draft_mpp import SOURCES, build, geometry, preview


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class DraftGeometryTests(unittest.TestCase):
    def test_rectangle_calipers_are_true_chords_not_bbox_diagonal_for_axes(self):
        g=geometry([[2,2],[10,2],[10,8],[2,8]],20,20)
        self.assertEqual(g['diameter_px'],10)
        self.assertEqual(g['axis_h_px'],8)
        self.assertEqual(g['axis_v_px'],6)
        for name in ('longest','h','v'):
            expected=g['diameter_px'] if name=='longest' else g['axis_'+name+'_px']
            self.assertAlmostEqual(math.dist(*g[name]),expected)

    def test_invalid_outlines_rejected(self):
        for points in (
            [[-1,2],[3,2],[3,4]], [[1,1],[2,2],[3,3]],
            [[1,1],[8,8],[1,8],[8,1]], [[1,1],[8,1],[4,4],[8,8],[1,8]],
            [[1,1],[8,1],[8,float('nan')]], [[1,1],[9,1],[9,9],[1,9]],
        ):
            with self.subTest(points=points),self.assertRaises(ValueError):
                geometry(points,9,9)

    def test_rotated_outline_horizontal_and_vertical_endpoints(self):
        g=geometry([[5,0],[10,5],[5,10],[0,5]],11,11)
        self.assertEqual(g['axis_h_px'],10)
        self.assertEqual(g['axis_v_px'],10)
        self.assertEqual(g['h'],[[0,5],[10,5]])
        self.assertEqual(g['v'],[[5,0],[5,10]])


class DraftPreviewTests(unittest.TestCase):
    def setUp(self):
        self.protocol={'min_cells':30,'min_images':15,'max_cells_per_image':3,
                       'review_seed':43,'review_fraction':.2,
                       'known_mpp':dict(zip(SOURCES,[.5,.42,.49]))}
        self.records=[]
        for s in SOURCES:
            for i in range(30):
                self.records.append(dict(measurement_id=f'{s}_{i:02d}',candidate_id=f'{s}_{i//2}',
                    source=s,cell_type='lymph_nucleus',decision='draft_eligible',
                    diameter_px=7/self.protocol['known_mpp'][s]))

    def test_complete_synthetic_preview_is_never_release(self):
        r=preview(self.records,self.protocol)
        self.assertEqual(r['status'],'draft_only_unreviewed')
        self.assertEqual(r['formal_accepted_cells'],0)
        self.assertFalse(r['physical_calibration_claimed'])
        self.assertIsNone(r['approved_mpp'])
        self.assertEqual(r['targets'],{})
        for s,v in r['markers']['lymph_nucleus']['leave_one_out'].items():
            self.assertAlmostEqual(v['relative_error'],0)
        self.assertIsNone(r['markers']['rbc']['leave_one_out'])

    def test_uncertain_objects_excluded_and_missing_source_blocks_loo(self):
        rows=copy.deepcopy(self.records)
        for r in rows:
            if r['source']=='BreakHis':r['decision']='uncertain'
        report=preview(rows,self.protocol)['markers']['lymph_nucleus']
        self.assertIsNone(report['leave_one_out'])
        self.assertFalse(report['method_failed'])
        self.assertEqual(report['counts']['BreakHis']['missing_cells'],30)
        self.assertEqual(report['counts']['BreakHis']['missing_images'],15)

    def test_review_draw_uses_locked_seed_and_sorted_ids(self):
        r=preview(list(reversed(self.records)),self.protocol)['markers']['lymph_nucleus']
        for s in SOURCES:
            ids=sorted(v['measurement_id'] for v in self.records if v['source']==s)
            self.assertEqual(r['counts'][s]['review_measurement_ids'],random.Random(43).sample(ids,6))

    def test_excess_cells_cannot_satisfy_sample_target(self):
        rows=copy.deepcopy(self.records)
        for r in rows:r['candidate_id']=r['source']
        with self.assertRaises(ValueError):preview(rows,self.protocol)


class DraftBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.kit=self.root/'kit';self.data=self.root/'data'
        self.kit.mkdir();self.data.mkdir();self.frozen=self.root/'FROZEN.json';self.frozen.write_text('{}')
        Image.new('RGB',(32,32),'pink').save(self.data/'image.png')
        candidate=dict(candidate_id='example',source='CRC-VAL-HE-7K',image_path='image.png',queue_order=1,group_id='fixture:example',
                       width=32,height=32,raw_sha256=digest(self.data/'image.png'))
        with (self.kit/'candidates.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(candidate));w.writeheader();w.writerow(candidate)
        protocol={'min_cells':30,'min_images':15,'max_cells_per_image':3,'review_seed':43,'review_fraction':.2,
                  'known_mpp':dict(zip(SOURCES,[.5,.42,.49])),
                  'candidate_sha256':digest(self.kit/'candidates.csv'),'frozen_sha256':digest(self.frozen)}
        (self.kit/'protocol.json').write_text(json.dumps(protocol))
        (self.kit/'protocol.sha256').write_text(digest(self.kit/'protocol.json'))
        (self.kit/'measurements.csv').write_text('formal unchanged\n')
        self.annotations=self.root/'annotations.json'
        self.object=dict(measurement_id='D1_example',candidate_id='example',cell_type='lymph_nucleus',
                         decision='draft_eligible',polygon=[[10,10],[20,10],[20,20],[10,20]],note='Synthetic fixture')

    def run_build(self,objects=None,out=None):
        self.annotations.write_text(json.dumps({'objects':objects or [self.object]}))
        return build(self.kit,self.annotations,out or self.root/'draft',self.data,self.frozen)

    def test_rendered_draft_keeps_formal_input_and_review_pending(self):
        before=digest(self.kit/'measurements.csv'); self.run_build()
        out=self.root/'draft'
        self.assertTrue((out/'objects/D1_example_roi.png').is_file())
        self.assertTrue((out/'image_medians.csv').is_file())
        self.assertTrue((out/'cohort_summary.csv').is_file())
        self.assertEqual(before,digest(self.kit/'measurements.csv'))
        with (out/'draft_measurements.csv').open(encoding='utf-8-sig') as f:row=next(csv.DictReader(f))
        self.assertEqual(row['review_status'],'draft_unreviewed');self.assertEqual(row['checked_by'],'')
        self.assertEqual(row['group_id'],'fixture:example')
        with (out/'review_return.csv').open(encoding='utf-8-sig') as f:review=next(csv.DictReader(f))
        self.assertTrue(all(review[k]=='' for k in ('checked_by','review_date','redrawn_x1','redrawn_h_px','redrawn_v_px')))
        self.assertIn('href="#D1_example"',(out/'index.html').read_text())
        with self.assertRaises(FileExistsError):self.run_build()

    def test_approved_status_and_formal_output_location_rejected(self):
        for edit in ({'review_status':'checked'},{'checked_by':'invented_reviewer'}):
            with self.subTest(edit=edit),self.assertRaises(ValueError):self.run_build([{**self.object,**edit}])
        with self.assertRaises(ValueError):self.run_build(out=self.kit/'draft')

    def test_source_tamper_blocks_build(self):
        Image.new('RGB',(32,32),'blue').save(self.data/'image.png')
        with self.assertRaisesRegex(ValueError,'Raw source SHA'):self.run_build()

    def test_maximum_three_across_both_markers(self):
        objects=[{**self.object,'measurement_id':f'd_{i}','cell_type':'rbc' if i%2 else 'lymph_nucleus'} for i in range(4)]
        with self.assertRaisesRegex(ValueError,'Too many draft cells'):self.run_build(objects)


if __name__=='__main__':unittest.main()
