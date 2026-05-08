import os
import shutil
import random
from tqdm import tqdm

# 🟢 Locks the randomness so your thesis experiments are perfectly reproducible!
random.seed(42)

# ==========================================
# ⚙️ CONFIGURATION - DATASETS & RATIOS
# ==========================================

COPY_AUDIO_FILES = False 

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

def main():
    if COPY_AUDIO_FILES:
        os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    # Delete the merged train metadata if it exists
    merged_train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    if os.path.exists(merged_train_meta_path):
        os.remove(merged_train_meta_path)

    global_used_speakers = set()

    # Process each split
    for split_name in ["eval", "dev", "train"]:
        if split_name not in SPLIT_CONFIG: 
            continue
        datasets = SPLIT_CONFIG[split_name]
        
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        split_final_selection = []
        current_split_speakers = set() 
        
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
            
            # 2. READ STRICT ASVSPOOF METADATA
            bonafide_by_speaker = {}
            spoof_by_attack = {} 
            
            for meta_path in dataset["meta_files"]:
                if not os.path.exists(meta_path):
                    continue
                    
                with open(meta_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip('\n').split()
                        
                        # Strict format check: SPEAKER_ID FILE_ID ATTACK_TYPE - LABEL
                        if len(parts) < 5:
                            continue
                            
                        speaker_id = parts[0]
                        file_id = parts[1].replace('.flac', '').replace('.wav', '').strip()
                        attack_type = parts[2]
                        label = parts[4].lower()

                        # Skip if we don't have the audio file
                        if file_id not in available_files:
                            continue
                            
                        perfect_meta_line = f"{speaker_id} {file_id} {attack_type} - {label}\n"

                        file_data = {
                            "file_id": file_id,
                            "speaker_id": speaker_id,
                            "path": available_files[file_id],
                            "meta_line": perfect_meta_line
                        }
                        
                        if label == "bonafide":
                            if speaker_id not in bonafide_by_speaker: bonafide_by_speaker[speaker_id] = []
                            bonafide_by_speaker[speaker_id].append(file_data)
                        elif label == "spoof":
                            if attack_type not in spoof_by_attack: spoof_by_attack[attack_type] = {}
                            if speaker_id not in spoof_by_attack[attack_type]: spoof_by_attack[attack_type][speaker_id] = []
                            spoof_by_attack[attack_type][speaker_id].append(file_data)

            # 3. HELPER: EXTRACT SPEAKERS SAFELY
            def extract_files_by_speaker(speaker_dict, target_count):
                selected = []
                speakers = list(speaker_dict.keys())
                random.shuffle(speakers) 
                
                for spk in speakers:
                    if len(selected) >= target_count:
                        break
                        
                    if spk in global_used_speakers and spk not in current_split_speakers:
                        continue
                        
                    files_to_add = speaker_dict[spk]
                    selected.extend(files_to_add)
                    
                    global_used_speakers.add(spk)
                    current_split_speakers.add(spk)
                    
                return selected[:target_count]

            # 4. PERFORM EXTRACTIONS
            selected_bonafide = extract_files_by_speaker(bonafide_by_speaker, dataset["target_bonafide"])
            
            selected_spoof = []
            if spoof_by_attack:
                attack_types = list(spoof_by_attack.keys())
                target_spoof = dataset["target_spoof"]
                base_quota = target_spoof // len(attack_types)
                remainder = target_spoof % len(attack_types)
                
                print(f"   ⚖️ Balancing {target_spoof} spoof files across {len(attack_types)} attack types: {attack_types}")
                
                for i, atk in enumerate(attack_types):
                    quota = base_quota + (1 if i < remainder else 0)
                    atk_selected = extract_files_by_speaker(spoof_by_attack[atk], quota)
                    selected_spoof.extend(atk_selected)
                    
            # 🟢 5. CALCULATE & PRINT FILES PER SPEAKER
            b_speaker_counts = {}
            for item in selected_bonafide:
                b_speaker_counts[item["speaker_id"]] = b_speaker_counts.get(item["speaker_id"], 0) + 1
                
            s_speaker_counts = {}
            for item in selected_spoof:
                s_speaker_counts[item["speaker_id"]] = s_speaker_counts.get(item["speaker_id"], 0) + 1

            unique_b_speakers = len(b_speaker_counts)
            unique_s_speakers = len(s_speaker_counts)

            print(f"   🎯 Ratio Achieved: {len(selected_bonafide)} Bonafide ({unique_b_speakers} speakers) | {len(selected_spoof)} Spoof ({unique_s_speakers} speakers).")
            
            # Format the dictionary nicely so it doesn't look like messy code
            print(f"      👉 Bonafide Breakdown: {', '.join(f'{k}: {v}' for k, v in b_speaker_counts.items())}")
            print(f"      👉 Spoof Breakdown:    {', '.join(f'{k}: {v}' for k, v in s_speaker_counts.items())}")
            
            split_final_selection.extend(selected_bonafide + selected_spoof)
            
        # -------------------------------------------------------------
        # Mix and output files
        # -------------------------------------------------------------
        print(f"\n🔄 Compiling data for {split_name.upper()}...")
        random.shuffle(split_final_selection)
        
        final_meta_lines = []
        final_lst_lines = []
        
        for item in tqdm(split_final_selection, desc=f"   Processing data"):
            if COPY_AUDIO_FILES:
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
        print(f"   👥 Total Unique Speakers in {split_name.upper()} Split: {len(current_split_speakers)}")

    print("\n🎉 ALL SPLITS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()