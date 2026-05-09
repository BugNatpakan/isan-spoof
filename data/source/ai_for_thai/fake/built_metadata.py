import os

# --- CONFIGURATION ---
# Base directory where your TSV files are stored
base_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\ai_for_thai\fake"

# The names of the splits you want to process
splits = ["train", "test"]

# Standard labels for real speech
label = "spoof"
attack_type = "-"

print("🚀 Starting Batch TSV to ASVspoof conversion...\n")

for split in splits:
    # Set the input and output paths dynamically for "train" then "test"
    input_tsv = os.path.join(base_dir, f"{split}.tsv")  # Looks for train.tsv, then test.tsv
    output_meta = os.path.join(base_dir, f"metadata.{split}.txt")
    output_lst = os.path.join(base_dir, f"{split}.lst")
    
    # Check if the TSV file exists before trying to process it
    if not os.path.exists(input_tsv):
        print(f"⚠️ Warning: File not found: {input_tsv}. Skipping...")
        continue
        
    print(f"📂 Processing '{split.upper()}' dataset...")
    files_found = 0
    
    with open(input_tsv, 'r', encoding='utf-8') as f_in, \
         open(output_meta, 'w', encoding='utf-8') as f_meta, \
         open(output_lst, 'w', encoding='utf-8') as f_lst:
        
        # 1. Read and skip the header line (speaker_id file_name gender ...)
        header = f_in.readline()

        # 2. Process line by line
        for line in f_in:
            # Use \t to split by Tab, protecting the spaces inside the sentences
            parts = line.strip('\n').split('\t')
            
            # Ensure the line has all the expected columns
            if len(parts) < 6:
                continue
                
            # Extract data
            raw_speaker_id = parts[0].strip()
            file_name = parts[1].strip()
            environment = parts[4].strip() 
            
            # Format the IDs perfectly
            speaker_id = f"thai_spoof_{int(raw_speaker_id):03d}"  # Converts 28 to thai_028
            file_id = file_name.replace('.wav', '').strip() # Removes .wav
            
            # 🟢 Create perfect ASVspoof format: SPEAKER_ID FILE_ID ATTACK_TYPE ENVIRONMENT LABEL
            meta_line = f"{speaker_id} {file_id} {environment} {attack_type} {label}\n"
            
            # Write to files
            f_meta.write(meta_line)
            f_lst.write(f"{file_id}\n")
            
            files_found += 1

    print(f"   ✅ Successfully processed {files_found} files.")
    print(f"   📄 Metadata saved to: {output_meta}")
    print(f"   📄 LST saved to:      {output_lst}\n")

print("🎉 All TSV datasets processed successfully!")