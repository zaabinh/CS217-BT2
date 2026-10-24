"""Malformed imports and failed edits must not corrupt a validated snapshot."""
import json
import shutil

import pytest

import knowledge_base
from knowledge_base import Chemical, DATA_DIR, KnowledgeBase, Reaction


@pytest.fixture
def kb(tmp_path):
    for name in ("chemicals.json", "reactions.json"):
        shutil.copy(DATA_DIR / name, tmp_path / name)
    return KnowledgeBase(tmp_path)


@pytest.mark.parametrize("field", ["weights", "cost"])
@pytest.mark.parametrize("value", [True, False, 1.9, "2", 0, -1, float("nan"), float("inf")])
def test_integer_fields_never_silently_coerce(kb, field, value):
    raw = kb.reactions[0].to_dict()
    raw[field] = [value, *raw["weights"][1:]] if field == "weights" else value
    with pytest.raises(ValueError):
        Reaction.from_dict(raw)


@pytest.mark.parametrize("value", [True, 0, -1, float("nan"), float("inf"), "12"])
def test_atomic_mass_must_be_finite_positive_number(value):
    with pytest.raises(ValueError):
        Chemical.from_dict({"Formula": "C", "Name": ["Carbon"], "Atomic mass": value})


@pytest.mark.parametrize("kind", ["duplicate_formula", "duplicate_id", "unbalanced", "bad_names", "bad_root"])
def test_load_rejects_invalid_snapshot_without_overwriting_memory(kb, kind):
    chemicals = json.loads(kb.chem_file.read_text(encoding="utf-8"))
    reactions = json.loads(kb.react_file.read_text(encoding="utf-8"))
    if kind == "duplicate_formula":
        chemicals.append(chemicals[0])
    elif kind == "duplicate_id":
        reactions[1]["id"] = reactions[0]["id"]
    elif kind == "unbalanced":
        reactions[0]["weights"][0] += 1
    elif kind == "bad_names":
        chemicals[0]["Name"] = "Not a list"
    else:
        reactions = {"not": "a list"}
    before = kb.revision
    original = kb.chemicals, kb.reactions
    kb.chem_file.write_text(json.dumps(chemicals), encoding="utf-8")
    kb.react_file.write_text(json.dumps(reactions), encoding="utf-8")
    with pytest.raises(ValueError):
        kb.load()
    assert kb.revision == before
    assert kb.chemicals is original[0] and kb.reactions is original[1]


def test_revision_detects_direct_mutation_and_revalidates(kb):
    before = kb.revision
    assert kb.ensure_valid() == []
    kb.reactions[0].cost = True
    assert kb.revision != before
    assert kb.ensure_valid()
    assert any(issue["level"] == "Lỗi" for issue in kb.check_consistency())


def test_malformed_public_record_is_rejected_without_crashing(kb):
    kb.reactions.append(None)
    assert kb.ensure_valid()
    assert kb.check_consistency()[0]["level"] == "Lỗi"


def test_unchanged_snapshot_uses_cached_validation(kb, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("The unchanged snapshot should not be validated twice")
    monkeypatch.setattr(kb, "validate_reaction", unexpected)
    assert kb.ensure_valid() == []


def test_failed_second_file_replace_restores_files_and_memory(kb, monkeypatch):
    original_files = {p: p.read_bytes() for p in (kb.chem_file, kb.react_file)}
    original_revision = kb.revision
    replace = knowledge_base.os.replace
    calls = 0

    def fail_second(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated disk error")
        return replace(source, target)

    monkeypatch.setattr(knowledge_base.os, "replace", fail_second)
    with pytest.raises(OSError):
        kb.delete_reaction("R01")
    assert kb.revision == original_revision
    assert all(p.read_bytes() == content for p, content in original_files.items())
    assert {p.name for p in kb.data_dir.iterdir()} == {"chemicals.json", "reactions.json"}


def test_invalid_default_does_not_replace_valid_kb(kb):
    defaults = kb.data_dir / "default"
    defaults.mkdir()
    for path in (kb.chem_file, kb.react_file):
        shutil.copy(path, defaults / path.name)
    (defaults / "reactions.json").write_text("{}", encoding="utf-8")
    before = kb.revision
    with pytest.raises(ValueError):
        kb.reset_default()
    assert kb.revision == before
    assert KnowledgeBase(kb.data_dir).revision == before
