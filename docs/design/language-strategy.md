# Language strategy

> Why this repository uses **both** Python and Julia, and what each owns.

## 1. The question

The work splits into two very different kinds of task:

1. **Text & structure work** — tokenize and parse an authoring grammar, build an
   AST, normalize it into an IR, validate it, serialize it, and **generate** code
   for other languages.
2. **Symbolic & numeric work** — turn the IR into a ModelingToolkit `System`,
   simulate, linearize, and analyze it.

These have different "natural" languages. Forcing both into one runtime would
either make the parser carry a heavy symbolic dependency, or make the symbolic
work fight a language poor at parsing and CLI ergonomics.

## 2. The split

| Concern | Language | Module |
|---|---|---|
| CLI / orchestration | Python | `src/model_parser/cli.py` |
| Tokenizer + expression parser | Python | `frontends/expr_parser.py` |
| Authoring frontend (INI → IR) | Python | `frontends/exprtk_ini.py` |
| IR data model + JSON Schema | Python (Pydantic) | `ir/`, `schema.py` |
| Validators (semantic + profile) | Python | `validation/` |
| **Codegen** IR → MTK `.jl` | Python | `backends/julia_mtk.py` |
| IR → `System` (in memory) | Julia | `julia/ModelParserJL` |
| Simulation / analysis / conformance reference | Julia | `julia/ModelParserJL` (+ SciML) |

The boundary between the two languages is the **IR JSON file** — a plain,
language-neutral artifact. Neither side imports the other; they communicate only
through the IR.

## 3. Why Python owns the AST/IR and the codegen

- **Parsing & CLI strength.** Python has excellent tooling for tokenizers,
  data modeling (Pydantic → free JSON Schema + validation), and CLIs (Typer).
- **No symbolic runtime needed to emit code.** Generating a `.jl` file is pure
  string assembly from the IR tree; it needs no Julia process, so `parse` and
  `emit` are fast, dependency-light, and CI-friendly.
- **Ecosystem alignment.** The org repository map already earmarks a Python
  orchestration CLI (`apc-tooling`); this repository is its concrete, focused
  first incarnation.

## 4. Why Julia owns the `System` build

- **Natural fit.** ModelingToolkit is a Julia library; building a `System` is
  idiomatic there and benefits directly from MTK v11's faster TTFX.
- **Two complementary paths, same contract.**
  - *Codegen* (`emit julia`, Python) → a durable, diffable `.jl` artifact. This
    is the default and the version-controlled form (see
    [ADR 0002](../decisions/0002-codegen-over-serialized-system.md)).
  - *In-memory loader* (`ModelParserJL.build_system`, Julia) → builds the
    `System` from IR JSON at run time, for dynamic/interactive use and as the
    conformance reference.

Because both consume the same IR and the same expression vocabulary, they cannot
drift apart silently — conformance tests pin them to the same fixtures.

## 5. Avoiding the three-semantics trap

The known failure mode (org risk note) is having **three** independent
implementations of expression semantics: Julia string rewrites, C++ ExprTk, and
Python. This repository prevents that by:

- representing expressions as an **explicit tree** in the IR (one semantics),
- making every backend a *renderer* of that tree (no re-parsing),
- testing rendering at the IR level (the same fixture drives Python codegen and,
  in time, the Julia loader and a C++ backend).

A future C++/`realtime-cpp` backend is therefore *another renderer of the same
tree*, not a fourth parser.

## 6. Operational notes

- Python deps via **uv** (`uv add` / `uv sync`); Julia deps via **Pkg**.
- The Julia package keeps `Manifest.toml` out of version control (see
  `.gitignore`); the Python `uv.lock` is committed.
- The Julia path is optional: a user who only wants IR → `.jl` never needs a
  Julia runtime; a user who wants in-memory systems never needs the generated
  file. Both are first-class.
