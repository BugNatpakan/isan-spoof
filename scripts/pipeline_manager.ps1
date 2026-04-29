# ====================================================================
# Anti-Spoof Project Pipeline Manager
# ====================================================================

# --- Define Global Paths ---
$BaseDir = "D:\work\AI frontier\project AntiSpoof\isan-spoof"
$ScriptDir = "$BaseDir\scripts"
$ResultsDir = "$BaseDir\results"
$ModelsDir = "$BaseDir\models\lcnn"
$ScoringScript = "$BaseDir\results\final_score.py"

# --- Helper Function for Inference ---
function Run-Inference {
    param (
        [string]$TrainDatasetName,
        [string]$TestDatasetName,
        [string]$TestDataRoot,
        [string]$TestProtocol
    )
    
    # Generate a timestamp (DayMonthYear_HourMinSec)
    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"
    
    $ModelPath = "$ModelsDir\$TrainDatasetName\trained_network.pt"
    
    # Nested output directory
    $OutputDir = "$ResultsDir\$TrainDatasetName\$TestDatasetName"
    
    # The file where inference scores will be saved (raw at the end)
    $SaveResultLoc = "$OutputDir\eval_results_${Timestamp}_raw.txt"

    # Ensure the nested output directory exists
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }

    Write-Host "`n[+] Starting Inference Phase" -ForegroundColor Yellow
    Write-Host " -> Using Model: $TrainDatasetName" -ForegroundColor Cyan
    Write-Host " -> Evaluating On: $TestDatasetName" -ForegroundColor Cyan
    Write-Host " -> Saving Scores To: `"$SaveResultLoc`"" -ForegroundColor Cyan

    # Set the Python environment variables for config.py
    $env:DATA_ROOT = "$TestDataRoot"
    $env:TEST_PROTO = "$TestProtocol"

    Set-Location -Path "$ScriptDir"
    
    # Run the Python inference script and redirect ALL output to the results text file
    # comment below line to dry run
    # python main.py --inference --model-forward-with-file-name --trained-model "$ModelPath" --batch-size 1 > "$SaveResultLoc"
    
    # uncomment below lines to mock the inference output for testing the scoring script without running actual inference
    # ------------------ DRY RUN ------------------
    Write-Host "[DRY RUN] python main.py --inference --model-forward-with-file-name --trained-model `"$ModelPath`" --batch-size 1 > `"$SaveResultLoc`"" -ForegroundColor Magenta
    Write-Host "[DRY RUN] Would execute: python main.py --inference --trained-model `"$ModelPath`" > `"$SaveResultLoc`"" -ForegroundColor Magenta        
    
    $MetaPath = "$TestDataRoot$TestProtocol"
    if (Test-Path "$MetaPath") {
        Write-Host "[DRY RUN] Generating mock scores (Exactly 20.00% EER) using IDs from $TestProtocol..." -ForegroundColor Magenta
        
        # Read the whole file to cleanly separate 100 Reals and 100 Fakes
        $allLines = Get-Content "$MetaPath"
        $bonafides = @($allLines | Where-Object { $_.ToLower().Contains("bonafide") } | Select-Object -First 100)
        $spoofs = @($allLines | Where-Object { -not $_.ToLower().Contains("bonafide") } | Select-Object -First 100)
        
        $mockScores = @()
        
        # Process the 100 Bonafide files (Force exactly 20 to be "wrong")
        for ($i = 0; $i -lt $bonafides.Count; $i++) {
            $id = ($bonafides[$i] -split '\s+')[1]
            # First 20 get a spoof score (-1.0), the other 80 get a real score (1.0)
            $score = if ($i -lt 20) { -1.0 } else { 1.0 }
            $mockScores += "Output, $id, -, $score"
        }
        
        # Process the 100 Spoof files (Force exactly 20 to be "wrong")
        for ($i = 0; $i -lt $spoofs.Count; $i++) {
            $id = ($spoofs[$i] -split '\s+')[1]
            # First 20 get a real score (1.0), the other 80 get a spoof score (-1.0)
            $score = if ($i -lt 20) { 1.0 } else { -1.0 }
            $mockScores += "Output, $id, -, $score"
        }
        
        $mockScores | Out-File -FilePath "$SaveResultLoc" -Encoding utf8
    } else {
        Write-Host "[!] DRY RUN ERROR: Could not find metadata at $MetaPath to generate IDs." -ForegroundColor Red
    }
    # ---------------- END DRY RUN ----------------


    Write-Host "`n[+] Inference Complete. Scores saved to `"$SaveResultLoc`"" -ForegroundColor Green
}

# --- Helper Function for Inference Menu ---
function Show-InferenceDatasetMenu {
    param([string]$SelectedTrainDataset)

    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "   Select Inference Dataset (Test Set)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. ASVspoof 2019 LA"
    Write-Host "2. Thai Central (Bonafide + Spoof)"
    Write-Host "3. Isan (Bonafide + Spoof)"
    Write-Host "4. typhoon_isan (Test Split) + isan_tts_spoofs (Test Split)"
    Write-Host "5. Back to Main Menu"
    
    $infChoice = Read-Host "Please select an option (1-5)"
    
    # NOTE: Update the DataRoot and Protocol text files to match your actual folders
    switch ($infChoice) {
        "1" { Run-Inference -TrainDatasetName $SelectedTrainDataset -TestDatasetName "ASVspoof_2019_LA" -TestDataRoot "$BaseDir\data\ASVspoof_2019_LA" -TestProtocol "\metadata.eval.txt" }
        "2" { Run-Inference -TrainDatasetName $SelectedTrainDataset -TestDatasetName "Thai_Central" -TestDataRoot "$BaseDir\data\Thai" -TestProtocol "\metadata_thai.eval.txt" }
        "3" { Run-Inference -TrainDatasetName $SelectedTrainDataset -TestDatasetName "Isan" -TestDataRoot "$BaseDir\data\Isan" -TestProtocol "\metadata_isan.eval.txt" }
        "4" { Run-Inference -TrainDatasetName $SelectedTrainDataset -TestDatasetName "Typhoon_Isan_TTS" -TestDataRoot "$BaseDir\data\Typhoon" -TestProtocol "\metadata_typhoon.eval.txt" }
        "5" { return }
        Default { Write-Host "Invalid selection." -ForegroundColor Red }
    }
}

# --- Main Menu Loop ---
$keepRunning = $true
while ($keepRunning) {
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "   ANTI-SPOOF PROJECT PIPELINE MANAGER" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. Train model"
    Write-Host "2. Run Inference"
    Write-Host "3. Run Scoring"
    Write-Host "4. Exit"
    Write-Host "==========================================" -ForegroundColor Cyan

    $mainChoice = Read-Host "Please select an option (1-4)"

    switch ($mainChoice) {
        "1" {
            # --- TRAINING MENU ---
            Write-Host "`n==========================================" -ForegroundColor Cyan
            Write-Host "   Select Training Dataset" -ForegroundColor Cyan
            Write-Host "==========================================" -ForegroundColor Cyan
            Write-Host "1. ASVspoof 2019 LA"
            Write-Host "2. Thai Central"
            Write-Host "3. Isan"
            Write-Host "4. ASV + Thai Central + Isan"
            Write-Host "5. Back"
            
            $trainChoice = Read-Host "Please select an option (1-4)"
            $trainSaveDir = ""

            switch ($trainChoice) {
                # NOTE: Update the DataRoot and Protocol text files to match your actual folders
                "1" { 
                    $trainSaveDir = "ASVspoof_2019_LA"
                    $env:DATA_ROOT = "$BaseDir\data\ASVspoof_2019_LA"
                    # $env:LIST_NAME = "full.lst"  # uncomment this line to use the split list for training
                    $env:TRAIN_PROTO = "\ASVspoof2019.LA.cm.trn.dev.txt"
                }
                "2" { 
                    $trainSaveDir = "Thai_Central"
                    $env:DATA_ROOT = "$BaseDir\data\Thai"
                    # $env:LIST_NAME = "full.lst"  # uncomment this line to use the split list for training
                    $env:TRAIN_PROTO = "\Thai_train_protocol.txt"
                }
                "3" { 
                    $env:DATA_ROOT = "$BaseDir\data\Isan"
                    $env:LIST_NAME = "full.lst"  # uncomment this line to use the split list for training
                    $env:TRAIN_PROTO = "\metadata.full.txt"
                }
                "4" { 
                    $trainSaveDir = "ASV_Thai_Isan"
                    $env:DATA_ROOT = "$BaseDir\data\Combined"
                    # $env:LIST_NAME = "full.lst"  # uncomment this line to use the split list for training
                    $env:TRAIN_PROTO = "\Combined_train_protocol.txt"
                }
                "5" { continue }
            }

            if ($trainSaveDir) {
                Write-Host "`n[+] Starting Training using data from: `"$env:DATA_ROOT`"" -ForegroundColor Yellow
                Set-Location -Path "$ScriptDir"
                
                # Run the Python training script
                # comment below line to dry run
                python main.py --epochs 10 --batch-size 16 --save-model-dir "$ModelsDir\$trainSaveDir" --model-forward-with-file-name
                
                # uncomment below lines to mock the inference output for testing the scoring script without running actual inference
                # Write-Host "[DRY RUN] python main.py --epochs 10 --batch-size 16 --save-model-dir `"$ModelsDir\$trainSaveDir`" --model-forward-with-file-name" -ForegroundColor Magenta
                # Write-Host "[DRY RUN] Would execute: python main.py with train data `"$env:DATA_ROOT`"" -ForegroundColor Magenta
            }
        }
        
        "2" {
            # --- INFERENCE: SELECT MODEL MENU ---
            Write-Host "`n==========================================" -ForegroundColor Cyan
            Write-Host "   Select Model (Trained Dataset)" -ForegroundColor Cyan
            Write-Host "==========================================" -ForegroundColor Cyan
            Write-Host "1. ASVspoof 2019 LA"
            Write-Host "2. Thai Central"
            Write-Host "3. ASV + Thai Central + Isan"
            Write-Host "4. Back"
            
            $modelChoice = Read-Host "Please select an option (1-4)"
            
            switch ($modelChoice) {
                "1" { Show-InferenceDatasetMenu -SelectedTrainDataset "ASVspoof_2019_LA" }
                "2" { Show-InferenceDatasetMenu -SelectedTrainDataset "Thai_Central" }
                "3" { Show-InferenceDatasetMenu -SelectedTrainDataset "ASV_Thai_Isan" }
                "4" { continue }
            }
        }
        
        "3" {
            # --- SCORING MENU ---
            Write-Host "`n[?] Enter the path to the Score file you want to evaluate:" -ForegroundColor Yellow
            $scoreFilePath = Read-Host "(e.g., ../results/ASVspoof_2019_LA/Isan/eval_results_raw.txt)"

            Write-Host "`n==========================================" -ForegroundColor Cyan
            Write-Host "   Select Metadata File for Scoring" -ForegroundColor Cyan
            Write-Host "==========================================" -ForegroundColor Cyan
            Write-Host "1. ASVspoof 2019 LA"
            Write-Host "2. Thai Central (Bonafide + Spoof)"
            Write-Host "3. Isan (Bonafide + Spoof)"
            Write-Host "4. typhoon_isan (Test Split) + isan_tts_spoofs (Test Split)"
            Write-Host "5. Back"

            $metaChoice = Read-Host "Please select an option (1-5)"
            $metaFile = ""

            switch ($metaChoice) {
                # Update these to where your scoring ground truths live
                "1" { $metaFile = "$BaseDir\data\ASVspoof_2019_LA\metadata.eval.txt" }
                "2" { $metaFile = "$BaseDir\data\Thai\metadata.eval.txt" }
                "3" { $metaFile = "$BaseDir\data\Isan\metadata.eval.txt" }
                "4" { $metaFile = "$BaseDir\data\Typhoon\metadata.eval.txt" }
                "5" { continue }
            }

            if ($metaFile -and $scoreFilePath) {
                Write-Host "`n[+] Running Scoring Script..." -ForegroundColor Yellow
                
                # comment below line to dry run
                python "$ScoringScript" --score-file "$scoreFilePath" --meta-file "$metaFile"
            
                # uncomment below lines to mock the inference output for testing the scoring script without running actual inference
                # Write-Host "[DRY RUN] python `"$ScoringScript`" --score-file `"$scoreFilePath`" --meta-file `"$metaFile`"" -ForegroundColor Magenta
                # Write-Host "[DRY RUN] Would execute: python final_score.py --score-file `"$scoreFilePath`" --meta-file `"$metaFile`"" -ForegroundColor Magenta
            }
        }
        
        "4" {
            # --- EXIT ---
            Write-Host "`nExiting Pipeline Manager..." -ForegroundColor Green
            $keepRunning = $false
        }
        
        Default {
            Write-Host "Invalid selection. Please try again." -ForegroundColor Red
        }
    }
}