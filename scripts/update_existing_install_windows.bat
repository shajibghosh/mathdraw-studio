@echo off
setlocal
call conda activate mathdraw-studio
if errorlevel 1 (
  echo Could not activate the mathdraw-studio environment.
  exit /b 1
)
python -m pip install -e .
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 exit /b 1
echo.
echo MathDraw Studio 0.2.1 is installed and the regression tests passed.
