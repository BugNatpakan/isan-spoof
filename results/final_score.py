import os
import argparse
import numpy as np
import datetime
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_curve

def calculate_eer(y_true, y_score):
    """Calculates the Equal Error Rate (EER) and the best threshold."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    fnr = 1 - tpr
    idx = np.nanargmin(np.absolute(fpr - fnr))
    eer_threshold = thresholds[idx]
    return fpr[idx] * 100, fpr[idx] * 100, fnr[idx] * 100, eer_threshold

def calculate_minDCF(y_true, y_score, p_target=0.01, c_miss=1, c_fa=1):
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    fnr = 1 - tpr
    dcf_scores = c_miss * fnr * p_target + c_fa * fpr * (1 - p_target)
    return np.min(dcf_scores)

def get_strict_threshold(y_true, y_score, target_far=0.01):
    """
    Calculates a threshold that guarantees a low False Alarm Rate (FAR).
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_score, pos_label=1)
    
    # 1. Ignore the artificial 'inf' threshold added by scikit-learn
    valid_mask = ~np.isinf(thresholds)
    clean_thresholds = thresholds[valid_mask]
    clean_fpr = fpr[valid_mask]
    
    # 2. Find all thresholds where FAR is less than or equal to the target
    valid_indices = np.where(clean_fpr <= target_far)[0]
    
    if len(valid_indices) > 0:
        # 3. Pick the LAST index (the most forgiving threshold that still stops hackers)
        strict_threshold = clean_thresholds[valid_indices[-1]]
    else:
        # Fallback if the target is impossible for this dataset
        strict_threshold = np.max(clean_thresholds)
        
    print(f"\n[+] Strict Threshold for FAR <= {target_far*100:.2f}%: {strict_threshold:.4f}\n")
    return strict_threshold

def clean_raw_scores(raw_file, clean_file):
    """Handles UTF-16 raw files and extracts 'Output,' lines."""
    if not os.path.exists(raw_file): return False
    count = 0
    with open(clean_file, 'w', encoding='utf-8') as outfile:
        with open(raw_file, 'r', encoding='utf-16', errors='ignore') as infile:
            for line in infile:
                if "Output," in line:
                    parts = line.split(",")
                    if len(parts) >= 4:
                        file_id = parts[1].strip()
                        score_raw = parts[3].strip()
                        score_clean = ''.join(c for c in score_raw if c.isdigit() or c in '.-')
                        if file_id and score_clean:
                            outfile.write(f"{file_id} {score_clean}\n")
                            count += 1
    return count > 0

def evaluate_experiment(score_file, meta_file, exp_name):
    y_true, y_score = [], []
    curr_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Setup paths
    temp_clean_file = score_file.replace("_raw.txt", "_clean.txt")
    dt = os.path.basename(score_file).replace("results_", "").replace("_raw.txt", "")
    
    # 2. Clean the UTF-16 raw file first
    if not clean_raw_scores(score_file, temp_clean_file):
        print(f"[!] Error: Could not process raw file {score_file}")
        return

    # 3. Load Metadata
    truth_labels = {}
    with open(meta_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            p = line.strip().split()
            if len(p) >= 2:
                truth_labels[p[1]] = 1 if ('bonafide' in line.lower() or 'genuine' in line.lower()) else 0

    # 4. Load Cleaned Scores
    with open(temp_clean_file, 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip().split()
            if len(p) >= 2 and p[0] in truth_labels:
                y_true.append(truth_labels[p[0]])
                y_score.append(float(p[1]))
    
    y_true, y_score = np.array(y_true), np.array(y_score)
    if len(y_true) == 0:
        print("[!] No matching IDs found.")
        return

    # 5. Calculate Metrics
    eer, eer_far, eer_frr, eer_threshold = calculate_eer(y_true, y_score)
    min_dcf = calculate_minDCF(y_true, y_score)
    
    # Define the strict threshold
    threshold = get_strict_threshold(y_true, y_score, target_far=0.01)
    # threshold = 0
    # threshold = eer_threshold

    # 6. Calculate Correct Guesses AND New Errors based on STRICT threshold
    bonafide_idx = (y_true == 1)
    bonafide_total = np.sum(bonafide_idx)
    bonafide_correct = np.sum(y_score[bonafide_idx] >= threshold)
    false_rejections = bonafide_total - bonafide_correct # Real users blocked
    
    spoof_idx = (y_true == 0)
    spoof_total = np.sum(spoof_idx)
    spoof_correct = np.sum(y_score[spoof_idx] < threshold)
    false_alarms = spoof_total - spoof_correct # Hackers let in

    # Calculate actual FAR and FRR percentages at this new threshold
    strict_far = (false_alarms / spoof_total) * 100 if spoof_total > 0 else 0
    strict_frr = (false_rejections / bonafide_total) * 100 if bonafide_total > 0 else 0

    # 7. Generate Report
    res = (f"==============================================\n"
           f"           EXPERIMENT METRICS REPORT          \n"
           f"==============================================\n"
           f" Date            : {curr_date}\n"
           f" Experiment Name : {exp_name}\n"
           f" EER Threshold   : {eer_threshold:.4f}\n"
           f" Strict Threshold: {threshold:.4f}\n"
           f"----------------------------------------------\n"
           f" [BONAFIDE] Correct: {bonafide_correct}/{bonafide_total} ({bonafide_correct/bonafide_total*100:.2f}%)\n"
           f" [SPOOF]    Correct: {spoof_correct}/{spoof_total} ({spoof_correct/spoof_total*100:.2f}%)\n"
           f"----------------------------------------------\n"
           f" * Equal Error Rate (EER)   : {eer:.4f}%\n"
           f" * False Alarm (FAR)        : {strict_far:.4f}%\n"
           f" * False Reject (FRR)       : {strict_frr:.4f}%\n"
           f" * Minimum DCF (minDCF)     : {min_dcf:.6f}\n"
           f"==============================================\n")
    
    print(res)

    # 8. Save the Report to a Text File
    output_dir = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\report"
    report_file_path = os.path.join(output_dir, f"{exp_name}_report_{dt}.txt")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write(res)
    
    
    print(f"[+] Saved metrics report to: {report_file_path}\n")

    # Optional: Log to MLflow if needed
    try:
        import mlflow
        
        print("[+] Searching MLflow for matching training run...")
        
        # Search MLflow for the training run with the exact same name (e.g., "E5_lfcc")
        # This assumes you are using the default experiment ID "0"
        runs = mlflow.search_runs(filter_string=f"tags.mlflow.runName = '{exp_name}'")
        
        if not runs.empty:
            # Grab the ID of the most recent training run with that name
            auto_run_id = runs.iloc[0].run_id
            print(f"[+] Found existing MLflow run for {exp_name} (ID: {auto_run_id}). Appending metrics...")
            mlflow_ctx = mlflow.start_run(run_id=auto_run_id)
        else:
            # Fallback just in case training wasn't logged or name mismatched
            print(f"[!] No training run found for {exp_name}. Creating a new standalone run...")
            mlflow_ctx = mlflow.start_run(run_name=f"{exp_name}_Scoring")
            
        with mlflow_ctx:
            mlflow.log_metric(f"{exp_name}_EER", eer)
            mlflow.log_metric(f"{exp_name}_Strict_FAR", strict_far)
            mlflow.log_metric(f"{exp_name}_Strict_FRR", strict_frr)
            mlflow.log_metric(f"{exp_name}_Min_DCF", min_dcf)
            mlflow.log_metric(f"{exp_name}_Bona_Correct", bonafide_correct)
            mlflow.log_metric(f"{exp_name}_Spoof_Correct", spoof_correct)
            print("[+] Successfully logged metrics to MLflow!")
            
    except Exception as e:
        print(f"[!] MLflow logging skipped or failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-file", required=True)
    parser.add_argument("--meta-file", required=True)
    parser.add_argument("--exp-name", default="E1")
    args = parser.parse_args()
    evaluate_experiment(args.score_file, args.meta_file, args.exp_name)