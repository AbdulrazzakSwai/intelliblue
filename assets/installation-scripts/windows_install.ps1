Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       IntelliBlue - Automated Installer for Windows" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# -------------------------------------------
# Check for Administrator privileges
# -------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[-] This installer requires Administrator privileges." -ForegroundColor Red
    Write-Host "    Please run PowerShell as Administrator." -ForegroundColor Yellow
    Read-Host "    Press Enter to exit..."
    return
}

# -------------------------------------------
# Pre-requisite Checks
# -------------------------------------------
Write-Host "[*] [1/6] Checking for required tools..." -ForegroundColor Yellow

# Check Git
$gitInstalled = $false
try {
    $null = Get-Command "git" -ErrorAction Stop
    $gitVer = (git --version)
    Write-Host "      [+] Found Git: $gitVer" -ForegroundColor Green
    $gitInstalled = $true
} catch {
    Write-Host "      [-] Git is NOT installed." -ForegroundColor Red
}

# Check Python
$pythonInstalled = $false
try {
    $null = Get-Command python -ErrorAction Stop
    $pyVer = ((python --version) 2>&1).Trim()
    if ($pyVer -match "Python\s+\d+\.\d+(\.\d+)?") {
        Write-Host "      [+] Found Python: $pyVer" -ForegroundColor Green
        $pythonInstalled = $true
    }
    else {
        throw "Invalid Python response"
    }
}
catch {
    Write-Host "      [-] Python is NOT installed." -ForegroundColor Red
}

# Check Ollama
$ollamaInstalled = $false
try {
    $null = Get-Command "ollama" -ErrorAction Stop
    $ollamaVer = (ollama --version)
    Write-Host "      [+] Found Ollama: $ollamaVer" -ForegroundColor Green
    $ollamaInstalled = $true
} catch {
    Write-Host "      [-] Ollama is NOT installed." -ForegroundColor Red
}

# Check Npcap
$npcapInstalled = (Test-Path "C:\Program Files\Npcap\NPFInstall.exe") -or (Test-Path "C:\Windows\System32\Npcap\NPFInstall.exe")
if ($npcapInstalled) {
    Write-Host "      [+] Found Npcap." -ForegroundColor Green
} else {
    Write-Host "      [-] Npcap is NOT installed." -ForegroundColor Red
}

Write-Host ""

# -------------------------------------------
# Install Missing Tools
# -------------------------------------------
Write-Host "[*] [2/6] Installing missing tools (This may take a while)..." -ForegroundColor Yellow

if ($gitInstalled -and $pythonInstalled -and $ollamaInstalled -and $npcapInstalled) {
    Write-Host "      [+] All tools are installed, no need to install anything." -ForegroundColor Green
}

if (-not $gitInstalled) {
    Write-Host "      [*] Installing Git..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe" -OutFile "$env:TEMP\git_installer.exe"
    if (Test-Path "$env:TEMP\git_installer.exe") {
        Start-Process -FilePath "$env:TEMP\git_installer.exe" -ArgumentList "/VERYSILENT /NORESTART" -Wait -NoNewWindow
        Remove-Item "$env:TEMP\git_installer.exe" -Force
        Write-Host "      [+] Git installed successfully." -ForegroundColor Green
        $env:Path += ";C:\Program Files\Git\cmd"
    } else {
        Write-Host "      [-] Failed to download Git. Please install manually." -ForegroundColor Red
        Read-Host "      Press Enter to exit..."
        return
    }
}

if (-not $pythonInstalled) {
    Write-Host "      [*] Installing Python 3.12..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe" -OutFile "$env:TEMP\python_installer.exe"
    if (Test-Path "$env:TEMP\python_installer.exe") {
        Start-Process -FilePath "$env:TEMP\python_installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait -NoNewWindow
        Remove-Item "$env:TEMP\python_installer.exe" -Force
        Write-Host "      [+] Python installed successfully." -ForegroundColor Green
        # Try to refresh path for current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-Host "      [-] Failed to download Python. Please install manually." -ForegroundColor Red
        Read-Host "      Press Enter to exit..."
        return
    }
}

if (-not $ollamaInstalled) {
    Write-Host "      [*] Installing Ollama..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile "$env:TEMP\OllamaSetup.exe"
    if (Test-Path "$env:TEMP\OllamaSetup.exe") {
        Start-Process -FilePath "$env:TEMP\OllamaSetup.exe" -ArgumentList "/VERYSILENT /NORESTART" -Wait -NoNewWindow
        Remove-Item "$env:TEMP\OllamaSetup.exe" -Force
        Write-Host "      [+] Ollama installed successfully." -ForegroundColor Green
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Start Ollama service if not running
        Write-Host "      [*] Starting Ollama background process..." -ForegroundColor Cyan
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    } else {
        Write-Host "      [-] Failed to download Ollama. Please install manually." -ForegroundColor Red
        Read-Host "      Press Enter to exit..."
        return
    }
}

if (-not $npcapInstalled) {
    Write-Host "      [*] Installing Npcap (interactive dialog may appear)..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://npcap.com/dist/npcap-1.80.exe" -OutFile "$env:TEMP\npcap_installer.exe"
    if (Test-Path "$env:TEMP\npcap_installer.exe") {
        Start-Process -FilePath "$env:TEMP\npcap_installer.exe" -Wait -NoNewWindow
        Remove-Item "$env:TEMP\npcap_installer.exe" -Force
        Write-Host "      [+] Npcap installed successfully." -ForegroundColor Green
    } else {
        Write-Host "      [-] Failed to download Npcap. Please install manually." -ForegroundColor Red
    }
}

Write-Host ""

# -------------------------------------------
# Install and run Llama models
# -------------------------------------------
Write-Host "[*] [3/6] Setting up Llama models (This may take a while)..." -ForegroundColor Yellow
$ollamaList = (ollama list 2>&1)

$models = @("llama3", "llama3.2")
foreach ($model in $models) {
    if ($ollamaList -match "$model") {
        Write-Host "      [+] $model model already installed." -ForegroundColor Green
    } else {
        Write-Host "      [*] Pulling $model model via Ollama (This may take a while)..." -ForegroundColor Cyan
        ollama pull $model
        if ($LASTEXITCODE -ne 0) {
            Write-Host "      [-] Failed to pull $model model." -ForegroundColor Red
            Write-Host "          Make sure Ollama is running and try: ollama pull $model" -ForegroundColor Yellow
        } else {
            Write-Host "      [+] $model model ready." -ForegroundColor Green
        }
    }
}

Write-Host ""

# -------------------------------------------
# Clone Repository
# -------------------------------------------
Write-Host "[*] [4/6] Cloning IntelliBlue repository..." -ForegroundColor Yellow
$installDir = "$HOME\Desktop\IntelliBlue"
if (Test-Path $installDir) {
    Write-Host "      [*] Directory already exists at $installDir" -ForegroundColor Cyan
    Write-Host "      [*] Skipping clone." -ForegroundColor Yellow
} else {
    git clone https://github.com/AbdulrazzakSwai/IntelliBlue.git $installDir -q *>$null
}
Set-Location $installDir
Write-Host ""

# -------------------------------------------
# Setup Virtual Environment
# -------------------------------------------
Write-Host "[*] [5/6] Setting up Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv *>$null
    Write-Host "      [+] Created virtual environment (venv/)." -ForegroundColor Green
} else {
    Write-Host "      [+] Virtual environment already exists." -ForegroundColor Green
}

Write-Host ""

# -------------------------------------------
# Install Dependencies
# -------------------------------------------
Write-Host "[*] [6/6] Installing Python dependencies (This may take a while)..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".\venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "      [-] Failed to install Python dependencies." -ForegroundColor Red
    Read-Host "      Press Enter to exit..."
    return
}
Write-Host "      [+] Dependencies installed successfully." -ForegroundColor Green
Write-Host ""

# -------------------------------------------
# Completion prompt
# -------------------------------------------
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "           Installation Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start IntelliBlue, simply run these commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  cd $installDir" -ForegroundColor White
Write-Host "  Set-ExecutionPolicy Bypass -Scope Process; . .\venv\Scripts\Activate" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""
Write-Host "The application will be available at http://localhost:5000" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$response = Read-Host "[?] Would you like to run IntelliBlue now? (y/n)"
if ($response -match "^y") {
    Write-Host "[*] Starting IntelliBlue..." -ForegroundColor Cyan
    & ".\venv\Scripts\python.exe" app.py
}
