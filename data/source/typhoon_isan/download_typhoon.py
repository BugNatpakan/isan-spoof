# Run this as download_typhoon.py
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="typhoon-ai/thai-dialect-isan-dataset",
    repo_type="dataset",
    local_dir=r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan"
)

print("Typhoon Isan downloaded!")