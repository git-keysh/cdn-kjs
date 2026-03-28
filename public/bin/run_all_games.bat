@echo off
echo ========================================
echo    PC GAMES COLLECTION
echo ========================================
echo.
echo Available games:
echo.
setlocal enabledelayedexpansion
set count=0
set game1=dart.exe
echo 1. dart.exe
set /a count=1
set game2=puzzle.exe
echo 2. puzzle.exe
set /a count=2

echo.
set /p choice="Enter game number (1-%count%) or 'q' to quit: "

if "%choice%"=="q" goto end
if "%choice%"=="" goto end

REM Check if choice is a number
echo %choice%|findstr /r "^[0-9]*$">nul
if errorlevel 1 (
    echo Invalid selection!
    pause
    goto end
)

REM Execute the selected game
if %choice% EQU 1 start "" "%game1%"
if %choice% EQU 2 start "" "%game2%"
if %choice% EQU 3 start "" "%game3%"
if %choice% EQU 4 start "" "%game4%"
if %choice% EQU 5 start "" "%game5%"
if %choice% EQU 6 start "" "%game6%"
if %choice% EQU 7 start "" "%game7%"
if %choice% EQU 8 start "" "%game8%"
if %choice% EQU 9 start "" "%game9%"

echo.
echo Launching game...
timeout /t 2 /nobreak >nul

:end
echo.
echo Thank you for playing!
pause
