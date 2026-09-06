---
name: cobruh-config
description: Author, inspect, compose, override, validate, and debug Cobruh YAML configuration trees; use when editing defaults, groups, packages, schemas, interpolation, or hash-guarded config sources.
license: MIT
---

# Cobruh configuration

Use this skill for Cobruh YAML source work. Prefer the Cobruh MCP tools when available; otherwise use the equivalent `cobruh` CLI commands.

## Safe workflow

1. Call `list_configs`, or run `cobruh catalog --root <configs> --project-root <project>`. Catalog records contain logical names, exact YAML paths, and registered schema sources.
2. With MCP, call `read_config_source` before editing and retain its SHA-256.
3. Edit only root-relative `.yaml` or `.yml` sources. Never use absolute paths, traversal, or escaping symlinks.
4. With MCP, call `write_config_source` with `expected_sha256` when replacing a file. Omit the hash only when creating a file.
5. Call `compose_config`, or run `cobruh inspect <name> --root <configs> --project-root <project>`.
6. Verify `data`, `choices`, leaf `provenance`, `types`, and `validation`; focus with `node` or `--node` when useful.

## Defaults

A `defaults` list accepts:

- `_self_`, inserting the current source at that position;
- a config include such as `base`, resolved relative to the containing source directory;
- an absolute config include such as `/base`, resolved from `config_root`;
- `group: option`, `optional group: option`, or `override group: option`;
- a null group placeholder, such as `optional cache: null`;
- a list of options, such as `augment: [crop, flip]`, merged left to right as one choice.

If `_self_` is omitted, the current source composes last. Unprefixed groups resolve relative to the containing source. A later `override group` replaces the earlier option and every nested layer it owned, so stale keys do not survive.

Relocate an entry with `@package`, for example `model@primary: small`. `_here_` means the containing package, `_group_` means the absolute group package, and `_global_` means the root. Packages are defaults-list syntax; Cobruh has no comment-based package directive.

## Overrides

Defaults/group operations run before dotted value mutations; value mutations then run left to right:

- `path=value`: replace an existing path.
- `+path=value`: create a missing path; fail if it exists.
- `++path=value`: create or replace a path.
- `~path`: delete an existing path.
- `~path=value`: delete only when the current value equals the parsed YAML value.
- `group=option`: replace a selected config group.
- `+group=option`: add an unselected config group.
- `~group`: remove a selected group and its nested layers.

Group forms also accept `group@package`. Values use YAML scalar/list/mapping parsing; an empty right-hand side is `""`. Comma-separated group choices and override functions are sweeps and require Hydra.

## Schemas and inspection

Register Draft 2020-12 JSON Schemas in Python with `Cobruh(..., schemas={"config": "schema.json"})`, or repeat `--schema NAME=PATH` on project CLI commands. Schema files are UTF-8 `.json` mappings no larger than 1 MiB, contained by `project_root`; only local `#...` references are accepted.

Resolved compositions validate automatically. `resolve=false` skips validation deliberately. `Cobruh.inspect()` and `compose_config` return exactly `name`, `node`, `data`, `sources`, `choices`, `provenance`, `types`, and `validation`; focused JSON Pointers are rebased so the selected root is `""`.

## Interpolation

Supported forms are `${path.to.value}`, `${env:NAME}`, and `${env:NAME,default}`. An exact reference preserves its value type; an embedded token is stringified. Resolution runs after defaults, group overrides, and value overrides. Provenance remains attached to the field containing the expression.
