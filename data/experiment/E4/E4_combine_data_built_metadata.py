import os
import shutil
import random
from tqdm import tqdm

random.seed(42)

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================

COPY_AUDIO_FILES = True # Set to True if you actually want to copy the .wav/.flac files

root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E4"
DEST_AUDIO_DIR = os.path.join(root_output_dir, "wav_all")
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = os.path.join(root_output_dir, "scp")

# 🎯 DEFINE YOUR SPLITS & DATASETS HERE
SPLIT_CONFIG = {
    "train": [
        {
            "name": "ASVspoof2019LA", 
            "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"],
            "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"],
            "target_bonafide": 1000, "target_spoof": 1000    
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
            "target_bonafide": 1000, "target_spoof": 1000    
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
            "target_bonafide": 3000, "target_spoof": 3000    
        }
    ],
    "dev": [
        {
            "name": "ASVspoof2019LA", 
            "audio_dirs": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\wav_all"],
            "meta_files": [r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\combine\metadata.all.txt"],
            "target_bonafide": 250, "target_spoof": 250    
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
            "target_bonafide": 250, "target_spoof": 250    
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
            "target_bonafide": 750, "target_spoof": 750    
        }
    ],
    "eval": [
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
            "target_bonafide": 1000, "target_spoof": 1000
        }
    ]
}

# ==========================================

def main():
    if COPY_AUDIO_FILES:
        os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    global_used_speakers = set()
    partially_used_log = []

    for split_name in ["train", "eval", "dev",]:
        if split_name not in SPLIT_CONFIG: 
            continue
            
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        datasets = SPLIT_CONFIG[split_name]
        split_final_selection = []
        
        for dataset in datasets:
            print(f"\n📁 Dataset: {dataset['name']}")
            
            # --- 1. MAP AUDIO FILES ---
            audio_map = {} 
            for source_dir in dataset["audio_dirs"]:
                if not os.path.exists(source_dir):
                    print(f"❌ ERROR: Cannot find audio folder: {source_dir}")
                    continue
                for filename in os.listdir(source_dir):
                    if filename.endswith(('.flac', '.wav')):
                        orig_file_id = filename.replace('.flac', '').replace('.wav', '')
                        audio_map[orig_file_id.lower()] = {
                            "orig_id": orig_file_id,
                            "path": os.path.join(source_dir, filename)
                        }
            
            # --- 2. READ METADATA ---
            speakers_dict = {}
            
            for meta_path in dataset["meta_files"]:
                if not os.path.exists(meta_path):
                    print(f"❌ ERROR: Cannot find metadata file: {meta_path}")
                    continue
                    
                with open(meta_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip('\n').split()
                        if len(parts) < 2: continue
                            
                        speaker_id = parts[0]
                        
                        # 🛑 LEAK PREVENTION: Ignore speaker if already used in a previous split!
                        if speaker_id in global_used_speakers:
                            continue
                        
                        # find File ID
                        file_id = None
                        file_path = None
                        for p in parts:
                            clean_p = p.replace('.flac', '').replace('.wav', '').lower()
                            if clean_p in audio_map:
                                file_id = audio_map[clean_p]["orig_id"]  # Get the real casing
                                file_path = audio_map[clean_p]["path"]
                                break
                                
                        if not file_id: continue
                            
                        # Labeling
                        line_lower = line.lower()
                        if "bonafide" in line_lower or "genuine" in line_lower:
                            label = "bonafide"
                        elif "spoof" in line_lower or "fake" in line_lower:
                            label = "spoof"
                        else:
                            continue
                            
                        # Format standard metadata line
                        attack_type = "-"
                        if len(parts) >= 5 and label == "spoof":
                            attack_type = parts[2]
                            
                        perfect_meta_line = f"{speaker_id} {file_id} {attack_type} - {label}\n"

                        if speaker_id not in speakers_dict:
                            speakers_dict[speaker_id] = {"bonafide": [], "spoof": []}
                            
                        speakers_dict[speaker_id][label].append({
                            "file_id": file_id,
                            "path": file_path,
                            "meta_line": perfect_meta_line
                        })

            available_speakers = list(speakers_dict.keys())
            random.shuffle(available_speakers)

            # --- 3. EXTRACT QUOTAS SAFELY ---
            target_b = dataset["target_bonafide"]
            target_s = dataset["target_spoof"]
            
            selected_b = []
            selected_s = []
            skipped_speakers = []
            
            while available_speakers and (len(selected_b) < target_b or len(selected_s) < target_s):
                spk = available_speakers.pop(0)
                spk_data = speakers_dict[spk]
                
                orig_b = len(spk_data["bonafide"])
                orig_s = len(spk_data["spoof"])
                
                needs_b = len(selected_b) < target_b
                needs_s = len(selected_s) < target_s
                has_b = orig_b > 0
                has_s = orig_s > 0
                
                if (needs_b and has_b) or (needs_s and has_s):
                    used_b = 0
                    used_s = 0
                    
                    if needs_b:
                        needed = target_b - len(selected_b)
                        taken = spk_data["bonafide"][:needed]
                        selected_b.extend(taken)
                        used_b = len(taken)
                        
                    if needs_s:
                        needed = target_s - len(selected_s)
                        taken = spk_data["spoof"][:needed]
                        selected_s.extend(taken)
                        used_s = len(taken)
                        
                    # Lock this speaker globally so future splits can never use them
                    global_used_speakers.add(spk)
                    
                    leftover_b = orig_b - used_b
                    leftover_s = orig_s - used_s
                    
                    if leftover_b > 0 or leftover_s > 0:
                        partially_used_log.append({
                            "dataset": dataset['name'], "speaker": spk, "split": split_name,
                            "used_b": used_b, "leftover_b": leftover_b,
                            "used_s": used_s, "leftover_s": leftover_s
                        })
                else:
                    skipped_speakers.append(spk)
            
            print(f"   🎯 Achieved: [{len(selected_b)}/{target_b}] Bonafide | [{len(selected_s)}/{target_s}] Spoof")
            split_final_selection.extend(selected_b + selected_s)
            
        # --- 4. MIX & WRITE OUTPUT FOR THIS SPLIT ---
        print(f"\n🔄 Compiling data for {split_name.upper()}...")
        random.shuffle(split_final_selection)
        
        final_meta_lines = []
        final_lst_lines = []
        
        for item in tqdm(split_final_selection, desc=f"   Processing data"):
            if COPY_AUDIO_FILES:
                ext = os.path.splitext(item["path"])[1] 
                dest_path = os.path.join(DEST_AUDIO_DIR, item["file_id"] + ext)
                if not os.path.exists(dest_path):
                    shutil.copy2(item["path"], dest_path)
                
            final_meta_lines.append(item["meta_line"])
            final_lst_lines.append(item["file_id"] + "\n")

        # Output logic
        lst_output_path = os.path.join(DEST_LST_DIR, f"{split_name}.lst")
        meta_output_path = os.path.join(DEST_META_DIR, f"metadata.{split_name}.txt")

        with open(meta_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_meta_lines)
            
        with open(lst_output_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lst_lines)

    # --- 5. AUTO-MERGE DEV INTO TRAIN METADATA ---
    train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    dev_meta_path = os.path.join(DEST_META_DIR, "metadata.dev.txt")

    if os.path.exists(train_meta_path) and os.path.exists(dev_meta_path):
        with open(train_meta_path, 'a', encoding='utf-8') as f_train:
            with open(dev_meta_path, 'r', encoding='utf-8') as f_dev:
                f_train.write("\n" + f_dev.read())
        print(f"\n✅ Appended DEV labels into: metadata.train.txt")

    # --- 6. REPORT PARTIALLY USED SPEAKERS ---
    report_path = os.path.join(root_output_dir, "discarded_audio_report.txt")
    total_unused_b, total_unused_s = 0, 0
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== PARTIALLY USED SPEAKERS (Discarded to Prevent Leaks) ===\n")
        for p in partially_used_log:
            total_unused_b += p["leftover_b"]
            total_unused_s += p["leftover_s"]
            log_line = (f"Dataset: {p['dataset']:<14} | Speaker: {p['speaker']:<15} | Split: {p['split']:<5} | "
                        f"Used [B:{p['used_b']:<4} S:{p['used_s']:<4}] | "
                        f"Leftover [B:{p['leftover_b']:<4} S:{p['leftover_s']:<4}]")
            f.write(log_line + "\n")
            
        summary = f"\Total Discarded Files -> Bonafide: {total_unused_b}, Spoof: {total_unused_s}"
        f.write(summary + "\n")
        
    print(f"\n🎉 DATASET BUILD COMPLETE!")
    print(f"📊 A detailed report of discarded files to prevent leaks was saved to: {report_path}")

if __name__ == "__main__":
    main()