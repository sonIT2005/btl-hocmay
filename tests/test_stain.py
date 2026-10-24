import unittest
import numpy as np
from pathlib import Path
from PIL import Image
from src.data.stain import MacenkoNormalizer, StainError

class StainTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.basis = np.array([[0.65,0.07],[0.70,0.99],[0.29,0.11]])
        concentration = rng.gamma(2, 0.4, (2, 128*128))
        self.image = np.clip(256*np.exp(-self.basis@concentration).T-1,0,255).astype('uint8').reshape(128,128,3)

    def test_two_distinct_stains_and_self_reconstruction(self):
        normalizer = MacenkoNormalizer().fit(self.image)
        self.assertLess(np.linalg.cond(normalizer.target_basis), 50)
        transformed = normalizer.transform(self.image)
        self.assertLess(np.abs(transformed.astype(float)-self.image).mean(), 8)
        self.assertLess(np.mean(np.all(transformed<10,axis=2)), 0.01)

    def test_blank_image_is_explicit_failure(self):
        with self.assertRaises(StainError):
            MacenkoNormalizer().fit(np.full((32,32,3),255,dtype='uint8'))

    def test_unfitted_is_explicit_failure(self):
        with self.assertRaises(StainError):
            MacenkoNormalizer().transform(self.image)

    def test_bright_blue_tissue_is_not_classified_as_glass(self):
        p=Path(__file__).resolve().parents[1]/'data/raw/LC25000/lung_image_sets/lung_aca/lungaca1179.jpeg'
        if not p.exists():self.skipTest('Local bright-blue integration fixture unavailable')
        with Image.open(p) as im:a=np.asarray(im.convert('RGB').crop((272,272,496,496)))
        n=MacenkoNormalizer().fit(self.image)
        with Image.open(p) as im:profile=n.profile(np.asarray(im.convert('RGB')))
        result=n.transform(a,source_profile=profile)
        self.assertEqual(result.shape,a.shape)
        self.assertLess(float(np.mean(np.all(result<10,axis=2))),.01)

    def test_agrees_with_independent_torchstain_dense_fixture(self):
        import torchstain
        root=Path(__file__).resolve().parents[1]/'data/raw'
        if not (root/'LC25000').exists():self.skipTest('Local integration fixtures unavailable')
        with Image.open(root/'LC25000/colon_image_sets/colon_aca/colonca1.jpeg') as im:
            ref=np.asarray(im.convert('RGB'))[::2,::2]
        with Image.open(root/'LungHist700/images/aca_bd/aca_bd_20x_0.jpg') as im:
            a=np.asarray(im.convert('RGB').crop((0,0,224,224)))
        ours=MacenkoNormalizer().fit(ref).transform(a)
        independent=torchstain.normalizers.MacenkoNormalizer(backend='numpy')
        independent.fit(ref,Io=256)
        expected,_,_=independent.normalize(a,Io=256,stains=False)
        self.assertLess(float(np.abs(ours.astype(float)-expected).mean()),2)

    def test_whole_source_profile_preserves_local_structure(self):
        root=Path(__file__).resolve().parents[1]/'data/raw'
        if not (root/'LC25000').exists():self.skipTest('Local integration fixtures unavailable')
        with Image.open(root/'LC25000/colon_image_sets/colon_aca/colonca1.jpeg') as im:ref=np.asarray(im.convert('RGB'))
        with Image.open(root/'LungHist700/images/aca_bd/aca_bd_20x_0.jpg') as im:a=np.asarray(im.convert('RGB'))
        n=MacenkoNormalizer().fit(ref);out=n.transform(a[:224,:224],source_profile=n.profile(a))
        correlation=np.corrcoef(a[:224,:224].mean(axis=2).ravel(),out.mean(axis=2).ravel())[0,1]
        self.assertGreater(correlation,.6)

if __name__ == '__main__': unittest.main()
