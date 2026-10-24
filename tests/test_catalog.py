import unittest
from src.data.catalog import parse_breakhis,MAPPINGS

class CatalogTests(unittest.TestCase):
    def test_patient_sections_do_not_leak(self):
        a=parse_breakhis('SOB_B_A-14-22549AB-40-001.png')
        b=parse_breakhis('SOB_B_A-14-22549CD-100-002.png')
        self.assertEqual(a['case_group_id'],b['case_group_id'])
        self.assertNotEqual(a['patient_id'],b['patient_id'])
        self.assertNotEqual(a['slide_id'],b['slide_id'])

    def test_scc_and_aca_all_grades(self):
        for grade in ['bd','md','pd']:
            self.assertEqual(MAPPINGS['LungHist700']['aca_'+grade],1)
            self.assertEqual(MAPPINGS['LungHist700']['scc_'+grade],2)

    def test_crc_only_two_tissues(self):
        self.assertEqual(MAPPINGS['CRC-VAL-HE-7K'],{'NORM':3,'TUM':4})

if __name__=='__main__':unittest.main()
