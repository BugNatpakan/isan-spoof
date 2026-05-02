# ====================================================================
# Anti-Spoof Pipeline Manager V3 (Self-Contained Experiment Structure)
# ====================================================================

$DRY_RUN       = $false   # Set to $false to run actual python scripts

# --- GLOBAL PATHS ---
$BaseDir       = "D:\work\AI frontier\project AntiSpoof\isan-spoof"
$ScriptDir     = "$BaseDir\scripts"
$ResultsDir    = "$BaseDir\results"
$ModelsDir     = "$BaseDir\models"
$ScoringScript = "$BaseDir\results\final_score.py"
$ExpDir        = "$BaseDir\data\experiment"

# --- DEFAULT FILENAMES INSIDE EACH 'E' FOLDER ---
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

    if (-not (Test-Path -Path $SaveModelDir)) {
        Write-Host "[i] Creating missing model directory: $SaveModelDir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $SaveModelDir -Force | Out-Null
    }

    Set-Location -Path "$ScriptDir"
    $TrainCommand = 'python -u main.py --epochs 10 --batch-size 8 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name --run-name "' + $ExpName +'"'
    
    if ($DRY_RUN) { Write-Host "[DRY RUN] $TrainCommand" -ForegroundColor Magenta } 
    else { Write-Host $TrainCommand; Invoke-Expression $TrainCommand }
    return "$SaveModelDir\trained_network.pt"
}

function Run-Inference {
    param ([string]$ExpName, [string]$ModelPath = "")
    $TargetDir      = "$ExpDir\$ExpName"
    $env:DATA_ROOT  = $TargetDir
    $env:TEST_PROTO = "\" + $EvalProtoName
    $env:LIST_NAME  = $EvalListName
        
    if ($ModelPath -eq "") {
        $useE1Model = @("E1", "E1.5", "E2")
        if ($ExpName -in $useE1Model) { $ModelPath = "$ModelsDir\E1\trained_network.pt" } 
        else { $ModelPath = "$ModelsDir\$ExpName\trained_network.pt" }
    }

    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }
    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"     
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"

    Write-Host "`n[+] [INFERENCE] Evaluating Model for: $ExpName" -ForegroundColor Yellow
    
    Set-Location -Path "$ScriptDir"
    
    # --- THE FIX IS ON THIS LINE ---
    # We lock the features to 'lfcc' and 'lcnn' so it matches the E4 weights perfectly!
    $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 --feature_type lfcc --architecture lcnn > "' + $SaveResultLoc + '"'
   
    if ($DRY_RUN) { Write-Host "[DRY RUN] $InfCommand" -ForegroundColor Magenta } 
    else { Write-Host $InfCommand; Invoke-Expression $InfCommand }

    return $SaveResultLoc
}

function Run-Scoring {
    param ([string]$ScoreFile, [string]$ExpName)
    $MetaPath = "$ExpDir\$ExpName\" + $EvalProtoName
    
    Write-Host "`n[+] [SCORING] Calculating EER for $ExpName..." -ForegroundColor Yellow
    $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $ScoreFile + '" --meta-file "' + $MetaPath + '"' + ' --exp-name "' + $ExpName + '"'
    # 'python "D:\work\AI frontier\project AntiSpoof\isan-spoof\results\final_score.py" --score-file "' + $ScoreFile + '" --meta-file "' + $MetaPath + '"' + ' --exp-name "' + $ExpName + '"'
    if ($DRY_RUN) { Write-Host "[DRY RUN] $ScoreCommand" -ForegroundColor Magenta } 
    else { Write-Host $ScoreCommand; Invoke-Expression $ScoreCommand }
}

# =========================================================
# E5 SPECIFIC FUNCTIONS (FEATURE ABLATION)
# =========================================================

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

    $TrainCommand = 'python -u main.py --epochs 10 --num-workers 4 --batch-size 4 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name --run-name "' + $ExpName + '" --feature_type ' + $feat

    $resumeTraining = $false  # Set to $true to enable auto-resume from latest epoch
    if ($resumeTraining) {
        $LatestEpoch = Get-ChildItem -Path $SaveModelDir -Filter "epoch_*.pt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($null -ne $LatestEpoch) {
            $TrainCommand += ' --trained-model "' + $LatestEpoch.FullName + '"'
            Write-Host "[INFO] Resuming training from: $($LatestEpoch.Name)" -ForegroundColor Cyan
        }
    }

    Write-Host "    -> Data Root  : $($env:DATA_ROOT)" -ForegroundColor DarkGray
    Write-Host "    -> Feature    : $feat" -ForegroundColor DarkGray
    Write-Host "    -> Model Dir  : $SaveModelDir" -ForegroundColor DarkGray

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

    $ModelPath = "$ModelsDir\$ExpName\trained_network.pt"
    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }

    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"
    Set-Location -Path "$ScriptDir"

    $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 --feature_type ' + $feat + ' > "' + $SaveResultLoc + '"'

    if ($DRY_RUN) { Write-Host "[DRY RUN] $InfCommand" -ForegroundColor Magenta }
    else { Write-Host $InfCommand; Invoke-Expression $InfCommand }
}

function Run-E5-Scoring {
    param ([string]$feat)
    Write-Host "`n[+] [SCORING] Calculating EER for E5 $($feat.ToUpper())..." -ForegroundColor Yellow
    $ExpName = "E5_$feat"
    $MetaPath = "$ExpDir\E4\" + $EvalProtoName
    $OutputDir = "$ResultsDir\$ExpName"

    if (Test-Path $OutputDir) {
        $newestRawFile = Get-ChildItem -Path $OutputDir -Filter "*.txt" | Where-Object { $_.Name -like "*raw.txt" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($newestRawFile) {
            $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $newestRawFile.FullName + '" --meta-file "' + $MetaPath + '" --exp-name "' + $ExpName + '"'
            if ($DRY_RUN) { Write-Host "[DRY RUN] $ScoreCommand" -ForegroundColor Magenta }
            else { Invoke-Expression $ScoreCommand }
        } else { Write-Host "[-] No raw inference files found in $OutputDir. Run inference first." -ForegroundColor Red }
    } else { Write-Host "[-] Directory $OutputDir does not exist. Run inference first." -ForegroundColor Red }
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
            "4" { Run-E5-Train -feat $feat; Run-E5-Inference -feat $feat; Run-E5-Scoring -feat $feat }
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
        Write-Host "1. LFCC (Baseline)"
        Write-Host "2. MFCC"
        Write-Host "3. CQCC"
        Write-Host "4. Fusion (LFCC + MFCC)"
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

# =========================================================
# E6 SPECIFIC FUNCTIONS (ARCHITECTURE ABLATION)
# =========================================================

function Run-E6-Train {
    param ([string]$arch)
    Write-Host "`n[+] [TRAIN] Starting E6 $($arch.ToUpper())..." -ForegroundColor Yellow
    $ExpName = "E6_$arch"
    $TargetDir = "$ExpDir\E4"
    $env:DATA_ROOT = $TargetDir
    $env:TRAIN_PROTO = "\" + $TrainProtoName
    $env:LIST_NAME = $TrainListName
    $env:TEST_PROTO = "\" + $EvalProtoName

    $SaveModelDir = "$ModelsDir\$ExpName"
    if (-not (Test-Path -Path $SaveModelDir)) { New-Item -ItemType Directory -Path $SaveModelDir -Force | Out-Null }
    Set-Location -Path "$ScriptDir"

    $TrainCommand = 'python -u main.py --epochs 10 --num-workers 4 --batch-size 4 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name --run-name "' + $ExpName + '" --feature_type lfcc --architecture ' + $arch
    
    $LatestEpoch = Get-ChildItem -Path $SaveModelDir -Filter "epoch_*.pt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($resumeTraining) {
        if ($null -ne $LatestEpoch) {
            $TrainCommand += ' --trained-model "' + $LatestEpoch.FullName + '"'
            Write-Host "[INFO] Resuming training from: $($LatestEpoch.Name)" -ForegroundColor Cyan
        }
    }

    if ($DRY_RUN) { Write-Host "[DRY RUN] $TrainCommand" -ForegroundColor Magenta }
    else { Invoke-Expression $TrainCommand }
}

function Run-E6-Inference {
    param ([string]$arch)
    Write-Host "`n[+] [INFERENCE] Evaluating E6 $($arch.ToUpper())..." -ForegroundColor Yellow
    $ExpName = "E6_$arch"
    $TargetDir = "$ExpDir\E4"
    $env:DATA_ROOT = $TargetDir
    $env:TEST_PROTO = "\" + $EvalProtoName
    $env:LIST_NAME = $EvalListName

    $SaveModelDir = "$ModelsDir\$ExpName"
    $ModelPath = "$SaveModelDir\trained_network.pt"
    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }
    
    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"
    Set-Location -Path "$ScriptDir"

    $InfCommand = 'python main.py --inference --model-forward-with-file-name --trained-model "' + $ModelPath + '" --batch-size 1 --feature_type lfcc --architecture ' + $arch + ' > "' + $SaveResultLoc + '"'

    if ($DRY_RUN) { Write-Host "[DRY RUN] $InfCommand" -ForegroundColor Magenta }
    else { Invoke-Expression $InfCommand }
}

function Run-E6-Scoring {
    param ([string]$arch)
    Write-Host "`n[+] [SCORING] Calculating EER for E6 $($arch.ToUpper())..." -ForegroundColor Yellow
    $ExpName = "E6_$arch"
    $TargetDir = "$ExpDir\E4"
    $OutputDir = "$ResultsDir\$ExpName"
    $MetaPath = "$TargetDir\" + $EvalProtoName

    if (Test-Path $OutputDir) {
        $newestRawFile = Get-ChildItem -Path $OutputDir -Filter "*.txt" | Where-Object { $_.Name -like "*raw.txt" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($newestRawFile) {
            $SaveResultLoc = $newestRawFile.FullName
            $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $SaveResultLoc + '" --meta-file "' + $MetaPath + '" --exp-name "' + $ExpName + '"'
            if ($DRY_RUN) { Write-Host "[DRY RUN] $ScoreCommand" -ForegroundColor Magenta }
            else { Invoke-Expression $ScoreCommand }
        } else { Write-Host "[-] No raw inference files found." -ForegroundColor Red }
    } else { Write-Host "[-] Directory $OutputDir does not exist." -ForegroundColor Red }
}

function Menu-E6-GMM-Action {
    $keepGMMMenu = $true
    while ($keepGMMMenu) {
        Write-Host "`n------------------------------------------" -ForegroundColor Yellow
        Write-Host "   ACTION MENU FOR: E6 GMM" -ForegroundColor Yellow
        Write-Host "------------------------------------------" -ForegroundColor Yellow
        Write-Host "1. Run Full GMM Pipeline (Train -> Inference -> Auto-Score)"
        Write-Host "2. Run Scoring Only (Requires previous inference file)"
        Write-Host "3. Go Back to Architectures"

        $actChoice = Read-Host "Select an action"
        switch ($actChoice) {
            "1" { 
                Write-Host "`n[+] [GMM BASELINE] Starting Full GMM Pipeline..." -ForegroundColor Yellow
                Set-Location -Path "$ScriptDir"
                $GmmCommand = 'python run_gmm.py'
                if ($DRY_RUN) { Write-Host "[DRY RUN] $GmmCommand" -ForegroundColor Magenta }
                else { Invoke-Expression $GmmCommand }
            }
            "2" { 
                Write-Host "`n[+] [SCORING] Calculating EER for E6 GMM..." -ForegroundColor Yellow
                $TargetDir = "$ExpDir\E4"
                $OutputDir = "$ResultsDir\E6_gmm"
                $MetaPath = "$TargetDir\$EvalProtoName"

                if (Test-Path $OutputDir) {
                    $newestRawFile = Get-ChildItem -Path $OutputDir -Filter "*.txt" | Where-Object { $_.Name -like "*raw.txt" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                    if ($newestRawFile) {
                        $SaveResultLoc = $newestRawFile.FullName
                        $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $SaveResultLoc + '" --meta-file "' + $MetaPath + '" --exp-name "E6_GMM"'
                        if ($DRY_RUN) { Write-Host "[DRY RUN] $ScoreCommand" -ForegroundColor Magenta }
                        else { Invoke-Expression $ScoreCommand }
                    } else { Write-Host "[-] No raw inference files found in $OutputDir. Run Full Pipeline first!" -ForegroundColor Red }
                } else { Write-Host "[-] Directory $OutputDir does not exist. Run Full Pipeline first!" -ForegroundColor Red }
            }
            "3" { $keepGMMMenu = $false }
            Default { Write-Host "Invalid choice." -ForegroundColor Red }
        }
    }
}

function Menu-E6-Action {
    param ([string]$arch)
    $keepActionMenu = $true
    while ($keepActionMenu) {
        Write-Host "`n------------------------------------------" -ForegroundColor Yellow
        Write-Host "   ACTION MENU FOR: E6 $($arch.ToUpper())" -ForegroundColor Yellow
        Write-Host "------------------------------------------" -ForegroundColor Yellow
        Write-Host "1. Train Only"
        Write-Host "2. Inference Only"
        Write-Host "3. Scoring Only"
        Write-Host "4. Run All 3 (Train -> Inference -> Score)"
        Write-Host "5. Go Back to Architectures"

        $actChoice = Read-Host "Select an action"
        switch ($actChoice) {
            "1" { Run-E6-Train -arch $arch }
            "2" { Run-E6-Inference -arch $arch }
            "3" { Run-E6-Scoring -arch $arch }
            "4" { 
                Run-E6-Train -arch $arch
                Run-E6-Inference -arch $arch
                Run-E6-Scoring -arch $arch
            }
            "5" { $keepActionMenu = $false }
            Default { Write-Host "Invalid choice." -ForegroundColor Red }
        }
    }
}

function Menu-E6-Ablation {
    $keepE6Menu = $true
    while ($keepE6Menu) {
        Write-Host "`n==========================================" -ForegroundColor Cyan
        Write-Host "   E6: ARCHITECTURE ABLATION SUBMENU" -ForegroundColor Cyan
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "1. LCNN (Baseline)"
        Write-Host "2. ResNet"
        Write-Host "3. GMM (Traditional ML Baseline)"
        Write-Host "4. Return to Main Menu"

        $e6Choice = Read-Host "Select an Architecture to work with"
        switch ($e6Choice) {
            "1" { Menu-E6-Action -arch "lcnn" }
            "2" { Menu-E6-Action -arch "resnet" }
            "3" { Menu-E6-GMM-Action }
            "4" { Write-Host "Returning to Main Menu..." -ForegroundColor Green; $keepE6Menu = $false }
            Default { Write-Host "Invalid choice. Please select 1-4." -ForegroundColor Red }
        }
    }
}


# =========================================================
# STANDARD EXPERIMENT RUNNER
# =========================================================

function Run-FullExperiment {
    param ([string]$ExpName)
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "   STARTING FULL EXPERIMENT: $ExpName" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    Run-Train -ExpName $ExpName
    $scorePath = Run-Inference -ExpName $ExpName
    Run-Scoring -ScoreFile $scorePath -ExpName $ExpName

    Write-Host "`n[SUCCESS] EXPERIMENT $ExpName COMPLETED!" -ForegroundColor Green
}

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

# ---------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------

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
    Write-Host "5. Open E5 (Feature Ablation) Submenu"
    Write-Host "6. Open E6 (Architecture Ablation) Submenu"
    Write-Host "7. Exit"
    Write-Host "8. run custom pipeline"
    
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
        "5" { Menu-E5-Ablation }
        "6" { Menu-E6-Ablation }
        "7" { Write-Host "`nExiting Pipeline Manager..." -ForegroundColor Green; $keepRunning = $false }
        "8" { 
            Write-Host "`n[Custom pipeline] Running E5-2 (fusion), E6-2, E6-3" -ForegroundColor Yellow
            
            # # run E5-3 (fusion)
            # Write-Host "`n[+] [Fusion BASELINE] Starting Full Fusion Pipeline..." -ForegroundColor Yellow
            # $customFeat = "fusion"  # Change to "mfcc", "cqcc", or "fusion" to test other features
            # Run-E5-Train -feat $customFeat; Run-E5-Inference -feat $customFeat; Run-E5-Scoring -feat $customFeat


            # run E6-2 (ResNet)
            $customArch = "resnet"  
            Write-Host "`n[+] [ResNet BASELINE] Starting Full ResNet Pipeline..." -ForegroundColor Yellow
            Run-E6-Train -arch $customArch
            Run-E6-Inference -arch $customArch
            Run-E6-Scoring -arch $customArch

            # # run E6-3 (GMM)
            # Write-Host "`n[+] [GMM BASELINE] Starting Full GMM Pipeline..." -ForegroundColor Yellow
            # Set-Location -Path "$ScriptDir"
            # $GmmCommand = 'python run_gmm.py'
            # Invoke-Expression $GmmCommand 
        }
    }
}
