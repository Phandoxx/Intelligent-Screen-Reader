@echo off

:: Check if C++ redist is installed (check both 64-bit and 32-bit registry locations)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Visual C++" | findstr "Redistributable" >nul 2>&1
if %errorlevel% equ 0 goto redist_found

reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Visual C++" | findstr "Redistributable" >nul 2>&1
if %errorlevel% equ 0 goto redist_found

:: Not found — download and install
echo Visual C++ Redistributable NOT found. Downloading...
curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"

if not exist "%TEMP%\vc_redist.x64.exe" (
    echo Download failed - file not found. Check your internet connection.
    pause
    exit /b 1
)

for %%A in ("%TEMP%\vc_redist.x64.exe") do if %%~zA lss 1000000 (
    echo Download failed - file too small, may be corrupt.
    pause
    exit /b 1
)

echo Installing...
"%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
set INST_ERR=%errorlevel%

if "%INST_ERR%"=="0" echo Installation complete.
if "%INST_ERR%"=="1638" echo Already installed - newer version exists, skipping.
if "%INST_ERR%"=="3010" echo Installed - reboot required to complete.
if not "%INST_ERR%"=="0" if not "%INST_ERR%"=="1638" if not "%INST_ERR%"=="3010" (
    echo Installation failed with error code %INST_ERR%.
    pause
    exit /b 1
)
goto redist_done

:redist_found
echo Visual C++ Redistributable is already installed.

:redist_done

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
python -m pip install customtkinter
::start "" pythonw "%~dp0main.py" ::no console
start "" python "%~dp0main.py" :: console on
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
::start "" pythonw "%~dp0main.py" ::no console
start "" python "%~dp0main.py" :: console on
goto end

:end
