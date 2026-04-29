import os

# dataset_type = "eval" 
dataset_type = "trn"  

# --- CONFIGURATION ---
# 1. Point this to the folder containing S1, S2, etc.
input_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\ai_for_thai\fake\wav_"+dataset_type 
# 2. Where to save the text file
output_meta = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\ai_for_thai\fake\thaispoof_metadata." + dataset_type + ".txt"
output_lst = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\ai_for_thai\fake\thaispoof_" + dataset_type + ".lst"

# Standard ASVspoof format: [Speaker_ID] [File_ID] - [Label] -
# For this dataset, we label them all as 'spoof'
label = "spoof"

files_found = 0

with open(output_meta, 'w') as f:
    # Walk through the folder and all subfolders (S1, S2, etc.)
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(".wav") or filename.endswith(".flac"):
                # Get the file name without the extension (e.g., 'S1_001')
                file_id = os.path.splitext(filename)[0]
                
                # Use the folder name as the Speaker ID
                speaker_id = file_id.split('_')[2]  # Assuming format is S1_001, S2_002, etc.
                
                # Write the line in ASVspoof format
                # Format: Speaker_ID File_ID - Label -
                f.write(f"S{speaker_id} {file_id} - {label} -\n")
                files_found += 1
                
with open(output_lst, 'w') as f:
    # Walk through the folder and all subfolders (S1, S2, etc.)
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith(".wav") or filename.endswith(".flac"):
                # Get the file name without the extension (e.g., 'S1_001')
                file_id = os.path.splitext(filename)[0]
                
                # Write the line in ASVspoof format
                # Format: Speaker_ID File_ID - Label -
                f.write(f"{file_id}\n")
                

print(f"Done! Found {files_found} files.")
print(f"Metadata file created at: {output_meta}")
print(f"List file created at: {output_lst}")