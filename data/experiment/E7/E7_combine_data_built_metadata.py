import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ UNIVERSAL CONFIGURATION
# ==========================================

random.seed(42)

root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E7"
DEST_AUDIO_DIR = os.path.join(root_output_dir, "wav_all")
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = os.path.join(root_output_dir, "scp")

# 🎯 DEFINE YOUR SPLITS HERE
# You can point any split to any combination of datasets. The script will 
# automatically manage speaker-disjointness to prevent data leaks.
SPLIT_CONFIG = {
    "train": {
        "audio_dirs": [
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all",
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
        ],
        "meta_files": [
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
        ],
        "target_bonafide": 2500, 
        "target_spoof": 2500
    },
    "dev": {
        "audio_dirs": [
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all",
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all"
        ],
        "meta_files": [
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
            r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt"
        ],
        "target_bonafide": 500,  
        "target_spoof": 500
    },
    "eval": {
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
    }
}

# ==========================================

def main():
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    global_used_speakers = set()
    partially_used_log = []

    # Process each split independently
    for split_name, cfg in SPLIT_CONFIG.items():
        print(f"\n" + "="*50)
        print(f"🚀 PROCESSING SPLIT: [{split_name.upper()}]")
        print(f"="*50)
        
        target_b = cfg["target_bonafide"]
        target_s = cfg["target_spoof"]

        # --- 1. MAP AUDIO FOR THIS SPLIT ---
        audio_map = {} 
        for d in cfg["audio_dirs"]:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if f.endswith(('.flac', '.wav')):
                    audio_map[os.path.splitext(f)[0]] = os.path.join(d, f)

        # --- 2. BUILD SPEAKER DICTIONARY FOR THIS SPLIT ---
        speakers_dict = {}
        for meta_path in cfg["meta_files"]:
            if not os.path.exists(meta_path): continue
            with open(meta_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 2: continue
                    
                    speaker_id = parts[0]
                    
                    # 🛑 THE LEAK PREVENTER: Skip if speaker was already used in a previous split
                    if speaker_id in global_used_speakers:
                        continue
                        
                    file_id = None
                    for p in parts:
                        clean_p = p.replace('.flac','').replace('.wav','')
                        if clean_p in audio_map:
                            file_id = clean_p
                            break
                    
                    if not file_id: continue
                    
                    label = "bonafide" if "bonafide" in line.lower() else "spoof"
                    
                    if speaker_id not in speakers_dict:
                        speakers_dict[speaker_id] = {"bonafide": [], "spoof": []}
                        
                    speakers_dict[speaker_id][label].append({
                        "file_id": file_id, 
                        "path": audio_map[file_id], 
                        "line": line.strip() + "\n"
                    })

        available_speakers = list(speakers_dict.keys())
        print(f"✅ Found {len(available_speakers)} safe, unused speakers in source folders.")

        random.shuffle(available_speakers)

        selected_b = []
        selected_s = []
        skipped_speakers = [] 

        # --- 3. DRAW DATA UNTIL TARGETS ARE MET ---
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
                        "speaker": spk, "split": split_name,
                        "used_b": used_b, "leftover_b": leftover_b,
                        "used_s": used_s, "leftover_s": leftover_s
                    })
            else:
                # Put them back into the queue in case we need them later in THIS split
                skipped_speakers.append(spk)

        # Warnings if data is insufficient
        if len(selected_b) < target_b or len(selected_s) < target_s:
            print(f"⚠️ WARNING: Ran out of data! Got [{len(selected_b)}/{target_b}] Bonafide and [{len(selected_s)}/{target_s}] Spoof.")

        final_selection = selected_b + selected_s
        random.shuffle(final_selection)

        # --- 4. COPY FILES ---
        meta_lines, lst_lines = [], []
        for item in tqdm(final_selection, desc=f"   Copying {split_name} files"):
            ext = os.path.splitext(item["path"])[1]
            dest = os.path.join(DEST_AUDIO_DIR, item["file_id"] + ext)
            if not os.path.exists(dest):
                shutil.copy2(item["path"], dest)
            
            meta_lines.append(item["line"])
            lst_lines.append(item["file_id"] + "\n")

        with open(os.path.join(DEST_META_DIR, f"metadata.{split_name}.txt"), 'w', encoding='utf-8') as f:
            f.writelines(meta_lines)
        with open(os.path.join(DEST_LST_DIR, f"{split_name}.lst"), 'w', encoding='utf-8') as f:
            f.writelines(lst_lines)
        
        print(f"   ✨ {split_name} complete: {len(selected_b)} Bonafide, {len(selected_s)} Spoof")

    # --- 5. AUTO-MERGE DEV INTO TRAIN ---
    print("\n" + "="*50)
    print("🚀 POST-PROCESSING")
    print("="*50)
    train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    dev_meta_path = os.path.join(DEST_META_DIR, "metadata.dev.txt")

    if os.path.exists(train_meta_path) and os.path.exists(dev_meta_path):
        with open(train_meta_path, 'a', encoding='utf-8') as f_train:
            with open(dev_meta_path, 'r', encoding='utf-8') as f_dev:
                f_train.write("\n" + f_dev.read())
        print(f"✅ Appended DEV labels into: metadata.train.txt")

    # --- 6. REPORT PARTIALLY USED SPEAKERS ---
    report_path = os.path.join(root_output_dir, "discarded_audio_report.txt")
    total_unused_b, total_unused_s = 0, 0
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== PARTIALLY USED SPEAKERS (Discarded to Prevent Leaks) ===\n")
        print("\n📊 Analyzing Partially Discarded Audio...")
        for p in partially_used_log:
            total_unused_b += p["leftover_b"]
            total_unused_s += p["leftover_s"]
            log_line = (f"Speaker: {p['speaker']:<15} | Split: {p['split']:<6} | "
                        f"Used [B:{p['used_b']:<4} S:{p['used_s']:<4}] | "
                        f"Leftover [B:{p['leftover_b']:<4} S:{p['leftover_s']:<4}]")
            f.write(log_line + "\n")
            
        summary = f"\nGrand Total Discarded Files -> Bonafide: {total_unused_b}, Spoof: {total_unused_s}"
        print(summary)
        f.write(summary + "\n")
        
    print(f"✅ Discarded audio report saved to: {report_path}")
    print("\n🎉 UNIVERSAL DATASET BUILD COMPLETE!")

if __name__ == "__main__":
    main()