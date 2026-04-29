import os
import pandas as pd
import torch
import random
from TTS.api import TTS
from tqdm import tqdm

# --- CONFIGURATION ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TSV_PATH = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\bonafide\test.tsv"     # ไฟล์ต้นฉบับ
OUTPUT_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\fake\wav_eval"      # ที่เก็บไฟล์ที่สร้าง
REF_VOICES_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\fake\ref_voices"      # โฟลเดอร์เก็บเสียงต้นแบบ (.wav)

# 1. โหลดโมเดล (ใช้ VRAM ประมาณ 4.5GB)
print("🚀 Loading XTTS v2 onto RTX 4050...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(DEVICE)

def get_random_speaker():
    """สุ่มเลือกไฟล์เสียงต้นแบบจากโฟลเดอร์"""
    speakers = [f for f in os.listdir(REF_VOICES_DIR) if f.endswith('.wav')]
    return os.path.join(REF_VOICES_DIR, random.choice(speakers))

def generate_dataset():
    # สร้างโฟลเดอร์สำหรับเก็บผลลัพธ์
    wav_out = os.path.join(OUTPUT_DIR, "wav")
    os.makedirs(wav_out, exist_ok=True)

    # อ่านข้อมูลจาก TSV
    df = pd.read_csv(TSV_PATH, sep='\t')
    
    # ถ้าอยากทดสอบก่อน 100 ไฟล์ ให้ใช้บรรทัดล่างนี้:
    df = df.head(100)

    results = []

    # เริ่มการสร้างเสียง
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Generating XTTS Audio"):
        text = str(row['sentence'])
        file_id = row['path'].replace('.mp3', '')
        
        # เลือกเสียงต้นแบบแบบสุ่ม
        ref_speaker = get_random_speaker()
        out_filename = f"fake_xtts_{file_id}.wav"
        out_path = os.path.join(wav_out, out_filename)

        try:
            # XTTS จะสร้างเสียงภาษาไทยโดยเลียนแบบเสียงต้นแบบ
            tts.tts_to_file(
                text=text,
                speaker_wav=ref_speaker,
                language="th",
                file_path=out_path
            )
            
            # เก็บข้อมูลลง List เพื่อทำ TSV ใหม่
            new_row = row.to_dict()
            new_row['path'] = out_filename
            new_row['speaker_cloned'] = os.path.basename(ref_speaker)
            results.append(new_row)
            
        except Exception as e:
            print(f"\n❌ Error generating {file_id}: {e}")

    # บันทึกเป็น TSV ไฟล์ใหม่
    new_tsv_path = os.path.join(OUTPUT_DIR, "fake_xtts_dataset.tsv")
    pd.DataFrame(results).to_csv(new_tsv_path, sep='\t', index=False)
    print(f"\n✅ Done! Dataset saved to {new_tsv_path}")

if __name__ == "__main__":
    generate_dataset()