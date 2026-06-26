# Capability Preflight

Top-level scan skills should run this read-only helper before substantive scan
work to confirm the current agent runtime can actually perform the requested
scan, and to surface honest warnings when it cannot.

This preflight is **agent-naive**.
It evaluates only facts the calling agent supplies about its own runtime — whether it can delegate to subagents, run them concurrently, nest delegation, and track goals.
It reads no host configuration files, so it behaves the same under any host.

## Run the helper

Resolve `<python_command>` to the configured Python interpreter (`$PYTHON` when one is provided), otherwise `python` on Windows and `python3` on Unix-like hosts.
Resolve `<plugin_dir>` to this plugin's install directory.
The command is written on one line so it works in PowerShell, Command Prompt, and POSIX shells:

```text
<python_command> <plugin_dir>/scripts/config_preflight.py --profile <capability-profile> --runtime-check delegation_available=<true|false> --runtime-check nested_delegation_available=<true|false> --runtime-check goal_tools_available=<true|false> --worker-slots <N>
```

Instead of `--profile`, you may pass `--skill <skill-id>` (for example
`--skill security-scan`) to resolve the profile from the registry routes.

Determine each value from your own tool surface:

- `delegation_available`: `true` if you can spawn subagents or parallel workers (a task, agent, or multi-agent tool).
  If such tools may be deferred rather than listed up front, search your tool surface before passing `false`.
  Pass `false` only after discovery fails to expose a usable delegation tool.
- `nested_delegation_available`: `true` if a spawned subagent can itself spawn subagents.
  Pass `false` for single-level delegation; omit if unknown.
- `goal_tools_available`: `true` if you have goal, task, or todo-tracking tools
  that persist objectives across steps.
- `--worker-slots <N>`: how many subagents you can run concurrently.
  Use your host's known concurrency cap.
  Omit it if unknown — capacity requirements then return `unknown` (advisory) rather than failing.

## Run it in a worker when you can

If delegation is available, run the helper in one dedicated worker before substantive scan work and have it return a compact summary: the executed command and exit code, the overall status, any unmet or unknown capabilities, and the applicable guidance.
This keeps preflight detail out of the primary scan context.
A "dispatch" means a successful worker-spawn that returns a concrete worker id; wait for that specific id and accept a result only from it.
If spawning fails or returns no id, run the helper directly in the parent and report the spawn failure — never invent or reconstruct a helper result.
If delegation is unavailable, run the helper directly so it can report the degraded or blocked path.

## Interpret the result

The helper prints one JSON result and exits `0` (ready), `1` (blocked), or `2` (incomplete, or a top-level `status: "error"` envelope).
Use the helper result as the source of truth; do not reinterpret requirements yourself.

Each requirement carries a severity:

- `block`: the requested workflow cannot be claimed honestly when the capability
  is unmet.
- `warn`: the workflow can continue only on the documented degraded path.
- `suggest`: the workflow can continue, but mention the improvement when it
  materially affects long-running scan quality or resumability.

Overall status:

- `ready`: continue.
  Explain any `warn` or `suggest` limitations and use the degraded path where one applies.
- `incomplete`: one or more capabilities are `unknown` — for example, worker capacity was not supplied, or a runtime check was omitted.
  Establish the missing fact from your tool surface and rerun, or continue on the degraded path while stating clearly what is unverified.
  Do not treat `incomplete` as evidence that a capability is available.
- `blocked`: a `block`-severity capability failed.
  Present the exact failing reasons and the advisory `remediation.guidance`, and do not claim the blocked workflow.
  Offer a narrower or single-agent path only if it can satisfy the request honestly.

Remediation here is **advisory host guidance** (for example, "enable subagent delegation" or "allow at least six concurrent subagents"), not edits to any configuration file.
Present it to the user; never silently change host settings.
Do not warn merely because the runtime differs from a suggestion — warn or block only when an evaluated capability requirement is actually unmet.
