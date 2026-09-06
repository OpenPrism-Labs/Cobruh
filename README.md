<div align="center">

# Cobruh

### Configuration that coding agents can actually operate.

Compose project-owned YAML into plain Python. Run configured targets. Give trusted local agents a safe, inspectable interface through MCP.

[![CI](https://github.com/OpenPrism-Labs/Cobruh/actions/workflows/ci.yml/badge.svg)](https://github.com/OpenPrism-Labs/Cobruh/actions/workflows/ci.yml)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-111111.svg)](LICENSE)

[Quick start](#quick-start) · [Agent setup](#connect-your-agent) · [Configuration reference](#configuration-reference) · [Python API](#python-api)

</div>

---

Cobruh is a small configuration runtime for modern Python projects. One explicit project object owns one configuration tree. The same composition rules power Python, the CLI, MCP tools, examples, and portable Agent Skills.

No singleton state. No custom config containers. No generated working directories. No hidden execution context.

```python
from cobruh import Cobruh

project = Cobruh("configs", project_root=".")
config = project.compose("config", overrides=["model=vgg", "optimizer.lr=0.01"])
```

## One configuration system. Two first-class users.

<table>
<tr>
<td width="50%" valign="top">

### For your application

- Deterministic YAML composition
- Ordinary Python dictionaries
- Two-stage typed overrides
- Environment and config interpolation
- Recursive allowlisted target construction
- Zero global configuration state

</td>
<td width="50%" valign="top">

### For your coding agent

- Discoverable MCP tools and resources
- Ordered choices and leaf provenance
- Draft 2020-12 schema validation and type metadata
- Atomic config updates
- Bounded runtime results
- Portable skills for four agent platforms

</td>
</tr>
</table>

## Quick start

### 1. Install

Core Cobruh depends on PyYAML and `jsonschema`:

```console
pip install cobruh
```

For the trusted local MCP server:

```console
pip install 'cobruh[agentic]'
```

Cobruh supports CPython 3.10 through 3.14.

### 2. Own your configuration

```text
configs/
├── config.yaml
├── model/
│   ├── resnet50.yaml
│   └── vgg.yaml
└── optimizer/
    └── adam.yaml
```

```yaml
# configs/config.yaml
defaults:
  - model: resnet50
  - optimizer: adam

batch_size: 32
run_name: ${model.name}-${batch_size}
```

```yaml
# configs/model/resnet50.yaml
name: resnet
layers: 50
```

```yaml
# configs/model/vgg.yaml
name: vgg
layers: 16
```

```yaml
# configs/optimizer/adam.yaml
name: adam
lr: 0.001
```

### 3. Compose from Python

```python
from cobruh import Cobruh

project = Cobruh("configs", project_root=".")

config = project.compose(
    "config",
    overrides=[
        "model=vgg",
        "model.layers=19",
        "optimizer.lr=0.01",
        "+debug.enabled=true",
    ],
)

assert config["model"] == {"name": "vgg", "layers": 19}
assert config["optimizer"]["lr"] == 0.01
assert config["debug"] == {"enabled": True}
assert config["run_name"] == "vgg-32"
```

That is the entire runtime model: an explicit project in, a plain mapping out.

## A deliberately small language

Cobruh keeps the useful parts of hierarchical configuration and rejects the ambient machinery.

| Capability | Syntax | Contract |
|---|---|---|
| Relative or root include | `base`, `/base` | Relative to the containing source, or `config_root` with `/` |
| Position current file | `_self_` | Current source merges at that exact point |
| Select group | `model: resnet50` | Relative group selection with an ordered choice record |
| Optional placeholder | `optional cache: null` | Records an optional selection without loading a source |
| Replace selection | `override model: large` | Removes the old option and every nested layer it owned |
| Relocate selection | `model@primary: small` | Uses a dotted package; also supports `_here_`, `_group_`, `_global_` |
| Replace/add/set value | `x=1`, `+x=1`, `++x=1` | Existing only, missing only, or either |
| Delete value/group | `~x`, `~x=1`, `~model` | Delete, conditionally delete, or remove a selected group |
| Reference config | `${model.layers}` | Exact tokens preserve the value type |
| Read environment | `${env:NAME,default}` | Optional string fallback |

Mappings deep-merge. Lists and scalars replace. Defaults/group operations establish the source tree first; dotted mutations then apply left to right; interpolation runs last.

| Area | Cobruh and Hydra | Deliberately Hydra-only |
|---|---|---|
| Composition | Hierarchical defaults, `_self_`, relative/absolute groups, packages, optional/null/override entries | Config search paths, ConfigStore, structured dataclasses, OmegaConf containers and custom resolvers |
| Overrides | Group selection plus typed replace/add/set/delete mutations | Sweeps, override functions, multirun grammar |
| Inspection | Choices, sources, leaf provenance, schema types, validation | Hydra app help and shell tab completion |
| Execution | Recursive target construction with an explicit allowlist | Decorators, launchers, sweepers, plugins, callbacks, rerun |
| Runtime | Explicit object, plain dictionaries, no composition side effects | Automatic run directories, logging setup, job lifecycle |

## Targets without magic context

Cobruh can turn a mapping into a Python object:

```yaml
service:
  _target_: my_project.service.Service
  _args_: [primary]
  timeout: 10
  client:
    _target_: my_project.client.Client
```

```python
runtime = Cobruh(
    "configs",
    project_root=".",
    allowed_targets=(
        "my_project.service.Service",
        "my_project.client.Client",
    ),
)
service = runtime.instantiate(config["service"])
```

Target-bearing children instantiate recursively. `_partial_: true` returns `functools.partial`; `_recursive_: false` passes nested mappings unchanged. Explicit method arguments override configured arguments.

Project-local imports work without permanently changing the process: Cobruh prepends `project_root` only during resolution and construction, then restores `sys.path`.

> [!CAUTION]
> Instantiation is deny-by-default. Allow exact fully qualified targets or prefixes ending in `.*` through `allowed_targets` or trusted CLI process options. Cobruh checks the configured name before import and the callable's canonical identity before invocation; MCP calls and YAML cannot widen policy.

## Native experiment tracking

Cobruh passes composed configurations into W&B and Aim and returns each tracker's native run object. Install either integration or both:

```console
pip install 'cobruh[wandb]'
pip install 'cobruh[aim]'
pip install 'cobruh[tracking]'
```

W&B supports Cobruh's full CPython 3.10–3.14 range. Aim 3.29's required `aimrocks` package publishes wheels through CPython 3.12, so the `aim` dependency is installed only on CPython 3.10–3.12; `init_aim` reports this limitation explicitly on newer interpreters.

### Weights & Biases

```python
from cobruh import Cobruh, init_wandb

config = Cobruh("configs", project_root=".").compose(
    overrides=["model=vgg", "optimizer.lr=0.01"],
)

with init_wandb(config, project="image-classification") as run:
    run.log({"train/loss": 0.42, "epoch": 1})
```

`init_wandb` forwards every keyword argument to `wandb.init(config=...)`. Offline mode, run IDs, resuming, grouping, tags, and native logging therefore work without a second Cobruh abstraction.

### Aim

```python
from cobruh import Cobruh, init_aim

config = Cobruh("configs", project_root=".").compose(
    overrides=["model=vgg", "optimizer.lr=0.01"],
)

run = init_aim(config, repo=".aim", experiment="image-classification")
try:
    run.track(0.42, name="loss", step=1, context={"subset": "train"})
finally:
    run.close()
```

`init_aim` stores the composed configuration under Aim's conventional `hparams` key and forwards every other keyword argument to `aim.Run`. Use `config_key="config"` to choose another metadata key. The returned object is the native Aim `Run`.

## Built for agentic configuration work

A coding agent should not guess which files exist, overwrite concurrent changes, import targets just to understand configuration, or infer where a value came from. Cobruh gives it a purpose-built local protocol:

```text
catalog → read + hash → write atomically → inspect + validate → instantiate if authorized
```

The MCP server exposes exactly five tools:

| Tool | Purpose |
|---|---|
| `list_configs` | Discover config and option records with exact YAML and schema paths |
| `read_config_source` | Read UTF-8 YAML with its SHA-256 |
| `write_config_source` | Create or hash-guardedly replace a source |
| `compose_config` | Return focused data, choices, provenance, types, and validation |
| `instantiate_config` | Execute an allowed target and return a bounded result |

It also publishes `cobruh://catalog` and `cobruh://skills`, plus the `author_config` and `debug_config` prompts.

Source tools are rooted, extension-restricted, symlink-safe, size-bounded, mapping-validated, and atomic. Replacements require the current SHA-256. Stale writes fail before mutation.

## Connect your agent

Start the default stdio server with absolute paths and an explicit execution policy:

```console
/absolute/project/.venv/bin/cobruh mcp \
  --root /absolute/project/configs \
  --project-root /absolute/project \
  --schema config=schema.json \
  --allow-target my_project.factories.*
```

<details>
<summary><strong>Codex</strong></summary>

```toml
[mcp_servers.cobruh]
command = "/absolute/project/.venv/bin/cobruh"
args = ["mcp", "--root", "/absolute/project/configs", "--project-root", "/absolute/project"]
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

```console
claude mcp add cobruh -- /absolute/project/.venv/bin/cobruh mcp --root /absolute/project/configs --project-root /absolute/project
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

Create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cobruh": {
      "command": "/absolute/project/.venv/bin/cobruh",
      "args": ["mcp", "--root", "/absolute/project/configs", "--project-root", "/absolute/project"]
    }
  }
}
```

</details>

<details>
<summary><strong>VS Code / GitHub Copilot</strong></summary>

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "cobruh": {
      "type": "stdio",
      "command": "/absolute/project/.venv/bin/cobruh",
      "args": ["mcp", "--root", "/absolute/project/configs", "--project-root", "/absolute/project"]
    }
  }
}
```

</details>

### Loopback HTTP

Streamable HTTP is available for local integrations:

```console
cobruh mcp \
  --root /absolute/project/configs \
  --project-root /absolute/project \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000
```

Endpoint: `http://127.0.0.1:8000/mcp`. Non-loopback hosts are rejected rather than exposing an unauthenticated code-execution server.

## Skills included

Cobruh ships with three portable Agent Skills:

| Skill | Activates for |
|---|---|
| `cobruh-config` | Authoring, defaults, overrides, interpolation, and verification |
| `cobruh-runtime` | Target mappings, recursive construction, and execution safety |
| `cobruh-mcp` | MCP registration, discovery, installation, and troubleshooting |

Install them without copying files by hand:

```console
cobruh skills list
cobruh skills install --agent codex --project /absolute/project
cobruh skills install --agent all --scope user
cobruh skills install --agent cursor --skill cobruh-config --force
```

| Agent | Project | User |
|---|---|---|
| Codex | `.agents/skills` | `~/.agents/skills` |
| Claude Code | `.claude/skills` | `~/.claude/skills` |
| GitHub Copilot | `.github/skills` | `~/.copilot/skills` |
| Cursor | `.cursor/skills` | `~/.cursor/skills` |

`--agent` is required. Project scope is the default. Installs are preflighted across every requested target; identical content is a no-op, conflicts require `--force`, and mutation failures roll back.

## CLI

The CLI is the same project API exposed for scripts and humans:

```console
cobruh catalog --root configs --project-root . --schema config=schema.json
cobruh compose config --root configs --project-root . --set model=vgg optimizer.lr=0.01 --format json
cobruh inspect config --root configs --project-root . --schema config=schema.json --node model
cobruh compose config --root configs --no-resolve --format yaml
cobruh instantiate config --root configs --project-root . --allow-target my_project.Service --node service
```

Repeat `--schema NAME=PATH` on any project command. Repeat `--allow-target TARGET` only on trusted `instantiate` and `mcp` processes. Machine output goes to stdout. Diagnostics go to stderr. Expected user and configuration failures return status 2. Runtime results include a fully qualified type, a `repr` bounded to 4096 characters, and a `value` only when JSON serialization succeeds.

## Configuration reference

<details>
<summary><strong>Source and project invariants</strong></summary>

- `Cobruh(config_root, project_root=...)` resolves both paths immediately.
- `config_root` must be an existing directory contained by `project_root`.
- `project_root` defaults to `config_root.parent`.
- Sources must be UTF-8 `.yaml` or `.yml` mappings no larger than 1 MiB.
- Empty YAML documents compose as `{}`.
- Logical names may include or omit their extension.
- Traversal, symlink escape, duplicate extension variants, malformed YAML, non-mapping roots, missing includes, and cycles raise `ConfigError`.
- Catalog data and source provenance are deterministic.

</details>

<details>
<summary><strong>Defaults</strong></summary>

Defaults accept `_self_`; relative or `/` root config includes; and one-key `group`, `optional group`, or `override group` mappings. Options may be strings, null placeholders, or lists merged left to right:

```yaml
defaults:
  - /base
  - model@primary: small
  - augment: [crop, flip]
  - optional cache: null
  - override model@primary: large
  - _self_
```

Unprefixed includes and groups resolve relative to the containing source directory. `_self_` inserts that source at its listed position; omission means current-file-last. The default destination follows the selected group. `@package` relocates content; `_here_`, `_group_`, and `_global_` select the containing, absolute-group, or root package. Packages exist only in defaults entries—YAML comment directives are not interpreted.

</details>

<details>
<summary><strong>Overrides and interpolation</strong></summary>

`path=value` replaces an existing path; `+path=value` adds a missing path; `++path=value` creates or replaces; `~path` deletes; and `~path=value` deletes only on equality. `group=option`, `+group=option`, and `~group` replace, add, or remove source selections, with optional `group@package`. An empty right-hand side is the empty string. Comma-separated group choices and override functions require Hydra.

All group operations run before dotted value mutations, which then run left to right. Supported interpolation is `${path.to.value}`, `${env:NAME}`, and `${env:NAME,default}`. Exact config references preserve scalar, list, and mapping types; embedded expressions stringify. `resolve=False` leaves expressions unchanged and skips schema validation.

</details>

<details>
<summary><strong>Schemas and inspection</strong></summary>

Register schemas with `Cobruh(..., schemas={"config": "schema.json"})` or CLI `--schema NAME=PATH`. Cobruh accepts Draft 2020-12 mapping schemas from memory or project-contained UTF-8 `.json` files up to 1 MiB. Only local `#...` references are allowed. Resolved compositions validate automatically with deterministic RFC 6901 instance and schema pointers.

`Cobruh.inspect(name, overrides=(), resolve=True, node="")` returns exactly `name`, `node`, `data`, `sources`, `choices`, `provenance`, `types`, and `validation`. Focused inspection accepts scalar, list, or mapping values and rebases provenance and type pointers to `""`. `catalog()` returns config/option records with `name`, exact `path`, and schema source.

</details>

<details>
<summary><strong>Target fields</strong></summary>

- `_target_`: required nonempty builtin or importable attribute
- `_args_`: optional positional sequence
- `_partial_`: optional boolean, false by default
- `_recursive_`: optional boolean, true by default

`allowed_targets` defaults to empty. Rules are exact fully qualified targets or prefixes ending in `.*`; empty entries and bare `*` are invalid. Short configured builtins normalize to `builtins.<name>`. Both the configured and resolved canonical identities must match policy. Reserved fields never reach the constructor. Explicit positional arguments replace `_args_`; explicit keywords override configured values.

</details>

## Python API

Cobruh exports exactly nine names:

```python
from cobruh import (
    Cobruh,
    CobruhError,
    ConfigError,
    IntegrationError,
    OverrideError,
    TargetError,
    init_aim,
    init_wandb,
    __version__,
)
```

`CobruhError` is the common base. `OverrideError` derives from `ConfigError`. `TargetError` covers target resolution and construction. `IntegrationError` covers invalid tracking input and missing optional tracker dependencies; errors raised by an installed tracker remain native.

## Development

```console
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -e '.[dev,agentic]'
.venv/bin/python -m pytest
.venv/bin/python -m ruff format --check src tests examples
.venv/bin/python -m ruff check src tests examples
.venv/bin/python -m mypy src/cobruh
```

CI runs behavior tests on CPython 3.10 through 3.14 and separately builds and exercises the installed wheel outside the checkout.

## License

Cobruh is available under the [MIT License](LICENSE).
