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

    Write-Host "`n[+] [TRAIN] Starting Training for: $ExpName" -ForegroundColor Yellow
    Write-Host "    -> Data Root : $($env:DATA_ROOT)" -ForegroundColor DarkGray
    

    # Ensure the model save directory exists before Python tries to use it!
    if (-not (Test-Path -Path $SaveModelDir)) {
        Write-Host "[i] Creating missing model directory: $SaveModelDir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $SaveModelDir -Force | Out-Null
    }

    Set-Location -Path "$ScriptDir"
    $TrainCommand = 'python -u main.py --epochs 10 --batch-size 8 --save-model-dir "' + $SaveModelDir + '" --model-forward-with-file-name'
    
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
        $useE4Model = @("E4", "E5", "E6")
        
        if ($ExpName -in $useE1Model) {
            $ModelPath = "$ModelsDir\E1\trained_network.pt"
        } elseif ($ExpName -in $useE4Model) {
            $ModelPath = "$ModelsDir\E4\trained_network.pt"
        } else {
            $ModelPath = "$ModelsDir\$ExpName\trained_network.pt"
        }
    }

    Write-Host "Running inference using model: $ModelPath"

    $Timestamp = Get-Date -Format "ddMMyyyy_HHmmss"     

    $OutputDir = "$ResultsDir\$ExpName"
    if (!(Test-Path "$OutputDir")) { New-Item -ItemType Directory -Path "$OutputDir" -Force | Out-Null }
    $SaveResultLoc = "$OutputDir\results_${Timestamp}_raw.txt"

    Write-Host "`n[+] [INFERENCE] Evaluating Model for: $ExpName" -ForegroundColor Yellow
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
        Invoke-Expression $InfCommand
        Write-Host $InfCommand
    }
    # ---------------- END DRY RUN ----------------

    return $SaveResultLoc
}

function Run-Scoring {
    param ([string]$ScoreFile, [string]$ExpName)
    $MetaPath = "$ExpDir\$ExpName\" + $EvalProtoName
    
    Write-Host "`n[+] [SCORING] Calculating EER for $ExpName..." -ForegroundColor Yellow
    Write-Host "    -> Score File: $ScoreFile" -ForegroundColor Cyan
    
    $ScoreCommand = 'python "' + $ScoringScript + '" --score-file "' + $ScoreFile + '" --meta-file "' + $MetaPath + '"'

    $DRY_RUN = $false # Force actual scoring to run since it's fast and we want to see results
    if ($DRY_RUN) {
        Write-Host "[DRY RUN] Would execute: $ScoreCommand" -ForegroundColor Magenta
    } else {
        Invoke-Expression $ScoreCommand
        Write-Host $ScoreCommand
    }
}

function Run-FullExperiment {
    param ([string]$ExpName)
    Write-Host "`n==========================================" -ForegroundColor Green
    Write-Host "   STARTING FULL EXPERIMENT: $ExpName" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    $modelPath = Run-Train -ExpName $ExpName
    $scorePath = Run-Inference -ExpName $ExpName -ModelPath $modelPath
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
    Write-Host "5. Exit"
    
    $mainChoice = Read-Host "Select an option"

    switch ($mainChoice) {
        "1" { 
            $exp = Select-Experiment
            if ($exp) { Run-Train -ExpName $exp }
        }
        "2" { 
            $exp = Select-Experiment
            if ($exp) { Run-Inference -ExpName $exp }
        }
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
        "4" { 
            $exp = Select-Experiment
            if ($exp) { Run-FullExperiment -ExpName $exp }
        }
        "5" { 
            Write-Host "`nExiting Pipeline Manager..." -ForegroundColor Green
            $keepRunning = $false
        }
    }
}