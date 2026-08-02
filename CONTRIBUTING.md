# Contributing to MathDraw Studio

Contributions that improve mathematical correctness, image fidelity, portability, documentation, testing, or accessibility are welcome.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,documents]"
pytest -q
python -m compileall -q src tests scripts
```

The optional image-format dependencies can be installed with:

```bash
python -m pip install -e ".[formats]"
```

## Contribution procedure

1. Create an issue for a substantial change so that its mathematical and software scope can be discussed.
2. Create a focused branch from `main`.
3. Add or update tests for every behavior change and defect correction.
4. Preserve numerical reproducibility and document any intentional approximation.
5. Run the complete test suite and linter before opening a pull request.
6. Explain the mathematical representation, parameter-domain assumptions, and accuracy implications in the pull request.

## Mathematical requirements

A new representation or detector should state:

- the coordinate convention;
- the basis functions or geometric primitives;
- parameter domains and normalization;
- approximation or exactness conditions;
- computational complexity;
- numerical stability considerations;
- reconstruction and evaluation procedures.

Do not describe a finite approximation as an exact representation unless the conditions for exactness are explicitly satisfied.

## Code style

- Python 3.10 or newer.
- Type annotations for public functions and nontrivial data structures.
- Lines limited to 120 characters unless mathematical readability requires otherwise.
- No silent exception suppression in processing or export paths.
- User-facing failures must report the failed stage and the underlying exception.

## Pull-request checklist

- [ ] Tests pass locally.
- [ ] Ruff reports no errors.
- [ ] Public behavior is documented.
- [ ] Equation output remains syntactically valid.
- [ ] Large-output behavior has been considered.
- [ ] No generated user data or local paths are committed.
