# Canonical IR specification

> The IR shape is defined in code (`src/model_parser/ir/`) and exported as JSON
> Schema (`schemas/canonical-ir.schema.json`). This document explains the shape
> and the expression sub-language; the schema is the machine-checkable source of
> truth.

## 1. Scope

The IR describes a model **scaffold**: structure, declarations, and equations.
It is backend-independent and carries no execution context. Parameter sets and
scenarios are *sibling* contracts, not part of the IR.

## 2. Top-level shape

```jsonc
{
  "ir_version": "0.1.0",          // SemVer of the IR schema
  "model": {
    "name": "monod_simple",
    "description": "…",
    "source_version": "1.0",      // version from the authoring file
    "metadata": {}
  },
  "independent_variable": "t",
  "parameters": [ { "name": "mu_max", "default": 0.4, "unit": null, "description": null } ],
  "states":     [ { "name": "x0", "unit": null, "description": null, "roles": [] } ],
  "inputs":     [ /* Variable */ ],
  "outputs":    [ /* Variable */ ],
  "locals":     [ { "name": "mu", "expr": <Expr>, "unit": null, "description": null } ],
  "equations": {
    "differential": [ { "state": "x0", "rhs": <Expr> } ],
    "outputs":      [ { "output": "y0", "rhs": <Expr> } ]
  },
  "profiles": ["julia-analysis"],
  "provenance": {
    "tool": "model-parser@0.1.0",
    "created_at": "<ISO 8601>",
    "source_format": "exprtk-ini",
    "source_file": "model_monod_simple.ini",
    "content_hash": "sha256:…"
  }
}
```

### Naming convention

States are `x0..x{n-1}`, inputs `u0..`, outputs `y0..` (mirroring the authoring
format). Locals keep their authored names (e.g. `X`, `S`, `mu`). All names share
one namespace; duplicates are a validation error.

### Identity

`provenance.content_hash` is `sha256` over the canonical JSON of the IR body
**excluding** `provenance`. Downstream artifacts reference a scaffold by this
hash, not by file path. For how this interacts with a versioned model library,
SemVer, and git, see
[`model-library-and-versioning.md`](model-library-and-versioning.md).

## 3. Expression sub-language

Expressions are an explicit tagged tree, not strings (see
[ADR 0003](../decisions/0003-explicit-expression-ir.md)). Three node kinds:

```jsonc
{ "kind": "num", "value": 0.4 }
{ "kind": "sym", "name": "mu_max" }
{ "kind": "call", "op": "+", "args": [ <Expr>, <Expr> ] }
```

All operators and functions are uniform `call` nodes keyed by `op`.

| Category | `op` values | Arity |
|---|---|---|
| Arithmetic | `+` `-` `*` `/` `^` | 2 |
| Unary minus | `neg` | 1 |
| Comparison | `<` `>` `<=` `>=` `==` `!=` | 2 |
| Functions | `max` `min` `sqrt` `exp` `log` `abs` | n / 1 |
| Conditional | `ifelse` | 3 |

### Normalization from ExprTk

The INI frontend normalizes authoring spellings into this vocabulary:

- `pow(a, b)` → `{"op": "^", "args": [a, b]}`
- `if(c, a, b)` → `{"op": "ifelse", "args": [c, a, b]}`
- unary `-x` → `{"op": "neg", "args": [x]}`

Precedence and associativity are fixed by the parser (`^` is right-associative;
comparisons bind loosest among supported operators). This is why string rewrites
are avoided: precedence is resolved once, in one place.

### Semantics notes (ExprTk vs Julia)

`ifelse` is **eager** in both ExprTk and Julia symbolic contexts (both branches
are evaluated), which matches MTK's symbolic `ifelse`. Backends must not silently
substitute short-circuit `if`. Numeric literals are emitted as `Float64` by the
Julia backend (e.g. `2` → `2.0`) to keep parameter typing predictable under
MTK v11 parameter-splitting.

## 4. What the IR does *not* contain

- Initial values (`x0`, `u0`) — these are **scenario** data and are dropped by
  the frontend with a `WARN`.
- Fitted parameter values beyond bootstrap defaults — these are a **parameter
  set**.
- Solver settings, horizons, MPC tuning, controller data — out of scope.

## 5. Versioning

`ir_version` follows SemVer. Additive, backward-compatible fields → MINOR.
Breaking shape changes → MAJOR, and require migration tooling plus an ADR. The
JSON Schema is regenerated and committed on every shape change:

```bash
uv run model-parser schema -o schemas/canonical-ir.schema.json
```

## 6. Validation layers

Validation is distinct from conformance (org vocabulary):

- **Structural** — types and required fields (Pydantic, at load time).
- **Semantic** — undeclared/duplicate symbols, missing equations, local
  ordering / cycles.
- **Profile** — is the IR within a backend's accepted subset?

See `src/model_parser/validation/validators.py`.
