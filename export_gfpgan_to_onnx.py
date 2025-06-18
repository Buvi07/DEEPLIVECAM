import torch
import torch.nn as nn
import os
import sys

# Add GFPGAN to the path if needed
sys.path.insert(0, os.path.abspath("GFPGAN"))

from basicsr.archs.gfpganv1_clean_arch import GFPGANv1Clean  # GFPGAN backbone
import onnx

# Model and output paths
model_path = "D:\Deep-Live-Cam-2.0\Deep-Live-Cam-2.0\models\GFPGANv1.4.pth"
onnx_output_path = "D:\Deep-Live-Cam-2.0\Deep-Live-Cam-2.0\models\gfpgan.onnx"

# Instantiate model architecture (match GFPGANv1.4)
model = GFPGANv1Clean(
    out_size=512,
    num_style_feat=512,
    channel_multiplier=2,
    decoder_load_path=None,
    fix_decoder=True,
    num_mlp=8,
    input_is_latent=False,
    different_w=True,
    narrow=1
)

# Load weights (key matching may be needed)
ckpt = torch.load(model_path, map_location='cpu')
model.load_state_dict(ckpt['params_ema'], strict=False)
model.eval()

# Dummy input (batch=1, 3 channels, 512x512)
dummy_input = torch.randn(1, 3, 512, 512)

# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    onnx_output_path,
    input_names=['input'],
    output_names=['output'],
    opset_version=11,
    do_constant_folding=True,
    dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
)

print(f"Exported to {onnx_output_path}")
