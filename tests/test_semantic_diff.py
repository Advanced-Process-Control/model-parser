"""Tests for semantic IR comparison and bump inference."""

import textwrap

import pytest

from model_parser.frontends.exprtk_ini import parse_ini_text
from model_parser.io import load_ir, save_ir, with_content_hash
from model_parser.ir import IRModel
from model_parser.semantic_diff import BumpLevel, compare_ir


def _parse(ini: str) -> IRModel:
    return with_content_hash(parse_ini_text(textwrap.dedent(ini), source_file="x.ini").ir)


def test_compare_identical_returns_none():
    ir = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -x0
        """
    )
    r = compare_ir(ir, ir.model_copy(deep=True))
    assert r.bump is BumpLevel.NONE
    assert not r.items


def test_description_only_is_patch(tmp_path):
    base = _parse(
        """\
        [ModelInfo]
        Name = a
        Description = one
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -x0
        """
    )
    path = tmp_path / "a.ir.json"
    save_ir(base, path)
    data = IRModel.model_validate(load_ir(path).model_dump(mode="json"))
    data.model.description = "two"
    if data.provenance:
        data.provenance.content_hash = None
    new = with_content_hash(data)
    r = compare_ir(base, new)
    assert r.bump is BumpLevel.PATCH
    assert any(i.code == "model-description" for i in r.items)


def test_parameter_default_change_is_patch():
    a = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [Parameters]
        k = 1.0
        [StateEquations]
        dx0 = -k * x0
        """
    )
    b = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [Parameters]
        k = 2.0
        [StateEquations]
        dx0 = -k * x0
        """
    )
    r = compare_ir(a, b)
    assert r.bump is BumpLevel.PATCH


def test_equation_change_is_major():
    a = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -x0
        """
    )
    b = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -2 * x0
        """
    )
    r = compare_ir(a, b)
    assert r.bump is BumpLevel.MAJOR


def test_appended_parameter_is_minor():
    a = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [Parameters]
        k = 1.0
        [StateEquations]
        dx0 = -k * x0
        """
    )
    b = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [Parameters]
        k = 1.0
        m = 0.5
        [StateEquations]
        dx0 = -k * x0
        """
    )
    r = compare_ir(a, b)
    assert r.bump is BumpLevel.MINOR


def test_model_rename_is_major():
    a = _parse(
        """\
        [ModelInfo]
        Name = a
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -x0
        """
    )
    b = _parse(
        """\
        [ModelInfo]
        Name = b
        [Dimensions]
        num_states = 1
        num_inputs = 0
        num_outputs = 0
        [StateEquations]
        dx0 = -x0
        """
    )
    r = compare_ir(a, b)
    assert r.bump is BumpLevel.MAJOR


@pytest.mark.parametrize("epoch", ["946684800", "1577836800"])
def test_source_date_epoch_stable_created_at(monkeypatch, epoch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", epoch)
    r1 = parse_ini_text(
        textwrap.dedent(
            """\
            [ModelInfo]
            Name = a
            [Dimensions]
            num_states = 1
            num_inputs = 0
            num_outputs = 0
            [StateEquations]
            dx0 = -x0
            """
        ),
        source_file="a.ini",
    )
    r2 = parse_ini_text(
        textwrap.dedent(
            """\
            [ModelInfo]
            Name = a
            [Dimensions]
            num_states = 1
            num_inputs = 0
            num_outputs = 0
            [StateEquations]
            dx0 = -x0
            """
        ),
        source_file="b.ini",
    )
    assert r1.ir.provenance is not None and r2.ir.provenance is not None
    assert r1.ir.provenance.created_at == r2.ir.provenance.created_at
