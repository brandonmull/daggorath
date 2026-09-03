# CUDA Works Under WSL

`nvidia-smi` under WSL reported an RTX 3080, and the torch install selected the `+cu130` build — `torch.cuda.is_available()` is `True`. No special setup was needed; pip's Linux wheel picked up the GPU-capable variant automatically.
