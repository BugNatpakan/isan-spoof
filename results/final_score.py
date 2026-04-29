import os
import argparse
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_curve

def calculate_eer(y_true, y_score):
    """Calculates the Equal Error Rate (EER)."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)
    return eer * 100

def calculate_minDCF(y_true, y_score, p_target=0.01, c_miss=1, c_fa=1):
    """Calculates the minimum Detection Cost Function (minDCF)."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    fnr = 1 - tpr
    dcf_scores = c_miss * fnr * p_target + c_fa * fpr * (1 - p_target)
    return np.min(dcf_scores)

def clean_raw_scores(raw_file, clean_file):
    if not os.path.exists(raw_file):
        print(f"[!] Error: Could not find raw file at {raw_file}")
        return False
    
    count = 0
    # Process line-by-line (Streaming) instead of readlines()
    with open(clean_file, 'w', encoding='utf-8') as outfile:
        # We try UTF-8 with ignore directly, as it handles 99% of ANSI junk cleanly
        with open(raw_file, 'r', encoding='utf-16', errors='ignore') as infile:
            for line in infile:
                if "Output," in line:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        file_id = parts[1].strip()
                        score_raw = parts[3].strip()
                        
                        # Clean ANSI codes or non-numeric characters from score
                        score_clean = ''.join(c for c in score_raw if c.isdigit() or c in '.-')
                        
                        if file_id and score_clean:
                            outfile.write(f"{file_id} {score_clean}\n")
                            count += 1
                            
    return count > 0

if __name__ == "__main__":
    print("\n[i] Starting score evaluation...\n")
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-file", required=True)
    parser.add_argument("--meta-file", required=True)
    args = parser.parse_args()

    # --- Path Logic ---
    raw_path = os.path.abspath(args.score_file)
    raw_filename = os.path.basename(raw_path)
    timestamp = raw_filename.replace("results_", "").replace("_raw.txt", "")
    
    # Logic to extract train/test names from path: .../results/TRAIN_NAME/TEST_NAME/file.txt
    parts = raw_path.split(os.sep)
    try:
        test_name = parts[-2]
        train_name = parts[-3]
    except IndexError:
        test_name, train_name = "unknown_test", "unknown_train"

    report_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\report"
    if not os.path.exists(report_dir): os.makedirs(report_dir)

    cleaned_score_file_name = f"eval_scores_{timestamp}_clean.txt"
    cleaned_score_file = os.path.join(os.path.dirname(raw_path), cleaned_score_file_name)
    final_report_path = os.path.join(report_dir, f"{train_name}_{test_name}_report_{timestamp}.txt")

    # --- NEW ERROR PRINT: Check if Metadata exists ---
    if not os.path.exists(args.meta_file):
        print(f"[!] FATAL ERROR: Could not find metadata file at:")
        print(f"    {args.meta_file}")
        print("    Please check your paths and try again.\n")
        exit(1)

    # --- Execution ---
    if clean_raw_scores(raw_path, cleaned_score_file):
        truth_labels = {}
        with open(args.meta_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                p = line.strip().split()
                if len(p) >= 2:
                    # Ground truth: 1 for bonafide/genuine, 0 for spoof/fake
                    # (Added 'genuine' here too just to be bulletproof for your datasets)
                    truth_labels[p[1]] = 1 if ('bonafide' in line.lower() or 'genuine' in line.lower()) else 0

        y_true, y_score = [], []
        
        # Keep track of score IDs for debugging
        score_file_ids = [] 
        
        with open(cleaned_score_file, 'r') as f:
            for line in f:
                p = line.strip().split()
                if len(p) >= 2:
                    score_id = p[0]
                    score_file_ids.append(score_id)
                    if score_id in truth_labels:
                        y_true.append(truth_labels[score_id])
                        y_score.append(float(p[1]))

        if y_true:
            # --- SAFETY CHECK ---
            bonafide_count = sum(y_true)
            spoof_count = len(y_true) - bonafide_count
            
            print(f"[i] Matches found -> Bonafide: {bonafide_count} | Spoof: {spoof_count}")
            
            if bonafide_count == 0 or spoof_count == 0:
                print("\n[!] MATH ERROR PREVENTION: Cannot calculate EER or minDCF.")
                print("    Reason: The dataset must contain at least one Bonafide AND one Spoof file.")
                print("    Check your metadata or your dry-run mock IDs!\n")
            else:
                # --- NORMAL EXECUTION ---
                eer = calculate_eer(y_true, y_score)
                dcf = calculate_minDCF(y_true, y_score)
                
                res = (f"=======================================\n"
                       f" EVALUATION REPORT\n"
                       f"=======================================\n"
                       f"Score File : {cleaned_score_file_name}\n"
                       f"Train Mode : {train_name}\n"
                       f"Test Set   : {test_name}\n"
                       f"EER        : {eer:.4f}%\n"
                       f"minDCF     : {dcf:.4f}\n"
                       f"=======================================\n")
                print(f"\n{res}")
                with open(final_report_path, 'w') as f: f.write(res)
                print(f"[+] Report securely saved to: {final_report_path}\n")
        else:
            # --- NEW DIAGNOSTIC ERROR PRINT ---
            print("\n[!] CRITICAL ERROR: No matching file IDs found between your Score file and Metadata file.")
            print("    This usually means the text formatting or column layout is different.")
            
            meta_samples = list(truth_labels.keys())[:5]
            score_samples = score_file_ids[:5]
            
            print(f"\n    -> Total IDs in Metadata : {len(truth_labels)}")
            print(f"    -> Total IDs in Scores   : {len(score_file_ids)}")
            print("\n    [DIAGNOSTIC COMPARISON]")
            print(f"    Metadata File IDs look like this : {meta_samples}")
            print(f"    Score File IDs look like this    : {score_samples}")
            print("\n    Hint: Do they have different file extensions (like .flac) attached? Are they missing a prefix?\n")