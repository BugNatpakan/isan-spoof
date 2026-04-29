import os
import shutil
import random
from tqdm import tqdm
import soundfile as sf  # <-- Added for WAV to FLAC conversion

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES & RATIO
# ==========================================

# 1. Define how many files of each class you want (This is your ratio limit)
# For example: 1000 bonafide and 1000 spoof = 1:1 ratio. 
# Set to None to use all available files.
TARGET_BONAFIDE_COUNT = None
TARGET_SPOOF_COUNT = None

# 2. Source Folders (Where your current WAV files are)
SOURCE_WAV_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G1",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G2",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G3",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G4",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\G5",
]

# 3. Original Metadata Files (To know which file is spoof/bonafide)
ORIGINAL_METADATA_FILES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\genuine.tsv"
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
    
    # Ensure LST directory exists before we start processing
    if not os.path.exists(os.path.dirname(OUTPUT_LST_FILE)):
        os.makedirs(os.path.dirname(OUTPUT_LST_FILE), exist_ok=True)

    print("🔍 STEP 1: Mapping all available WAV files...")
    available_files = {} # Dictionary to store {file_id: full_file_path}
    
    for source_dir in SOURCE_WAV_DIRS: # <-- Changed to iterate through your WAV dirs
        if not os.path.exists(source_dir):
            print(f"⚠️ Warning: Source directory not found: {source_dir}")
            continue
            
        for filename in os.listdir(source_dir):
            if filename.endswith('.wav'): # <-- Changed to look for .wav
                file_id = filename.replace('.wav', '') # <-- Changed to strip .wav
                available_files[file_id] = os.path.join(source_dir, filename)
                
    print(f"✅ Found {len(available_files)} total WAV files on disk.\n")

    print("📊 STEP 2: Reading metadata and categorizing files...")
    bonafide_pool = []
    spoof_pool = []
    
    for meta_path in ORIGINAL_METADATA_FILES:
        if not os.path.exists(meta_path):
            print(f"⚠️ Warning: Metadata file not found: {meta_path}")
            continue
            
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 🛑 CRITICAL FIX FOR TSV: 
                # strip('\n') removes only the line break, and split('\t') splits ONLY on tabs.
                parts = line.strip('\n').split('\t')
                
                # Check to prevent errors on empty lines
                if len(parts) < 2:
                    continue
                   
                speaker_id = parts[0] # Column 1 is the Speaker ID 
                file_id = parts[1].split(".")[0] # Column 2 is the File ID
                label = "bonafide"  
                

                # Only add to our pools if the physical audio file actually exists
                if file_id in available_files:
                    file_data = {
                        "file_id": file_id,
                        "path": available_files[file_id],
                        "meta_line": line.strip() + "\n",
                        "speaker_id": speaker_id,
                        "label": label
                    }
                    
                    if label == "bonafide":
                        bonafide_pool.append(file_data)
                    elif label == "spoof":
                        spoof_pool.append(file_data)

    print(f"✅ Categorized {len(bonafide_pool)} Bonafide files and {len(spoof_pool)} Spoof files available.\n")

    print("⚖️ STEP 3: Applying ratio and selecting files...")
    # Shuffle pools so we get a random selection of files instead of just the first ones
    random.shuffle(bonafide_pool)
    random.shuffle(spoof_pool)
    
    # Slice the lists to match your target counts (If None, it takes all of them)
    selected_bonafide = bonafide_pool[:TARGET_BONAFIDE_COUNT]
    selected_spoof = spoof_pool[:TARGET_SPOOF_COUNT]
    
    # Combine the selected files into one master list
    final_selection = selected_bonafide + selected_spoof
    # Shuffle one more time so bonafide and spoof are mixed together in your new list
    random.shuffle(final_selection) 
    
    print(f"✅ Selected exactly {len(selected_bonafide)} Bonafide and {len(selected_spoof)} Spoof files to process.\n")

    print("🚀 STEP 4: Converting WAV to FLAC and generating text lists...")
    final_meta_lines = []
    final_lst_lines = []
    
    for item in tqdm(final_selection, desc="Converting & Saving"):
        src_path = item["path"]
        dest_path = os.path.join(DEST_FLAC_DIR, item["file_id"] + ".flac")
        
        # 1. Read WAV and write as FLAC
        if not os.path.exists(dest_path):
            try:
                data, samplerate = sf.read(src_path)
                sf.write(dest_path, data, samplerate, format='FLAC')
            except Exception as e:
                print(f"\n❌ Error converting {src_path}: {e}")
                continue # Skip adding to list if conversion fails
            
        # 2. Store the lines for our text files
        final_meta_lines.append("S_" + item["speaker_id"].zfill(7) + " " + item["file_id"] + " - " + item["label"] + " - \n") # <-- Adjusted to match ASVspoof format
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