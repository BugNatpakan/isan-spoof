import os

# The exact folder MLflow is crying about
bad_folder = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\scripts\mlruns\1"
os.makedirs(bad_folder, exist_ok=True)

# We create a dummy file that tells MLflow this experiment is officially "deleted"
yaml_content = """artifact_location: file:///D:/work/AI frontier/project AntiSpoof/isan-spoof/scripts/mlruns/1
creation_time: 1710000000000
experiment_id: '1'
last_update_time: 1710000000000
lifecycle_stage: deleted
name: corrupted_experiment
"""

with open(os.path.join(bad_folder, "meta.yaml"), "w") as f:
    f.write(yaml_content)

print("✅ MLflow corruption fixed! You can now run your pipeline.")