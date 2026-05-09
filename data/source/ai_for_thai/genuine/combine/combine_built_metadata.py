import os
import shutil
import random
from tqdm import tqdm
import soundfile as sf  # <-- Added for WAV to FLAC conversion

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES & RATIO
# ==========================================

random.seed(42) # For reproducibility

# 1. Define how many files of each class you want
TARGET_BONAFIDE_COUNT = None
TARGET_SPOOF_COUNT = None

# Default labels for this dataset
DEFAULT_LABEL = "bonafide" 
DEFAULT_ATTACK_TYPE = "-"

# 2. Source Folders (Where your current WAV files are)
SOURCE_WAV_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G1",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G2",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G3",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G4",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G5",
]

# 3. 🟢 NEW: Point directly to the TSV files instead of the built txt files
ORIGINAL_TSV_FILES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\train.tsv",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\test.tsv"
]

# 4. Target Destinations (Where the new FLAC files will go)
root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine"
DEST_FLAC_DIR = root_output_dir + r"\wav_all"
OUTPUT_METADATA_FILE = root_output_dir + r"\metadata.all.txt"
OUTPUT_LST_FILE = root_output_dir + r"\all.lst"

# ==========================================

def main():
    os.makedirs(DEST_FLAC_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_METADATA_FILE), exist_ok=True)
    
    if not os.path.exists(os.path.dirname(OUTPUT_LST_FILE)):
        os.makedirs(os.path.dirname(OUTPUT_LST_FILE), exist_ok=True)

    print("🔍 STEP 1: Mapping all available WAV files...")
    available_files = {} 
    
    for source_dir in SOURCE_WAV_DIRS: 
        if not os.path.exists(source_dir):
            print(f"⚠️ Warning: Source directory not found: {source_dir}")
            continue
            
        for filename in os.listdir(source_dir):
            if filename.endswith('.wav'): 
                file_id = filename.replace('.wav', '').replace('thai',f'thai_').strip()
                file_id = f"{file_id.split('_')[0]}_{DEFAULT_LABEL}_{int(file_id.split('_')[-1]):06d}"
                file_name = filename.strip()
                available_files[file_id] = os.path.join(source_dir, filename)
                
    print(f"✅ Found {len(available_files)} total WAV files on disk.\n")

    print("📊 STEP 2: Reading TSV files and categorizing...")
    bonafide_pool = []
    spoof_pool = []
    
    for tsv_path in ORIGINAL_TSV_FILES:
        if not os.path.exists(tsv_path):
            print(f"⚠️ Warning: TSV file not found: {tsv_path}")
            continue
            
        with open(tsv_path, 'r', encoding='utf-8') as f:
            header = f.readline() # Skip the header
            
            for line in f:
                
                # 🟢 FIX 1: Split by ANY whitespace. This completely fixes the Tab vs Space issue!
                parts = line.strip().split("\t")
                
                # If the line doesn't even have 5 words, it's a blank line, skip it.
                if len(parts) < 5:
                    continue
                   
                # Extract columns
                raw_speaker_id = parts[0]
                file_name = parts[1].replace('_', f'_{DEFAULT_LABEL}_')
                
                # 🟢 FIX 2: Since sentences have random spaces, 'environment' is ALWAYS the 2nd to last word!
                environment = "-"
                
                # Format IDs
                # Try/except block added just in case the ID isn't a clean number
                try:
                    speaker_id = f"thai_{DEFAULT_LABEL}_{int(raw_speaker_id):03d}" 
                except ValueError:
                    speaker_id = f"thai_{DEFAULT_LABEL}_{raw_speaker_id}"
                    
                file_id = file_name.replace('.wav', '').strip() 
                
                # Only process if we actually have the WAV file on disk
                if file_id in available_files:
                    
                    # Format: SPEAKER_ID FILE_ID ENVIRONMENT ATTACK_TYPE LABEL
                    meta_line = f"{speaker_id} {file_id} {environment} {DEFAULT_ATTACK_TYPE} {DEFAULT_LABEL}\n"
                    
                    file_data = {
                        "file_id": file_id,
                        "path": available_files[file_id],
                        "file_name": file_name.replace('.wav', '').strip(),
                        "meta_line": meta_line,
                        "speaker_id": speaker_id,
                        "label": DEFAULT_LABEL
                    }
                    
                    if DEFAULT_LABEL == "bonafide":
                        bonafide_pool.append(file_data)
                    elif DEFAULT_LABEL == "spoof":
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

    print("🚀 STEP 4: Converting WAV to FLAC and generating text lists...")
    final_meta_lines = []
    final_lst_lines = []
    
    for item in tqdm(final_selection, desc="Converting & Saving"):
        src_path = item["path"]
        dest_path = os.path.join(DEST_FLAC_DIR, item["file_name"] + ".flac")
        
        # 1. Convert WAV to FLAC
        if not os.path.exists(dest_path):
            try:
                data, samplerate = sf.read(src_path)
                sf.write(dest_path, data, samplerate, format='FLAC')
            except Exception as e:
                print(f"\n❌ Error converting {src_path}: {e}")
                continue 
            
        # 2. Append the lines we pre-formatted directly from the TSV
        final_meta_lines.append(item["meta_line"])
        final_lst_lines.append(item["file_id"] + "\n")

    with open(OUTPUT_METADATA_FILE, 'w', encoding='utf-8') as f:
        f.writelines(final_meta_lines)
        
    with open(OUTPUT_LST_FILE, 'w', encoding='utf-8') as f:
        f.writelines(final_lst_lines)

    print("\n🎉 Process Complete!")
    print(f"📄 Output Metadata: {OUTPUT_METADATA_FILE}")
    print(f"📄 Output LST:      {OUTPUT_LST_FILE}")

if __name__ == "__main__":
    main()