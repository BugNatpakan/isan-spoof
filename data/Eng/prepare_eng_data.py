import os
import shutil
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# 🛑 TESTING LIMIT (Set to an integer like 50 for testing, or None for full run)
TEST_LIMIT = None 

# 1. Audio source folders to merge
AUDIO_SOURCES = [
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_trn",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_dev",
    r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\wav_eval"
]

# 2. Text files to copy and verify (Keep them separate)
TEXT_FILES = [
    {
        "meta_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.train.trn.txt",
        "lst_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan\scp\train.lst",
        "meta_dst_name": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\metadata.train.txt",
        "lst_dst_name": r"\scp\train.lst"
    },
    {
        "meta_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.dev.trl.txt",
        "lst_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan\scp\dev.lst",
        "meta_dst_name": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\metadata.dev.txt",
        "lst_dst_name": r"\scp\dev.lst"
    },
    {
        "meta_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\ASVspoof2019.LA.cm.eval.trl.txt",
        "lst_src": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan\scp\eval.lst",
        "meta_dst_name": r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ASVspoof_2019_LA\metadata.eval.txt",
        "lst_dst_name": r"\scp\eval.lst"
    }
]

# 3. Destination Directories
DEST_AUDIO_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Eng\wav_all"
DEST_TEXT_DIR  = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Eng"
# ==========================================

def main():
    os.makedirs(DEST_AUDIO_DIR, exist_ok=True)
    os.makedirs(DEST_TEXT_DIR, exist_ok=True)

    # ==========================================
    # 🎵 PHASE 1: MERGE AUDIO FILES
    # ==========================================
    print(f"📂 Merging audio into: {DEST_AUDIO_DIR}")
    if TEST_LIMIT:
        print(f"🛑 TEST MODE ACTIVE: Limiting to {TEST_LIMIT} files per folder.")

    total_audio_copied = 0
    
    for source_dir in AUDIO_SOURCES:
        if not os.path.exists(source_dir):
            print(f"⚠️ Audio source not found, skipping: {source_dir}")
            continue

        files = [f for f in os.listdir(source_dir) if f.endswith(('.wav', '.flac'))]
        
        # Apply the test limit here
        if TEST_LIMIT is not None:
            files = files[:TEST_LIMIT]

        for filename in tqdm(files, desc=f"Copying from {os.path.basename(source_dir)}"):
            src_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(DEST_AUDIO_DIR, filename)
            
            # Copy only if it doesn't already exist to avoid redundant overwrites
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                total_audio_copied += 1

    print(f"✅ Total audio files copied: {total_audio_copied}\n")

    # ==========================================
    # 📄 PHASE 2: VERIFY AND COPY TEXT FILES
    # ==========================================
    print(f"📂 Verifying text files and saving to: {DEST_TEXT_DIR}")
    
    for item in TEXT_FILES:
        meta_src = item["meta_src"]
        lst_src = item["lst_src"]
        
        # Extract just the filename to append to the DEST_TEXT_DIR correctly
        meta_dst = os.path.join(DEST_TEXT_DIR, os.path.basename(item["meta_dst_name"]))
        lst_dst = os.path.join(DEST_TEXT_DIR, os.path.basename(item["lst_dst_name"]))

        valid_meta_lines = []
        valid_lst_lines = []
        missing_count = 0

        # --- Process Metadata ---
        if os.path.exists(meta_src):
            with open(meta_src, 'r', encoding='utf-8') as f:
                meta_lines = f.readlines()
                
            for line in tqdm(meta_lines, desc=f"Scanning {os.path.basename(meta_src)}", leave=False):
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                file_id = parts[1] # The 2nd column is the file name (no extension)
                wav_exists = os.path.exists(os.path.join(DEST_AUDIO_DIR, file_id + ".wav"))
                flac_exists = os.path.exists(os.path.join(DEST_AUDIO_DIR, file_id + ".flac"))
                
                if wav_exists or flac_exists:
                    valid_meta_lines.append(line.strip() + "\n")
                else:
                    missing_count += 1
        else:
            print(f"⚠️ Metadata source not found: {meta_src}")

        # --- Process LST ---
        if os.path.exists(lst_src):
            with open(lst_src, 'r', encoding='utf-8') as f:
                lst_lines = f.readlines()
                
            for line in tqdm(lst_lines, desc=f"Scanning {os.path.basename(lst_src)}", leave=False):
                file_id = line.strip()
                if not file_id:
                    continue
                    
                wav_exists = os.path.exists(os.path.join(DEST_AUDIO_DIR, file_id + ".wav"))
                flac_exists = os.path.exists(os.path.join(DEST_AUDIO_DIR, file_id + ".flac"))
                
                if wav_exists or flac_exists:
                    valid_lst_lines.append(file_id + "\n")
        else:
            print(f"⚠️ LST source not found: {lst_src}")

        # --- Save Validated Files ---
        if valid_meta_lines:
            with open(meta_dst, 'w', encoding='utf-8') as f:
                f.writelines(valid_meta_lines)
            
        if valid_lst_lines:
            with open(lst_dst, 'w', encoding='utf-8') as f:
                f.writelines(valid_lst_lines)

        print(f"✅ Verified {os.path.basename(meta_dst)}: {len(valid_meta_lines)} valid lines. (Dropped {missing_count} missing files)")

    print("\n🎉 Process Complete! Your audio is merged and your lists are verified.")

if __name__ == "__main__":
    main()