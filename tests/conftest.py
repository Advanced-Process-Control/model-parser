"""Shared test fixtures."""

import textwrap

import pytest


@pytest.fixture
def monod_ini() -> str:
    return textwrap.dedent(
        """\
        [ModelInfo]
        Name = monod_simple
        Description = Simple CSTR with Monod kinetics
        Version = 1.0

        [Dimensions]
        num_states  = 2
        num_inputs  = 0
        num_outputs = 2

        [Parameters]
        mu_max = 0.4     ; Maximum specific growth rate [1/h]
        K_S    = 0.01    ; Half-saturation constant [g/L]
        Y_XS   = 0.5     ; Yield coefficient [-]

        [StateEquationLocals]
        var X   := max(x0, 0);
        var S   := max(x1, 0);
        var mu  := mu_max * S / (K_S + S);

        [StateEquations]
        dx0 = mu * X
        dx1 = - mu * X / Y_XS

        [OutputEquations]
        y0 = X
        y1 = mu

        [x0]
        0.05
        15.0
        """
    )
