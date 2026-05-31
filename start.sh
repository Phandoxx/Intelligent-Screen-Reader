#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Note: Visual C++ Redistributable check is Windows-only and has been skipped."

# ─────────────────────────────────────────────
# Check if Python is installed
# ─────────────────────────────────────────────
PYTHON_CMD=""

if command -v python3 &>/dev/null; then
    echo "Python found (python3)."
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    echo "Python found (python)."
    PYTHON_CMD="python"
else
    echo "Python not found. Attempting to install..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -y
            sudo apt-get install -y python3 python3-venv
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm python
        else
            echo "Unsupported Linux distro. Please install Python 3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            brew install python
        else
            echo "Homebrew not found. Please install Python 3 from https://www.python.org/downloads/"
            exit 1
        fi
    else
        echo "Unsupported OS: $OSTYPE. Please install Python 3 manually."
        exit 1
    fi
    PYTHON_CMD="python3"
    if ! command -v "$PYTHON_CMD" &>/dev/null; then
        echo "Python installation failed. Please restart your shell and try again."
        exit 1
    fi
fi

#!/bin/bash
# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Note: Visual C++ Redistributable check is Windows-only and has been skipped."

# ─────────────────────────────────────────────
# Check if Python is installed
# ─────────────────────────────────────────────
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    echo "Python found (python3)."
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    echo "Python found (python)."
    PYTHON_CMD="python"
else
    echo "Python not found. Attempting to install..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -y
            sudo apt-get install -y python3 python3-venv
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm python
        else
            echo "Unsupported Linux distro. Please install Python 3 manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            brew install python
        else
            echo "Homebrew not found. Please install Python 3 from https://www.python.org/downloads/"
            exit 1
        fi
    else
        echo "Unsupported OS: $OSTYPE. Please install Python 3 manually."
        exit 1
    fi
    PYTHON_CMD="python3"
fi

# ─────────────────────────────────────────────
# Install system dependencies
# ─────────────────────────────────────────────
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing system dependencies..."
    
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y \
            python3-tk \
            python3-venv \
            tesseract-ocr \
            espeak espeak-ng \
            scrot \
            xclip \
            libxcb-xinerama0 \
            libxcb-cursor0
        echo "System dependencies installed successfully."
        
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter python3-venv tesseract-ocr espeak espeak-ng scrot xclip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk python-tk tesseract espeak scrot xclip
    else
        echo "Unsupported Linux distro. Please install required packages manually."
    fi
fi

# ─────────────────────────────────────────────
# Remove broken venv if it exists and recreate
# ─────────────────────────────────────────────
if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo "Removing broken virtual environment..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
        echo "venv creation failed. Trying to fix..."
        PY_VERSION=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        sudo apt-get install -y "python${PY_VERSION}-venv" 2>/dev/null || true
        rm -rf "$VENV_DIR"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi
fi

# Use the venv's Python and pip
PYTHON_CMD="$VENV_DIR/bin/python"
PIP_CMD="$VENV_DIR/bin/pip"

# ─────────────────────────────────────────────
# Install Python dependencies
# ─────────────────────────────────────────────
echo "Installing Python dependencies..."
"$PIP_CMD" install --upgrade pip
"$PIP_CMD" install ultralytics pillow pytesseract pyautogui gtts pyttsx3 playsound3 psutil pi-heif customtkinter

# ─────────────────────────────────────────────
# Launch main.py
# ─────────────────────────────────────────────
echo "Launching main.py..."
"$PYTHON_CMD" "$SCRIPT_DIR/main.py"
