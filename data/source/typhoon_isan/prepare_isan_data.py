import pandas as pd
import librosa
import soundfile as sf
import os
import pyarrow.parquet as pq
from tqdm import tqdm

# --- CONFIGURATION ---
# Point this to the FOLDER containing your 250 parquet files
parquet_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan\data" 
output_folder = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan\flac"
protocol_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\typhoon_isan\isan_metadata.txt"

os.makedirs(output_folder, exist_ok=True)

# 1. Get a list of all parquet files in the folder
all_files = [f for f in os.listdir(parquet_dir) if f.endswith('.parquet')]
print(f"Found {len(all_files)} parquet files to process.")

protocol_entries = []
global_index = 0

# 2. Loop through every file
for file_name in all_files:
    file_path = os.path.join(parquet_dir, file_name)
    print(f"\n--- Processing file: {file_name} ---")
    
    try:
        parquet_file = pq.ParquetFile(file_path)
        
        # Process this specific file in small batches to save RAM
        for batch in parquet_file.iter_batches(batch_size=10):
            df_batch = batch.to_pandas()
            
            for _, row in df_batch.iterrows():
                # Hugging Face audio format check
                audio_data = row['audio']
                audio_array = audio_data['array']
                original_sr = audio_data['sampling_rate']
                
                file_id = f"ISAN_{global_index:06d}"
                
                # Resample 48k -> 16k
                audio_16k = librosa.resample(audio_array, orig_sr=original_sr, target_sr=16000)
                
                # Save as .flac
                output_path = os.path.join(output_folder, f"{file_id}.flac")
                sf.write(output_path, audio_16k, 16000)
                
                # Add to metadata (Label: bonafide)
                protocol_entries.append(f"ISAN_SPK_{global_index} {file_id} - bonafide -")
                global_index += 1
                
            print(f"Total files extracted so far: {global_index}", end='\r')
            
    except Exception as e:
        print(f"\n[!] Error in file {file_name}: {e}")

# 3. Save the final protocol file
with open(protocol_file, 'w') as f:
    for entry in protocol_entries:
        f.write(entry + "\n")

print(f"\n\nFinished! Successfully processed {len(all_files)} files.")
print(f"Total audio files generated: {global_index}")
print(f"Metadata file saved at: {protocol_file}")