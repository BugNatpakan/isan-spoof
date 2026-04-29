import os
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - PATH VARIABLES
# ==========================================

# 1. Your master metadata file (the one that has everything mixed together)
MASTER_METADATA_FILE = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1\metadata.all.txt"

# 2. Where to save the new split lists
LST_OUTPUT_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1\scp"
# 3. Where to save the new split metadata files
METADATA_OUTPUT_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E1"

# ==========================================

def main():
    os.makedirs(LST_OUTPUT_DIR, exist_ok=True)
    os.makedirs(METADATA_OUTPUT_DIR, exist_ok=True)

    print("📊 STEP 1: Reading Master Metadata and splitting by T / D / E ...")
    
    # Pools to hold the lines for each split
    train_meta, dev_meta, eval_meta = [], [], []
    train_lst, dev_lst, eval_lst = [], [], []
    
    unknown_count = 0

    if not os.path.exists(MASTER_METADATA_FILE):
        print(f"❌ Master metadata file not found: {MASTER_METADATA_FILE}")
        return
        
    with open(MASTER_METADATA_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        for line in tqdm(lines, desc="Sorting Data"):
            # Handle tabs or spaces smoothly
            parts = line.strip('\n').split('\t')
            if len(parts) < 2:
                parts = line.strip().split()
                
            if len(parts) < 2:
                continue
                
            # Column 2 is the File ID (e.g., LA_E_2520601)
            file_id = parts[1].strip()
            
            # 🔍 Check the indicator in the File ID to know where it belongs
            if "_T_" in file_id:
                train_meta.append(line)
                train_lst.append(file_id + "\n")
            elif "_D_" in file_id:
                dev_meta.append(line)
                dev_lst.append(file_id + "\n")
            elif "_E_" in file_id:
                eval_meta.append(line)
                eval_lst.append(file_id + "\n")
            else:
                unknown_count += 1

    print(f"\n✅ Sorting Complete!")
    print(f"   - Train: {len(train_lst)} files")
    print(f"   - Dev:   {len(dev_lst)} files")
    print(f"   - Eval:  {len(eval_lst)} files")
    if unknown_count > 0:
        print(f"   ⚠️ Ignored {unknown_count} lines because they didn't have _T_, _D_, or _E_ in the filename.")

    print("\n🚀 STEP 2: Saving the new separated files...")
    
    # Save TRAIN files
    with open(os.path.join(METADATA_OUTPUT_DIR, "metadata.train.txt"), 'w', encoding='utf-8') as f:
        f.writelines(train_meta)
    with open(os.path.join(LST_OUTPUT_DIR, "train.lst"), 'w', encoding='utf-8') as f:
        f.writelines(train_lst)
        
    # Save DEV files
    with open(os.path.join(METADATA_OUTPUT_DIR, "metadata.dev.txt"), 'w', encoding='utf-8') as f:
        f.writelines(dev_meta)
    with open(os.path.join(LST_OUTPUT_DIR, "dev.lst"), 'w', encoding='utf-8') as f:
        f.writelines(dev_lst)
        
    # Save EVAL files
    with open(os.path.join(METADATA_OUTPUT_DIR, "metadata.eval.txt"), 'w', encoding='utf-8') as f:
        f.writelines(eval_meta)
    with open(os.path.join(LST_OUTPUT_DIR, "eval.lst"), 'w', encoding='utf-8') as f:
        f.writelines(eval_lst)

    print(f"\n🎉 Process Complete! Metadata files saved to: {METADATA_OUTPUT_DIR}")
    print(f"\n🎉 Process Complete! LST files saved to: {LST_OUTPUT_DIR}")

if __name__ == "__main__":
    main()