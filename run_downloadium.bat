@echo off
setlocal

REM Run Downloadium (single_file_project) from repo root.
set "REPO_DIR=%~dp0"

set "PY_EXE=%REPO_DIR%.venv\Scripts\python.exe"
if exist "%PY_EXE%" (
  set "PY_CMD=%PY_EXE%"
) else (
  set "PY_CMD=python"
)

"%PY_CMD%" "%REPO_DIR%single_file_project\main.py"

if errorlevel 1 (
  echo.
  echo Falha ao iniciar o Downloadium.
  echo Verifique se as dependencias estao instaladas (ex.: pip install -r single_file_project\requirements.txt)
  pause
)

endlocal
