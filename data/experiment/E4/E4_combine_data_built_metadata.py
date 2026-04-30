import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - DATASETS & RATIOS
# ==========================================

# Where all the copied audio files and text files will be saved separately
root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E4"
DEST_AUDIO_DIR = os.path.join(root_output_dir, "wav_all")
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = os.path.join(root_output_dir, "scp")

# Configure multiple datasets per split, with specific ratios for EACH dataset.
SPLIT_CONFIG = {
    "train": [
        {
            "name": "ASVspoof2019LA", # Example of a dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"
            ],
            "target_bonafide": 1000, # Extracts exactly 1000 bonafide from ASVspoof2019LA
            "target_spoof": 1000     # Extracts exactly 1000 spoof from ASVspoof2019LA
        },
        {
            "name": "ai_for_thai", # Example of a second dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
            ],
            "target_bonafide": 1000, # Extracts exactly 1000 bonafide from another_dataset
            "target_spoof": 1000     # Extracts exactly 1000 spoof from another_dataset
        },
        {
            "name": "isan", # Example of a second dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"
            ],
            "target_bonafide": 3000, # Extracts exactly 3000 bonafide from another_dataset
            "target_spoof": 3000     # Extracts exactly 3000 spoof from another_dataset
        }
    ],
    "dev": [
        {
            "name": "ASVspoof2019LA", # Example of a dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"
            ],
            "target_bonafide": 250, # Extracts exactly 1000 bonafide from ASVspoof2019LA
            "target_spoof": 250     # Extracts exactly 1000 spoof from ASVspoof2019LA
        },
        {
            "name": "ai_for_thai", # Example of a second dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
            ],
            "target_bonafide": 250, # Extracts exactly 1000 bonafide from another_dataset
            "target_spoof": 250     # Extracts exactly 1000 spoof from another_dataset
        },
        {
            "name": "isan", # Example of a second dataset mixed into train
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"
            ],
            "target_bonafide": 750, # Extracts exactly 3000 bonafide from another_dataset
            "target_spoof": 750     # Extracts exactly 3000 spoof from another_dataset
        }
        
    ],
    "eval": [
        {
            "name": "isan",
            "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                           r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"],
            "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                           r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"],
            "target_bonafide": 1000,
            "target_spoof": 1000
        },
    ]
}
# ==========================================

def main():
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    # Global memory to prevent any data leakage across splits
    used_files = set() 

    # Process each split (train, dev, eval)
    for split_name, datasets in SPLIT_CONFIG.items():
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        split_final_selection = []
        
        # Process each individual dataset within the split
        for dataset in datasets:
            print(f"\n📁 Dataset: {dataset['name']}")
            
            # 1. MAP AUDIO FILES FOR THIS SPECIFIC DATASET
            available_files = {} 
            for source_dir in dataset["audio_dirs"]:
                if not os.path.exists(source_dir):
                    print(f"   ⚠️ Dir not found: {source_dir}")
                    continue
                for filename in os.listdir(source_dir):
                    if filename.endswith(('.flac', '.wav')):
                        file_id = filename.replace('.flac', '').replace('.wav', '')
                        available_files[file_id] = os.path.join(source_dir, filename)
            
            # 2. READ METADATA & CATEGORIZE
            ds_bonafide_pool = []
            ds_spoof_pool = []
            
            for meta_path in dataset["meta_files"]:
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
                            
                        # Dynamically find file_id
                        file_id = None
                        for part in parts:
                            clean_part = part.replace('.flac', '').replace('.wav', '').strip()
                            if clean_part in available_files:
                                file_id = clean_part
                                break
                        
                        if not file_id:
                            continue
                            
                        # 🛑 LEAKAGE CHECK
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
                            ds_bonafide_pool.append(file_data)
                        elif label == "spoof":
                            ds_spoof_pool.append(file_data)

            # 3. APPLY THIS DATASET'S RATIO LIMITS
            random.shuffle(ds_bonafide_pool)
            random.shuffle(ds_spoof_pool)
            
            # Extract exactly the requested amount for THIS dataset
            selected_bonafide = ds_bonafide_pool[:dataset["target_bonafide"]]
            selected_spoof = ds_spoof_pool[:dataset["target_spoof"]]
            
            print(f"   ✅ Available Unused: {len(ds_bonafide_pool)} Bonafide | {len(ds_spoof_pool)} Spoof")
            print(f"   🎯 Locked Ratio:     {len(selected_bonafide)} Bonafide | {len(selected_spoof)} Spoof extracted.")
            
            # Add this dataset's selected files into the master split pool
            split_final_selection.extend(selected_bonafide + selected_spoof)
            
        # -------------------------------------------------------------
        # All datasets for this split are loaded. Now we mix and copy!
        # -------------------------------------------------------------
        print(f"\n🔄 Mixing all {len(split_final_selection)} files for {split_name.upper()}...")
        random.shuffle(split_final_selection)
        
        final_meta_lines = []
        final_lst_lines = []
        
        for item in tqdm(split_final_selection, desc=f"   Copying data"):
            src_path = item["path"]
            ext = os.path.splitext(src_path)[1] 
            dest_path = os.path.join(DEST_AUDIO_DIR, item["file_id"] + ext)
            
            # Copy audio
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                
            # Add to text lists
            final_meta_lines.append(item["meta_line"])
            final_lst_lines.append(item["file_id"] + "\n")
            
            # Mark this file as USED globally
            used_files.add(item["file_id"])

        # SAVE SEPARATED TEXT FILES
        meta_output_path = os.path.join(DEST_META_DIR, f"metadata.{split_name}.txt")
        lst_output_path = os.path.join(DEST_LST_DIR, f"{split_name}.lst")
        
        with open(meta_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_meta_lines)
            
        with open(lst_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lst_lines)
            
        print(f"   📝 Saved Meta to: {meta_output_path}")
        print(f"   📝 Saved LST to:  {lst_output_path}")

    print("\n🎉 ALL SPLITS COMPLETED SUCCESSFULLY!")
    print(f"📂 Audio combined in: {DEST_AUDIO_DIR}")
    print(f"📂 Metadata generated in: {DEST_META_DIR}")
    print(f"📂 LST files generated in: {DEST_LST_DIR}")

if __name__ == "__main__":
    main()