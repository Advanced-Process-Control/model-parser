"""
    ModelParserJL

Load a canonical model IR (produced by the `model-parser` Python CLI) directly
into a ModelingToolkit `System`, **in memory**, without a code-generation step.

This is the complementary path to the Python `emit julia` codegen backend:

- **Codegen** (`model-parser emit julia`) produces a re-runnable `.jl` artifact;
  it is the durable, version-controlled form (see ADR 0002).
- **`ModelParserJL.build_system`** consumes the IR JSON at run time; it is for
  dynamic / interactive workflows where writing a file is unnecessary.

Both consume the *same* IR contract, so they stay semantically aligned.

The IR `System` is built targeting ModelingToolkit v11 idioms (`System(eqs, t)`,
`mtkcompile`, `t_nounits`/`D_nounits`).
"""
module ModelParserJL

using JSON3
using ModelingToolkit
using ModelingToolkit: t_nounits as t, D_nounits as D

export load_ir, build_system

"""
    load_ir(path) -> JSON3.Object

Read a canonical IR JSON file from disk and return the parsed object.
"""
load_ir(path::AbstractString) = JSON3.read(read(path, String))

# Map IR op names to Julia callables for symbolic construction.
const _BINARY = Dict{String,Function}(
    "+" => +, "-" => -, "*" => *, "/" => /, "^" => ^,
    "<" => <, ">" => >, "<=" => <=, ">=" => >=, "==" => ==,
)
const _FUNCS = Dict{String,Function}(
    "max" => max, "min" => min, "sqrt" => sqrt, "exp" => exp,
    "log" => log, "abs" => abs, "ifelse" => ifelse,
)

"""Recursively turn an IR expression node into a Symbolics expression."""
function _to_symbolic(node, syms::Dict{String,Any})
    kind = node["kind"]
    if kind == "num"
        return Float64(node["value"])
    elseif kind == "sym"
        name = String(node["name"])
        haskey(syms, name) || error("IR references undeclared symbol: $name")
        return syms[name]
    elseif kind == "call"
        op = String(node["op"])
        args = [_to_symbolic(a, syms) for a in node["args"]]
        if op == "neg"
            return -args[1]
        elseif haskey(_BINARY, op)
            return _BINARY[op](args[1], args[2])
        elseif haskey(_FUNCS, op)
            return _FUNCS[op](args...)
        else
            error("Unsupported IR operator/function: $op")
        end
    else
        error("Unknown IR node kind: $kind")
    end
end

_tvar(name) = only(@variables $(Symbol(name))(t))

function _param(name, default)
    p = only(@parameters $(Symbol(name)))
    default === nothing ? p : ModelingToolkit.setdefault(p, Float64(default))
end

"""
    build_system(ir) -> System

Build a compiled ModelingToolkit `System` from a parsed IR object (see
[`load_ir`](@ref)). Inputs declared in the IR are passed to `mtkcompile`.
"""
function build_system(ir)
    syms = Dict{String,Any}()

    for v in ir["states"];  syms[String(v["name"])] = _tvar(v["name"]); end
    for v in ir["inputs"];  syms[String(v["name"])] = _tvar(v["name"]); end
    for v in ir["outputs"]; syms[String(v["name"])] = _tvar(v["name"]); end
    for l in ir["locals"];  syms[String(l["name"])] = _tvar(l["name"]); end
    for p in ir["parameters"]
        syms[String(p["name"])] = _param(p["name"], get(p, "default", nothing))
    end

    eqs = Equation[]
    for l in ir["locals"]
        push!(eqs, syms[String(l["name"])] ~ _to_symbolic(l["expr"], syms))
    end
    for d in ir["equations"]["differential"]
        push!(eqs, D(syms[String(d["state"])]) ~ _to_symbolic(d["rhs"], syms))
    end
    for o in ir["equations"]["outputs"]
        push!(eqs, syms[String(o["output"])] ~ _to_symbolic(o["rhs"], syms))
    end

    name = Symbol(ir["model"]["name"])
    @named sys = System(eqs, t)
    sys = ModelingToolkit.rename(sys, name)

    input_syms = [syms[String(v["name"])] for v in ir["inputs"]]
    return isempty(input_syms) ? mtkcompile(sys) :
           mtkcompile(sys; inputs = [ModelingToolkit.unwrap(u) for u in input_syms])
end

end # module
