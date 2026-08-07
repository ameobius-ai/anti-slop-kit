@echo off
REM anti-slop-kit plugin installer for Windows
REM Requires Python 3.8+ and Git

echo Installing anti-slop-kit plugin for Windows...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\anti-slop-kit
echo Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy plugin files
echo Copying plugin files...
xcopy /E /I /Y "plugin" "%INSTALL_DIR%\plugin" >nul
xcopy /E /I /Y "tools" "%INSTALL_DIR%\tools" >nul
xcopy /E /I /Y "hooks" "%INSTALL_DIR%\hooks" >nul
xcopy /E /I /Y "evals" "%INSTALL_DIR%\evals" >nul
xcopy /E /I /Y "docs" "%INSTALL_DIR%\docs" >nul
xcopy /Y "SKILL.md" "%INSTALL_DIR%\" >nul
xcopy /Y "RESULTS.md" "%INSTALL_DIR%\" >nul
xcopy /Y "README.md" "%INSTALL_DIR%\" >nul

REM Create bin directory
set BIN_DIR=%LOCALAPPDATA%\anti-slop-kit\bin
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

REM Create anti-slop.bat wrapper
echo Creating anti-slop command wrapper...
(
echo @echo off
echo python "%INSTALL_DIR%\tools\aslint\lint_tool.py" %%*
) > "%BIN_DIR%\anti-slop.bat"

REM Add to PATH for current user
echo Adding %BIN_DIR% to PATH...
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set CURRENT_PATH=%%B

if "%CURRENT_PATH%"=="" (
    setx PATH "%BIN_DIR%"
) else (
    echo %CURRENT_PATH% | findstr /I /C:"%BIN_DIR%" >nul
    if errorlevel 1 (
        setx PATH "%CURRENT_PATH%;%BIN_DIR%"
    )
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo anti-slop-kit has been installed to:
echo   %INSTALL_DIR%
echo.
echo The 'anti-slop' command has been added to your PATH.
echo.
echo IMPORTANT: You need to restart your command prompt or
echo open a new one for the PATH changes to take effect.
echo.
echo After restarting, you can use:
echo   anti-slop lint README.md
echo   anti-slop rewrite original.md rewrite.md
echo   anti-slop eval
echo.
echo To uninstall, run: plugin\uninstall.bat
echo.
pause