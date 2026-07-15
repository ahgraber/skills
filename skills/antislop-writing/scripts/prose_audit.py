#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Mechanical prose-audit tripwires for the antislop-writing skill.

Report-only: measures sentence rhythm (including staccato and uniform-length
runs), contrast-move constructions, heavy and-coordination, shape proxies for
three rewrite-class tells (self-answered questions, anaphora, false ranges),
and punctuation densities in a markdown document's body prose, then lists the
stretches each tripwire flags. The counts flag text for rereading; the reread
decides. The numeric constants are starting heuristics, and the baselines they
derive from are document-wide averages — argument-dense passages legitimately
run hotter locally. Each report ends with densities from one signed human
corpus as a point of reference, not a target.

Usage:
    prose_audit.py FILE [FILE ...] [--window 500] [--json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
import sys

# Starting heuristics (see SKILL.md workflow step 5).
LONG_SENTENCE_WORDS = 30
SHORT_SENTENCE_WORDS = 12
LONG_RUN_LIMIT = 2  # more than this many consecutive long sentences flags
SHORT_SHARE_FLOOR = 1 / 7  # fewer short sentences than this share flags
CONTRAST_WORDS_PER_HIT = 300  # denser than one contrast per this many words flags
AND_COORDINATION_LIMIT = 3  # this many " and " joints in one sentence flags
PARATAXIS_RUN = 4  # this many consecutive short sentences flags a staccato run
UNIFORM_RUN = 3  # this many consecutive near-equal-length sentences flags
UNIFORM_TOLERANCE = 2  # word-count spread that still counts as near-equal
UNIFORM_MIN_WORDS = 8  # uniform runs of shorter sentences are parataxis's job
ANAPHORA_RUN = 3  # consecutive sentences opening with the same two words flags
SHORT_ANSWER_WORDS = 6  # an answer this short after a question reads as staged

# Densities measured on one signed human corpus (38 blog posts, ~46k body
# words). A point of reference for reading the report, not a target: another
# writer's register will differ, and argument-dense passages run hotter.
REFERENCE = {
    "sentence_mean_words": 25.4,
    "sentence_stdev_words": 15.8,
    "short_share": 0.11,
    "contrast_words_per_hit": 1030,
    "em_dash_words_per_hit": 578,
    "exclamation_words_per_hit": 265,
    "ellipsis_words_per_hit": 1401,
}

# The contrast move, by syntax. One rhetorical device; count them together.
# The two cross-sentence forms span a boundary, so they contribute to totals
# but not to the per-sentence window scan.
CONTRAST_PATTERNS: dict[str, re.Pattern[str]] = {
    "rather than": re.compile(r"\brather\s+than\b", re.IGNORECASE),
    "instead of": re.compile(r"\binstead\s+of\b", re.IGNORECASE),
    "not because": re.compile(r"\bnot\s+because\b", re.IGNORECASE),
    "not just/only": re.compile(r"\bnot\s+(?:just|only|merely)\b", re.IGNORECASE),
    ", not Y": re.compile(r",\s*not\s+[a-z]"),
    "not X; it is Y": re.compile(
        r"\b(?:is|are|was|were)\s+not\b[^.;!?—]{0,60}[.;!?—][\s_*]*(?:it|they|this|that)\s+(?:is|are|was|were)\b",
        re.IGNORECASE,
    ),
    "doesn't X; it Ys": re.compile(
        r"\b(?:don't|doesn't|didn't|do not|does not|did not)\s+\w+\b[^.;!?—]{0,60}[.;!?—][\s_*]*(?:it|they)\s+\w+",
        re.IGNORECASE,
    ),
}

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_CODE_FENCE = re.compile(r"^(```|~~~).*?^\1\s*$", re.DOTALL | re.MULTILINE)
_SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}", re.DOTALL)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Lines that are structure rather than body prose.
_NON_PROSE_PREFIXES = ("#", "|", ">", "-", "*", "+", "!", "[")
_ORDERED_ITEM = re.compile(r"^\d+[.)]\s")
_FOOTNOTE_DEF = re.compile(r"^\[\^[^\]]+\]:")


def extract_body(markdown: str) -> str:
    """Return the body prose of a markdown document as one string.

    Strips YAML frontmatter, fenced code, Hugo shortcodes, and HTML comments,
    then drops structural lines: headings, tables, blockquotes (usually quoted
    material, not the author's prose), list items, images, footnote
    definitions, and link-reference lines.
    """
    text = _FRONTMATTER.sub("", markdown)
    text = _CODE_FENCE.sub("", text)
    text = _SHORTCODE.sub("", text)
    text = _HTML_COMMENT.sub("", text)
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(_NON_PROSE_PREFIXES):
            continue
        if _ORDERED_ITEM.match(line) or _FOOTNOTE_DEF.match(line):
            continue
        lines.append(line)
    return " ".join(lines)


def split_sentences(body: str) -> list[str]:
    """Split body prose into sentences, keeping only real ones (>2 words)."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(body) if len(s.split()) > 2]


def _excerpt(sentence: str, limit: int = 80) -> str:
    return sentence if len(sentence) <= limit else sentence[: limit - 1] + "…"


def rhythm_stats(sentences: list[str]) -> dict:
    """Sentence-length statistics and the long-run / short-share tripwires."""
    lengths = [len(s.split()) for s in sentences]
    if not lengths:
        return {"sentences": 0, "flags": []}
    flags: list[str] = []

    runs: list[tuple[int, int]] = []  # (start index, run length)
    run_start, run_len = 0, 0
    for i, n in enumerate(lengths):
        if n > LONG_SENTENCE_WORDS:
            if run_len == 0:
                run_start = i
            run_len += 1
        else:
            if run_len > LONG_RUN_LIMIT:
                runs.append((run_start, run_len))
            run_len = 0
    if run_len > LONG_RUN_LIMIT:
        runs.append((run_start, run_len))
    for start, length in runs:
        flags.append(
            f"{length} consecutive sentences over {LONG_SENTENCE_WORDS} words, "
            f'starting at: "{_excerpt(sentences[start])}"'
        )

    short_share = sum(1 for n in lengths if n < SHORT_SENTENCE_WORDS) / len(lengths)
    if short_share < SHORT_SHARE_FLOOR:
        flags.append(
            f"only {short_share:.0%} of sentences are under {SHORT_SENTENCE_WORDS} words "
            f"(floor {SHORT_SHARE_FLOOR:.0%}) — claims may be buried in long sentences"
        )

    # Staccato runs: consecutive short sentences read as fragment cadence.
    run_start, run_len = 0, 0
    for i, n in enumerate(lengths):
        if n < SHORT_SENTENCE_WORDS:
            if run_len == 0:
                run_start = i
            run_len += 1
        else:
            if run_len >= PARATAXIS_RUN:
                flags.append(
                    f"{run_len} consecutive sentences under {SHORT_SENTENCE_WORDS} words "
                    f'(staccato run), starting at: "{_excerpt(sentences[run_start])}"'
                )
            run_len = 0
    if run_len >= PARATAXIS_RUN:
        flags.append(
            f"{run_len} consecutive sentences under {SHORT_SENTENCE_WORDS} words "
            f'(staccato run), starting at: "{_excerpt(sentences[run_start])}"'
        )

    # Uniform-length runs: near-identical word counts read as a metronome.
    i = 0
    while i <= len(lengths) - UNIFORM_RUN:
        window_lens = lengths[i : i + UNIFORM_RUN]
        if min(window_lens) >= UNIFORM_MIN_WORDS and max(window_lens) - min(window_lens) <= UNIFORM_TOLERANCE:
            run_end = i + UNIFORM_RUN
            while run_end < len(lengths) and abs(lengths[run_end] - window_lens[0]) <= UNIFORM_TOLERANCE:
                run_end += 1
            flags.append(
                f"{run_end - i} consecutive sentences of near-identical length "
                f'(~{window_lens[0]} words each), starting at: "{_excerpt(sentences[i])}"'
            )
            i = run_end
        else:
            i += 1

    return {
        "sentences": len(lengths),
        "mean_words": round(statistics.mean(lengths), 1),
        "stdev_words": round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0.0,
        "short_share": round(short_share, 3),
        "long_share": round(sum(1 for n in lengths if n > LONG_SENTENCE_WORDS) / len(lengths), 3),
        "flags": flags,
    }


def contrast_stats(body: str, sentences: list[str], window: int) -> dict:
    """Contrast-move counts by syntax, overall density, and hot windows."""
    by_syntax = {name: len(pat.findall(body)) for name, pat in CONTRAST_PATTERNS.items()}
    total = sum(by_syntax.values())
    words = len(body.split())
    flags: list[str] = []

    # Non-overlapping word windows; flag any window denser than the heuristic.
    if total and words:
        threshold = max(1, round(window / CONTRAST_WORDS_PER_HIT))
        position = 0
        window_text: list[str] = []
        count_in_window = 0
        for sentence in sentences:
            hits = sum(len(pat.findall(sentence)) for pat in CONTRAST_PATTERNS.values())
            count_in_window += hits
            window_text.append(sentence)
            position += len(sentence.split())
            if position >= window:
                if count_in_window > threshold:
                    flags.append(
                        f"{count_in_window} contrast constructions in one ~{window}-word stretch "
                        f'(threshold {threshold}), near: "{_excerpt(window_text[0])}"'
                    )
                position = 0
                count_in_window = 0
                window_text = []

    return {
        "total": total,
        "by_syntax": {k: v for k, v in by_syntax.items() if v},
        "words_per_contrast": round(words / total) if total else None,
        "flags": flags,
    }


def coordination_stats(sentences: list[str]) -> dict:
    """Sentences that coordinate three or more facts with 'and'."""
    flagged = []
    for sentence in sentences:
        joints = len(re.findall(r"\band\b", sentence, re.IGNORECASE))
        if joints >= AND_COORDINATION_LIMIT:
            flagged.append({"and_count": joints, "sentence": _excerpt(sentence)})
    return {
        "flagged_sentences": flagged,
        "flags": [f'{item["and_count"]}× "and" in one sentence — re-rank: "{item["sentence"]}"' for item in flagged],
    }


def shape_stats(body: str, sentences: list[str]) -> dict:
    """Shape proxies for three rewrite-class tells; the reread judges each."""
    flags: list[str] = []

    # Self-answered rhetorical question: "The result? Devastating." Detected on
    # the raw segment sequence, since the staged fragments are shorter than the
    # real-sentence filter keeps.
    segments = [s.strip() for s in _SENTENCE_SPLIT.split(body) if s.strip()]
    for i, segment in enumerate(segments[:-1]):
        answer = segments[i + 1]
        if segment.endswith("?") and len(answer.split()) <= SHORT_ANSWER_WORDS:
            flags.append(f'question answered by a staged short sentence: "{_excerpt(segment)} {_excerpt(answer)}"')

    # Anaphora: consecutive sentences opening with the same two words.
    openers = [tuple(s.lower().split()[:2]) for s in sentences]
    i = 0
    while i <= len(openers) - ANAPHORA_RUN:
        run_end = i + 1
        while run_end < len(openers) and openers[run_end] == openers[i]:
            run_end += 1
        if run_end - i >= ANAPHORA_RUN:
            flags.append(
                f'{run_end - i} consecutive sentences open with "{" ".join(openers[i])}" '
                f'(anaphora), starting at: "{_excerpt(sentences[i])}"'
            )
            i = run_end
        else:
            i += 1

    # False range: "from X to Y" posing as a spectrum. Numeric ranges are real
    # ranges, so matches containing digits are skipped.
    false_ranges = []
    for match in re.finditer(r"\bfrom\s+\w+(?:\s+\w+){0,3}?\s+to\s+\w+", body, re.IGNORECASE):
        span = match.group(0)
        if not any(ch.isdigit() for ch in span):
            false_ranges.append(span)
            flags.append(f'"from X to Y" range — is there a meaningful middle? "{_excerpt(span)}"')

    return {"false_ranges": false_ranges, "flags": flags}


def punctuation_stats(body: str) -> dict:
    """Punctuation densities, reported against the reference corpus, never flagged."""
    words = len(body.split())
    counts = {
        "em_dash": body.count("—") + len(re.findall(r"\s--\s", body)),
        "exclamation": body.count("!"),
        "ellipsis": body.count("…") + body.count("..."),
    }
    return {
        "counts": counts,
        "words_per_hit": {k: round(words / v) if v else None for k, v in counts.items()},
    }


def audit_file(path: Path, window: int) -> dict:
    """Audit one markdown file and return its stats and tripwire flags."""
    body = extract_body(path.read_text(encoding="utf-8"))
    sentences = split_sentences(body)
    rhythm = rhythm_stats(sentences)
    contrast = contrast_stats(body, sentences, window)
    coordination = coordination_stats(sentences)
    shape = shape_stats(body, sentences)
    punctuation = punctuation_stats(body)
    return {
        "file": str(path),
        "words": len(body.split()),
        "rhythm": rhythm,
        "contrast": contrast,
        "coordination": coordination,
        "shape": shape,
        "punctuation": punctuation,
        "reference": REFERENCE,
        "flags": rhythm.get("flags", []) + contrast["flags"] + coordination["flags"] + shape["flags"],
    }


def render_report(result: dict) -> str:
    """Format one audit result as a human-readable report block."""
    lines = [f"== {result['file']} =="]
    rhythm = result["rhythm"]
    lines.append(f"body words: {result['words']}, sentences: {rhythm.get('sentences', 0)}")
    if rhythm.get("sentences"):
        lines.append(
            f"sentence length: mean {rhythm['mean_words']}w, sd {rhythm['stdev_words']}, "
            f"short {rhythm['short_share']:.0%}, long {rhythm['long_share']:.0%}"
        )
    contrast = result["contrast"]
    if contrast["total"]:
        breakdown = ", ".join(f"{k}: {v}" for k, v in contrast["by_syntax"].items())
        lines.append(
            f"contrast moves: {contrast['total']} (1 per {contrast['words_per_contrast']} words) — {breakdown}"
        )
    else:
        lines.append("contrast moves: 0")
    punct = result["punctuation"]
    punct_parts = []
    for name, count in punct["counts"].items():
        density = punct["words_per_hit"][name]
        punct_parts.append(f"{name} {count}" + (f" (1/{density}w)" if density else ""))
    lines.append("punctuation: " + ", ".join(punct_parts))
    if result["flags"]:
        lines.append("tripwires flagged for rereading:")
        lines.extend(f"  - {flag}" for flag in result["flags"])
    else:
        lines.append("tripwires: nothing flagged")
    ref = result["reference"]
    lines.append(
        "reference (one signed human corpus; a comparison point, not a target): "
        f"mean {ref['sentence_mean_words']}w sd {ref['sentence_stdev_words']}, "
        f"short {ref['short_share']:.0%}, contrast 1/{ref['contrast_words_per_hit']}w, "
        f"em-dash 1/{ref['em_dash_words_per_hit']}w, exclamation 1/{ref['exclamation_words_per_hit']}w, "
        f"ellipsis 1/{ref['ellipsis_words_per_hit']}w"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: audit each file and print a report or JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="markdown files to audit")
    parser.add_argument("--window", type=int, default=500, help="contrast window size in words")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a report")
    args = parser.parse_args(argv)

    results = [audit_file(path, args.window) for path in args.files]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n\n".join(render_report(r) for r in results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
