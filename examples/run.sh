#!/usr/bin/env bash
# Run the full model-parser pipeline for the bundled example models.
# Usage: ./examples/run.sh   (from the repository root)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out="$here/outputs"
mkdir -p "$out"

for model in monod_simple thermal_tank; do
  ini="$here/models/model_${model}.ini"
  ir="$out/${model}.ir.json"
  jl="$out/${model}.jl"
  rhs="$out/${model}_rhs.jl"

  echo "== $model: parse =="
  uv run model-parser parse "$ini" -o "$ir"

  echo "== $model: validate (julia-analysis) =="
  uv run model-parser validate "$ir" --profile julia-analysis

  echo "== $model: emit julia =="
  uv run model-parser emit julia "$ir" -o "$jl"
  echo "wrote $jl"

  echo "== $model: emit julia-rhs =="
  uv run model-parser emit julia-rhs "$ir" -o "$rhs"
  echo "wrote $rhs"
  echo
done

echo "Done. Generated IR + Julia views in $out"
