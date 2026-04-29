import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# --- ใช้ Path จริงจากเครื่องของคุณ ---
INPUT_MP3_DIR = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\bonafide\clips"
OUTPUT_ROOT = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\cv-corpus-25.0-2026-03-09\bonafide\processed"

# ใช้ 8 Threads (ปลอดภัย ไม่ทำให้ Windows ค้าง และเร็วพอที่จะเสร็จในเวลาไม่นาน)
NUM_WORKERS = 8 

def process_with_ffmpeg(filename):
    input_path = os.path.join(INPUT_MP3_DIR, filename)
    base_name = filename.replace('.mp3', '')
    
    wav_path = os.path.join(OUTPUT_ROOT, "wav", f"{base_name}.wav")
    flac_path = os.path.join(OUTPUT_ROOT, "flac", f"{base_name}.flac")
    
    # คำสั่ง: MP3 -> 16kHz Mono -> เซฟเป็น WAV และ FLAC พร้อมกัน
    cmd = [
        "ffmpeg", "-y", "-v", "error", 
        "-i", input_path,
        "-ar", "16000", "-ac", "1", wav_path,
        "-ar", "16000", "-ac", "1", flac_path
    ]
    
    try:
        # subprocess.DEVNULL จะซ่อนข้อความรกๆ ของ FFmpeg ไม่ให้บัง Progress bar
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception as e:
        return False

def main():
    # 1. สร้างโฟลเดอร์ปลายทาง
    os.makedirs(os.path.join(OUTPUT_ROOT, "wav"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_ROOT, "flac"), exist_ok=True)

    # 2. อ่านรายชื่อไฟล์ MP3
    print("🔍 กำลังค้นหาไฟล์ MP3...")
    all_files = [f for f in os.listdir(INPUT_MP3_DIR) if f.endswith('.mp3')]
    total_files = len(all_files)
    
    if total_files == 0:
        print("❌ ไม่พบไฟล์ MP3 ตรวจสอบโฟลเดอร์อีกครั้งครับ")
        return

    print(f"🚀 เริ่มแปลงไฟล์ทั้งหมด {total_files} ไฟล์ ด้วย {NUM_WORKERS} Workers...")

    # 3. รันแปลงไฟล์พร้อม Progress Bar
    success_count = 0
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # ใช้ tqdm ร่วมกับ executor.map
        results = list(tqdm(executor.map(process_with_ffmpeg, all_files), total=total_files, desc="Processing"))
    
    success_count = sum(1 for r in results if r is True)

    print(f"\n✅ เสร็จสิ้น! แปลงไฟล์สำเร็จ: {success_count} / {total_files}")
    print(f"📂 ไฟล์ทั้งหมดถูกเก็บไว้ที่: {OUTPUT_ROOT}")

if __name__ == "__main__":
    main()