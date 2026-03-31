@echo off
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH="
for /r "%SCRIPT_DIR%" %%f in (ipf.exe) do (
    set "EXE_PATH=%%~dpf"
    goto :f
)
goto :e
:f
set "EXE_PATH=%EXE_PATH:~0,-1%"
setx PATH "%PATH%;%EXE_PATH%" >nul
:e
exit