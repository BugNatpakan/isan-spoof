import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES & RATIO
# ==========================================

# 1. Define how many files of each class you want (This is your ratio limit)
# For example: 1000 bonafide and 1000 spoof = 1:1 ratio
TARGET_BONAFIDE_COUNT = 1000
TARGET_SPOOF_COUNT = 1000

# 2. Source Folders (Where your current FLAC files are)
SOURCE_FLAC_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
]

# 3. Original Metadata Files (To know which file is spoof/bonafide)
ORIGINAL_METADATA_FILES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
]

# 4. Target Destinations (Where the new files will go)
DEST_FLAC_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1.5\wav_all"
OUTPUT_METADATA_FILE = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1.5\metadata.eval.txt"
OUTPUT_LST_FILE = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1.5\scp\eval.lst"

# ==========================================

def main():
    # 🛠️ FIX 1: Ensure all destination folders (including scp) exist BEFORE we do anything else
    os.makedirs(DEST_FLAC_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_METADATA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_LST_FILE), exist_ok=True)

    print("🔍 STEP 1: Mapping all available FLAC files...")
    available_files = {} 
    
    for source_dir in SOURCE_FLAC_DIRS:
        if not os.path.exists(source_dir):
            print(f"⚠️ Warning: Source directory not found: {source_dir}")
            continue
            
        for filename in os.listdir(source_dir):
            if filename.endswith('.flac'):
                file_id = filename.replace('.flac', '')
                available_files[file_id] = os.path.join(source_dir, filename)
                
    print(f"✅ Found {len(available_files)} total FLAC files on disk.\n")

    print("📊 STEP 2: Reading metadata and categorizing files dynamically...")
    bonafide_pool = []
    spoof_pool = []
    
    for meta_path in ORIGINAL_METADATA_FILES:
        if not os.path.exists(meta_path):
            print(f"⚠️ Warning: Metadata file not found: {meta_path}")
            continue
            
        with open(meta_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                # Handle both tabs and spaces cleanly
                parts = line.strip('\n').split('\t')
                if len(parts) < 2:
                    parts = line.strip().split()
                
                if len(parts) < 2:
                    continue
                    
                # 🛠️ FIX 2: Dynamic Column Matching! 
                # Instead of assuming the column, check if any word in the line matches an available audio file.
                file_id = None
                for part in parts:
                    clean_part = part.replace('.flac', '').replace('.wav', '').strip()
                    if clean_part in available_files:
                        file_id = clean_part
                        break
                
                if not file_id:
                    # Print a helpful debug warning for the first line that fails so we can see what's wrong
                    if i == 0:
                        print(f"\n⚠️ DEBUG: Could not match audio file for the first line in {os.path.basename(meta_path)}")
                        print(f"   Line contents: {parts}\n")
                    continue

                # Dynamically find the label by just checking if the word exists in the line
                line_lower = line.lower()
                if "bonafide" in line_lower:
                    label = "bonafide"
                elif "spoof" in line_lower:
                    label = "spoof"
                else:
                    continue # Skip if it has neither label

                # Add the matched file to our pool
                file_data = {
                    "file_id": file_id,
                    "path": available_files[file_id],
                    "meta_line": line.strip('\n') + "\n"
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
    
    print(f"✅ Selected exactly {len(selected_bonafide)} Bonafide and {len(selected_spoof)} Spoof files to copy.\n")

    print("🚀 STEP 4: Copying files and generating text lists...")
    final_meta_lines = []
    final_lst_lines = []
    
    for item in tqdm(final_selection, desc="Processing Output"):
        src_path = item["path"]
        dest_path = os.path.join(DEST_FLAC_DIR, item["file_id"] + ".flac")
        
        # 1. Copy the physical FLAC file
        if not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)
            
        # 2. Store the lines for our text files
        final_meta_lines.append(item["meta_line"])
        final_lst_lines.append(item["file_id"] + "\n")

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