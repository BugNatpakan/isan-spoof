import pandas as pd
import librosa
import soundfile as sf
import os
import pyarrow.parquet as pq
from tqdm import tqdm

# ==========================================
# ⚙️ CONFIGURATION - PATHS & SETTINGS
# ==========================================

# Point this to the FOLDER containing your downloaded Hugging Face .parquet files
parquet_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\data" 

# Base output folder
base_output_folder = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan"

# The subfolders it will create for the audio files
wav_folder = os.path.join(base_output_folder, "wav")
flac_folder = os.path.join(base_output_folder, "flac")

# Output text files
output_meta = os.path.join(base_output_folder, "metadata.all.txt")
output_lst = os.path.join(base_output_folder, "all.lst")

# Standard ASVspoof Labels for this real dataset
LABEL = "bonafide"
ATTACK_TYPE = "-"
ENVIRONMENT = "-"

# To keep track of the global file numbering across all parquet files

# ==========================================

def main():
    # Create the necessary directories
    os.makedirs(wav_folder, exist_ok=True)
    os.makedirs(flac_folder, exist_ok=True)
    global_file_id = 0  

    # Get all parquet files
    all_files = [f for f in os.listdir(parquet_dir) if f.endswith('.parquet')]
    print(f"🔍 Found {len(all_files)} parquet files to process.\n")

    meta_lines = []
    lst_lines = []

    # Loop through every parquet file
    for file_name in all_files:
        file_path = os.path.join(parquet_dir, file_name)
        print(f"🚀 Processing file: {file_name} ...")
        
        try:
            parquet_file = pq.ParquetFile(file_path)
            
            # Process in small batches to prevent RAM crashes
            for batch in parquet_file.iter_batches(batch_size=50):
                df_batch = batch.to_pandas()
                
                for _, row in df_batch.iterrows():
                    # 1. Extract Hugging Face audio array
                    audio_data = row['audio']
                    audio_array = audio_data['array']
                    original_sr = audio_data['sampling_rate']
                    
                    # 2. Extract Original Name for SPEAKER tracking
                    raw_name = str(row['name'])
                    
                    parts = raw_name.split(';')
                    clean_name = f"Typhoon_Isan_{raw_name.split(';')[-1].split('.')[0]}"
                    
                    try:    
                        speaker_id = f"isan_{parts[2]} " 
                    except IndexError:
                        # Fallback if a filename doesn't match the exact pattern
                        speaker_id = f"isan_spk_{global_file_id:05d}"
                        
                    # 🟢 3. GENERATE GLOBAL FILE ID (e.g. ISAN_000000)
                    file_id = f"ISAN_{global_file_id:06d}"
                    
                    # 4. Resample audio to exactly 16kHz
                    if original_sr != 16000:
                        audio_16k = librosa.resample(audio_array, orig_sr=original_sr, target_sr=16000)
                    else:
                        audio_16k = audio_array
                    
                    # 5. Save to BOTH formats using the new GLOBAL FILE ID
                    wav_path = os.path.join(wav_folder, f"{file_id}.wav")
                    flac_path = os.path.join(flac_folder, f"{file_id}.flac")
                    
                    sf.write(wav_path, audio_16k, 16000, format='WAV')
                    sf.write(flac_path, audio_16k, 16000, format='FLAC')
                    
                    # 6. Format ASVspoof line: SPEAKER_ID FILE_ID ENVIRONMENT ATTACK_TYPE LABEL
                    meta_line = f"{speaker_id} {file_id} {ENVIRONMENT} {ATTACK_TYPE} {LABEL}\n"
                    
                    meta_lines.append(meta_line)
                    lst_lines.append(f"{file_id}\n")
                    
                    global_file_id += 1
                    
                print(f"   ⏳ Files extracted so far: {global_file_id}", end='\r')
            print() # Print newline after the batch completes
                
        except Exception as e:
            print(f"\n[!] ❌ Error in file {file_name}: {e}")

    # Write the compiled metadata files at the end
    print("\n📝 Saving metadata lists...")
    with open(output_meta, 'w', encoding='utf-8') as f_meta:
        f_meta.writelines(meta_lines)
        
    with open(output_lst, 'w', encoding='utf-8') as f_lst:
        f_lst.writelines(lst_lines)

    print("\n🎉 ALL DONE!")
    print(f"✅ Total audio files generated: {global_file_id} (.wav and .flac)")
    print(f"📄 Metadata saved at: {output_meta}")
    print(f"📄 List saved at: {output_lst}")

if __name__ == "__main__":
    main()