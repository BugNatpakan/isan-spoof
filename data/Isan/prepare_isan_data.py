import os
import shutil
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split

''' 
    This script is used to combine datasets, create ASVspoof-style metadata files, 
    and split them into stratified train, dev, and eval files (.lst and metadata).
'''

# ==========================================
# ⚙️ CONFIGURATION (Set your folders here)
# ==========================================
DIR_1 = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan\flac"
LABEL_1 = "bonafide"
PREFIX_1 = "real_" 

DIR_2 = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan\flac"
LABEL_2 = "spoof"
PREFIX_2 = "fake_"

# Output Directories
OUTPUT_AUDIO_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan\wav_all"
OUTPUT_METADATA_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan"
OUTPUT_SCP_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\Isan\scp"

TRAIN_SIZE = 0.80 

# 🚧 TESTING / LIMIT
MAX_FILES_PER_CLASS = 20 # Set to None to process all files
# ==========================================

def process_folder(source_dir, label, prefix, output_dir, metadata_list, limit=None):
    if not os.path.exists(source_dir):
        print(f"⚠️ Directory not found, skipping: {source_dir}")
        return

    files = [f for f in os.listdir(source_dir) if f.endswith('.wav') or f.endswith('.flac')]
    
    if not files:
        print(f"⚠️ No files found in {source_dir}")
        return

    if limit is not None:
        files = files[:limit]
        print(f"📁 Processing directory: {source_dir} (Label: {label}) -> Limited to {limit} files")
    else:
        print(f"📁 Processing directory: {source_dir} (Label: {label}) -> All {len(files)} files")
    
    for filename in tqdm(files, desc=f"Copying {label}"):
        # Extract base name without extension
        base_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        # New names
        new_base_name = f"{prefix}{base_name}"
        new_filename = f"{new_base_name}{ext}" 
        
        src_path = os.path.join(source_dir, filename)
        dst_path = os.path.join(output_dir, new_filename)
        
        # Copy the file
        shutil.copy2(src_path, dst_path)
        
        # --- Format for ASVspoof ---
        col1_speaker = "ISAN_SPK"               
        col2_file_id = new_base_name            
        col3_env = "-"                          
        col4_attack = "-" if label == "bonafide" else "TTS" 
        col5_label = label                      
        
        asv_format_line = f"{col1_speaker} {col2_file_id} {col3_env} {col4_attack} {col5_label}"
        
        metadata_list.append({
            "base_name": new_base_name,
            "label": label,
            "metadata_line": asv_format_line
        })

def main():
    os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_METADATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_SCP_DIR, exist_ok=True)
    
    metadata_list = []

    process_folder(DIR_1, LABEL_1, PREFIX_1, OUTPUT_AUDIO_DIR, metadata_list, limit=MAX_FILES_PER_CLASS)
    process_folder(DIR_2, LABEL_2, PREFIX_2, OUTPUT_AUDIO_DIR, metadata_list, limit=MAX_FILES_PER_CLASS)

    if not metadata_list:
        print("❌ No audio files were processed. Exiting.")
        return

    # --- NEW: Create Full .lst and Metadata ---
    full_lst_path = os.path.join(OUTPUT_SCP_DIR, "full.lst")
    full_metadata_path = os.path.join(OUTPUT_METADATA_DIR, "metadata.full.txt")
    
    with open(full_lst_path, 'w', encoding='utf-8') as f_lst, \
         open(full_metadata_path, 'w', encoding='utf-8') as f_meta:
        for item in metadata_list:
            f_lst.write(f"{item['base_name']}\n")
            f_meta.write(f"{item['metadata_line']}\n")
            
    print(f"\n✅ Master files created:")
    print(f"   - LST: {full_lst_path}")
    print(f"   - META: {full_metadata_path}")

    # ==========================================
    # ✂️ SPLITTING LOGIC START
    # ==========================================
    print("\n⏳ Starting dataset split...")
    df = pd.DataFrame(metadata_list)
    total_files = len(df)
    
    stratify_col = df['label'] if len(df['label'].unique()) > 1 else None

    # Split: Train vs Temp
    train_df, temp_df = train_test_split(
        df, 
        train_size=TRAIN_SIZE, 
        random_state=42, 
        stratify=stratify_col
    )
    
    # Split: Temp -> Dev and Eval
    stratify_temp = temp_df['label'] if stratify_col is not None else None
    dev_df, eval_df = train_test_split(
        temp_df, 
        test_size=0.50, 
        random_state=42, 
        stratify=stratify_temp
    )

    # 6. Save split files (Both .lst and .txt metadata)
    def save_split_files(dataframe, subset_name):
        lst_path = os.path.join(OUTPUT_SCP_DIR, f"{subset_name}.lst")
        meta_path = os.path.join(OUTPUT_METADATA_DIR, f"metadata.{subset_name}.txt")
        
        # Write .lst file (just the filename)
        with open(lst_path, 'w', encoding='utf-8') as f_lst:
            for _, row in dataframe.iterrows():
                f_lst.write(f"{row['base_name']}\n")
                
        # Write ASVspoof metadata file
        with open(meta_path, 'w', encoding='utf-8') as f_meta:
            for _, row in dataframe.iterrows():
                f_meta.write(f"{row['metadata_line']}\n")
                
        return lst_path, meta_path

    # Execute the saves
    train_lst, train_meta = save_split_files(train_df, "train")
    dev_lst, dev_meta = save_split_files(dev_df, "dev")
    eval_lst, eval_meta = save_split_files(eval_df, "eval")

    print("\n🎉 Splitting Complete!")
    print(f"📊 Total files processed: {total_files}")
    print(f"🔹 Train set : {len(train_df)} files -> {train_meta}")
    print(f"🔹 Dev set   : {len(dev_df)} files -> {dev_meta}")
    print(f"🔹 Eval set  : {len(eval_df)} files -> {eval_meta}")

if __name__ == "__main__":
    main()