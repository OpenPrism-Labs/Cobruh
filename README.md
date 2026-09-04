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
- Sequential, typed overrides
- Environment and config interpolation
- Recursive target construction
- Zero global configuration state

</td>
<td width="50%" valign="top">

### For your coding agent

- Discoverable MCP tools and resources
- Source provenance on every composition
- SHA-256 guarded writes
- Atomic config updates
- Bounded runtime results
- Portable skills for four agent platforms

</td>
</tr>
</table>

## Quick start

### 1. Install

Core Cobruh depends only on PyYAML:

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
| Include config | `base` | Root-relative, recursive composition |
| Position current file | `_self_` | Current source merges at that exact point |
| Select group | `model: resnet50` | Loads `model/resnet50.yaml` under `model` |
| Replace value | `model.layers=101` | Existing dotted path only |
| Add value | `+debug.enabled=true` | Missing path only |
| Select option | `model=vgg` | Existing config group only |
| Reference config | `${model.layers}` | Exact tokens preserve the value type |
| Read environment | `${env:NAME,default}` | Optional string fallback |

Mappings deep-merge. Lists and scalars replace. Defaults and overrides apply left to right. Interpolation runs last.

Cobruh intentionally does not emulate plugin systems, multirun, ConfigStore, structured dataclasses, output-directory management, optional/null defaults, or override-default syntax.

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
service = project.instantiate(config["service"])
```

Target-bearing children instantiate recursively. `_partial_: true` returns `functools.partial`; `_recursive_: false` passes nested mappings unchanged. Explicit method arguments override configured arguments.

Project-local imports work without permanently changing the process: Cobruh prepends `project_root` only during resolution and construction, then restores `sys.path`.

> [!CAUTION]
> Target instantiation executes configured Python code. Use it only with trusted configuration and explicit intent. The MCP runtime tool carries the same authority as its server process.

## Built for agentic configuration work

A coding agent should not guess which files exist, overwrite concurrent changes, or execute targets just to understand a config. Cobruh gives it a purpose-built local protocol:

```text
catalog → read + hash → write atomically → compose + verify → instantiate if intended
```

The MCP server exposes exactly five tools:

| Tool | Purpose |
|---|---|
| `list_configs` | Discover root configs, groups, and options |
| `read_config_source` | Read UTF-8 YAML with its SHA-256 |
| `write_config_source` | Create or hash-guardedly replace a source |
| `compose_config` | Return composed data and ordered provenance |
| `instantiate_config` | Execute an intended target and return a bounded result |

It also publishes `cobruh://catalog` and `cobruh://skills`, plus the `author_config` and `debug_config` prompts.

Source tools are rooted, extension-restricted, symlink-safe, size-bounded, mapping-validated, and atomic. Replacements require the current SHA-256. Stale writes fail before mutation.

## Connect your agent

Start the default stdio server with absolute paths:

```console
/absolute/project/.venv/bin/cobruh mcp \
  --root /absolute/project/configs \
  --project-root /absolute/project
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
cobruh catalog --root configs --project-root .
cobruh compose config --root configs --project-root . --set model=vgg optimizer.lr=0.01 --format json
cobruh compose config --root configs --no-resolve --format yaml
cobruh instantiate config --root configs --project-root . --node service
```

Machine output goes to stdout. Diagnostics go to stderr. Expected user and configuration failures return status 2. Runtime results include a fully qualified type, a `repr` bounded to 4096 characters, and a `value` only when JSON serialization succeeds.

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

A defaults entry is `_self_`, a root-relative config string, or a one-key group mapping:

```yaml
defaults:
  - base
  - _self_
  - model: resnet50
```

Entries compose left to right. `_self_` inserts the current source at that position; an omitted `_self_` means current-file-last. Group selections nest under their group key. Includes may define defaults recursively.

</details>

<details>
<summary><strong>Overrides and interpolation</strong></summary>

`path=value` replaces, `+path=value` creates, and `group=option` selects. Values use `yaml.safe_load`, and overrides are sequential.

Supported interpolation is `${path.to.value}`, `${env:NAME}`, and `${env:NAME,default}`. Exact config references preserve scalar, list, and mapping types; embedded expressions stringify. `compose(resolve=False)` leaves expressions unchanged. Missing values and cycles are errors with their full key chain.

</details>

<details>
<summary><strong>Target fields</strong></summary>

- `_target_`: required nonempty builtin or importable attribute
- `_args_`: optional positional sequence
- `_partial_`: optional boolean, false by default
- `_recursive_`: optional boolean, true by default

Reserved fields never reach the constructor. Explicit positional arguments replace `_args_`; explicit keywords override configured values. Resolution, signature, and construction failures raise `TargetError` with target and nested config paths while preserving the cause.

</details>

## Python API

Cobruh exports exactly six names:

```python
from cobruh import (
    Cobruh,
    CobruhError,
    ConfigError,
    OverrideError,
    TargetError,
    __version__,
)
```

`CobruhError` is the common base. `OverrideError` derives from `ConfigError`. `TargetError` covers target resolution and construction.

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
