import os
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_curve

experiment_number = "E2"

# 1. Paths
raw_score_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results" + "\\" + experiment_number + r"_scores\eval_results_raw.txt"
cleaned_score_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results" + "\\" + experiment_number + r"_scores\eval_scores.txt"
truth_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment" + "\\" + experiment_number + r"\metadata.eval.txt"
final_report_file = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results" + "\\" + experiment_number + r"_report.txt"

def calculate_eer(y_true, y_score):
    """Calculates the Equal Error Rate (EER)."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)
    return eer * 100

def clean_raw_scores():
    if not os.path.exists(raw_score_file):
        print(f"[!] Error: Could not find raw file at {raw_score_file}")
        return False
        
    print("Cleaning raw scores...")
    count = 0
    lines = []
    
    # Try reading as UTF-16 (PowerShell format) first
    try:
        with open(raw_score_file, 'r', encoding='utf-16') as infile:
            lines = infile.readlines()
    except UnicodeError:
        # If it fails, fallback to standard UTF-8 (CMD/Python format)
        with open(raw_score_file, 'r', encoding='utf-8', errors='ignore') as infile:
            lines = infile.readlines()

    # Now write the clean scores
    with open(cleaned_score_file, 'w', encoding='utf-8') as outfile:
        for line in lines:
            if "Output," in line:
                parts = line.split(",")
                if len(parts) >= 4:
                    file_id = parts[1].strip()
                    score_raw = parts[3].strip()
                    
                    # Strip any leftover hidden color codes
                    score_clean = ''.join(c for c in score_raw if c.isdigit() or c in '.-')
                    
                    if file_id and score_clean:
                        outfile.write(f"{file_id} {score_clean}\n")
                        count += 1
                        
    print(f"Successfully cleaned {count} scores and saved to eval_scores.txt!\n")
    return count > 0

print(f"--- Running Scoring for Experiment {experiment_number} ---")

# Step A: Clean the messy raw scores
if not clean_raw_scores():
    exit()

# Step B: Load Ground Truth (Bulletproof Version)
print(f"Loading truth labels from: {truth_file}")
truth_labels = {}
if os.path.exists(truth_file):
    # Added encoding='utf-8' and errors='ignore' just in case the metadata has weird characters too
    with open(truth_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                file_id = parts[1] # ID is in column 2
                
                # If the word 'bonafide' is ANYWHERE in this line, it's real (1). Else, spoof (0).
                if 'bonafide' in line.lower():
                    truth_labels[file_id] = 1
                else:
                    truth_labels[file_id] = 0

# Step C: Load Cleaned Scores
print(f"Loading model scores from: {cleaned_score_file}")
y_true = []
y_score = []

if os.path.exists(cleaned_score_file):
    with open(cleaned_score_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                file_id = parts[0]
                try:
                    score = float(parts[1])
                    if file_id in truth_labels:
                        y_true.append(truth_labels[file_id])
                        y_score.append(score)
                except ValueError:
                    continue

# Step D: Calculate EER
if len(y_score) == 0:
    print("\n[!] Error: No matching IDs found! Check if file IDs in scores match the ground truth.")
else:
    # DEBUG: Let's prove we found the files!
    bonafide_count = sum(y_true)
    spoof_count = len(y_true) - bonafide_count
    print(f"\n[Success] Matches found -> Bonafide (Reals): {bonafide_count} | Spoofs (Fakes): {spoof_count}")
    
    if bonafide_count == 0 or spoof_count == 0:
        print("[!] Math Error Prevention: Cannot calculate EER because we are missing either Real or Fake files.")
        exit()

    eer_val = calculate_eer(y_true, y_score)
    result_text = (
        f"=======================================\n"
        f"       EXPERIMENT {experiment_number} RESULTS\n"
        f"=======================================\n"
        f"Total Files Evaluated : {len(y_score)}\n"
        f"Equal Error Rate (EER): {eer_val:.2f}%\n"
        f"=======================================\n"
    )
    
    print("\n" + result_text)
    
    os.makedirs(os.path.dirname(final_report_file), exist_ok=True)
    with open(final_report_file, 'w') as f:
        f.write(result_text)
    print(f"Report securely saved to: {final_report_file}")