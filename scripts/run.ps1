# --- Project Pipeline Script ---

# Define Paths
$scriptDir = "D:\work\AI frontier\project AntiSpoof\isan-spoof\scripts"
$scoringScript = "D:\work\AI frontier\project AntiSpoof\isan-spoof\results\final_score.py"

# Function to show a menu
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   ANTI-SPOOF PROJECT PIPELINE MANAGER" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. Start Training (10 Epochs)"
Write-Host "2. Run Inference (E2 Evaluation)"
Write-Host "3. Run Scoring (Calculate EER)"
Write-Host "4. Exit"
Write-Host "==========================================" -ForegroundColor Cyan

$choice = Read-Host "Please select an option (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n[+] Starting Training..." -ForegroundColor Yellow
        Set-Location -Path $scriptDir
        python main.py --epochs 10 --batch-size 16 --save-model-dir ../model --model-forward-with-file-name
    }
    
    "2" {
        Write-Host "`n[+] Starting Inference..." -ForegroundColor Yellow
        Set-Location -Path $scriptDir
        # Ensure output directory exists
        if (!(Test-Path "../results/E2_scores")) { New-Item -ItemType Directory -Path "../results/E2_scores" }
        
        python main.py --inference --model-forward-with-file-name --trained-model ../models/lcnn/trained_network.pt --save-trained-name ../results/E2_scores/eval_scores.txt --batch-size 1 > ../results/E2_scores/eval_results_raw.txt
        Write-Host "Inference Complete. Scores saved to results/E2_scores/eval_scores.txt" -ForegroundColor Green
    }
    
    "3" {
        Write-Host "`n[+] Running Scoring Script..." -ForegroundColor Yellow
        python $scoringScript
    }
    
    "4" {
        Write-Host "Exiting..."
        exit
    }
    
    Default {
        Write-Host "Invalid selection. Please run the script again." -ForegroundColor Red
    }
}

# Keep window open if run via right-click
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")