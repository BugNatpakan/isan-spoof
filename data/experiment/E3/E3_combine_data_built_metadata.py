import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - DATASETS & RATIOS
# ==========================================

# Where all the copied audio files and text files will be saved separately
root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E3"
DEST_AUDIO_DIR = root_output_dir + r"\wav_all"
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = root_output_dir + r"\scp"

# Configure exactly where each split comes from and how many files it needs.
# You can set Dataset 1 for Train/Dev, and Dataset 2 for Eval.
SPLIT_CONFIG = {
    "train": {
        # ---- DATASET 1 ----
        "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"],
        "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"],
        "target_bonafide": 3000,
        "target_spoof": 3000
    },
    "dev": {
        # ---- DATASET 1 (Same as Train) ----
        "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"],
        "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"],
        "target_bonafide": 1000,
        "target_spoof": 1000
    },
    "eval": {
        # ---- DATASET 2 (Totally separate dataset for testing) ----
        "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"],
        "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                       r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"],
        "target_bonafide": 1000,
        "target_spoof": 1000
    }
}
# ==========================================

def main():
    # Make sure all three destination folders exist
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    # This global set remembers which files have been used so Train and Dev 
    # NEVER accidentally use the exact same audio files (prevents data leakage).
    used_files = set() 

    # We process each split one by one (train -> dev -> eval)
    for split_name in ["train", "dev", "eval"]:
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        config = SPLIT_CONFIG[split_name]
        
        # 1. MAP AUDIO FILES
        print(f"🔍 Mapping available FLAC/WAV files...")
        available_files = {} 
        for source_dir in config["audio_dirs"]:
            if not os.path.exists(source_dir):
                print(f"   ⚠️ Dir not found: {source_dir}")
                continue
            for filename in os.listdir(source_dir):
                if filename.endswith(('.flac', '.wav')):
                    file_id = filename.replace('.flac', '').replace('.wav', '')
                    available_files[file_id] = os.path.join(source_dir, filename)
                    
        print(f"   ✅ Found {len(available_files)} total audio files in source folders.")

        # 2. READ METADATA & CATEGORIZE
        print(f"📊 Categorizing Bonafide and Spoof files...")
        bonafide_pool = []
        spoof_pool = []
        
        for meta_path in config["meta_files"]:
            if not os.path.exists(meta_path):
                print(f"   ⚠️ Meta not found: {meta_path}")
                continue
                
            with open(meta_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip('\n').split('\t')
                    if len(parts) < 2:
                        parts = line.strip().split()
                    if len(parts) < 2:
                        continue
                        
                    # Find the file_id dynamically
                    file_id = None
                    for part in parts:
                        clean_part = part.replace('.flac', '').replace('.wav', '').strip()
                        if clean_part in available_files:
                            file_id = clean_part
                            break
                    
                    if not file_id:
                        continue
                        
                    # 🛑 CRITICAL CHECK: Has this file already been used by an earlier split?
                    if file_id in used_files:
                        continue 

                    # Find the label
                    line_lower = line.lower()
                    if "bonafide" in line_lower:
                        label = "bonafide"
                    elif "spoof" in line_lower:
                        label = "spoof"
                    else:
                        continue 

                    file_data = {
                        "file_id": file_id,
                        "path": available_files[file_id],
                        "meta_line": line.strip('\n') + "\n"
                    }
                    
                    if label == "bonafide":
                        bonafide_pool.append(file_data)
                    elif label == "spoof":
                        spoof_pool.append(file_data)

        print(f"   ✅ Available unused pool: {len(bonafide_pool)} Bonafide | {len(spoof_pool)} Spoof")

        # 3. APPLY RATIO / LIMITS
        random.shuffle(bonafide_pool)
        random.shuffle(spoof_pool)
        
        selected_bonafide = bonafide_pool[:config["target_bonafide"]]
        selected_spoof = spoof_pool[:config["target_spoof"]]
        
        final_selection = selected_bonafide + selected_spoof
        random.shuffle(final_selection)
        
        print(f"   🎯 Target locked: Selected {len(selected_bonafide)} Bonafide | {len(selected_spoof)} Spoof")

        # 4. COPY FILES AND GENERATE TEXT
        final_meta_lines = []
        final_lst_lines = []
        
        for item in tqdm(final_selection, desc=f"   Copying {split_name.upper()} data"):
            src_path = item["path"]
            
            # Keep original extension so we don't break files
            ext = os.path.splitext(src_path)[1] 
            dest_path = os.path.join(DEST_AUDIO_DIR, item["file_id"] + ext)
            
            # Copy audio
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                
            # Add to text lists
            final_meta_lines.append(item["meta_line"])
            final_lst_lines.append(item["file_id"] + "\n")
            
            # Mark this file as USED so the next split can't grab it
            used_files.add(item["file_id"])

        
        # 5. SAVE SEPARATED TEXT FILES
        meta_output_path = os.path.join(DEST_META_DIR, f"metadata.{split_name}.txt")
        lst_output_path = os.path.join(DEST_LST_DIR, f"{split_name}.lst")
        
        with open(meta_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_meta_lines)
            
        with open(lst_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lst_lines)
            
        print(f"   📝 Saved Meta to: {meta_output_path}")
        print(f"   📝 Saved LST to:  {lst_output_path}")

    print("\n🚀 STEP: Auto-Merging Dev Metadata into Train Metadata...")
    train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    dev_meta_path = os.path.join(DEST_META_DIR, "metadata.dev.txt")

    if os.path.exists(train_meta_path) and os.path.exists(dev_meta_path):
        with open(train_meta_path, 'a', encoding='utf-8') as f_train:
            with open(dev_meta_path, 'r', encoding='utf-8') as f_dev:
                f_train.write("\n" + f_dev.read())
        print(f"✅ Successfully appended DEV labels into: metadata.train.txt")
    else:
        print("⚠️ Skipped auto-merge (No train or dev metadata found).")
        
    print("\n🎉 ALL DONE!")
    
    print("\n🎉 ALL SPLITS COMPLETED SUCCESSFULLY!")
    print(f"📂 Audio combined in: {DEST_AUDIO_DIR}")
    print(f"📂 Metadata generated in: {DEST_META_DIR}")
    print(f"📂 LST files generated in: {DEST_LST_DIR}")

if __name__ == "__main__":
    main()