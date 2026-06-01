# TODO: `emit cpp` (real-time C++ backend)

## Goal

Implement **`model-parser emit cpp`** that lowers IR into a **deterministic,
real-time-safe** C++ representation for PLC / embedded targets, aligned with the
existing **`realtime-cpp`** validation profile.

## Why

- Second major consumer of the same IR after Julia, proving the hub-and-spoke
  design (one expression tree, many renderers).
- Org roadmap: trajectory or numerical parity checks against the Julia path
  where feasible.

## Scope hints

- Constrain to profile-checked operators/functions only; reject or warn clearly.
- Pure codegen in Python; no new runtime dependency for users who only need IR
  or Julia.

## References

- [`docs/design/model-parser.md`](../design/model-parser.md) roadmap §4.
- `src/model_parser/validation/validators.py` (profile behaviour).

## Acceptance sketch

- CLI: `emit cpp` with `-o` path.
- Tests: small IR fixture and expected `.cpp` (or fragment) under `tests/` or
  `examples/`.
