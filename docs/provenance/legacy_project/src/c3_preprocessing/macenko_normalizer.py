"""
Thuật toán Macenko Stain Normalization cho ảnh mô bệnh học nhuộm H&E.
Dựa trên nguyên lý quang học định luật Beer-Lambert.
Tài liệu gốc: M. Macenko et al., "A method for normalizing histology slides for quantitative analysis", ISBI 2009.
Phụ trách: Đông / Huy (Module C3)
"""

import sys
import numpy as np
from PIL import Image

# Đảm bảo UTF-8 cho Windows console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MacenkoNormalizer:
    def __init__(self, Io=255, alpha=1, beta=0.15):
        """
        Io: Cường độ ánh sáng ban đầu (255 cho ảnh 8-bit).
        alpha: Ngưỡng percentile góc cực biên (1% và 99%).
        beta: Ngưỡng loại bỏ nền quang học (OD threshold).
        """
        self.Io = Io
        self.alpha = alpha
        self.beta = beta
        self.HERef = None
        self.maxCRef = None

    def fit(self, target_image):
        """
        Huấn luyện / trích xuất đặc trưng màu từ ảnh mẫu chuẩn (Reference Image).
        target_image: numpy array (H, W, 3) hoặc đường dẫn file ảnh.
        """
        if isinstance(target_image, str):
            target_image = np.array(Image.open(target_image).convert("RGB"))
        self.HERef, self.maxCRef = self._get_stain_matrix(target_image)

    def _get_stain_matrix(self, img):
        """Ước lượng ma trận Stain Vectors H&E và nồng độ cực đại (99th percentile)"""
        img = img.astype(np.float64)
        h, w, c = img.shape
        img = img.reshape((-1, 3))

        # Chuyển đổi sang Optical Density (OD)
        OD = -np.log((img + 1.0) / self.Io)
        
        # Lọc bỏ pixel nền trống
        ODhat = OD[~np.any(OD < self.beta, axis=1)]
        if len(ODhat) < 10:
            # Fallback nếu ảnh quá ít mô
            return np.eye(3)[:2], np.array([1.0, 1.0])

        # Phân tích SVD trên ma trận hiệp phương sai của OD
        _, _, V = np.linalg.svd(ODhat, full_matrices=False)
        # 2 vector riêng có trị riêng lớn nhất tương ứng mặt phẳng H&E
        That = np.dot(ODhat, V[:2, :].T)

        # Tính góc của các pixel trên mặt phẳng
        phi = np.arctan2(That[:, 1], That[:, 0])
        minPhi = np.percentile(phi, self.alpha)
        maxPhi = np.percentile(phi, 100 - self.alpha)

        # Khôi phục stain vector của H và E
        vMin = np.dot(V[:2, :].T, np.array([np.cos(minPhi), np.sin(minPhi)]))
        vMax = np.dot(V[:2, :].T, np.array([np.cos(maxPhi), np.sin(maxPhi)]))

        # H có màu tím hơn (thành phần R nhỏ hơn), E có màu hồng hơn
        if vMin[0] > vMax[0]:
            HE = np.array([vMin, vMax])
        else:
            HE = np.array([vMax, vMin])

        # Chuẩn hóa độ dài vector đơn vị
        HE = HE / np.linalg.norm(HE, axis=1)[:, None]

        # Tính ma trận nồng độ C
        C = np.linalg.lstsq(HE.T, OD.T, rcond=None)[0]
        maxC = np.percentile(C, 99, axis=1)

        return HE, maxC

    def transform(self, src_image):
        """
        Chuẩn hóa ảnh đầu vào về hệ màu của ảnh mẫu tham chiếu.
        src_image: numpy array (H, W, 3) dạng uint8.
        """
        if self.HERef is None or self.maxCRef is None:
            raise ValueError("Cần gọi .fit(reference_image) trước khi transform!")

        is_pil = False
        if isinstance(src_image, Image.Image):
            src_image = np.array(src_image.convert("RGB"))
            is_pil = True
        elif isinstance(src_image, str):
            src_image = np.array(Image.open(src_image).convert("RGB"))

        h, w, c = src_image.shape
        img = src_image.astype(np.float64).reshape((-1, 3))

        # Tính OD ảnh nguồn
        OD = -np.log((img + 1.0) / self.Io)
        
        # Tìm stain matrix và max concentration của ảnh nguồn
        try:
            HE_src, maxC_src = self._get_stain_matrix(src_image)
            # Nồng độ trên ảnh nguồn
            C = np.linalg.lstsq(HE_src.T, OD.T, rcond=None)[0]
            
            # Chuẩn hóa nồng độ theo ảnh đích
            maxC_src = np.maximum(maxC_src, 1e-6)
            C = C / maxC_src[:, None]
            C = C * self.maxCRef[:, None]

            # Tái tạo lại ảnh từ vector H&E của ảnh đích
            OD_norm = np.dot(self.HERef.T, C)
            img_norm = self.Io * np.exp(-OD_norm)
            img_norm = np.clip(img_norm.T, 0, 255).astype(np.uint8)
            img_norm = img_norm.reshape((h, w, 3))
            
            if is_pil:
                return Image.fromarray(img_norm)
            return img_norm
        except Exception:
            # Nếu có lỗi tính toán (ví dụ ảnh toàn màu trắng), giữ nguyên ảnh gốc
            return src_image
