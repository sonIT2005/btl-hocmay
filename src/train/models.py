"""Tên ngắn dùng trong run_name → trọng số timm (mục 5.1). Cả hai đều pretrain ImageNet-1k."""
import timm

MODELS = {
    'convnext': 'convnext_tiny.fb_in1k',
    'swin': 'swin_tiny_patch4_window7_224.ms_in1k',
}


def build_model(name, num_classes, pretrained=True):
    return timm.create_model(MODELS[name], pretrained=pretrained, num_classes=num_classes)


def norm_stats(model):
    cfg = model.pretrained_cfg
    return cfg['mean'], cfg['std']
