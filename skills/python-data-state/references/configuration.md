# Configuration and Settings

## Outcome

Configuration is explicit, validated early, and safe to operate.

## Standards

- Use environment-driven configuration for deploy-specific values.
- Prefer typed settings with `pydantic-settings` (or equivalent typed schemas).
- Validate critical configuration at startup, not lazily during request handling.

## Safety Rules

- Fail fast on missing required configuration.
- Fail fast on invalid configuration values and units.
- Avoid import-time configuration side effects; build settings in startup/bootstrap paths.
- Keep secrets out of source code, test fixtures, and logs.

## Organization and Evolution

- Separate application settings from feature flags and runtime state.
- Use explicit defaults only for non-sensitive optional values.
- Allow test overrides via explicit injection/fixtures, not mutable module globals.
- Keep configuration schema documented and versioned when needed.
