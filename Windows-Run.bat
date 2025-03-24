@echo off
setlocal EnableDelayedExpansion

:: Placeholder for GitHub repository URL
set GITHUB_URL=https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
:: Example: set GITHUB_URL=https://github.com/NephyMephy/NCBA-mp3.git

:: Script name
set SCRIPT_NAME=music_link_downloader.py
:: Directory to clone into
set TARGET_DIR=NCBA_mp3_downloader

echo Checking for Python 3...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python 3 is not installed. Attempting to install with winget...
    winget --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo winget not found. Please install Python 3 manually from https://www.python.org/downloads/
        echo Make sure to add Python to PATH during installation.
        pause
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --scope machine --silent
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Python automatically. Please install manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    :: Refresh PATH for this session
    set "PATH=%PATH%;%ProgramFiles%\Python312\;%ProgramFiles%\Python312\Scripts\"
    python --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Python installation failed or PATH not updated. Please restart the script or install manually.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found !PYTHON_VERSION!

echo Checking for Git...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git is not installed. Attempting to install with winget...
    winget --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo winget not found. Please install Git manually from https://git-scm.com/downloads
        pause
        exit /b 1
    )
    winget install -e --id Git.Git --scope machine --silent
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Git automatically. Please install manually from https://git-scm.com/downloads
        pause
        exit /b 1
    )
    :: Refresh PATH for this session (Git typically installs to Program Files)
    set "PATH=%PATH%;%ProgramFiles%\Git\cmd\"
    git --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Git installation failed or PATH not updated. Please restart the script or install manually.
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('git --version') do set GIT_VERSION=%%i
echo Found !GIT_VERSION!

echo Cloning repository from %GITHUB_URL%...
if exist "%TARGET_DIR%" (
    echo Directory %TARGET_DIR% already exists. Pulling latest changes...
    cd /d "%TARGET_DIR%"
    git pull origin main
) else (
    git clone %GITHUB_URL% "%TARGET_DIR%"
    cd /d "%TARGET_DIR%"
)

echo No additional Python packages needed (using only Python standard library)

echo Running the script...
python "%SCRIPT_NAME%"

echo Done!
pause