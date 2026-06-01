# Future work (tracked tasks)

Short, actionable briefs for larger features. Each file is one theme; when work
starts, promote the outcome into ADRs, [`docs/design/model-parser.md`](../design/model-parser.md), and the roadmap there.

| Task | Summary |
|------|---------|
| [emit-ini-round-trip](emit-ini-round-trip.md) | `emit ini` and round-trip tests so INI stays a generated view, not a second handwritten source of truth. |
| [emit-cpp-realtime-backend](emit-cpp-realtime-backend.md) | `emit cpp` for the `realtime-cpp` profile with deterministic subset and parity checks. |
| [ir-schema-migrations](ir-schema-migrations.md) | Tooling and docs when `ir_version` bumps (MAJOR): migrations, schema regen, consumer notice. |
| [parameter-set-contract-cli](parameter-set-contract-cli.md) | Standard parameter-set artifact referencing scaffold by `content_hash`; optional CLI helpers. |
| [conformance-fixtures-parity](conformance-fixtures-parity.md) | Shared IR fixtures, expected codegen output, Julia loader parity, trajectory checks later. |
| [ini-dimensions-inference](ini-dimensions-inference.md) | Optional ExprTk INI enhancement: infer `num_states` / `num_inputs` / `num_outputs` from equations. |
| [diff-bump-hardening](diff-bump-hardening.md) | Tighten `diff` / `bump` policy, edge cases, `--strict` / exit codes for CI gates. |

These are **not** a substitute for GitHub issues or ADRs when behaviour is decided.
