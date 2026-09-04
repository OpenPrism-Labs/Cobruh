---
name: cobruh-config
description: Author, inspect, compose, override, and debug Cobruh YAML configuration trees; use when editing defaults, groups, interpolation, or hash-guarded config sources.
license: MIT
---

# Cobruh configuration

Use this skill for Cobruh YAML source work. Prefer the Cobruh MCP tools when they are available. Otherwise use the equivalent `cobruh` CLI commands.

## Safe workflow

1. Call `list_configs`, or run `cobruh catalog --root <configs> --project-root <project>`.
2. With MCP, call `read_config_source` before editing and retain its SHA-256.
3. Edit only root-relative `.yaml` or `.yml` sources. Never use absolute paths, traversal, or symlinks.
4. With MCP, call `write_config_source` with `expected_sha256` when replacing a file. Omit the hash only when creating a file.
5. Call `compose_config`, or run `cobruh compose <name> --root <configs> --project-root <project> --format json`.
6. Treat composition success and the resulting values as the verification contract.

## Defaults

A `defaults` list accepts only:

- `_self_`, which inserts the current source at that position;
- a root-relative config name such as `base`;
- a one-key group selection such as `{model: resnet50}`.

Entries compose left to right. If `_self_` is omitted, the current source composes last. Mappings deep-merge; lists and scalars replace. Group selections nest under the group key.

Do not author optional defaults, override-default syntax, null defaults, multirun syntax, ConfigStore entries, or plugin syntax.

## Overrides

Use the same grammar through Python, CLI, and MCP:

- `path=value` replaces an existing dotted path.
- `+path=value` creates a missing path and fails if it exists.
- `group=option` selects an existing option from a config group.

Values use YAML parsing. Overrides are sequential, so `model=vgg` may be followed by `model.layers=19`.

## Interpolation

Supported forms:

- `${path.to.value}`
- `${env:NAME}`
- `${env:NAME,default}`

An exact reference token preserves the referenced value's type. A token embedded in text is stringified. Resolution happens after defaults and overrides. Use `--no-resolve` or `resolve=false` only when inspecting unresolved expressions.
