# ====================================================================
# Anti-Spoof Pipeline Manager V3 (Self-Contained Experiment Structure)
# ====================================================================

$DRY_RUN       = $false   # Set to $false to run actual python scripts

# --- GLOBAL PATHS ---
$BaseDir       = "D:\work\AI frontier\project AntiSpoof\isan-spoof"
$ScriptDir     = "$BaseDir\scripts"
$ResultsDir    = "$BaseDir\results"
$ModelsDir     = "$BaseDir\models\lcnn"
$ScoringScript = "$BaseDir\results\final_score.py"
$ExpDir        = "$BaseDir\data\experiment"

# --- DEFAULT FILENAMES INSIDE EACH 'E' FOLDER ---
# (Change these if you named your lists differently inside the E folders)
$TrainProtoName = "metadata.train.txt"
$TrainListName  = "train.lst"
$EvalProtoName  = "metadata.eval.txt"
$EvalListName   = "eval.lst"

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

function Run-Train {
    param ([string]$ExpName)
    $env:PYTHONUNBUFFERED = "1"
    $TargetDir       = "$ExpDir\$ExpName"
    $env:DATA_ROOT   = $TargetDir
    $env:TRAIN_PROTO = "\" + $TrainProtoName
    $env:LIST_NAME   = $TrainListName
    $SaveModelDir    = "$ModelsDir\$ExpName"

    $useE1Model = @( "E1.5", "E2")
    $useE4Model = @( "E5", "E6")
    if ($ExpName -in $useE1Model) {
        write-host "[INFO] Using pre-trained E1 model for $ExpName" -ForegroundColor Cyan
        return "$ModelsDir\E1\trained_network.pt"
    }
    if ($ExpName -in $useE4Model) {
        write-host "[INFO] Using pre-trained E4 model for $ExpName" -ForegroundColor Cyan
        return "$ModelsDir\E4\trained_network.pt"
    }

    Write-Host "`n[+] [TRAIN] Starting Training for: $ExpName at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")" -ForegroundColor Yellow
    Write-Host "    -> Data Root : $($env:DATA_ROOT)" -ForegroundColor DarkGray
    Write-Host "    -> Train Proto : $($env:TRAIN_PROTO)" -ForegroundColor DarkGray
    Write-Host "    -> List Name : $($env:LIST_NAME)" -ForegroundColor DarkGray

    # Ensure the model save directory exists before Python tries to use it!
    if (-not (Test-Path -Path $SaveModelDir)) {
        Write-Host "[i] Creating missing model directory: $SaveModelDir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $SaveModelDir -Force | Out-Null
    }

    Set-Location -Path "$ScriptDir"
    $TrainCommand = 'python -u main.py --epochs 10 --batch-size 8 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name --run-name "' + $ExpName +'"'
    
    if ($DRY_RUN) {
        Write-Host "[DRY RUN] Would execute: $TrainCommand" -ForegroundColor Magenta
        if (!(Test-Path "$SaveModelDir")) { New-Item -ItemType Directory -Path "$SaveModelDir" -Force | Out-Null }
        "Mock" | Out-File -FilePath "$SaveModelDir\trained_network.pt" -Encoding utf8
    } else {
        Write-Host $TrainCommand
        Invoke-Expression $TrainCommand
    }
    return "$SaveModelDir\trained_network.pt"
}

function Run-Inference {
    param ([string]$ExpName,
           [string]$ModelPath = "")
    $TargetDir      = "$ExpDir\$ExpName"
    $env:DATA_ROOT  = $TargetDir
    $env:TEST_PROTO = "\" + $EvalProtoName
    $env:LIST_NAME  = $EvalListName
        
    if ($ModelPath -eq "") {
        $useE1Model = @("E1", "E1.5", "E2")
        
        if ($ExpName -in $useE1Model) {
            $ModelPath = "$ModelsDir\E1\trained_network.pt"
        } else {
            $ModelPath = "$ModelsDir\$ExpName\trained_network.pt"
        }
    }

    Write-Host "Running inference using model: $ModelPath"

    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"     

    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"

    Write-Host "`n[+] [INFERENCE] Evaluating Model for: $ExpName at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")" -ForegroundColor Yellow
    Write-Host "    -> Test Root : $($env:DATA_ROOT)" -ForegroundColor DarkGray
    
    Set-Location -Path "$ScriptDir"
    $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 > "' + $SaveResultLoc + '"'

    # ------------------ DRY RUN ------------------
    if ($DRY_RUN) {
        Write-Host "[DRY RUN] Would execute: python main.py --inference ..." -ForegroundColor Magenta
        
        # FIX: Using the correct V3 variables for the path!
        $MetaPath = "$TargetDir\$EvalProtoName"
        
        if (Test-Path "$MetaPath") {
            $allLines = Get-Content "$MetaPath"
            Write-Host "    -> Read $($allLines.Count) total lines from $MetaPath" -ForegroundColor DarkGray
            
            # Check for both "bonafide" AND "genuine" just in case
            $bonafides = @($allLines | Where-Object { $_.ToLower().Contains("bonafide") -or $_.ToLower().Contains("genuine") } | Select-Object -First 100)
            $spoofs = @($allLines | Where-Object { -not $_.ToLower().Contains("bonafide") -and -not $_.ToLower().Contains("genuine") } | Select-Object -First 100)
            
            Write-Host "    -> Found $($bonafides.Count) Real and $($spoofs.Count) Spoof files to mock." -ForegroundColor DarkGray
            
            if ($bonafides.Count -eq 0 -or $spoofs.Count -eq 0) {
                Write-Host "[!] WARNING: Could not find any Bonafide/Spoof lines! Check if the metadata file is empty." -ForegroundColor Red
            }

            $mockScores = [System.Collections.ArrayList]::new()
            
            # Process the Bonafide files (Force exactly 20 to be "wrong")
            for ($i = 0; $i -lt $bonafides.Count; $i++) {
                $id = ($bonafides[$i] -split '\s+')[1]
                $score = if ($i -lt 20) { -1.0 } else { 1.0 }
                [void]$mockScores.Add("Output, $id, -, $score")
            }
            
            # Process the Spoof files (Force exactly 20 to be "wrong")
            for ($i = 0; $i -lt $spoofs.Count; $i++) {
                $id = ($spoofs[$i] -split '\s+')[1]
                $score = if ($i -lt 20) { 1.0 } else { -1.0 }
                [void]$mockScores.Add("Output, $id, -, $score")
            }
            
            # Write to the file
            $mockScores | Out-File -FilePath "$SaveResultLoc" -Encoding utf8
            Write-Host "    -> SUCCESS: Saved $($mockScores.Count) mock scores to: $SaveResultLoc" -ForegroundColor Cyan

        } else {
            Write-Host "[!] DRY RUN ERROR: Could not find metadata at $MetaPath" -ForegroundColor Red
        }
    } else {
        Write-Host $InfCommand
        Invoke-Expression $InfCommand     
    }
    # ---------------- END DRY RUN ----------------

    return $SaveResultLoc
}

function Run-Scoring {
    param ([string]$ScoreFile, [string]$ExpName)
    $MetaPath = "$ExpDir\$ExpName\" + $EvalProtoName
    
    Write-Host "`n[+] [SCORING] Calculating EER for $ExpName..." -ForegroundColor Yellow
    Write-Host "    -> Score File: $ScoreFile" -ForegroundColor Cyan
    
    $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $ScoreFile + '" --meta-file "' + $MetaPath + '"' + ' --exp-name "' + $ExpName + '"'

    $DRY_RUN = $false # Force actual scoring to run since it's fast and we want to see results
    if ($DRY_RUN) {
        Write-Host "[DRY RUN] Would execute: $ScoreCommand" -ForegroundColor Magenta
    } else {
        Write-Host $ScoreCommand
        Invoke-Expression $ScoreCommand
    }
}

function Run-E5-Train {
    param ([string]$feat)
    Write-Host "`n[+] [TRAIN] Starting E5 $($feat.ToUpper())..." -ForegroundColor Yellow
    
    $ExpName = "E5_$feat"
    $TargetDir = "$ExpDir\E4"
    $env:DATA_ROOT = $TargetDir
    $env:TRAIN_PROTO = "\" + $TrainProtoName
    $env:LIST_NAME = $TrainListName
    $env:TEST_PROTO = "\" + $EvalProtoName

    $SaveModelDir = "$ModelsDir\$ExpName"
    if (-not (Test-Path -Path $SaveModelDir)) { New-Item -ItemType Directory -Path $SaveModelDir -Force | Out-Null }
    Set-Location -Path "$ScriptDir"

    # Base training command
    $TrainCommand = 'python -u main.py --epochs 10 --num-workers 4 --batch-size 4 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name --run-name "' + $ExpName + '" --feature_type ' + $feat
    
    # --- DYNAMIC RESUME LOGIC ---
    # 1. Search for the newest epoch file in the specific experiment folder
    $LatestEpoch = Get-ChildItem -Path $SaveModelDir -Filter "epoch_*.pt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    # 2. Check if a file was actually found
    if ($null -ne $LatestEpoch) {
        # File found! Append it to the command
        $ResumeModelPath = $LatestEpoch.FullName
        $TrainCommand += ' --trained-model "' + $ResumeModelPath + '"'
        Write-Host "[INFO] Found existing checkpoint. Resuming training from: $($LatestEpoch.Name)" -ForegroundColor Cyan
    } else {
        # Folder is empty, do nothing to the command
        Write-Host "[INFO] No previous epochs found. Starting brand new training from scratch." -ForegroundColor Green
    }
    # ----------------------------

    if ($DRY_RUN) { Write-Host "[DRY RUN] $TrainCommand" -ForegroundColor Magenta }
    else { Write-Host $TrainCommand; Invoke-Expression $TrainCommand }
}

function Run-E5-Inference {
    param ([string]$feat)
    Write-Host "`n[+] [INFERENCE] Evaluating E5 $($feat.ToUpper())..." -ForegroundColor Yellow
    
    $ExpName = "E5_$feat"
    $TargetDir = "$ExpDir\E4"
    $env:DATA_ROOT = $TargetDir
    $env:TEST_PROTO = "\" + $EvalProtoName
    $env:LIST_NAME = $EvalListName

    $SaveModelDir = "$ModelsDir\$ExpName"
    $ModelPath = "$SaveModelDir\trained_network.pt"
    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }
    
    
    Write-Host "Running inference using model: $ModelPath"

    Write-Host "`n[+] [INFERENCE] Evaluating Model for: $ExpName at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")" -ForegroundColor Yellow
    Write-Host "    -> Test Root : $($env:DATA_ROOT)" -ForegroundColor DarkGray
    
    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"
    Set-Location -Path "$ScriptDir"

    
    $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 --feature_type ' + $feat + ' > "' + $SaveResultLoc + '"'
    # $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 --feature_type ' + $feat

    if ($DRY_RUN) { Write-Host "[DRY RUN] $InfCommand" -ForegroundColor Magenta }
    else { 
        Write-Host $InfCommand
        Invoke-Expression $InfCommand 
    }
}

function Run-E5-Scoring {
    param ([string]$feat)
    Write-Host "`n[+] [SCORING] Calculating EER for E5 $($feat.ToUpper())..." -ForegroundColor Yellow
    
    $ExpName = "E5_$feat"
    $TargetDir = "$ExpDir\E4"
    $OutputDir = "$ResultsDir\$ExpName"
    $MetaPath = "$TargetDir\" + $EvalProtoName

    # Auto-find the newest result file for this feature
    if (Test-Path $OutputDir) {
        $newestRawFile = Get-ChildItem -Path $OutputDir -Filter "*.txt" | Where-Object { $_.Name -like "*raw.txt" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        
        if ($newestRawFile) {
            $SaveResultLoc = $newestRawFile.FullName
            $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $SaveResultLoc + '" --meta-file "' + $MetaPath + '" --exp-name "' + $ExpName + '"'
            if ($DRY_RUN) { Write-Host "[DRY RUN] $ScoreCommand" -ForegroundColor Magenta }
            else { Write-Host $ScoreCommand; Invoke-Expression $ScoreCommand }
        } else { Write-Host "[-] No raw inference files found in $OutputDir. Run Inference first!" -ForegroundColor Red }
    } else { Write-Host "[-] Directory $OutputDir does not exist. Run Inference first!" -ForegroundColor Red }
}

function Menu-E5-Action {
    param ([string]$feat)
    $keepActionMenu = $true
    while ($keepActionMenu) {
        Write-Host "`n------------------------------------------" -ForegroundColor Yellow
        Write-Host "   ACTION MENU FOR: E5 $($feat.ToUpper())" -ForegroundColor Yellow
        Write-Host "------------------------------------------" -ForegroundColor Yellow
        Write-Host "1. Train Only"
        Write-Host "2. Inference Only"
        Write-Host "3. Scoring Only"
        Write-Host "4. Run All 3 (Train -> Inference -> Score)"
        Write-Host "5. Go Back to Features"

        $actChoice = Read-Host "Select an action"
        switch ($actChoice) {
            "1" { Run-E5-Train -feat $feat }
            "2" { Run-E5-Inference -feat $feat }
            "3" { Run-E5-Scoring -feat $feat }
            "4" { 
                Run-E5-Train -feat $feat
                Run-E5-Inference -feat $feat
                Run-E5-Scoring -feat $feat
            }
            "5" { $keepActionMenu = $false }
            Default { Write-Host "Invalid choice." -ForegroundColor Red }
        }
    }
}

function Menu-E5-Ablation {
    $keepE5Menu = $true
    while ($keepE5Menu) {
        Write-Host "`n==========================================" -ForegroundColor Cyan
        Write-Host "   E5: FEATURE ABLATION SUBMENU" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "1. LFCC"
        Write-Host "2. MFCC"
        Write-Host "3. CQCC"
        Write-Host "4. Fusion"
        Write-Host "5. Return to Main Menu"

        $e5Choice = Read-Host "Select a Feature to work with"
        switch ($e5Choice) {
            "1" { Menu-E5-Action -feat "lfcc" }
            "2" { Menu-E5-Action -feat "mfcc" }
            "3" { Menu-E5-Action -feat "cqcc" }
            "4" { Menu-E5-Action -feat "fusion" }
            "5" { Write-Host "Returning to Main Menu..." -ForegroundColor Green; $keepE5Menu = $false }
            Default { Write-Host "Invalid choice. Please select 1-5." -ForegroundColor Red }
        }
    }
}
function Run-FullExperiment {
    param ([string]$ExpName)
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "   STARTING FULL EXPERIMENT: $ExpName" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    # 1. Run training, but DO NOT assign it to a variable!
    # This allows the training logs to print normally to your screen.
    Run-Train -ExpName $ExpName
    
    # 2. Run inference WITHOUT passing the model path. 
    # Your script will automatically find the model using its internal logic!
    $scorePath = Run-Inference -ExpName $ExpName
    
    # 3. Run scoring
    Run-Scoring -ScoreFile $scorePath -ExpName $ExpName

    Write-Host "`n[SUCCESS] EXPERIMENT $ExpName COMPLETED!" -ForegroundColor Green
}

# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------

function Select-Experiment {
    Write-Host "`n--- Select Experiment ---" -ForegroundColor Cyan
    Write-Host "1. E1"
    Write-Host "2. E1.5"
    Write-Host "3. E2"
    Write-Host "4. E3"
    Write-Host "5. E4"
    $choice = Read-Host "Select number"
    switch ($choice) {
        "1" { return "E1" } "2" { return "E1.5" } "3" { return "E2" }
        "4" { return "E3" } "5" { return "E4" } Default { return "" }
    }
}

$keepRunning = $true
while ($keepRunning) {
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "   ANTI-SPOOF PIPELINE MANAGER V3" -ForegroundColor Cyan
    if ($DRY_RUN) { Write-Host "   [DRY RUN MODE ENABLED]" -ForegroundColor Magenta }
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. Train an Experiment"
    Write-Host "2. Run Inference for an Experiment"
    Write-Host "3. Run Scoring for an Experiment"
    Write-Host "4. Run End-to-End Experiment"
    Write-Host "5. Open E5 (Feature Ablation) Submenu"  # <--- FIX THIS
    Write-Host "6. Exit"                                  # <--- FIX THIS
    
    $mainChoice = Read-Host "Select an option"

    switch ($mainChoice) {
        "1" { $exp = Select-Experiment; if ($exp) { Run-Train -ExpName $exp } }
        "2" { $exp = Select-Experiment; if ($exp) { Run-Inference -ExpName $exp } }
        "3" { 
            $exp = Select-Experiment
            if ($exp) {
                # Auto-find the newest score file for this experiment
                $expResultsDir = "$ResultsDir\$exp"
                if (Test-Path $expResultsDir) {
                    $newestRawFile = Get-ChildItem -Path $expResultsDir -Filter "*.txt" | Where-Object { $_.Name -like "*raw.txt" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                    if ($newestRawFile) {
                        Write-Host "Auto-selected newest raw file: $($newestRawFile.Name)" -ForegroundColor Cyan
                        Run-Scoring -ScoreFile $newestRawFile.FullName -ExpName $exp
                    } else { Write-Host "No raw score files found in $expResultsDir" -ForegroundColor Red }
                } else { Write-Host "No inference results found for $exp yet." -ForegroundColor Red }
            }
        }
        "4" { $exp = Select-Experiment; if ($exp) { Run-FullExperiment -ExpName $exp } }
        "5" { Menu-E5-Ablation } # <--- TRIGGER THE E5 MENU HERE
        "6" { Write-Host "`nExiting Pipeline Manager..." -ForegroundColor Green; $keepRunning = $false }
    }
}