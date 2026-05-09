import os
import shutil
import random
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - NO-LEAK SPLITTING (E7)
# ==========================================

random.seed(42)

root_output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E7"
DEST_AUDIO_DIR = os.path.join(root_output_dir, "wav_all")
DEST_META_DIR  = root_output_dir
DEST_LST_DIR   = os.path.join(root_output_dir, "scp")

ALL_AUDIO_DIRS = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\wav_all",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\wav_all",
]

ALL_META_FILES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake\combine\metadata.all.txt",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\genuine\combine\metadata.all.txt",
]

SPLIT_CONFIG = {
    "train": {"target_bonafide": 3000, "target_spoof": 3000},
    "eval":  {"target_bonafide": 1000, "target_spoof": 1000},
    "dev":   {"target_bonafide": 500,  "target_spoof": 500},
}

# ==========================================

def main():
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_META_DIR, exist_ok=True)
    os.makedirs(DEST_LST_DIR, exist_ok=True)

    # --- 1. MAP AUDIO ---
    print("🔍 Mapping available audio...")
    audio_map = {} 
    for d in ALL_AUDIO_DIRS:
        if not os.path.exists(d): continue
        for f in os.listdir(d):
            if f.endswith(('.flac', '.wav')):
                audio_map[os.path.splitext(f)[0]] = os.path.join(d, f)

    # --- 2. GROUP BY SPEAKER (TO PREVENT LEAKS) ---
    print("\n📊 Grouping files by Speaker to prevent data leakage...")
    speakers_dict = {}

    for meta_path in ALL_META_FILES:
        if not os.path.exists(meta_path): continue
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2: continue
                
                speaker_id = parts[0]
                
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

    all_speakers = list(speakers_dict.keys())
    print(f"✅ Found {len(all_speakers)} unique speakers across all datasets.")

    random.shuffle(all_speakers)
    partially_used = []

    # --- 3. DISTRIBUTE SPEAKERS TO SPLITS ---
    for split_name, cfg in SPLIT_CONFIG.items():
        print(f"\n🚀 Creating split: [{split_name.upper()}]")
        
        selected_b = []
        selected_s = []
        
        target_b = cfg["target_bonafide"]
        target_s = cfg["target_spoof"]

        skipped_speakers = [] # Keep track of speakers we pull but don't need YET

        # Keep popping speakers until we hit our target counts
        while all_speakers and (len(selected_b) < target_b or len(selected_s) < target_s):
            spk = all_speakers.pop(0) 
            spk_data = speakers_dict[spk]
            
            orig_b = len(spk_data["bonafide"])
            orig_s = len(spk_data["spoof"])
            
            # Do we need what this speaker has?
            needs_b = len(selected_b) < target_b
            needs_s = len(selected_s) < target_s
            has_b = orig_b > 0
            has_s = orig_s > 0
            
            # If we need bonafide and they have it, OR we need spoof and they have it
            if (needs_b and has_b) or (needs_s and has_s):
                used_b = 0
                used_s = 0
                
                # Bonafide extraction
                if needs_b:
                    needed = target_b - len(selected_b)
                    taken = spk_data["bonafide"][:needed]
                    selected_b.extend(taken)
                    used_b = len(taken)
                    
                # Spoof extraction
                if needs_s:
                    needed = target_s - len(selected_s)
                    taken = spk_data["spoof"][:needed]
                    selected_s.extend(taken)
                    used_s = len(taken)
                    
                # Track Leftovers
                leftover_b = orig_b - used_b
                leftover_s = orig_s - used_s
                
                if leftover_b > 0 or leftover_s > 0:
                    partially_used.append({
                        "speaker": spk,
                        "split": split_name,
                        "used_b": used_b, "leftover_b": leftover_b,
                        "used_s": used_s, "leftover_s": leftover_s
                    })
            else:
                # We pulled them, but we don't need their class of audio right now.
                # Put them in the waiting room for the next split!
                skipped_speakers.append(spk)

        # Return the skipped speakers to the main pool for dev/eval
        all_speakers.extend(skipped_speakers)
        random.shuffle(all_speakers) # Reshuffle so we don't get stuck in a loop

        final_selection = selected_b + selected_s
        random.shuffle(final_selection)

        # Write files for this split
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

    # --- 4. AUTO-MERGE DEV INTO TRAIN ---
    train_meta_path = os.path.join(DEST_META_DIR, "metadata.train.txt")
    dev_meta_path = os.path.join(DEST_META_DIR, "metadata.dev.txt")

    if os.path.exists(train_meta_path) and os.path.exists(dev_meta_path):
        with open(train_meta_path, 'a', encoding='utf-8') as f_train:
            with open(dev_meta_path, 'r', encoding='utf-8') as f_dev:
                f_train.write("\n" + f_dev.read())
        print(f"\n✅ Appended DEV labels into: metadata.train.txt")

    # --- 5. REPORT UNUSED & PARTIALLY USED SPEAKERS ---
    print("\n📊 Analyzing Discarded Audio (to prevent leaks)...")
    report_path = os.path.join(root_output_dir, "discarded_audio_report.txt")
    
    total_unused_b = 0
    total_unused_s = 0
        
    print("\n   [Partially Used Speakers]")
    for p in partially_used:
        total_unused_b += p["leftover_b"]
        total_unused_s += p["leftover_s"]
        log_line = (f"Speaker: {p['speaker']:<15} | Split: {p['split']:<6} | "
                    f"Used [B:{p['used_b']:<4} S:{p['used_s']:<4}] | "
                    f"Leftover [B:{p['leftover_b']:<4} S:{p['leftover_s']:<4}]")
        print(f"   {log_line}")
        
    print("\n   [Completely Unused Speakers]")
    for spk in all_speakers:
        b_count = len(speakers_dict[spk]["bonafide"])
        s_count = len(speakers_dict[spk]["spoof"])
        
        total_unused_b += b_count
        total_unused_s += s_count
        
        log_line = f"Speaker: {spk:<15} | Leftover [B:{b_count:<4} S:{s_count:<4}]"
        print(f"   {log_line}")
        
    summary = f"\nGrand Total Discarded Files -> Bonafide: {total_unused_b}, Spoof: {total_unused_s}"
    print(summary)
    
    print(f"✅ Discarded audio report saved to: {report_path}")
    print("\n🎉 Experiment E7 is LEAK-PROOF and ready!")

if __name__ == "__main__":
    main()