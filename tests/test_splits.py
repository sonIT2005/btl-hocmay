import unittest
import copy
from tools.prepare import assign_splits

class SplitTests(unittest.TestCase):
    def test_group_integrity_and_reproducibility_independent_of_input_order(self):
        rows=[{'label':0,'source':'LC25000','group_id':f'LC:{g}','source_image_path':f'{g}_{i}',
               'included':True,'split':''} for g in range(30) for i in range(4)]
        a=copy.deepcopy(rows);b=copy.deepcopy(rows[::-1]);assign_splits(a,42);assign_splits(b,42)
        self.assertEqual({r['source_image_path']:(r['split'],r['split_random']) for r in a},
                         {r['source_image_path']:(r['split'],r['split_random']) for r in b})
        for g in range(30):self.assertEqual(len({r['split'] for r in a if r['group_id']==f'LC:{g}'}),1)

    def test_external_is_never_internal(self):
        rows=[{'label':1,'source':'LungHist700','group_id':'Lung:1','source_image_path':'x',
               'included':True,'split':'xtest'}]
        assign_splits(rows,42)
        self.assertEqual(rows[0]['split'],'xtest');self.assertEqual(rows[0]['split_random'],'xtest')

if __name__=='__main__':unittest.main()
