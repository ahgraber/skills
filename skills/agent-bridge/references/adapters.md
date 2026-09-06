# Agent CLI adapters

For adding or correcting an adapter.
Working with a target agent needs none of this.

The live registry is `ADAPTERS` in `scripts/agent_bridge.py`; read it there rather than from a copy here.

## What an adapter carries

The tmux layer is identical for every CLI: one window per agent, bracketed paste to submit, screen hashing for idleness.
What varies is collected in an `Adapter`.

| Field                                              | What it decides                                               |
| -------------------------------------------------- | ------------------------------------------------------------- |
| `binary`                                           | what `spawn` runs, and what must be on `PATH`                 |
| `dangerous_flags`, `dangerous_values`              | which passthrough arguments `spawn` refuses                   |
| `config_assignment_flags`, `dangerous_config_keys` | gate-removing settings reached through a `key=value` override |
| `opaque_config_flags`                              | arguments that select non-default config                      |
| `prompt_flag`                                      | how `--prompt` reaches the CLI, or that it cannot             |
| `submit_key`                                       | the tmux key `send` presses after pasting                     |
| `model_flag`                                       | where `--model` goes                                          |
| `config_hint`                                      | the path named in the spawn's posture report                  |

## Initial prompts

`codex` and `claude` take a positional prompt; both `--help` outputs state it (`codex [OPTIONS] [PROMPT]`, `claude [options] [command] [prompt]`).

The rest are `PROMPT_UNSUPPORTED`, so `spawn` refuses `--prompt` for them.
The risk being avoided is specific: several of these CLIs use `-p` to run without a TUI, so a wrong guess leaves an empty window and no agent.

Fill `prompt_flag` only after reading the CLI's `--help` and confirming the form opens an interactive session.
Leave it at the default when you cannot confirm that.

## What the refusal list covers

A named switch is not the only way to open the approval gate.
`codex -c approval_policy=never` sets what `-a never` would, spelled differently.
Adapters therefore describe three shapes — the switch, a flag whose value names a mode, and a `key=value` config assignment — and `spawn` refuses all three.

A fourth is not refused.
`codex --profile` and `claude --settings` point the CLI at configuration other than its default, which is the normal way to select a stricter posture as well as a looser one.
Those spawns run, the posture is marked `OVERRIDDEN`, and the note names the argument.

The lists are a floor.
They come from each CLI's documentation, not from running the flags, so a gate-removing flag not on the list still reaches the CLI, and releases add flags.
`pi` has no entries because its approval model is unestablished: `pi --help` prints nothing without a terminal, and a sandbox that denies `openpty` cannot read it.

## Submit keys

`submit_key` is `Enter` everywhere today.
It is a field because the CLIs differ: pi documents `Enter` to steer a running turn and `Alt+Enter` to queue a follow-up.
`send --submit-key` overrides it per call.

## Adding an adapter

Add an entry to `ADAPTERS`.
Nothing else changes: `--agent` takes its choices from the registry keys, and the window tag records the adapter name so `send` finds the right submit key.
