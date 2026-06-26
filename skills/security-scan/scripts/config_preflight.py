#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Evaluate security-scan capability profiles against the current agent runtime.

This helper is agent-naive: it evaluates only facts the calling agent supplies
about its own runtime (whether it can delegate to subagents, run them
concurrently, nest delegation, and track goals). It reads no host-specific
configuration files, so it behaves the same under any coding-agent host.

Capability kinds (see preflight/capability-profiles.toml):
  runtime          - a boolean the agent supplies via --runtime-check NAME=BOOL
  worker_capacity  - an integer the agent supplies via --worker-slots N
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import tomllib

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PLUGIN_ROOT / "preflight" / "capability-profiles.toml"
VALID_SEVERITIES = {"block", "warn", "suggest"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--profile", help="Capability profile id to evaluate.")
    selector.add_argument("--skill", help="Top-level skill id to resolve through the registry routes.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Capability registry path. Defaults to the bundled registry.",
    )
    parser.add_argument(
        "--runtime-check",
        action="append",
        default=[],
        metavar="NAME=BOOL",
        help="Runtime capability the agent observes, e.g. delegation_available=true.",
    )
    parser.add_argument(
        "--worker-slots",
        type=non_negative_int,
        default=None,
        metavar="N",
        help="Number of subagents this host can run concurrently. Omit if unknown.",
    )
    return parser.parse_args()


def non_negative_int(value: str) -> int:
    """Parse a CLI integer and reject negative values."""
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected a non-negative integer")
    return parsed


def parse_bool(value: str) -> bool:
    """Parse a boolean from a true/false string."""
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"expected true or false, got {value!r}")


def parse_runtime_checks(values: list[str]) -> dict[str, bool]:
    """Parse repeated NAME=BOOL runtime-capability flags."""
    checks: dict[str, bool] = {}
    for raw in values:
        key, separator, value = raw.partition("=")
        if not separator or not key or not value:
            raise ValueError(f"expected NAME=BOOL, got {raw!r}")
        checks[key.strip()] = parse_bool(value)
    return checks


def read_toml(path: Path) -> dict[str, Any]:
    """Read and parse a TOML file."""
    with path.open("rb") as file:
        return tomllib.load(file)


def compare(actual: Any, op: str, expected: Any) -> bool:
    """Compare two values using a supported operator."""
    if op == "==":
        return actual == expected
    if op == ">=":
        return isinstance(actual, int) and not isinstance(actual, bool) and actual >= expected
    raise ValueError(f"unsupported comparison operator: {op!r}")


def resolve_profile(registry: dict[str, Any], *, profile: str | None, skill: str | None) -> str:
    """Resolve a capability profile id from an explicit id or a skill route."""
    if profile:
        return profile
    routes = {route["skill"]: route["profile"] for route in registry.get("routes", [])}
    try:
        return routes[str(skill)]
    except KeyError as error:
        raise ValueError(f"no capability profile route for skill {skill!r}") from error


def validate_registry(registry: dict[str, Any]) -> None:
    """Validate the capability registry structure."""
    capabilities = registry["capabilities"]
    for capability_id, capability in capabilities.items():
        kind = capability.get("kind")
        if kind not in {"runtime", "worker_capacity"}:
            raise ValueError(f"capability {capability_id!r} has unsupported kind {kind!r}")
    for profile_id, profile in registry["profiles"].items():
        for requirement in profile["requirements"]:
            if requirement["capability"] not in capabilities:
                raise ValueError(f"profile {profile_id!r} references unknown capability {requirement['capability']!r}")
            if requirement["severity"] not in VALID_SEVERITIES:
                raise ValueError(f"profile {profile_id!r} has unsupported severity {requirement['severity']!r}")


def evaluate_requirement(
    requirement: dict[str, Any],
    *,
    capabilities: dict[str, dict[str, Any]],
    runtime_checks: dict[str, bool],
    worker_slots: int | None,
) -> dict[str, Any]:
    """Evaluate one capability requirement against observed runtime facts."""
    capability_id = requirement["capability"]
    capability = capabilities[capability_id]
    result = {
        "capability": capability_id,
        "severity": requirement["severity"],
        "reason": requirement["reason"],
    }

    if capability["kind"] == "runtime":
        check = capability["check"]
        if check not in runtime_checks:
            return {**result, "status": "unknown", "check": check}
        actual = runtime_checks[check]
        return {**result, "status": "pass" if actual else "fail", "actual": actual, "check": check}

    if capability["kind"] == "worker_capacity":
        if worker_slots is None:
            return {**result, "status": "unknown", "check": "worker_slots"}
        passed = compare(worker_slots, capability["op"], capability["value"])
        return {
            **result,
            "status": "pass" if passed else "fail",
            "actual": worker_slots,
            "expected": {"op": capability["op"], "value": capability["value"]},
            "check": "worker_slots",
        }

    raise ValueError(f"unsupported capability kind: {capability['kind']!r}")


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    """Evaluate a capability profile and summarize readiness."""
    registry = read_toml(args.registry)
    validate_registry(registry)
    profile_id = resolve_profile(registry, profile=args.profile, skill=args.skill)
    try:
        profile = registry["profiles"][profile_id]
    except KeyError as error:
        raise ValueError(f"unknown capability profile: {profile_id!r}") from error

    runtime_checks = parse_runtime_checks(args.runtime_check)

    results = [
        evaluate_requirement(
            requirement,
            capabilities=registry["capabilities"],
            runtime_checks=runtime_checks,
            worker_slots=args.worker_slots,
        )
        for requirement in profile["requirements"]
    ]
    failed = [result for result in results if result["status"] == "fail"]
    unknown = [result for result in results if result["status"] == "unknown"]
    if any(result["severity"] == "block" for result in failed):
        status = "blocked"
    elif unknown:
        status = "incomplete"
    else:
        status = "ready"

    return {
        "version": registry["version"],
        "profile": profile_id,
        "description": profile["description"],
        "status": status,
        "worker_slots": args.worker_slots,
        "runtime_checks": runtime_checks,
        "results": results,
        "failed": failed,
        "unknown": unknown,
        "remediation": dict(profile.get("remediation", {})),
    }


def main() -> int:
    """Run the capability-profile preflight CLI."""
    try:
        payload = evaluate(parse_args())
    except (KeyError, OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["status"] == "blocked":
        return 1
    return 2 if payload["status"] == "incomplete" else 0


if __name__ == "__main__":
    sys.exit(main())
