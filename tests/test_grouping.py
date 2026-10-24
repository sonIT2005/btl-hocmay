import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import yaml
from threadpoolctl import threadpool_limits
from tools.group_lc import verify

ROOT=Path(__file__).resolve().parents[1]

class GroupingTests(unittest.TestCase):
    def test_real_augmentation_can_resize_axes_differently(self):
        folder=ROOT/'data/raw/LC25000/colon_image_sets/colon_aca'
        if not folder.exists():self.skipTest('Local LC25000 fixture unavailable')
        cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text())['grouping']
        with threadpool_limits(limits=1):
            result=verify(folder/'colonca1094.jpeg',folder/'colonca388.jpeg',cfg)
        self.assertIsNotNone(result)
        self.assertGreater(result['inlier_ratio'],.95)

    def test_strong_augmentation_axis_distortion_is_still_same_field(self):
        folder=ROOT/'data/raw/LC25000/colon_image_sets/colon_aca'
        if not folder.exists():self.skipTest('Local LC25000 fixture unavailable')
        cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text())['grouping']
        cfg.update(verification_size=512,sift_features=500,min_inliers=20)
        with threadpool_limits(limits=1):result=verify(folder/'colonca1004.jpeg',folder/'colonca3011.jpeg',cfg)
        self.assertIsNotNone(result)
        self.assertGreater(result['correlation'],.98)

    def test_odd_rotation_and_flip_recovered_but_other_tissue_rejected(self):
        source=ROOT/'data/raw/LC25000/lung_image_sets/lung_aca/lungaca1.jpeg'
        other=source.with_name('lungaca10.jpeg')
        if not source.exists():self.skipTest('Local LC25000 integration fixture unavailable')
        cfg=yaml.safe_load((ROOT/'configs/preparation.yaml').read_text())['grouping']
        cv2.setNumThreads(1)
        (ROOT/'outputs').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='test-grouping-') as temp,threadpool_limits(limits=1):
            self.assertTrue(Path(temp).resolve().is_relative_to(ROOT.resolve()))
            with Image.open(source) as im:
                altered=im.convert('RGB').transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(13,Image.Resampling.BICUBIC)
                path=Path(temp)/'odd_rotation.png';altered.save(path)
            self.assertIsNotNone(verify(source,path,cfg))
            # A separate file is used only when geometric verification establishes it is unrelated.
            # The concrete negative fixture here is a deterministic synthetic noise field.
            rng=np.random.default_rng(87)
            negative=Path(temp)/'unrelated.png'
            Image.fromarray(rng.integers(0,256,(768,768,3),dtype=np.uint8)).save(negative)
            self.assertIsNone(verify(source,negative,cfg))

if __name__=='__main__':unittest.main()
