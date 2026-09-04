# Cobruh

Cobruh composes ordinary Python mappings from a project-owned YAML tree. Version 0.2 uses one explicit `Cobruh` project object: no singleton state, decorator, config container, or compatibility layer.

Cobruh supports CPython 3.10, 3.11, 3.12, 3.13, and 3.14.

## Install

Core composition and runtime support require only PyYAML:

```console
pip install cobruh
```

Install the trusted local MCP adapter when a coding agent needs configuration authority:

```console
pip install 'cobruh[agentic]'
```

## Python API

The package exports exactly six names: `Cobruh`, `CobruhError`, `ConfigError`, `OverrideError`, `TargetError`, and `__version__`.

```python
from cobruh import Cobruh

project = Cobruh("configs", project_root=".")
print(project.catalog())
config = project.compose(
    "config",
    overrides=["model=vgg", "model.layers=19", "+run.debug=true"],
)
service = project.instantiate(config["service"])
```

Both roots resolve when `Cobruh` is constructed. `config_root` must be an existing directory contained by `project_root`; the project root defaults to the config root's parent. Every method is scoped to that object and keeps no process-global configuration state.

### YAML and defaults

Every source is a UTF-8 `.yaml` or `.yml` mapping of at most 1 MiB. An empty document means `{}`. Logical names may include or omit the extension. Traversal, source symlinks that escape the root, duplicate `.yaml`/`.yml` variants, malformed YAML, and non-mapping document roots are errors.

`defaults` accepts only three forms:

```yaml
defaults:
  - base
  - _self_
  - model: resnet50
```

- `_self_` inserts the current file at that position. If omitted, the current file composes last.
- A string includes a root-relative config.
- A one-key mapping selects `<group>/<option>.yaml` and nests it under the group key.

Entries compose left to right. Mappings deep-merge; lists and scalars replace. Includes may themselves have defaults. Missing sources and cycles report the include chain.

Cobruh deliberately does not implement optional or null defaults, override-default syntax, multirun, ConfigStore, structured dataclasses, output directories, or plugins.

### Overrides

Python, CLI, MCP, examples, and bundled skills share one sequential grammar:

- `path=value` replaces an existing dotted path.
- `+path=value` creates a missing path and fails if it already exists.
- `group=option` selects an option when `<config_root>/<group>` is a group directory.

Values use `yaml.safe_load`. Sequential application means `model=vgg` can be followed by `model.layers=19`. Unknown group options, invalid paths, missing replacement paths, and duplicate additions are errors.

### Interpolation

Interpolation runs after defaults and overrides:

- `${path.to.value}`
- `${env:NAME}`
- `${env:NAME,default}`

An exact reference token preserves a scalar, list, or mapping type. A token embedded in text stringifies its value. `compose(resolve=False)` leaves expressions unchanged. Missing values and interpolation cycles are errors with their key chain.

### Target runtime

A target mapping requires `_target_`. `_args_` is an optional sequence, `_partial_` an optional boolean, and `_recursive_` an optional boolean that defaults to true.

```yaml
service:
  _target_: my_project.service.Service
  _args_: [primary]
  timeout: 10
  client:
    _target_: my_project.client.Client
```

Target-bearing child mappings and lists instantiate recursively. `_recursive_: false` passes nested values unchanged. Explicit positional arguments to `instantiate()` replace `_args_`; explicit keywords override configured values. Project-local imports are available only during resolution and construction, and the original `sys.path` is restored afterward.

> **Trust boundary:** target instantiation imports Python and calls configured code. The MCP `instantiate_config` tool therefore permits arbitrary code execution with the server process's authority. Run it only for trusted local agents, trusted repositories, and an explicit user intent to execute the configured target.

## CLI

All machine results go to stdout; diagnostics go to stderr. Expected user and configuration errors exit with status 2.

```console
cobruh catalog --root configs --project-root .
cobruh compose config --root configs --project-root . --set model=vgg optimizer.lr=0.01 --format json
cobruh compose config --root configs --no-resolve --format yaml
cobruh instantiate config --root configs --project-root . --node service
```

Instantiation prints a bounded envelope containing the fully qualified result type, at most 4096 characters of `repr`, and `value` only when JSON serialization succeeds.

## Trusted local MCP server

The server exposes exactly:

- Tools: `list_configs`, `read_config_source`, `write_config_source`, `compose_config`, `instantiate_config`
- Resources: `cobruh://catalog`, `cobruh://skills`
- Prompts: `author_config`, `debug_config`

Source replacement is atomic and requires the SHA-256 returned by `read_config_source`; creation omits the hash. The server rejects absolute paths, traversal, non-YAML paths, symlinks, malformed/non-mapping YAML, stale hashes, and sources over 1 MiB.

Use absolute paths in host registration. These examples assume the executable is `/absolute/project/.venv/bin/cobruh`, the project is `/absolute/project`, and configs are `/absolute/project/configs`.

### Codex

```toml
[mcp_servers.cobruh]
command = "/absolute/project/.venv/bin/cobruh"
args = ["mcp", "--root", "/absolute/project/configs", "--project-root", "/absolute/project"]
```

### Claude Code

```console
claude mcp add cobruh -- /absolute/project/.venv/bin/cobruh mcp --root /absolute/project/configs --project-root /absolute/project
```

### Cursor

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

### VS Code / GitHub Copilot

Create `.vscode/mcp.json` without credentials:

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

### Streamable HTTP

```console
cobruh mcp --root /absolute/project/configs --project-root /absolute/project --transport streamable-http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`. Only loopback hosts are accepted; Cobruh refuses to expose this unauthenticated code-execution server on a network interface.

## Portable Agent Skills

Three skills ship inside the wheel: `cobruh-config`, `cobruh-runtime`, and `cobruh-mcp`.

```console
cobruh skills list
cobruh skills install --agent codex --scope project --project /absolute/project
cobruh skills install --agent all --scope user
cobruh skills install --agent cursor --skill cobruh-config --force
```

`--agent` is required and accepts `codex`, `claude`, `copilot`, `cursor`, or `all`. Project scope is the default. Destinations are:

| Agent | Project | User |
|---|---|---|
| Codex | `.agents/skills` | `~/.agents/skills` |
| Claude Code | `.claude/skills` | `~/.claude/skills` |
| GitHub Copilot | `.github/skills` | `~/.copilot/skills` |
| Cursor | `.cursor/skills` | `~/.cursor/skills` |

All three skills install unless repeated `--skill` options filter them. Identical content is a no-op. Differing content fails unless `--force` replaces only that named skill directory. Multi-agent installation preflights every destination and rolls back mutation failures.

## Development

```console
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -e '.[dev,agentic]'
.venv/bin/python -m pytest
.venv/bin/python -m ruff format --check src tests examples
.venv/bin/python -m ruff check src tests examples
.venv/bin/python -m mypy src/cobruh
```

The repository CI repeats behavior tests on CPython 3.10 through 3.14 and validates the built wheel outside the checkout.
