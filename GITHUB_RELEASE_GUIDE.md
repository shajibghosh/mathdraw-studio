# Immediate GitHub Release Guide

This guide assumes the repository name `mathdraw-studio` and release tag `v0.2.1`. Replace `YOUR_GITHUB_USERNAME` with the account or organization that will own the repository.

## Prerequisites

Install Git and GitHub CLI, then authenticate:

```bat
git --version
gh --version
gh auth login
```

## Create a new public repository and publish the source

Open Anaconda Prompt or PowerShell in the extracted repository directory:

```bat
git init
git branch -M main
git add .
git commit -m "Release MathDraw Studio 0.2.1"

gh repo create YOUR_GITHUB_USERNAME/mathdraw-studio --public --source=. --remote=origin --push --description "Convert images into geometric, Bezier, Fourier, and 2D DCT mathematical equations."
```

## Create the release tag

```bat
git tag -a v0.2.1 -m "MathDraw Studio 0.2.1"
git push origin v0.2.1
```

Pushing the tag starts `.github/workflows/release.yml`. The workflow runs linting and tests, builds the wheel and source distribution, generates SHA-256 checksums, and creates the GitHub release.

## Manual release alternative

Build and verify locally:

```bat
conda activate mathdraw-studio
python -m pip install --upgrade build twine
python -m pip install -e ".[dev]"
python -m compileall -q src tests scripts
pytest -q
python -m build
python -m twine check dist\*
```

Create the release from local assets:

```bat
gh release create v0.2.1 ^
  dist\mathdraw_studio-0.2.1-py3-none-any.whl ^
  dist\mathdraw_studio-0.2.1.tar.gz ^
  RELEASE_NOTES_v0.2.1.md ^
  --title "MathDraw Studio 0.2.1" ^
  --notes-file RELEASE_NOTES_v0.2.1.md ^
  --verify-tag
```

## Existing empty GitHub repository

When the repository already exists:

```bat
git init
git branch -M main
git add .
git commit -m "Release MathDraw Studio 0.2.1"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/mathdraw-studio.git
git push -u origin main
git tag -a v0.2.1 -m "MathDraw Studio 0.2.1"
git push origin v0.2.1
```

## Recommended repository settings

- Description: `Convert images into geometric, Bezier, Fourier, and 2D DCT mathematical equations.`
- Topics: `computer-vision`, `image-processing`, `mathematics`, `fourier-descriptors`, `dct`, `bezier-curves`, `python`, `tkinter`
- Enable Issues and Discussions.
- Enable private vulnerability reporting.
- Protect `main` after the first release by requiring the CI workflow.
