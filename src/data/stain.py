"""Macenko with a centered angular coordinate and explicit numerical guards.

No test-set statistics are fitted. Every source image estimates only its own
stain basis; one internal-training image supplies the shared target basis.
"""
from __future__ import annotations
import numpy as np

class StainError(ValueError):
    pass

class MacenkoNormalizer:
    def __init__(self, alpha=1, beta=0.15, max_condition_number=50):
        self.alpha, self.beta = alpha, beta
        self.max_condition_number = max_condition_number
        self.target_basis = self.target_concentrations = None

    def _estimate(self, image):
        image = np.asarray(image, dtype=np.float64)
        if image.ndim != 3 or image.shape[2] != 3:
            raise StainError("Expected HxWx3 RGB image")
        od = -np.log((image.reshape(-1, 3)+1.0)/256.0)
        # Start with the standard Macenko transparency criterion. If a bright
        # channel removes almost all tissue, relax beta explicitly, while the
        # OD-magnitude floor continues to reject glass. The beta is reported.
        tissue=None;used_beta=self.beta
        for threshold in dict.fromkeys([self.beta,.10,.05,.025,0.]):
            valid=np.all(od>=threshold,axis=1)&(np.linalg.norm(od,axis=1)>=self.beta)
            tissue=od[valid];used_beta=threshold
            if len(tissue)>=100:break
        if tissue is None or len(tissue) < 100:
            raise StainError("Insufficient optical-density tissue pixels")
        # Orient the first principal axis towards the positive OD cloud, so
        # angles are near zero instead of crossing the -pi/pi branch cut.
        _, vectors = np.linalg.eigh(np.cov(tissue.T))
        e1, e2 = vectors[:, -1].copy(), vectors[:, -2].copy()
        if np.dot(e1, tissue.mean(axis=0)) < 0:
            e1 *= -1
        angles = np.arctan2(tissue@e2, tissue@e1)
        center = np.arctan2(np.sin(angles).mean(), np.cos(angles).mean())
        centered = np.arctan2(np.sin(angles-center), np.cos(angles-center))
        lo, hi = np.percentile(centered, [self.alpha, 100-self.alpha])+center
        basis = np.column_stack([e1*np.cos(lo)+e2*np.sin(lo),
                                 e1*np.cos(hi)+e2*np.sin(hi)])
        basis /= np.linalg.norm(basis, axis=0)
        if basis[0, 0] < basis[0, 1]:
            basis = basis[:, ::-1]
        cond = float(np.linalg.cond(basis))
        if not np.isfinite(cond) or cond > self.max_condition_number:
            raise StainError(f"Degenerate stain basis: condition={cond:.3f}")
        concentrations = np.linalg.lstsq(basis, od.T, rcond=None)[0]
        concentrations = np.maximum(concentrations, 0)
        maximum = np.percentile(concentrations, 99, axis=1)
        if np.any(maximum < 1e-6) or not np.all(np.isfinite(maximum)):
            raise StainError("Invalid stain concentration percentiles")
        return basis, maximum, concentrations, used_beta

    def basis(self,image):
        return self._estimate(image)[:3]

    def profile(self,image,max_pixels=200000):
        image=np.asarray(image,dtype=np.uint8)
        stride=max(1,int(np.ceil(np.sqrt(image.shape[0]*image.shape[1]/max_pixels))))
        basis,maximum,_,beta=self._estimate(image[::stride,::stride])
        return {'basis':basis,'maximum':maximum,'beta_used':beta,'sampling_stride':stride}

    def fit(self, image):
        profile=self.profile(image)
        self.target_basis=profile['basis'];self.target_concentrations=profile['maximum']
        self.target_beta_used=profile['beta_used']
        return self

    def transform(self, image, source_profile=None):
        if self.target_basis is None:
            raise StainError("Fit a training reference before transform")
        image = np.asarray(image, dtype=np.uint8)
        if source_profile is None:
            _,maximum,concentrations,_=self._estimate(image)
        else:
            maximum=source_profile['maximum']
            od=-np.log((image.astype(np.float64).reshape(-1,3)+1)/256.)
            concentrations=np.maximum(np.linalg.lstsq(source_profile['basis'],od.T,rcond=None)[0],0)
        concentrations *= (self.target_concentrations/maximum)[:, None]
        od = self.target_basis@concentrations
        result = (256*np.exp(-od)).T-1
        if not np.all(np.isfinite(result)):
            raise StainError("Non-finite normalized pixels")
        result = np.clip(np.rint(result), 0, 255).astype(np.uint8).reshape(image.shape)
        # Preserve true white glass; OD factorization should not dye the glass.
        result[np.all(image >= 245, axis=2)] = image[np.all(image >= 245, axis=2)]
        return result

