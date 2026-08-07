@echo off
REM anti-slop-kit plugin uninstaller for Windows

echo Uninstalling anti-slop-kit plugin...
echo.

REM Set directories
set INSTALL_DIR=%LOCALAPPDATA%\anti-slop-kit
set BIN_DIR=%LOCALAPPDATA%\anti-slop-kit\bin

REM Remove installation directory
if exist "%INSTALL_DIR%" (
    echo Removing installation directory...
    rmdir /S /Q "%INSTALL_DIR%"
    echo   ✓ Removed %INSTALL_DIR%
)

REM Remove from PATH
echo Removing from PATH...
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set CURRENT_PATH=%%B

if not "%CURRENT_PATH%"=="" (
    set NEW_PATH=%CURRENT_PATH%;%BIN_DIR%;=%BIN_DIR%;=
    set NEW_PATH=!NEW_PATH:;;=;!;
    setx PATH "!NEW_PATH!"
    echo   ✓ Removed from PATH
)

REM Remove git hooks if they were installed
if exist ".git\hooks" (
    echo Removing git hooks...
    if exist ".git\hooks\pre-commit" (
        findstr /C:"anti-slop" ".git\hooks\pre-commit" >nul
        if not errorlevel 1 (
            del ".git\hooks\pre-commit"
            echo   ✓ Removed pre-commit hook
        )
    )
    if exist ".git\hooks\pre-push" (
        findstr /C:"anti-slop" ".git\hooks\pre-push" >nul
        if not errorlevel 1 (
            del ".git\hooks\pre-push"
            echo   ✓ Removed pre-push hook
        )
    )
)

echo.
echo ========================================
echo   Uninstallation Complete!
echo ========================================
echo.
echo anti-slop-kit has been completely removed.
echo.
echo IMPORTANT: Restart your command prompt for PATH
echo changes to take effect.
echo.
pause