import pandas as pd
import requests
import os
import time
import random
from pydub import AudioSegment
import concurrent.futures
from tqdm import tqdm

# ==========================================
# CONFIGURATION SETTINGS
# ==========================================
API_URL = "https://api.aiforthai.in.th/vaja"
API_KEY = "K11OIjWFLIIwysiCmgg5d5JP7qK2CaBv" # Recommend changing to your own API key
HEADERS = {
    'Apikey': API_KEY,
    'Content-Type': 'application/json'
}

OUTPUT_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\fake" 

SPEAKER_LIST = [
    "nana", "noina", "farah", "mewzy", "farsai", "prim", "ped", 
    "poom", "doikham", "praw", "wayu", "namphueng", "toon", "sanooch", "thanwa"
]

# MAX_FILES = None to process the entire dataset
MAX_FILES = 100 
MAX_WORKERS = 1

# ==========================================

def setup_directories():
    wav_dir = os.path.join(OUTPUT_DIR, 'wav')
    flac_dir = os.path.join(OUTPUT_DIR, 'flac')
    os.makedirs(wav_dir, exist_ok=True)
    os.makedirs(flac_dir, exist_ok=True)
    return wav_dir, flac_dir

def download_with_retry(url, max_retries=3):
    """Smartly wait and retry if the Vaja server hasn't finished rendering the audio yet."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200 and len(response.content) > 0:
                return response.content
        except requests.RequestException:
            pass
        time.sleep(1.5) # Wait before retrying
    return None

def process_single_file(item):
    """Function to handle a single row of data (runs in parallel)."""
    text = item['text']
    output_filename = item['original_filename']
    wav_dir = item['wav_dir']
    flac_dir = item['flac_dir']
    row_data = item['row_data']
    
    if len(text) > 400:
        text = text[:400]
        
    selected_speaker = random.choice(SPEAKER_LIST)
        
    payload = {
        'text': text,
        'speaker': selected_speaker
    }
    
    try:
        # 1. Request speech synthesis
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        wav_url = data.get('audio_url') or data.get('wav_url') 
        
        if not wav_url:
            return False, f"[{output_filename}] Missing URL in API response: {data}"
            
        # 2. Smart Download
        audio_content = download_with_retry(wav_url)
        if not audio_content:
            return False, f"[{output_filename}] Failed to download audio after 3 retries. URL: {wav_url}"
            
        # 3. Construct paths
        file_name_wav = f"fake_{output_filename}.wav"
        file_name_flac = f"fake_{output_filename}.flac"
        
        wav_path = os.path.join(wav_dir, file_name_wav)
        flac_path = os.path.join(flac_dir, file_name_flac)
        
        # 4. Save .wav
        with open(wav_path, "wb") as f:
            f.write(audio_content)
            
        # 5. Convert to .flac
        audio = AudioSegment.from_wav(wav_path)
        audio.export(flac_path, format="flac")
        
        # 6. Prepare the updated row
        new_row = row_data.copy()
        new_row['path'] = file_name_wav 
        new_row['vaja_speaker'] = selected_speaker 
        
        return True, new_row
        
    except Exception as e:
        
        return False, f"[{output_filename}] System Error: {str(e)}"

def process_tsv_fast(tsv_file, wav_dir, flac_dir):
    print(f"Reading file: {tsv_file}")
    df = pd.read_csv(tsv_file, sep='\t')
    
    if MAX_FILES is not None:
        df = df.head(MAX_FILES)
        
    # Prepare the data queue
    tasks = []
    for index, row in df.iterrows():
        text = str(row['sentence']).strip()
        original_filename = row['path'].replace('.mp3', '') 
        
        if text and text != 'nan':
            tasks.append({
                'text': text,
                'original_filename': original_filename,
                'wav_dir': wav_dir,
                'flac_dir': flac_dir,
                'row_data': row.to_dict() 
            })

    print(f"Starting generation for {len(tasks)} files using {MAX_WORKERS} workers...")
    
    successful_rows = []
    failed_logs = [] # NEW: List to catch all error messages
    fail_count = 0
    
    # Run the multithreaded pool with a progress bar
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(executor.map(process_single_file, tasks), total=len(tasks), desc="Processing Audio"))
        
        for success, result_data in results:
            if success:
                successful_rows.append(result_data) 
            else:
                fail_count += 1
                failed_logs.append(result_data) # Catch the error message here

    # Save the new TSV file
    if successful_rows:
        original_tsv_name = os.path.basename(tsv_file)
        new_tsv_path = os.path.join(OUTPUT_DIR, f"fake_{original_tsv_name}")
        
        df_out = pd.DataFrame(successful_rows)
        df_out.to_csv(new_tsv_path, sep='\t', index=False)
        print(f"\n✅ Saved new TSV file to: {new_tsv_path}")

    # NEW: Save the Error Log
    if failed_logs:
        log_path = os.path.join(OUTPUT_DIR, "error_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            for log in failed_logs:
                f.write(log + "\n")
        print(f"⚠️ Saved Error Log to: {log_path}")

    print("\n" + "="*40)
    print("🎉 PROCESSING COMPLETE 🎉")
    print(f"✅ Successfully created: {len(successful_rows)} files")
    print(f"❌ Failed: {fail_count} files (Check error_log.txt for details)")
    print("="*40)

if __name__ == "__main__":
    wav_folder, flac_folder = setup_directories()
    
    target_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\bonafide\test.tsv" 
    
    if os.path.exists(target_file):
        process_tsv_fast(target_file, wav_folder, flac_folder)
    else:
        print(f"Error: Could not find '{target_file}'")