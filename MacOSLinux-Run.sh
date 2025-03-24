#!/bin/bash

# Placeholder for GitHub repository URL
GITHUB_URL="https://github.com/NephyMephy/NCBA-mp3.git"

# Script name
SCRIPT_NAME="script.py"
# Directory to clone into
TARGET_DIR="NCBA_mp3_downloader"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check and install Homebrew (macOS)
install_brew() {
    if ! command -v brew &> /dev/null; then
        echo -e "${GREEN}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Homebrew installed successfully${NC}"
            # Add brew to PATH for this session
            eval "$(/opt/homebrew/bin/brew shellenv)" || eval "$(/usr/local/bin/brew shellenv)"
        else
            echo -e "${RED}Failed to install Homebrew. Please install it manually: https://brew.sh${NC}"
            exit 1
        fi
    fi
}

# Function to check and install Python 3
install_python() {
    echo -e "${GREEN}Checking for Python 3...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 not found. Attempting to install...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            install_brew
            brew install python@3.12
        elif command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
        else
            echo -e "${RED}Unsupported OS or package manager. Please install Python 3 manually:${NC}"
            echo "Download from: https://www.python.org/downloads/"
            exit 1
        fi
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}Python 3 installation failed. Please install manually.${NC}"
            exit 1
        fi
    fi
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}Found $PYTHON_VERSION${NC}"
}

# Function to check and install Git
install_git() {
    echo -e "${GREEN}Checking for Git...${NC}"
    if ! command -v git &> /dev/null; then
        echo -e "${RED}Git not found. Attempting to install...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            install_brew
            brew install git
        elif command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y git
        else
            echo -e "${RED}Unsupported OS or package manager. Please install Git manually:${NC}"
            echo "Download from: https://git-scm.com/downloads"
            exit 1
        fi
        if ! command -v git &> /dev/null; then
            echo -e "${RED}Git installation failed. Please install manually.${NC}"
            exit 1
        fi
    fi
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}Found $GIT_VERSION${NC}"
}

# Install prerequisites
install_python
install_git

echo -e "${GREEN}Cloning repository from $GITHUB_URL...${NC}"
if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR already exists. Pulling latest changes..."
    cd "$TARGET_DIR" || exit
    git pull origin main
else
    git clone "$GITHUB_URL" "$TARGET_DIR"
    cd "$TARGET_DIR" || exit
fi

echo -e "${GREEN}No additional Python packages needed (using only Python standard library)${NC}"

echo -e "${GREEN}Running the script...${NC}"
python3 "$SCRIPT_NAME"

echo -e "${GREEN}Done!${NC}"