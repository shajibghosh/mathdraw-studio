from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
    "src/mathdraw/__init__.py",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
]


def main() -> int:
    missing = [name for name in REQUIRED if not (ROOT / name).exists()]
    if missing:
        print("Missing release files:", *missing, sep="\n- ", file=sys.stderr)
        return 1

    with (ROOT / "pyproject.toml").open("rb") as stream:
        package_version = tomllib.load(stream)["project"]["version"]

    init_text = (ROOT / "src/mathdraw/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, re.MULTILINE)
    if not match:
        print("Could not find __version__ in src/mathdraw/__init__.py", file=sys.stderr)
        return 1
    runtime_version = match.group(1)

    if package_version != runtime_version:
        print(
            f"Version mismatch: pyproject.toml={package_version}, __init__.py={runtime_version}",
            file=sys.stderr,
        )
        return 1

    print(f"Release metadata verified for MathDraw Studio {package_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
