# Isan Spoof Detection Project

This project focuses on anti-spoofing detection for the Isan language, implementing various models and experiments for automatic speaker verification (ASV) spoof detection.

## Project Structure

- **data/**: Datasets and experimental data (note: data files (.wav, .flac, .mp3) are stored locally and not included in the repository due to size constraints).
  - ASV_Thai_Isan/: Mixed language datasets
  - Eng/: English datasets
  - experiment/: Experimental data
  - Isan/: Additional Isan data
  - source/: Source data

- **models/**: Model implementations.
  - lcnn/: LCNN-based models

- **results/**: Experiment results and scores.
  - final_score.py: Script for calculating final scores
  - E1/ to E6_*/: Individual experiment results
  - report/: Reports and summaries

- **scripts/**: Core scripts for training, testing, and pipeline management.
  - config.py: Configuration settings
  - main.py: Main script
  - run_gmm.py: GMM-based model script
  - pipeline_manager.ps1: PowerShell script to manage the entire pipeline
  - core_scripts/: Additional core modules
    - nn_manager/: Neural network management
  - sandbox/: Experimental scripts

## Setup

### Prerequisites
- Python 3.8+
- Conda (recommended for environment management)
- PowerShell (for pipeline manager)

### Installation

1. Create and activate the conda environment:
   ```bash
   conda create -n isan-spoof python=3.8
   conda activate isan-spoof
   ```

2. Install dependencies (if requirements.txt exists):
   ```bash
   pip install -r requirements.txt  # Check if available in scripts/ or root
   ```
   Note: Dependencies may need to be installed based on the scripts used.

3. Ensure data is available locally (not included in repo).

## Usage

### Running the Pipeline

1. Navigate to the `scripts` directory:
   ```bash
   cd scripts
   ```

2. Run the pipeline manager:
   ```powershell
   .\pipeline_manager.ps1
   ```
   This script manages the entire workflow, including training, testing, and evaluation.

### Pipeline Manager Details

The `pipeline_manager.ps1` is an interactive PowerShell script that automates running experiments (E1 to E6). It provides menus to select experiments and actions (Train, Inference, Scoring, or All).

- **Dry Run Mode**: Edit the script to set `$DRY_RUN = $true` to print commands without executing them (useful for testing).
- **Experiments**:
  - E1-E4: Standard experiments with different features/models.
  - E5: Feature ablation (LFCC, MFCC, CQCC, Fusion).
  - E6: Architecture ablation (GMM, ResNet).
- **Actions**:
  - Train: Trains the model for the selected experiment.
  - Inference: Runs evaluation on the trained model.
  - Scoring: Calculates EER and other metrics using `final_score.py`.
  - All: Runs Train -> Inference -> Scoring sequentially.
- **Usage**: Run the script, select an experiment, then choose an action. The script handles paths, environment variables, and command execution automatically.

### Individual Scripts

- **Training (NN Model)**: 
  ```bash
  cd scripts
  python -u main.py --epochs 10 --batch-size 8 --save-model-dir "../models/lcnn/CustomExp" --model-forward-with-file-name --run-name "Experimen_Name"`
  ```
  Adjust epochs, batch-size, models paths and experiment name as needed.

- **Testing/Inference**: 
  ```bash
  cd scripts
  python main.py --inference --model-forward-with-file-name --trained-model "../models/lcnn/Experiment_Name/trained_network.pt" --batch-size 1 --feature_type lfcc --architecture lcnn > "../results/Experiment_Name/results_raw.txt"
  ```
  Update the trained model path and output paths.

- **GMM Model Training/Testing**: 
  ```bash
  cd scripts
  python run_gmm.py
  ```

- **Scoring**: 
  ```bash
  python "../results/final_score.py" --score-file "../results/Experiment_Name/results_raw.txt" --meta-file "../data/experiment/Experiment_Name/metadata.eval.txt" --exp-name "Experiment_Name"
  

- **Configuration**: Edit `config.py` for settings

### Viewing Results

- Results are saved in `results/`
- Use `final_score.py` to compute scores
- Launch MLflow UI for experiment tracking:
  ```bash
  mlflow ui
  ```
  Access at http://localhost:5000

## Models

- LCNN (Lightweight Convolutional Neural Network)
- GMM (Gaussian Mixture Model)
- Other experimental models in `models/`

## Experiments

The project includes multiple experiments (E1 to E6) with different features and models:
- E1-E5: Various feature extractions (CQCC, LFCC, MFCC, fusion)
- E6: GMM and ResNet models

## Notes

- Data files are too large to include in the GitHub repository and must be stored locally.
- Ensure the local data paths are correctly configured in the scripts\pipeline_manager.ps1.


## License

This project is part of the Isan Anti-Spoof repository. Refer to the main repository's LICENSE.
