#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pytest>=8.0",
# ]
# ///
"""Tests for the antislop-writing prose_audit.py tripwire scanner."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPT = Path(__file__).parents[2] / "skills" / "antislop-writing" / "scripts" / "prose_audit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prose_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pa = _load_module()


def test_extract_body_strips_structure():
    doc = (
        "---\ntitle: x\n---\n"
        "# Heading\n\n"
        "Body prose stays in the result.\n\n"
        "> a blockquote is quoted material\n\n"
        "- a bullet item\n"
        "1. an ordered item\n\n"
        "| a | table |\n\n"
        "```\ncode = 1\n```\n\n"
        '{{< figure src="x" >}}\n\n'
        "[^note]: a footnote definition\n\n"
        "More body prose also stays."
    )
    body = pa.extract_body(doc)
    assert "Body prose stays" in body
    assert "More body prose" in body
    for absent in ("Heading", "blockquote", "bullet", "ordered", "table", "code", "figure", "footnote"):
        assert absent not in body


def test_sentence_split_ignores_fragments():
    sentences = pa.split_sentences("This is a real sentence. No. Another real sentence here.")
    assert len(sentences) == 2


def test_contrast_counts_by_syntax():
    body = (
        "We chose prose rather than fragments. "
        "It works instead of failing. "
        "This matters not because it is new, but because it is cheap. "
        "It is signal, not noise. "
        "This is not just a demo."
    )
    result = pa.contrast_stats(body, pa.split_sentences(body), window=500)
    assert result["total"] == 5
    assert result["by_syntax"]["rather than"] == 1
    assert result["by_syntax"]["instead of"] == 1
    assert result["by_syntax"][", not Y"] == 1


def test_contrast_cross_sentence_forms():
    body = (
        "The biggest problem is not intelligence. It is memory. "
        "The agent doesn't need a real filesystem. It needs the illusion of one."
    )
    result = pa.contrast_stats(body, pa.split_sentences(body), window=500)
    assert result["by_syntax"]["not X; it is Y"] == 1
    assert result["by_syntax"]["doesn't X; it Ys"] == 1
    plain = "The problem is not yet solved. Work continues on the remaining pieces."
    unmatched = pa.contrast_stats(plain, pa.split_sentences(plain), window=500)
    assert "not X; it is Y" not in unmatched["by_syntax"]


def test_and_coordination_flags_three_not_two():
    two = "The library is fast and it is small, and users like it."
    three = "The library is fast and small and stable and users like it and adopt it."
    assert pa.coordination_stats(pa.split_sentences(two))["flagged_sentences"] == []
    flagged = pa.coordination_stats(pa.split_sentences(three))["flagged_sentences"]
    assert len(flagged) == 1
    assert flagged[0]["and_count"] >= 3


def test_long_run_flags_three_consecutive_not_two():
    long_sentence = " ".join(["word"] * 35) + "."
    short_sentence = "A short one lands here."
    two_run = pa.rhythm_stats(pa.split_sentences(" ".join([long_sentence, long_sentence, short_sentence] * 3)))
    assert not any("consecutive" in flag for flag in two_run["flags"])
    three_run = pa.rhythm_stats(
        pa.split_sentences(" ".join([long_sentence, long_sentence, long_sentence] + [short_sentence] * 6))
    )
    assert any("consecutive" in flag for flag in three_run["flags"])


def test_short_share_floor_flags_monotone():
    long_sentence = " ".join(["word"] * 25) + "."
    stats = pa.rhythm_stats(pa.split_sentences(" ".join([long_sentence] * 10)))
    assert any("under" in flag for flag in stats["flags"])


def test_staccato_run_flags_four_not_three():
    short = "The cat sat down."
    long = "This considerably longer sentence provides enough words to break any staccato run cleanly."
    three = pa.rhythm_stats(pa.split_sentences(" ".join([short] * 3 + [long])))
    assert not any("staccato" in flag for flag in three["flags"])
    four = pa.rhythm_stats(pa.split_sentences(" ".join([short] * 4 + [long])))
    assert any("staccato" in flag for flag in four["flags"])


def test_uniform_length_run_flags_metronome():
    uniform = " ".join(
        ["Alpha beta gamma delta epsilon zeta eta theta iota kappa."] * 3
        + ["Short one lands."]
        + ["A very much longer sentence that runs on considerably to vary the rhythm of the paragraph here."]
    )
    stats = pa.rhythm_stats(pa.split_sentences(uniform))
    assert any("near-identical" in flag for flag in stats["flags"])
    varied = " ".join(
        [
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa.",
            "Short one lands.",
            "A very much longer sentence that runs on considerably to vary the rhythm of the paragraph here.",
        ]
    )
    assert not any("near-identical" in flag for flag in pa.rhythm_stats(pa.split_sentences(varied))["flags"])


def test_self_answered_question_flags_staged_answer():
    staged = (
        "The team shipped the feature on time. The result? Devastating. "
        "Everyone involved needed a long vacation afterward."
    )
    flags = pa.shape_stats(staged, pa.split_sentences(staged))["flags"]
    assert any("staged short sentence" in flag for flag in flags)
    genuine = (
        "What does this mean for the roadmap? "
        "It means the team must reprioritize the second quarter around the migration work already underway."
    )
    assert not any("staged" in flag for flag in pa.shape_stats(genuine, pa.split_sentences(genuine))["flags"])


def test_anaphora_flags_three_identical_openers():
    body = (
        "They assume users will pay for the product. "
        "They assume developers will build the integrations. "
        "They assume ecosystems will emerge around the platform. "
        "Reality rarely cooperates with assumptions like these."
    )
    flags = pa.shape_stats(body, pa.split_sentences(body))["flags"]
    assert any("anaphora" in flag for flag in flags)
    two = (
        "They assume users will pay for the product. "
        "They assume developers will build the integrations. "
        "Reality rarely cooperates with assumptions like these."
    )
    assert not any("anaphora" in flag for flag in pa.shape_stats(two, pa.split_sentences(two))["flags"])


def test_false_range_flags_abstractions_not_numbers():
    abstract = "The platform handles everything from innovation to cultural transformation."
    flags = pa.shape_stats(abstract, pa.split_sentences(abstract))["flags"]
    assert any("from X to Y" in flag for flag in flags)
    numeric = "The service runs from 9 to 5 on weekdays."
    assert pa.shape_stats(numeric, pa.split_sentences(numeric))["flags"] == []


def test_punctuation_counts_and_never_flags():
    body = "This sentence has an em-dash — right here! It also trails off… like this..."
    stats = pa.punctuation_stats(body)
    assert stats["counts"]["em_dash"] == 1
    assert stats["counts"]["exclamation"] == 1
    assert stats["counts"]["ellipsis"] == 2
    assert "flags" not in stats


def test_report_includes_reference_block(tmp_path, capsys):
    doc = tmp_path / "sample.md"
    doc.write_text("One plain sentence keeps this report small and readable.", encoding="utf-8")
    pa.main([str(doc)])
    out = capsys.readouterr().out
    assert "reference (one signed human corpus" in out
    assert "not a target" in out


def test_end_to_end_json(tmp_path):
    doc = tmp_path / "sample.md"
    doc.write_text(
        "---\ntitle: t\n---\n\n"
        "This document has body prose that the auditor should measure carefully. "
        "It is short. "
        "The auditor reports statistics rather than verdicts, and the reread decides.\n",
        encoding="utf-8",
    )
    exit_code = pa.main([str(doc), "--json"])
    assert exit_code == 0


def test_report_renders_without_error(tmp_path, capsys):
    doc = tmp_path / "sample.md"
    doc.write_text("A tiny document with one plain sentence for the report.", encoding="utf-8")
    pa.main([str(doc)])
    out = capsys.readouterr().out
    assert "sample.md" in out
    assert "contrast moves" in out


if __name__ == "__main__":
    sys.exit(
        pytest.main([__file__, "-v", f"--rootdir={Path(__file__).parent}", f"--confcutdir={Path(__file__).parent}"])
    )
