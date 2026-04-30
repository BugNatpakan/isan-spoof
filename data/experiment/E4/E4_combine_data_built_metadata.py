import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - DATASETS & RATIOS
# ==========================================

root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E4"
DEST_AUDIO_DIR = os.path.join(root_output_dir, "wav_all")
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = os.path.join(root_output_dir, "scp")

SPLIT_CONFIG = {
    "train": [
        {
            "name": "ASVspoof2019LA", 
            "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"],
            "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"],
            "target_bonafide": 1000, 
            "target_spoof": 1000    
        },
        {
            "name": "ai_for_thai", 
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
            ],
            "target_bonafide": 1000, 
            "target_spoof": 1000    
        },
        {
            "name": "isan", 
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"
            ],
            "target_bonafide": 3000, 
            "target_spoof": 3000    
        }
    ],
    "dev": [
        {
            "name": "ASVspoof2019LA", 
            "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"],
            "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"],
            "target_bonafide": 250, 
            "target_spoof": 250    
        },
        {
            "name": "ai_for_thai", 
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all", 
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
            ],
            "target_bonafide": 250, 
            "target_spoof": 250    
        },
        {
            "name": "isan", 
            "audio_dirs": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\wav_all",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\flac"
            ],
            "meta_files": [
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\isan_tts\combine\metadata.all.txt",
                r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.txt"
            ],
            "target_bonafide": 750, 
            "target_spoof": 750    
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
# 🧠 HELPER: SPEAKER IDENTIFICATION
# ==========================================
def get_speaker_id(file_id, parts):
    """Dynamically identifies the speaker from the filename or ASVspoof line."""
    # 1. ASVspoof format: SPEAKER_ID is parts[0], FILE_ID is parts[1]
    if len(parts) >= 2 and parts[1] == file_id:
        return parts[0]
    
    # 2. scb10x format: scb10x_is_m_008_fin_0159_m_017 -> speaker is m_008
    if "scb10x" in file_id:
        tokens = file_id.split('_')
        if len(tokens) >= 4:
            return f"scb10x_{tokens[3]}"
            
    # 3. Fallback: if parts[0] is not the file_id or a label, assume it's speaker
    if parts[0] not in [file_id, "bonafide", "spoof", "-", "genuine", "fake"]:
        return parts[0]
        
    # 4. If no clear speaker ID exists, treat the file as its own unique speaker
    return file_id 

# ==========================================

def main():
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    # Delete the merged train metadata if it exists so we don't append to an old run
    merged_train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    if os.path.exists(merged_train_meta_path):
        os.remove(merged_train_meta_path)

    # 🟢 NEW: Global memory to track which SPEAKERS have been used
    global_used_speakers = set()
    used_files = set() 

    # Process each split (train, dev, eval)
    # 🟢 SMART SPLIT: Process Eval first, then Dev, then Train
    for split_name in ["eval", "dev", "train"]:
        if split_name not in SPLIT_CONFIG: 
            continue
        datasets = SPLIT_CONFIG[split_name]
        
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        split_final_selection = []
        current_split_speakers = set() # Tracks speakers used in THIS specific split
        
        # Process each individual dataset within the split
        for dataset in datasets:
            print(f"\n📁 Dataset: {dataset['name']}")
            
            # 1. MAP AUDIO FILES
            available_files = {} 
            for source_dir in dataset["audio_dirs"]:
                if not os.path.exists(source_dir):
                    print(f"   ⚠️ Dir not found: {source_dir}")
                    continue
                for filename in os.listdir(source_dir):
                    if filename.endswith(('.flac', '.wav')):
                        file_id = filename.replace('.flac', '').replace('.wav', '')
                        available_files[file_id] = os.path.join(source_dir, filename)
            
            # 2. READ METADATA & CATEGORIZE BY SPEAKER
            bonafide_by_speaker = {}
            spoof_by_speaker = {}
            
            for meta_path in dataset["meta_files"]:
                if not os.path.exists(meta_path):
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
                            
                        # Extract Speaker ID
                        speaker_id = get_speaker_id(file_id, parts)

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
                            "speaker_id": speaker_id,
                            "path": available_files[file_id],
                            "meta_line": line.strip('\n') + "\n"
                        }
                        
                        if label == "bonafide":
                            if speaker_id not in bonafide_by_speaker: bonafide_by_speaker[speaker_id] = []
                            bonafide_by_speaker[speaker_id].append(file_data)
                        elif label == "spoof":
                            if speaker_id not in spoof_by_speaker: spoof_by_speaker[speaker_id] = []
                            spoof_by_speaker[speaker_id].append(file_data)

            # 3. EXTRACT ENTIRE SPEAKERS TO REACH TARGET RATIOS
            def extract_files_by_speaker(speaker_dict, target_count):
                selected = []
                speakers = list(speaker_dict.keys())
                random.shuffle(speakers)
                
                for spk in speakers:
                    if len(selected) >= target_count:
                        break
                        
                    # 🛑 PREVENT LEAKAGE: 
                    # If this speaker was used in a PREVIOUS split (e.g. Train), skip them completely!
                    if spk in global_used_speakers and spk not in current_split_speakers:
                        continue
                        
                    files_to_add = speaker_dict[spk]
                    selected.extend(files_to_add)
                    
                    # Lock this speaker globally so future splits (Dev/Eval) can't use them
                    global_used_speakers.add(spk)
                    current_split_speakers.add(spk)
                    
                # Trim to the exact requested target size
                return selected[:target_count]

            selected_bonafide = extract_files_by_speaker(bonafide_by_speaker, dataset["target_bonafide"])
            selected_spoof = extract_files_by_speaker(spoof_by_speaker, dataset["target_spoof"])
            
            # Print status
            total_b = sum(len(v) for v in bonafide_by_speaker.values())
            total_s = sum(len(v) for v in spoof_by_speaker.values())
            print(f"   ✅ Available:      {total_b} Bonafide | {total_s} Spoof")
            print(f"   🎯 Ratio Achieved: {len(selected_bonafide)} Bonafide | {len(selected_spoof)} Spoof.")
            
            # Add to the master pool for this split
            split_final_selection.extend(selected_bonafide + selected_spoof)
            
        # -------------------------------------------------------------
        # Mix and copy files
        # -------------------------------------------------------------
        print(f"\n🔄 Mixing all {len(split_final_selection)} files for {split_name.upper()}...")
        random.shuffle(split_final_selection)
        
        final_meta_lines = []
        final_lst_lines = []
        
        for item in tqdm(split_final_selection, desc=f"   Copying data"):
            src_path = item["path"]
            ext = os.path.splitext(src_path)[1] 
            dest_path = os.path.join(DEST_AUDIO_DIR, item["file_id"] + ext)
            
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                
            final_meta_lines.append(item["meta_line"])
            final_lst_lines.append(item["file_id"] + "\n")

        # MERGE TRAIN & DEV METADATA
        lst_output_path = os.path.join(DEST_LST_DIR, f"{split_name}.lst")
        
        if split_name in ["train", "dev"]:
            meta_output_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
            write_mode = 'a' 
        else:
            meta_output_path = os.path.join(DEST_META_DIR, f"metadata.{split_name}.txt")
            write_mode = 'w'

        with open(meta_output_path, write_mode, encoding='utf-8') as f:
            f.writelines(final_meta_lines)
            
        with open(lst_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lst_lines)
            
        print(f"   📝 Saved Meta to: {meta_output_path}")
        print(f"   📝 Saved LST to:  {lst_output_path}")

    print("\n🎉 ALL SPLITS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()