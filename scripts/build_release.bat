@echo off
setlocal
python -m pip install --upgrade build twine
if errorlevel 1 exit /b 1
python -m pip install -e ".[dev]"
if errorlevel 1 exit /b 1
python scripts\verify_release.py
if errorlevel 1 exit /b 1
python -m compileall -q src tests scripts
if errorlevel 1 exit /b 1
pytest -q
if errorlevel 1 exit /b 1
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m build
if errorlevel 1 exit /b 1
python -m twine check dist\*
if errorlevel 1 exit /b 1
powershell -NoProfile -Command "Get-ChildItem dist -File | Where-Object {$_.Name -ne 'SHA256SUMS.txt'} | ForEach-Object { '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name } | Set-Content dist\SHA256SUMS.txt"
if errorlevel 1 exit /b 1
echo Release files are in dist\.
endlocal
