import torch
print(torch.cuda.is_available())  # Should be True
model = torch.load('model.pth', map_location='cuda')  # make sure it's on GPU
