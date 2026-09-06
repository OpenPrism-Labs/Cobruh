---
name: cobruh-mcp
description: Install, launch, register, inspect, and troubleshoot the Cobruh trusted local MCP server and bundled skills for Codex, Claude Code, GitHub Copilot, or Cursor.
license: MIT
---

# Cobruh MCP

Use this skill when connecting a coding agent to Cobruh or when its tools, resources, prompts, schemas, or target policy are unavailable.

## Install and launch

Install the optional SDK adapter:

```console
pip install 'cobruh[agentic]'
cobruh mcp \
  --root /absolute/project/configs \
  --project-root /absolute/project \
  --schema config=schema.json \
  --allow-target my_project.factories.*
```

`--schema NAME=PATH` and `--allow-target TARGET` are repeatable trusted-process settings. Target policy is never accepted from MCP calls or YAML. Omit all allow rules to deny every target.

The default transport is stdio. Configure the host with the absolute path to `cobruh` and absolute root arguments. The server must write no ordinary output before stdio starts.

Streamable HTTP is optional and loopback-only:

```console
cobruh mcp --root /absolute/project/configs --project-root /absolute/project \
  --allow-target my_project.factories.* \
  --transport streamable-http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`. Cobruh rejects non-loopback hosts because the server is unauthenticated and authorized runtime instantiation executes code.

## Discoverable surface

Tools:

- `list_configs`: config and option records with exact source and schema paths.
- `read_config_source`: UTF-8 YAML plus its SHA-256.
- `write_config_source`: atomic creation or hash-guarded replacement.
- `compose_config`: focused inspection metadata; `resolve` defaults to true and `node` is optional.
- `instantiate_config`: executes only targets allowed when the server process started.

Resources are `cobruh://catalog` and `cobruh://skills`. Prompts are `author_config` and `debug_config`. The five tool names remain fixed.

Prefer these tools over shell or direct edits. Catalog and read first. Supply the current SHA-256 for replacements. After writes, call `compose_config` and verify `data`, `sources`, `choices`, rebased leaf `provenance`, `types`, and `validation`. Instantiate only with explicit user intent; a tool call cannot widen the server allowlist.

## Install bundled skills

```console
cobruh skills list
cobruh skills install --agent codex --scope project --project /absolute/project
```

Agents are `codex`, `claude`, `copilot`, `cursor`, or `all`. Scope defaults to `project`. Repeat `--skill` to filter. Identical installations are no-ops; differing content fails unless `--force` is supplied.

If installation fails, check destination parent symlinks, permissions, conflicting content, selected skill names, and whether `--scope user` points at the intended home directory.
