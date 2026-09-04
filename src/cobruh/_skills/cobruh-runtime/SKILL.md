---
name: cobruh-runtime
description: Build, review, instantiate, and debug Cobruh _target_ runtime mappings, including positional arguments, partials, recursive construction, and project-local Python imports.
license: MIT
---

# Cobruh target runtime

Use this skill for configuration that imports or constructs Python targets. Prefer `instantiate_config` through the Cobruh MCP server when available. Otherwise use `cobruh instantiate <name> --node <path> --root <configs> --project-root <project>` or `Cobruh.instantiate()`.

## Trust boundary

Instantiation imports Python and calls constructors or functions. It can execute arbitrary code from the configured target and repository. Execute only when the user intends code execution and the project and configuration are trusted. Composition alone does not instantiate targets.

## Target mapping

A target mapping requires a nonempty `_target_` import path:

```yaml
service:
  _target_: package.module.Service
  _args_: [primary]
  timeout: 10
  _partial_: false
  _recursive_: true
```

- `_target_`: builtin or importable module attribute.
- `_args_`: optional positional sequence.
- `_partial_`: optional boolean; returns `functools.partial` when true.
- `_recursive_`: optional boolean, true by default.

All non-reserved keys become keyword arguments. Explicit Python method positional arguments replace `_args_`; explicit keyword arguments override configured values.

With recursive construction enabled, target-bearing child mappings in mappings and lists instantiate before their parent. With `_recursive_: false`, nested data is passed unchanged.

## Project-local imports

Construct `Cobruh` with the actual `project_root`. Cobruh temporarily prepends that root to `sys.path` only while resolving and constructing targets, then restores the original path.

## Debugging

Read the `TargetError` target and nested config path. Check, in order:

1. `_target_` spelling and importability from `project_root`;
2. reserved field types;
3. nested target paths;
4. configured versus explicit arguments;
5. constructor signature and the chained original exception.
