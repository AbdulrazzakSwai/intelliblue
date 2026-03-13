#!/usr/bin/env bash

set -e

echo ""
echo "  ============================================================"
echo "       IntelliBlue - Automated Installer for Linux"
echo "  ============================================================"
echo ""

# -------------------------------------------
# Pre-requisite Checks
# -------------------------------------------
echo "  [1/6] Checking for required tools..."

# Check Git
if command -v git &>/dev/null; then
    GITVER=$(git --version | awk '{print $3}')
    echo "        Found Git: $GITVER"
else
    echo "        Git is NOT installed."
    GIT_MISSING=1
fi

# Check Python 3
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    echo "        Found Python 3: $PYVER"
else
    echo "        Python 3 is NOT installed."
    PY_MISSING=1
fi

# Check Ollama
if command -v ollama &>/dev/null; then
    OLLAMAVER=$(ollama --version)
    echo "        Found Ollama: $OLLAMAVER"
else
    echo "        Ollama is NOT installed."
    OLLAMA_MISSING=1
fi

# Check libpcap
if dpkg -s libpcap-dev &>/dev/null 2>&1 || rpm -q libpcap-devel &>/dev/null 2>&1 || pacman -Qs libpcap &>/dev/null 2>&1; then
    echo "        Found libpcap."
else
    echo "        libpcap is NOT installed."
    PCAP_MISSING=1
fi

echo ""

# -------------------------------------------
# Install Missing Tools
# -------------------------------------------
echo "  [2/6] Installing missing tools..."

if [ "$GIT_MISSING" = "1" ] || [ "$PY_MISSING" = "1" ] || [ "$PCAP_MISSING" = "1" ]; then
    echo "        Updating package manager and installing missing tools..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq >/dev/null 2>&1
        [ "$GIT_MISSING" = "1" ] && sudo apt-get install -y -qq git >/dev/null 2>&1
        [ "$PY_MISSING" = "1" ] && sudo apt-get install -y -qq python3 python3-pip python3-venv >/dev/null 2>&1
        [ "$PCAP_MISSING" = "1" ] && sudo apt-get install -y -qq libpcap-dev >/dev/null 2>&1
    elif command -v dnf &>/dev/null; then
        [ "$GIT_MISSING" = "1" ] && sudo dnf install -y -q git >/dev/null 2>&1
        [ "$PY_MISSING" = "1" ] && sudo dnf install -y -q python3 python3-pip >/dev/null 2>&1
        [ "$PCAP_MISSING" = "1" ] && sudo dnf install -y -q libpcap-devel >/dev/null 2>&1
    elif command -v pacman &>/dev/null; then
        [ "$GIT_MISSING" = "1" ] && sudo pacman -Sy --noconfirm -q git >/dev/null 2>&1
        [ "$PY_MISSING" = "1" ] && sudo pacman -Sy --noconfirm -q python python-pip >/dev/null 2>&1
        [ "$PCAP_MISSING" = "1" ] && sudo pacman -Sy --noconfirm -q libpcap >/dev/null 2>&1
    else
        echo "  [X] Could not detect package manager to install tools."
        echo "      Please install Git, Python 3, and libpcap manually."
        exit 1
    fi
    echo "        Tools installed successfully."
fi

if [ "$OLLAMA_MISSING" = "1" ]; then
    echo "        Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "  [X] Ollama installation failed."
        echo "      Please install it manually from https://ollama.com"
        exit 1
    fi
    echo "        Ollama installed successfully."
fi

echo ""

# -------------------------------------------
# Llama 3 Setup
# -------------------------------------------
echo "  [3/6] Setting up Llama 3 model..."

# Start Ollama service if not running
if ! pgrep -x "ollama" &>/dev/null; then
    echo "        Starting Ollama service..."
    ollama serve &>/dev/null &
    sleep 3
fi

if ollama list 2>/dev/null | grep -qi "llama3"; then
    echo "        Llama 3 model already installed."
else
    echo "        Pulling Llama 3 model via Ollama (This may take a while)..."
    ollama pull llama3
    if [ $? -ne 0 ]; then
        echo "  [!] Failed to pull Llama 3 model."
        echo "      Make sure Ollama is running and try:  ollama pull llama3"
    else
        echo "        Llama 3 model ready."
    fi
fi

echo "        Initializing Llama 3 model..."
ollama run llama3 "system initialization" > /dev/null 2>&1 || true

echo ""

# -------------------------------------------
# Clone Repository
# -------------------------------------------
echo "  [4/6] Cloning IntelliBlue repository..."
INSTALL_DIR="$HOME/IntelliBlue"
if [ -d "$INSTALL_DIR" ]; then
    echo "        Directory already exists at $INSTALL_DIR"
    echo "        Skipping clone. (Remove directory to re-clone)"
    cd "$INSTALL_DIR"
else
    git clone https://github.com/AbdulrazzakSwai/IntelliBlue.git "$INSTALL_DIR" -q >/dev/null 2>&1
    cd "$INSTALL_DIR"
fi

echo ""

# -------------------------------------------
# Python VENV
# -------------------------------------------
echo "  [5/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv >/dev/null 2>&1
    echo "        Created virtual environment (venv/)."
fi

source venv/bin/activate
echo ""

# -------------------------------------------
# Install Dependencies
# -------------------------------------------
echo "  [6/6] Installing Python dependencies..."
pip install --upgrade pip --quiet >/dev/null 2>&1
pip install -r requirements.txt --quiet >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "  [X] Failed to install Python dependencies."
    exit 1
fi
echo "        Dependencies installed successfully."

echo ""
echo "  ============================================================"
echo "           Installation Complete!"
echo "  ============================================================"
echo ""
echo "  To start IntelliBlue at any time:"
echo ""
echo "      cd $INSTALL_DIR"
echo "      source venv/bin/activate"
echo "      python3 app.py"
echo ""
echo "  The application will be available at http://localhost:5000"
echo "  ============================================================"
echo ""

read -p "Would you like to run IntelliBlue now? (y/n) " response
if [[ "$response" =~ ^[Yy]$ ]]; then
    python3 app.py
fi
