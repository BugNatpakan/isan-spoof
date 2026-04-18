import numpy as np
import os

# 1. Update these paths if necessary
raw_score_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\score\eval_results_raw.txt"
cleaned_score_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\score\eval_scores.txt"
truth_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\asvspoof2019\ASVspoof2019.LA.cm.eval.trl.txt"
final_report_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\E1_report.txt"

def clean_raw_scores():
    if not os.path.exists(raw_score_file):
        print(f"Error: Could not find raw file at {raw_score_file}")
        return False
        
    print("Cleaning raw scores...")
    count = 0
    with open(raw_score_file, 'r') as infile, open(cleaned_score_file, 'w') as outfile:
        for line in infile:
            if line.startswith("Output,"):
                parts = line.split(",")
                if len(parts) >= 4:
                    file_id = parts[1].strip()
                    score = parts[3].strip()
                    outfile.write(f"{file_id} {score}\n")
                    count += 1
                    
    print(f"Successfully cleaned {count} scores and saved to eval_scores.txt!\n")
    return True

def calculate_eer():
    scores = {}
    with open(cleaned_score_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                scores[parts[0]] = float(parts[-1])

    y_true = []
    y_score = []
    
    with open(truth_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            file_id = parts[1]
            label = 1 if parts[-1].lower() == "bonafide" else 0
            
            if file_id in scores:
                y_true.append(label)
                y_score.append(scores[file_id])

    if not y_true:
        print("No matching IDs found! Check if file IDs in scores match the ground truth.")
        return

    # --- NEW LIGHTWEIGHT EER MATH (NO SKLEARN REQUIRED) ---
    print("Calculating EER...")
    y_true = np.array(y_true)
    y_score = np.array(y_score)
    
    # Sort scores descending
    indices = np.argsort(y_score)[::-1]
    y_true = y_true[indices]
    
    # Calculate True Positive Rate and False Positive Rate
    tps = np.cumsum(y_true)
    fps = np.cumsum(1 - y_true)
    
    tpr = tps / tps[-1]
    fpr = fps / fps[-1]
    fnr = 1 - tpr
    
    # Find intersection where FPR and FNR are closest
    idx = np.nanargmin(np.absolute((fpr - fnr)))
    eer = fpr[idx] * 100
    # ------------------------------------------------------
    
    report = (
        f"Matched {len(y_true)} files.\n"
        f"-------------------------------\n"
        f"EER: {eer:.4f}%\n"
        f"-------------------------------"
    )
    
    print(report)
    
    with open(final_report_file, 'w') as f:
        f.write(report)
        
    print(f"Result successfully saved to: {final_report_file}")

if __name__ == "__main__":
    success = clean_raw_scores()
    if success:
        calculate_eer()