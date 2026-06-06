#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

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
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            brew install python
        else
            echo "Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -y && sudo apt-get install -y python3 python3-venv
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3
        elif command -v pacman &>/dev/null; then
            sudo pacman -Sy --noconfirm python
        else
            echo "Unsupported Linux distro. Please install Python 3 manually."; exit 1
        fi
    else
        echo "Unsupported OS. Please install Python 3 manually."; exit 1
    fi
    PYTHON_CMD="python3"
fi

# ─────────────────────────────────────────────
# Install system dependencies
# ─────────────────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing macOS system dependencies via Homebrew..."
    if ! command -v brew &>/dev/null; then
        echo "Homebrew is required. Install it from https://brew.sh"; exit 1
    fi
        brew install tesseract python-tk libheif
    # Note: macOS has built-in TTS (say) and screencapture — no espeak/scrot needed
    echo "macOS dependencies installed."

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Installing Linux system dependencies..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y \
            python3-tk python3-venv \
            tesseract-ocr \
            espeak espeak-ng \
            scrot xclip \
            libxcb-xinerama0 libxcb-cursor0
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-tkinter python3-venv tesseract-ocr espeak espeak-ng scrot xclip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tk python-tk tesseract espeak scrot xclip
    fi
fi

# ─────────────────────────────────────────────
# Create virtual environment
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Install Python dependencies
# ─────────────────────────────────────────────
echo "Installing Python dependencies..."
"$PIP_CMD" install --upgrade pip

echo "Installing Python dependencies..."
"$PIP_CMD" install --upgrade pip
"$PIP_CMD" install ultralytics pillow pytesseract pyautogui gtts pyttsx3 playsound3 psutil pi-heif customtkinter

#for macOS: pin numpy and opencv for compatibility (idk why it breaks on latest versions its stupid)
if [[ "$OSTYPE" == "darwin"* ]]; then
    "$PIP_CMD" install "numpy<2" "opencv-python==4.9.0.80"
fi

# ─────────────────────────────────────────────
# macOS: Remind user about permissions
# ─────────────────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "⚠️  macOS Note: If pyautogui fails, grant Accessibility & Screen Recording"
    echo "   permissions to Terminal in System Settings > Privacy & Security."
    echo ""
fi

# ─────────────────────────────────────────────
# Launch main.py
# ─────────────────────────────────────────────
echo "Launching main.py..."
"$PYTHON_CMD" "$SCRIPT_DIR/main.py"
