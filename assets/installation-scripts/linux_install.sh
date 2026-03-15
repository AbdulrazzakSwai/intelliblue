#!/usr/bin/env bash

set -e

# Define colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ============================================================"
echo "       IntelliBlue - Automated Installer for Linux"
echo "  ============================================================"
echo -e "${NC}"

# -------------------------------------------
# Pre-requisite Checks
# -------------------------------------------
echo -e "${YELLOW}  [*] [1/6] Checking for required tools...${NC}"

# Check Git
if command -v git &>/dev/null; then
    GITVER=$(git --version | awk '{print $3}')
    echo -e "${GREEN}      [+] Found Git: $GITVER${NC}"
else
    echo -e "${RED}      [-] Git is NOT installed.${NC}"
    GIT_MISSING=1
fi

# Check Python 3
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}      [+] Found Python 3: $PYVER${NC}"
else
    echo -e "${RED}      [-] Python 3 is NOT installed.${NC}"
    PY_MISSING=1
fi

# Check Ollama
if command -v ollama &>/dev/null; then
    OLLAMAVER=$(ollama --version)
    echo -e "${GREEN}      [+] Found Ollama: $OLLAMAVER${NC}"
else
    echo -e "${RED}      [-] Ollama is NOT installed.${NC}"
    OLLAMA_MISSING=1
fi

# Check libpcap
if dpkg -s libpcap-dev &>/dev/null 2>&1 || rpm -q libpcap-devel &>/dev/null 2>&1 || pacman -Qs libpcap &>/dev/null 2>&1; then
    echo -e "${GREEN}      [+] Found libpcap.${NC}"
else
    echo -e "${RED}      [-] libpcap is NOT installed.${NC}"
    PCAP_MISSING=1
fi

echo ""

# -------------------------------------------
# Install Missing Tools
# -------------------------------------------
echo -e "${YELLOW}  [*] [2/6] Installing missing tools (This may take a while)...${NC}"

if [ -z "$GIT_MISSING" ] && [ -z "$PY_MISSING" ] && [ -z "$OLLAMA_MISSING" ] && [ -z "$PCAP_MISSING" ]; then
    echo -e "${GREEN}      [+] All tools are installed, no need to install anything.${NC}"
fi

if [ "$GIT_MISSING" = "1" ] || [ "$PY_MISSING" = "1" ] || [ "$PCAP_MISSING" = "1" ]; then
    echo -e "${CYAN}      [*] Updating package manager and installing missing tools...${NC}"
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
        echo -e "${RED}  [-] Could not detect package manager to install tools.${NC}"
        echo -e "${RED}      Please install Git, Python 3, and libpcap manually.${NC}"
        exit 1
    fi
    echo -e "${GREEN}      [+] Tools installed successfully.${NC}"
fi

if [ "$OLLAMA_MISSING" = "1" ]; then
    echo -e "${CYAN}      [*] Installing Ollama...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}  [-] Ollama installation failed.${NC}"
        echo -e "${RED}      Please install it manually from https://ollama.com${NC}"
        exit 1
    fi
    echo -e "${GREEN}      [+] Ollama installed successfully.${NC}"
fi

echo ""

# -------------------------------------------
# Llama Models Setup
# -------------------------------------------
echo -e "${YELLOW}  [*] [3/6] Setting up Llama models (This may take a while)...${NC}"

# Start Ollama service if not running
if ! pgrep -x "ollama" &>/dev/null; then
    echo -e "${CYAN}      [*] Starting Ollama service...${NC}"
    ollama serve &>/dev/null &
    sleep 3
fi

for model in "llama3" "llama3.2"; do
    if ollama list 2>/dev/null | grep -qi "^${model}:"; then
        echo -e "${GREEN}      [+] ${model} model already installed.${NC}"
    else
        echo -e "${CYAN}      [*] Pulling ${model} model via Ollama (This may take a while)...${NC}"
        ollama pull ${model}
        if [ $? -ne 0 ]; then
            echo -e "${RED}  [-] Failed to pull ${model} model.${NC}"
            echo -e "${RED}      Make sure Ollama is running and try:  ollama pull ${model}${NC}"
        else
            echo -e "${GREEN}      [+] ${model} model ready.${NC}"
        fi
    fi
done

echo ""

# -------------------------------------------
# Clone Repository
# -------------------------------------------
echo -e "${YELLOW}  [*] [4/6] Cloning IntelliBlue repository...${NC}"
INSTALL_DIR="$HOME/Desktop/IntelliBlue"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}      [*] Directory already exists at $INSTALL_DIR${NC}"
    echo -e "${CYAN}      [*] Skipping clone. (Remove directory to re-clone)${NC}"
    cd "$INSTALL_DIR"
else
    git clone https://github.com/AbdulrazzakSwai/IntelliBlue.git "$INSTALL_DIR" -q >/dev/null 2>&1
    cd "$INSTALL_DIR"
fi

echo ""

# -------------------------------------------
# Python VENV
# -------------------------------------------
echo -e "${YELLOW}  [*] [5/6] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv >/dev/null 2>&1
    echo -e "${GREEN}      [+] Created virtual environment (venv/).${NC}"
fi

source venv/bin/activate
echo ""

# -------------------------------------------
# Install Dependencies
# -------------------------------------------
echo -e "${YELLOW}  [*] [6/6] Installing Python dependencies (This may take a while)...${NC}"
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}  [-] Failed to install Python dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}      [+] Dependencies installed successfully.${NC}"

echo ""
echo -e "${CYAN}"
echo "  ============================================================"
echo "           Installation Complete!"
echo "  ============================================================"
echo -e "${NC}"
echo "  To start IntelliBlue at any time:"
echo ""
echo "      cd $INSTALL_DIR"
echo "      source venv/bin/activate"
echo "      python3 app.py"
echo ""
echo "  The application will be available at http://localhost:5000"
echo -e "${CYAN}"
echo "  ============================================================"
echo -e "${NC}"
echo ""

read -p "[?] Would you like to run IntelliBlue now? (y/n) " response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}[*] Starting IntelliBlue...${NC}"
    python3 app.py
fi
