# Changelog

## v0.2.3 (2026-08-06)

- Add `emit python`: dependency-free `f_<model>(t, state, parameters[, inputs])` in SciPy argument order, plus `outputs_<model>` when the IR has output equations.
- Additive; IR schema and Julia targets unchanged.

## v0.2.2 (2026-06-03)

- Add `emit julia-rhs`: plain in-place `f_<model>!` and optional `outputs_<model>!` with IR declaration-order packing.
- Julia expression rendering shared between the MTK and RHS backends.

## v0.2.1 (2026-06-02)

- Fix the version string in `pyproject.toml` and `__init__.py` to match the tag.

## v0.2.0 (2026-06-02)

- Add `diff` (semantic IR comparison) and `bump` (advisory model SemVer bump), both with `--json`.
- INI frontend honours `SOURCE_DATE_EPOCH` for `provenance.created_at`.
- Document PyPI install via `pipx` or `uv tool`.

## v0.1.0 (2026-06-01)

- First release: canonical IR with JSON Schema and content hash, ExprTk-INI frontend, `emit julia` for ModelingToolkit v11, semantic and profile validation.
- CLI: `parse`, `emit julia`, `validate`, `inspect`, `ast`, `schema`.
- `ModelParserJL` loads IR into an in-memory MTK `System`.
- CI, MkDocs site on GitHub Pages, PyPI publishing via trusted publishing.
