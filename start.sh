#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

PYTHON_CMD=""

# Force Python 3.12 specifically
if command -v python3.12 &>/dev/null; then
    echo "Python 3.12 found."
    PYTHON_CMD="python3.12"
else
    echo "Python 3.12 not found. Attempting to install..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            brew install python@3.12
        else
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python@3.12
        fi
        # Set command to the specific Homebrew python3.12 executable if needed
        PYTHON_CMD="python3.12"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -y && sudo apt-get install -y python3.12 python3.12-venv
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3.12
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm python
        else
            echo "Unsupported Linux distro. Please install Python 3.12 manually."; exit 1
        fi
        PYTHON_CMD="python3.12"
    else
        echo "Unsupported OS. Please install Python 3.12 manually."; exit 1
    fi
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS system dependencies via Homebrew..."
    if ! command -v brew &>/dev/null; then
        echo "Homebrew is required. Install it from https://brew.sh"; exit 1
    fi
    # Installed python-tk@3.12 specifically to match Python 3.12
    brew install tesseract python-tk@3.12 libheif
    echo "macOS dependencies installed."
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing Linux system dependencies..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y python3-tk python3-venv tesseract-ocr espeak espeak-ng scrot xclip libxcb-xinerama0 libxcb-cursor0
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter python3-venv tesseract-ocr espeak espeak-ng scrot xclip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk python-tk tesseract espeak scrot xclip
    fi
fi

if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo "Removing broken virtual environment..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

PYTHON_CMD="$VENV_DIR/bin/python"
PIP_CMD="$VENV_DIR/bin/pip"

echo "Installing Python dependencies..."
"$PIP_CMD" install --upgrade pip
"$PIP_CMD" install ultralytics pillow pytesseract pyautogui gtts pyttsx3 playsound3 psutil pi-heif customtkinter

if [[ "$OSTYPE" == "darwin"* ]]; then
    "$PIP_CMD" install "numpy<2" "opencv-python==4.9.0.80"
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "macOS Note: If pyautogui fails, grant Accessibility and Screen Recording"
    echo "permissions to Terminal in System Settings > Privacy & Security."
    echo ""
fi

echo "Launching main.py..."
"$PYTHON_CMD" "$SCRIPT_DIR/main.py"
