# Windows PowerShell version of the ASVspoof download script

$UrlLinks = @(
    "https://www.asvspoof.org/asvspoof2021/LA-keys-full.tar.gz",
    "https://www.asvspoof.org/asvspoof2021/PA-keys-full.tar.gz",
    "https://www.asvspoof.org/asvspoof2021/DF-keys-full.tar.gz"
)

$Md5SumVals = @(
    "037592a0515971bbd0fa3bff2bad4abc",
    "a639ea472cf4fb564a62fbc7383c24cf",
    "dabbc5628de4fcef53036c99ac7ab93a"
)

# Loop through all 3 files
for ($i = 0; $i -lt $UrlLinks.Length; $i++) {
    $Url = $UrlLinks[$i]
    $ExpectedMd5 = $Md5SumVals[$i]
    
    # Extract just the filename (e.g., LA-keys-full.tar.gz) from the URL
    $PackName = Split-Path $Url -Leaf
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Downloading $PackName..." -ForegroundColor Cyan
    
    $downloadSuccess = $false
    $retryCount = 0
    
    # Try downloading with a simple retry loop if the server drops
    while (-not $downloadSuccess -and $retryCount -lt 5) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile $PackName -ErrorAction Stop
            $downloadSuccess = $true
        } catch {
            Write-Host "File server is busy. Re-try to download $Url" -ForegroundColor Yellow
            Start-Sleep -Seconds 1
            $retryCount++
        }
    }
    
    # Check if download completely failed
    if (-not (Test-Path $PackName)) {
        Write-Host "Failed to download the file. Please manually download $Url." -ForegroundColor Red
        continue # Skip to the next file
    }

    # Verify the MD5 Checksum
    Write-Host "Verifying checksum..."
    # PowerShell returns hashes in uppercase, so we force it to lowercase to match the array
    $FileHash = (Get-FileHash -Path $PackName -Algorithm MD5).Hash.ToLower()
    
    if ($FileHash -eq $ExpectedMd5) {
        Write-Host "Checksum match! Extracting $PackName..." -ForegroundColor Green
        tar -xzf $PackName
    } else {
        Write-Host "Downloaded file seems to be damaged. Checksum mismatch!" -ForegroundColor Red
        Write-Host "Expected: $ExpectedMd5"
        Write-Host "Got:      $FileHash"
        Write-Host "Please contact the organizers." -ForegroundColor Red
    }
}

Write-Host "`nAll operations complete!" -ForegroundColor Green