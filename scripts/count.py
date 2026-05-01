import pandas as pd
import os

def analyze_asvspoof_metadata(file_path):
    """Parses and calculates statistics for a single ASVspoof 2019 metadata file."""
    # ASVspoof 2019 metadata typical format:
    # SPEAKER_ID AUDIO_FILE_NAME ENVIRONMENT_ID SYSTEM_ID/ATTACK_ID KEY(bonafide/spoof)
    columns = ['speaker_id', 'file_name', 'environment_id', 'attack_id', 'label']
    
    # Check if file exists before trying to read it
    if not os.path.exists(file_path):
        print(f"\n[!] Error: The file '{file_path}' was not found. Skipping...")
        return

    try:
        # Read the space-separated text file
        df = pd.read_csv(file_path, sep=' ', names=columns, skipinitialspace=True)
    except Exception as e:
        print(f"\n[!] An error occurred while reading '{file_path}': {e}")
        return

    print("\n" + "=" * 50)
    print(f"ASVspoof 2019 Metadata Statistics")
    print(f"File: {file_path}")
    print("=" * 50)

    # 1. Overall Counts
    total_files = len(df)
    total_speakers = df['speaker_id'].nunique()
    print(f"Total Audio Files:     {total_files}")
    print(f"Total Unique Speakers: {total_speakers}\n")

    # 2. Label Distribution (Bonafide vs Spoof)
    print("--- Class Distribution ---")
    class_counts = df['label'].value_counts()
    for label, count in class_counts.items():
        percentage = (count / total_files) * 100
        print(f"{str(label).capitalize().ljust(10)}: {count} ({percentage:.2f}%)")
    print()

    # 3. Attack Types / System IDs
    print("--- Attack Types (System IDs) ---")
    # '-' is usually used to denote bonafide (no attack system)
    spoof_df = df[df['label'] == 'spoof']
    if not spoof_df.empty:
        attack_stats = spoof_df['attack_id'].value_counts()
        print(attack_stats.to_string())
    else:
        print("No spoofed files found in this metadata.")
    print()

    # 4. Speaker Statistics
    print("--- Files per Speaker ---")
    speaker_counts = df['speaker_id'].value_counts()
    print(f"Max files for a single speaker: {speaker_counts.max()}")
    print(f"Min files for a single speaker: {speaker_counts.min()}")
    print(f"Average files per speaker:      {speaker_counts.mean():.1f}")
    print("=" * 50)


if __name__ == "__main__":
    print("*** ASVspoof 2019 Metadata Analyzer ***")
    
    # Split the input string by commas and remove extra spaces around the filenames
    file_paths = [ r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\source\typhoon_isan\typhoon_metadata.eval.txt"
               ]
    
    # Loop through the cleaned list of files and analyze each one
    for path in file_paths:
        if path:  # Ensure the path is not empty
            analyze_asvspoof_metadata(path)
            
    print("\nAnalysis complete.")