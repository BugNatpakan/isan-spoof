import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES & RATIO
# ==========================================

# 1. Define how many files of each class you want (This is your ratio limit)
# For example: 1000 bonafide and 1000 spoof = 1:1 ratio. 
# Set to None to use all available files.
TARGET_BONAFIDE_COUNT = None
TARGET_SPOOF_COUNT = None

# 2. Source Folders (Where your current FLAC files are)
SOURCE_WAV_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_dev",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_trn",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_eval"
]

# 3. Original Metadata Files (To know which file is spoof/bonafide)
ORIGINAL_METADATA_FILES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.dev.trl.txt",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.train.trn.txt",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.eval.trl.txt"
]

# 4. Target Destinations (Where the new FLAC files will go)
root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine"
DEST_FLAC_DIR = root_output_dir + r"\wav_all"
OUTPUT_METADATA_FILE = root_output_dir + r"\metadata.all.txt"
OUTPUT_LST_FILE = root_output_dir + r"\all.lst"

# ==========================================

def main():
    os.makedirs(DEST_FLAC_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_METADATA_FILE), exist_ok=True)
    
    # Ensure LST directory exists before we start processing
    if not os.path.exists(os.path.dirname(OUTPUT_LST_FILE)):
        os.makedirs(os.path.dirname(OUTPUT_LST_FILE), exist_ok=True)

    print("🔍 STEP 1: Mapping all available flac files...")
    available_files = {} # Dictionary to store {file_id: full_file_path}
    
    for source_dir in SOURCE_WAV_DIRS:
        if not os.path.exists(source_dir):
            print(f"⚠️ Warning: Source directory not found: {source_dir}")
            continue
            
        for filename in os.listdir(source_dir):
            if filename.endswith('.flac'):
                file_id = filename.replace('.flac', '') 
                available_files[file_id] = os.path.join(source_dir, filename)
                
    print(f"✅ Found {len(available_files)} total FLAC files on disk.\n")

    print("📊 STEP 2: Reading metadata and categorizing files...")
    bonafide_pool = []
    spoof_pool = []
    
    for meta_path in ORIGINAL_METADATA_FILES:
        if not os.path.exists(meta_path):
            print(f"⚠️ Warning: Metadata file not found: {meta_path}")
            continue
            
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip('\n').split(' ')
                
                # Check to prevent errors on empty lines
                if len(parts) < 2:
                    continue
                   
                speaker_id = parts[0] # Column 1 is the Speaker ID 
                file_id = parts[1].split(".")[0] # Column 2 is the File ID
                environment = parts[2] # Column 3 is the Environment
                attack_type = parts[3] # Column 4 is the Attack Type
                label = parts[4] # Column 5 is the label (bonafide/spoof)  
                
                # Only add to our pools if the physical audio file actually exists
                if file_id in available_files:
                    file_data = {
                        "file_id": file_id,
                        "path": available_files[file_id],
                        "speaker_id": speaker_id,
                        "environment": environment,
                        "attack_type": attack_type,
                        "label": label
                    }
                    
                    if label == "bonafide":
                        bonafide_pool.append(file_data)
                    elif label == "spoof":
                        spoof_pool.append(file_data)

    print(f"✅ Categorized {len(bonafide_pool)} Bonafide files and {len(spoof_pool)} Spoof files available.\n")

    print("⚖️ STEP 3: Applying ratio and selecting files...")
    random.shuffle(bonafide_pool)
    random.shuffle(spoof_pool)
    
    selected_bonafide = bonafide_pool[:TARGET_BONAFIDE_COUNT]
    selected_spoof = spoof_pool[:TARGET_SPOOF_COUNT]
    
    final_selection = selected_bonafide + selected_spoof
    random.shuffle(final_selection) 
    
    print(f"✅ Selected exactly {len(selected_bonafide)} Bonafide and {len(selected_spoof)} Spoof files to process.\n")

    print("🚀 STEP 4: Copying FLAC files and generating text lists...")
    final_meta_lines = []
    final_lst_lines = []
    
    for item in tqdm(final_selection, desc="Copying & Saving"):     
        src_path = item["path"]
        dest_path = os.path.join(DEST_FLAC_DIR, item["file_id"] + ".flac")
        
        # 1. Physically copy the FLAC file (THIS WAS MISSING!)
        if not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)
            
        # 2. Store the lines for our text files
        final_meta_lines.append(f"{item['speaker_id']} {item['file_id']} {item['environment']} {item['attack_type']} {item['label']}\n")
        final_lst_lines.append(f"{item['file_id']}\n")

    # Write the validated lines to the new output files
    with open(OUTPUT_METADATA_FILE, 'w', encoding='utf-8') as f:
        f.writelines(final_meta_lines)
        
    with open(OUTPUT_LST_FILE, 'w', encoding='utf-8') as f:
        f.writelines(final_lst_lines)

    print("\n🎉 Process Complete!")
    print(f"📄 Output Metadata: {OUTPUT_METADATA_FILE}")
    print(f"📄 Output LST:      {OUTPUT_LST_FILE}")

if __name__ == "__main__":
    main()