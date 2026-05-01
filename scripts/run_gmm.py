import os
import sys
import numpy as np
import torchaudio
from sklearn.mixture import GaussianMixture
import time
from datetime import datetime

# --- CONFIGURATION ---
DATA_ROOT = r"D:\work\AI frontier\project AntiSpoof\isan-spoof\data\experiment\E4"
TRAIN_PROTO = os.path.join(DATA_ROOT, "metadata.train.txt")
EVAL_PROTO = os.path.join(DATA_ROOT, "metadata.eval.txt")
dt = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_FILE = os.path.join(r"D:\work\AI frontier\project AntiSpoof\isan-spoof\results\E6_gmm", f"results_{dt}_clean.txt")

N_COMPONENTS = 128 # Standard for ASVspoof GMM baselines
SUBSAMPLE_RATE = 10 # Take 1 out of every 10 frames to prevent RAM crashes

# Standard LFCC Extractor using torchaudio
lfcc_extractor = torchaudio.transforms.LFCC(
    sample_rate=16000,
    n_filter=20,
    n_lfcc=20,
    speckwargs={"n_fft": 512, "win_length": 320, "hop_length": 160}
)

def extract_features(flac_path):
    """ Loads audio and returns transposed LFCC frames """
    try:
        waveform, sr = torchaudio.load(flac_path)
        # Ensure 16k sample rate
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            waveform = resampler(waveform)
        
        lfcc = lfcc_extractor(waveform).squeeze(0).transpose(0, 1) # Shape: (Time, Features)
        return lfcc.numpy()
    except Exception as e:
        print(f"Error loading {flac_path}: {e}")
        return None

def train_gmm():
    print("--- 1. Extracting Training Features ---")
    bonafide_frames = []
    spoof_frames = []

    with open(TRAIN_PROTO, 'r') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) < 5: continue
        
        speaker, filename, _, _, label = parts[0], parts[1], parts[2], parts[3], parts[4]
        file_path = os.path.join(DATA_ROOT, f"{filename}.flac")
        
        feats = extract_features(file_path)
        if feats is not None:
            # Subsample features to save RAM!
            feats = feats[::SUBSAMPLE_RATE] 
            
            if label.lower() == 'bonafide':
                bonafide_frames.append(feats)
            else:
                spoof_frames.append(feats)

        if idx % 1000 == 0:
            print(f"Processed {idx}/{len(lines)} training files...")

    # Stack all frames into massive 2D arrays
    X_bonafide = np.vstack(bonafide_frames)
    X_spoof = np.vstack(spoof_frames)
    print(f"Total Bonafide frames for training: {X_bonafide.shape[0]}")
    print(f"Total Spoof frames for training: {X_spoof.shape[0]}")

    print("--- 2. Fitting Bonafide GMM (This will take a while) ---")
    gmm_bonafide = GaussianMixture(n_components=N_COMPONENTS, covariance_type='diag', max_iter=100, verbose=2)
    gmm_bonafide.fit(X_bonafide)

    print("--- 3. Fitting Spoof GMM (This will take a while) ---")
    gmm_spoof = GaussianMixture(n_components=N_COMPONENTS, covariance_type='diag', max_iter=100, verbose=2)
    gmm_spoof.fit(X_spoof)

    return gmm_bonafide, gmm_spoof

def evaluate_gmm(gmm_bonafide, gmm_spoof):
    print("--- 4. Evaluating Test Set ---")
    
    with open(EVAL_PROTO, 'r') as f:
        lines = f.readlines()

    results = []
    for idx, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) < 5: continue
        
        filename = parts[1]
        file_path = os.path.join(DATA_ROOT, f"{filename}.flac")
        
        feats = extract_features(file_path)
        if feats is not None:
            # Score against both models
            llk_bonafide = np.mean(gmm_bonafide.score_samples(feats))
            llk_spoof = np.mean(gmm_spoof.score_samples(feats))
            
            # Final Score = LLR (Log-Likelihood Ratio)
            final_score = llk_bonafide - llk_spoof
            
            # Format perfectly matches your PyTorch output
            results.append(f"Output, {filename}, -, {final_score:.6f}\n")
            
        if idx % 500 == 0:
            print(f"Scored {idx}/{len(lines)} test files...")

    # Save to your results folder
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        f.writelines(results)
    
    print(f"--- SUCCESS: Raw scores saved to {RESULTS_FILE} ---")

if __name__ == "__main__":
    gmm_b, gmm_s = train_gmm()
    evaluate_gmm(gmm_b, gmm_s)