# model-parser — product specification

> Authoritative specification for what this repository does. CLI semantics, the
> IR shape, and scope are defined here; code and ADRs must stay aligned with it.

## 1. Purpose

`model-parser` converts process-model definitions **to and from a canonical
intermediate representation (IR)**. It is the hub-and-spoke transformation tool
for the model *scaffold*: it parses an authoring format into a normalized,
backend-independent IR, and lowers that IR into target views.

```text
authoring (ExprTk INI)  --parse-->  AST  --normalize-->  canonical IR (JSON)
                                                          |
                                          emit julia      --> ModelingToolkit .jl
                                          emit julia-rhs  --> numerical f!/outputs! .jl
                                          emit cpp        --> (planned) realtime C++
                                          emit ini        --> (planned) round-trip
```

The IR is the **single semantic contract**. Adding a backend is one `lower` +
one `export`, not an N×N mesh of view-to-view translators (org
[ADR 0006](https://github.com/Advanced-Process-Control/.github)).

This tool is the concrete, near-term realization of the `apc-model-ir` +
`apc-tooling` roles sketched in the org repository map, scoped down to the
parser/IR/codegen responsibility and kept usable standalone.

## 2. Responsibilities

In scope:

- **Frontends** — parse an authoring format into the IR (`parse` + `normalize`).
  The first frontend is the ExprTk-style INI used by the MPC toolchain.
- **Canonical IR** — the data model, JSON serialization, content hashing, and a
  versioned JSON Schema.
- **Validation** — semantic checks (undeclared symbols, duplicate names,
  missing equations, local ordering) and backend-profile checks.
- **Backends** — lower the IR into a target view. Backends today: a
  ModelingToolkit (Julia) model script (`emit julia`) and a plain numerical
  ODE RHS plus optional output map (`emit julia-rhs`). A Julia companion package
  (`ModelParserJL`) loads the IR in memory.

Out of scope (sibling tools that *consume* the IR):

- parameter identification and fitted parameter sets;
- scenario definition and simulation execution;
- result/artifact storage, linearization, MPC synthesis;
- deployment, packaging, and any UI.

Keeping these out is deliberate: the parser stays small and the IR stays a
scaffold contract, not an everything-bucket (see the org risk note on
"scope creep into the parser").

## 3. The representation layers

| Layer | Role | On disk? |
|---|---|---|
| **Authoring** | What the engineer writes (ExprTk INI today). | yes (`.ini`) |
| **AST** | Syntax-oriented tree from the parser. Internal. | debug only |
| **Canonical IR** | Normalized, backend-independent scaffold semantics. | yes (`.ir.json`) |
| **Backend view** | A lowered target (MTK `.jl`, numerical RHS `.jl`, future C++). | yes (generated) |

The AST is in-memory; the IR is the durable interchange contract. The full IR
shape and the expression sub-language are specified in
[`ir-specification.md`](ir-specification.md).

## 4. Scaffold vs parameter set vs scenario

The IR describes the **scaffold** only: variables, roles, equations, units, and
parameter *declarations* (with optional default values for bootstrap
convenience). It deliberately does **not** carry:

- fitted parameter values → a **parameter set** (sibling JSON contract);
- initial values / input trajectories / horizons → a **scenario** (sibling JSON
  contract).

Consequently the INI frontend **drops** `[x0]` / `[u0]` sections with a `WARN`:
initial values are scenario data, not scaffold semantics. This matches the org
contracts ("initial values live in the scenario, not the scaffold").

## 5. CLI

```text
model-parser parse   <authoring-file> [--from exprtk-ini] [-o out.ir.json]
model-parser emit julia      <model.ir.json>             [-o out.jl]
model-parser emit julia-rhs  <model.ir.json>             [-o out.jl]
model-parser validate <model.ir.json | authoring-file> [--profile <name>]
model-parser inspect  <model.ir.json | authoring-file>
model-parser diff     <old.ir.json> <new.ir.json>         [--json]
model-parser bump     <old.ir.json> <new.ir.json>         [--json]
model-parser ast      <authoring-file>                      [-o out.json]
model-parser schema                                         [-o schema.json]
```

- `parse` is the **authoring → IR** transformation. Default and only frontend
  today is `exprtk-ini`.
- `emit <target>` is the **IR → view** transformation. Julia targets: `julia`
  (ModelingToolkit v11 scaffold) and `julia-rhs` (plain `f!` / optional
  `outputs!`). Designed to grow (`emit cpp`, `emit ini`) without touching
  existing targets.
- `validate` accepts either an IR `.json` or an authoring file (parsed on the
  fly), and an optional `--profile`.
- `inspect` prints a human summary; `ast` exports a debug tree; `schema` exports
  the JSON Schema.
- `diff` compares two canonical IR files and lists semantic changes; `bump`
  suggests a **SemVer bump** (`none` / `patch` / `minor` / `major`) for the model
  using a conservative policy (see
  [`model-library-and-versioning.md`](model-library-and-versioning.md)).

Exit codes: `0` success · `1` validation errors · `2` usage/load failure.
Diagnostics use the `OK` / `WARN` / `ERROR` vocabulary.

### Typical session

```bash
uv run model-parser parse  examples/models/model_monod_simple.ini -o monod.ir.json
uv run model-parser validate monod.ir.json --profile julia-analysis
uv run model-parser emit julia monod.ir.json -o monod.jl
uv run model-parser emit julia-rhs monod.ir.json -o monod_rhs.jl
```

## 6. Language split

Python owns the CLI, AST, IR, schema, validation, and codegen; Julia owns the
in-memory IR→`System` build and serves as the conformance reference. Rationale
and trade-offs: [`language-strategy.md`](language-strategy.md) and
[ADR 0001](../decisions/0001-python-cli-with-julia-backend.md).

## 7. Profiles

A **profile** declares which subset of the IR a backend accepts. Validation can
be run against a profile:

- `julia-analysis` — permissive; the full IR is allowed.
- `realtime-cpp` — restricted deterministic subset for PLC targets (first cut:
  a constrained operator/function set). Targeted, not yet code-generating.

Adding a profile is an ADR. Profiles are checked against the *same* IR, so one
model can be valid for Julia analysis while being rejected for a PLC target.

## 8. Roadmap

1. **Now (MVP):** ExprTk-INI frontend, canonical IR + schema, core validators,
   Julia codegen backend, Julia in-memory loader, example pipeline; semantic
   `diff` / `bump` for library workflows.
2. **Conformance:** shared IR fixtures with expected Julia output and (later)
   expected trajectories, run by both the Python codegen and `ModelParserJL`.
3. **Round-trip:** `emit ini` and `export` from a Julia/MTK view back to IR,
   with round-trip tests.
4. **Real-time C++ backend:** `emit cpp` for the `realtime-cpp` profile, with
   trajectory parity against the Julia path.
5. **Schema hardening:** richer units/bounds, role taxonomy, SemVer migrations.

## 9. Non-goals restated

`model-parser` is not a simulator, not an identification tool, not a deployment
pipeline, and not a UI. It is the parser/IR/codegen hub. Everything else
consumes its output.
