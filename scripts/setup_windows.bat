@echo off
setlocal
where conda >nul 2>nul
if errorlevel 1 (
  echo Conda was not found. Open Anaconda Prompt and run this script again.
  exit /b 1
)
call conda env create -f environment.yml
if errorlevel 1 exit /b 1
call conda activate mathdraw-studio
python -m pip install -e .
echo.
echo Installation complete. Run scripts\run_windows.bat
