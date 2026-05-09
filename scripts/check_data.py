import os

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
root_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E7" 
lst_dir = os.path.join(root_dir, "scp")
meta_dir = root_dir

lst_files = {
    "train": os.path.join(lst_dir, "train.lst"),
    "dev":   os.path.join(lst_dir, "dev.lst"),
    "eval":  os.path.join(lst_dir, "eval.lst")
}

counts = {
    "train": {
        "ASV": {"total":0, "bonafide":0, "spoof":0}, 
        "Thai": {"total":0, "bonafide":0, "spoof":0}, 
        "Isan": {"total":0, "bonafide":0, "spoof":0}
    }, 
    "dev": {
        "ASV": {"total":0, "bonafide":0, "spoof":0}, 
        "Thai": {"total":0, "bonafide":0, "spoof":0}, 
        "Isan": {"total":0, "bonafide":0, "spoof":0}
    },
    "eval": {
        "ASV": {"total":0, "bonafide":0, "spoof":0}, 
        "Thai": {"total":0, "bonafide":0, "spoof":0}, 
        "Isan": {"total":0, "bonafide":0, "spoof":0}
    }
}

# ==========================================
# 1. BUILD MASTER ANSWER KEY FROM ALL METADATA
# ==========================================
master_key = {}

for f_name in os.listdir(meta_dir):
    if f_name.startswith("metadata.") and f_name.endswith(".txt"):
        with open(os.path.join(meta_dir, f_name), 'r', encoding='utf-8') as f:
            for line in f:
                line_lower = line.strip().lower()
                parts = line_lower.split()
                
                for p in parts:
                    clean_p = p.replace('.flac', '').replace('.wav', '')
                    if len(clean_p) > 2: 
                        master_key[clean_p] = line_lower

# ==========================================
# 2. COUNT DIRECTLY FROM .LST FILES
# ==========================================
for split_name, lst_path in lst_files.items():
    if not os.path.exists(lst_path):
        continue
        
    with open(lst_path, 'r', encoding='utf-8') as f:
        for line in f:
            file_id = line.strip()
            if not file_id: continue
            
            # 🛑 FIX: Force the file_id to lowercase for the dictionary lookup!
            file_id_key = file_id.lower()
            meta_line = master_key.get(file_id_key, "")
            
            if not meta_line:
                print(f"⚠️ Warning: {file_id} found in {split_name}.lst but has no metadata!")
                continue
                
            # --- Determine Domain ---
            domain = None
            if "la_" in meta_line:
                domain = "ASV"
            elif ("thai_spoof" in meta_line or "thai_bonafide" in meta_line or "genuine" in meta_line) and "isan" not in meta_line:
                domain = "Thai"
            elif any(k in meta_line for k in ["rvc", "tts", "isan_spoof", "typhoon"]):
                domain = "Isan"
                
            # --- Determine Label ---
            label = None
            # 🛑 FIX: Safely catch "genuine" as well as "bonafide"
            if "bonafide" in meta_line or "genuine" in meta_line:
                label = "bonafide"
            elif "spoof" in meta_line:
                label = "spoof"
                
            # --- Apply to Counters ---
            if domain and label:
                counts[split_name][domain]["total"] += 1
                counts[split_name][domain][label] += 1

# ==========================================
# 3. PRINT RESULTS
# ==========================================
total_files = sum(
    counts[split][domain]["total"] 
    for split in counts for domain in counts[split]
)

print(f"\n📊 DATASET STATISTICS (Sourced strictly from .lst files) for {os.path.basename(root_dir)}")
print("="*60)
print(f"Total Files: {total_files}")

for split in counts:
    split_total = sum(counts[split][domain]['total'] for domain in counts[split])
    if split_total == 0:
        continue
        
    print(f"\n[{split.upper()}] - Total: {split_total}")
    print("-" * 40)
    
    for domain in counts[split]:
        domain_total = counts[split][domain]["total"]
        if domain_total > 0:
            b_count = counts[split][domain]["bonafide"]
            s_count = counts[split][domain]["spoof"]
            pct = (domain_total / total_files) * 100
            
            print(f"  {domain:<6}: {domain_total:<5} ({pct:>4.1f}%) | Bonafide: {b_count:<4} | Spoof: {s_count:<4}")
            
print("="*60)


# 1. BUILD MASTER DICTIONARY (File ID -> Speaker ID)
file_to_speaker = {}
for f_name in os.listdir(meta_dir):
    if f_name.startswith("metadata.") and f_name.endswith(".txt"):
        with open(os.path.join(meta_dir, f_name), 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    speaker = parts[0]
                    # Check every part of the line to find the file ID
                    for p in parts:
                        clean_p = p.replace('.flac', '').replace('.wav', '').lower()
                        if len(clean_p) > 2:
                            file_to_speaker[clean_p] = speaker

# 2. COLLECT SPEAKERS FOR EACH SPLIT
split_speakers = {"train": set(), "dev": set(), "eval": set()}

for split in ["train", "dev", "eval"]:
    lst_path = os.path.join(lst_dir, f"{split}.lst")
    if not os.path.exists(lst_path): continue
        
    with open(lst_path, 'r', encoding='utf-8') as f:
        for line in f:
            file_id = line.strip().lower()
            if file_id in file_to_speaker:
                split_speakers[split].add(file_to_speaker[file_id])

# 3. TEST FOR LEAKS (Intersections)
print("\nRUNNING DATA LEAK DETECTIVE...")
print("="*50)
print(f"Total Unique Speakers in TRAIN: {len(split_speakers['train'])}")
print(f"Total Unique Speakers in DEV:   {len(split_speakers['dev'])}")
print(f"Total Unique Speakers in EVAL:  {len(split_speakers['eval'])}")
print("-" * 50)

# Mathematical Intersection (Finds items that exist in BOTH sets)
train_dev_leak = split_speakers["train"].intersection(split_speakers["dev"])
train_eval_leak = split_speakers["train"].intersection(split_speakers["eval"])
dev_eval_leak = split_speakers["dev"].intersection(split_speakers["eval"])

if len(train_dev_leak) == 0 and len(train_eval_leak) == 0 and len(dev_eval_leak) == 0:
    print("✅ PERFECT! ZERO DATA LEAKAGE DETECTED.")
    print("All splits are 100% strictly speaker-disjoint.")
else:
    print("❌ WARNING! DATA LEAK DETECTED!")
    if train_dev_leak: print(f"   Train/Dev overlap: {train_dev_leak}")
    if train_eval_leak: print(f"   Train/Eval overlap: {train_eval_leak}")
    if dev_eval_leak: print(f"   Dev/Eval overlap: {dev_eval_leak}")
print("="*50)