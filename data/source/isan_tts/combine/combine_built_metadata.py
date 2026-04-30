import os
import shutil
import random
from tqdm import tqdm
import soundfile as sf  # <-- Added for WAV to FLAC conversion

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES & RATIO
# ==========================================

# 1. Define how many files of each class you want (This is your ratio limit)
TARGET_BONAFIDE_COUNT = None
TARGET_SPOOF_COUNT = None

# 2. Source Folders (Where your current WAV files are)
SOURCE_WAV_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\pure-rvc",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\pure-tts",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\tts-rvc",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\ex-1000"
]

# 3. Target Destinations (Where the new FLAC files will go)
root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine"
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
    available_files = {} # Dictionary to store data
    
    for source_dir in SOURCE_WAV_DIRS:
        if not os.path.exists(source_dir):
            print(f"⚠️ Warning: Source directory not found: {source_dir}")
            continue

        for subdir in os.listdir(source_dir):
            subdir_path = os.path.join(source_dir, subdir)
            
            # Skip if it is a file instead of a folder
            if not os.path.isdir(subdir_path):
                continue
                
            # Extract the names of the folders
            folder_name = os.path.basename(os.path.normpath(source_dir))
            subfolder_name = os.path.basename(os.path.normpath(subdir_path))
            
            for filename in os.listdir(subdir_path):
                if filename.endswith('.wav'):
                    file_id = filename.replace('.wav', '')
                    
                    # Store BOTH the path and the formatted speaker ID
                    available_files[file_id] = {
                        "path": os.path.join(subdir_path, filename),
                        "speaker_id": folder_name + "_" + subfolder_name 
                    }
                
    print(f"✅ Found {len(available_files)} total WAV files on disk.\n")

    print("📊 STEP 2: Categorizing files...")
    bonafide_pool = []
    spoof_pool = []
    
    # We don't need a metadata TSV file anymore! 
    # Just loop through the files we already found on the hard drive.
    for file_id, file_info in available_files.items():
        
        # As requested: ALL files in these folders are spoof
        label = "spoof"  
        
        file_data = {
            "file_id": file_id,
            "path": file_info["path"],
            "speaker_id": file_info["speaker_id"], 
            "label": label
        }
        
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
        dest_path = os.path.join(DEST_FLAC_DIR, item["file_id"] + ".flac")
        
        # 1. Read WAV and write as FLAC
        if not os.path.exists(dest_path):
            try:
                data, samplerate = sf.read(src_path)
                sf.write(dest_path, data, samplerate, format='FLAC')
            except Exception as e:
                print(f"\n❌ Error converting {src_path}: {e}")
                continue 
            
        # 2. Store the lines for our text files
        # This creates the exact ASVspoof format: "SPEAKER_ID AUDIO_ID - spoof - "
        final_meta_lines.append(item["speaker_id"] + " " + item["file_id"] + " - " + item["label"] + " - \n") 
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