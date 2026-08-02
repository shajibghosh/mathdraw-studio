# Release Checklist

## Source verification

- [ ] `pyproject.toml` and `src/mathdraw/__init__.py` contain the same version.
- [ ] `CHANGELOG.md` and release notes describe the release.
- [ ] Copyright and citation metadata are correct.
- [ ] No local paths, private data, credentials, or proprietary images are committed.

## Quality gates

```bash
python -m pip install -e ".[dev]"
python -m compileall -q src tests scripts
pytest -q
python -m build
python -m twine check dist/*
```

## Repository publication

- [ ] Default branch is `main`.
- [ ] GitHub Actions has read/write workflow permissions for releases when required.
- [ ] Private vulnerability reporting is enabled when available.
- [ ] Topics and repository description are configured.

## Release publication

- [ ] Create and push an annotated tag matching the package version.
- [ ] Confirm CI succeeds.
- [ ] Confirm the GitHub release contains the wheel, source distribution, release notes, and checksums.
- [ ] Test installation of the wheel in a clean environment.
