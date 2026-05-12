@echo off

:: check if C++ redist is installed
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Visual C++" | findstr "Redistributable" >nul
if %errorlevel% equ 0 (
    echo Visual C++ Redistributable is installed.
) else (
    echo Visual C++ Redistributable NOT found.
)
pause

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python found.
    goto install_deps
)

:: Also try py launcher
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python found via py launcher.
    goto install_deps_py
)


:: Python not found — download and run installer
echo Python not found. Downloading installer...
curl -o "%TEMP%\python_installer.exe" https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe

if not exist "%TEMP%\python_installer.exe" (
    echo Failed to download Python installer. Please check your internet connection.
    pause
    goto end
)

echo Running Python installer...
"%TEMP%\python_installer.exe" /passive InstallAllUsers=1 PrependPath=1 Include_pip=1

:: Refresh environment so python is now on PATH
call refreshenv >nul 2>&1

:: Verify install succeeded
python --version >nul 2>&1
if not %errorlevel% == 0 (
    echo Python was installed but may require a restart to be available on PATH.
    echo Please restart your computer and run this file again.
    pause
    goto end
)

:install_deps
python -m pip install --upgrade pip
python -m pip install ultralytics
python -m pip install pillow
python -m pip install pytesseract
python -m pip install pyautogui
python -m pip install gtts
python -m pip install pyttsx3
python -m pip install playsound3
python -m pip install psutil
start "" pythonw "%~dp0main.py"
goto end

:install_deps_py
python -m pip install --upgrade pip
python -m pip install ultralytics
python -m pip install pillow
python -m pip install pytesseract
python -m pip install pyautogui
python -m pip install gtts
python -m pip install pyttsx3
python -m pip install playsound3
python -m pip install psutil
start "" pythonw "%~dp0main.py"
goto end

:end