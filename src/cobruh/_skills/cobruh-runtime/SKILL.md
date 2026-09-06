---
name: cobruh-runtime
description: Build, authorize, instantiate, and debug Cobruh _target_ runtime mappings, including positional arguments, partials, recursive construction, project-local imports, and target allowlists.
license: MIT
---

# Cobruh target runtime

Use this skill for configuration that imports or constructs Python targets. Prefer `instantiate_config` through the Cobruh MCP server when available. Otherwise use `cobruh instantiate <name> --node <path> --root <configs> --project-root <project> --allow-target <target>` or `Cobruh.instantiate()`.

## Trust boundary

Instantiation is deny-by-default. It imports Python and calls constructors or functions only when every configured and canonical target identity matches a trusted-process allowlist. Composition and inspection never instantiate targets.

Configure policy in Python:

```python
project = Cobruh(
    "configs",
    project_root=".",
    allowed_targets=(
        "builtins.dict",
        "my_project.factories.*",
    ),
)
```

Or repeat `--allow-target TARGET` on CLI `instantiate` and `mcp`. Rules are exact fully qualified targets or prefixes ending in `.*`; empty rules and bare `*` are rejected. Short configured builtins such as `dict` normalize to `builtins.dict`. Cobruh checks the configured identity before import, then the callable's `__module__.__qualname__` before invocation, so denied modules are not imported and re-exports cannot bypass policy. MCP calls and YAML cannot change the allowlist.

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

All non-reserved keys become keyword arguments. Explicit Python positional arguments replace `_args_`; explicit keywords override configured values. With recursion enabled, target-bearing children in mappings, lists, and tuples use the same allowlist before their parent is invoked. `_recursive_: false` passes nested data unchanged.

## Project-local imports

Use the actual `project_root`. Cobruh temporarily prepends it to `sys.path` only while resolving and constructing targets, then restores the original path.

## Debugging

Read the `TargetError` target and nested config path. Check, in order:

1. configured and canonical names against the process allowlist;
2. `_target_` spelling and importability from `project_root`;
3. reserved field types;
4. nested target paths and their authorization;
5. configured versus explicit arguments;
6. constructor signature and the chained original exception.
