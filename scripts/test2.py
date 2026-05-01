# import torch
# from model import * # Assuming your model file is named model.py
# import sys

# # 1. Load the old weights
# model_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\models\lcnn\E4\trained_network_E4_old.pt"
# old_state = torch.load(model_path)

# # 2. Build the new model (Assuming your main class is called Model)
# # Adjust the arguments here to whatever your model needs to initialize LFCC!
# new_model = Model(feature_type='lfcc', architecture='lcnn') 
# new_state = new_model.state_dict()

# # 3. Compare them
# print("\n--- WEIGHTS IN E4 BUT MISSING IN NEW MODEL ---")
# for key in old_state.keys():
#     if key not in new_state:
#         print(key)

# print("\n--- NEW MODEL LAYERS THAT ARE EMPTY (RANDOM) ---")
# for key in new_state.keys():
#     if key not in old_state:
#         print(key)
        
        
        
        
import torch

# Path to the old E4 weights you just found
model_path = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\models\lcnn\E4\trained_network.pt"

# Load the found weights
checkpoint = torch.load(model_path)
new_state = {}

# Rename the keys to match your NEW model.py structure
for key, value in checkpoint.items():
    if key == "m_frontend.0.lfcc_fb":
        new_state["m_frontend.0.lfcc_extractor.lfcc_fb"] = value
    elif key == "m_frontend.0.l_dct.weight":
        new_state["m_frontend.0.lfcc_extractor.l_dct.weight"] = value
    else:
        new_state[key] = value

# Save it back
torch.save(new_state, model_path)
print("Successfully upgraded the found E4 weights!")