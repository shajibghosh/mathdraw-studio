#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade build twine
python -m pip install -e ".[dev]"
python scripts/verify_release.py
python -m compileall -q src tests scripts
pytest -q
rm -rf build dist *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*
(
  cd dist
  sha256sum * > SHA256SUMS.txt
)
echo "Release files are in dist/."
