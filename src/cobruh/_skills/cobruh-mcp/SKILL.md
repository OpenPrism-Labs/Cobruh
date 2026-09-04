---
name: cobruh-mcp
description: Install, launch, register, discover, and troubleshoot the Cobruh trusted local MCP server and bundled skills for Codex, Claude Code, GitHub Copilot, or Cursor.
license: MIT
---

# Cobruh MCP

Use this skill when connecting a coding agent to Cobruh or when its tools, resources, prompts, or bundled skills are unavailable.

## Install and launch

Install the optional SDK adapter:

```console
pip install 'cobruh[agentic]'
cobruh mcp --root /absolute/project/configs --project-root /absolute/project
```

The default transport is stdio. Configure the host with the absolute path to the `cobruh` executable and absolute root arguments. The server must write no ordinary output before the stdio transport starts.

Streamable HTTP is optional and loopback-only:

```console
cobruh mcp --root /absolute/project/configs --project-root /absolute/project --transport streamable-http --host 127.0.0.1 --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`. Cobruh rejects non-loopback hosts because the server is unauthenticated and runtime instantiation executes code.

## Discoverable surface

Tools:

- `list_configs`
- `read_config_source`
- `write_config_source`
- `compose_config`
- `instantiate_config`

Resources:

- `cobruh://catalog`
- `cobruh://skills`

Prompts:

- `author_config`
- `debug_config`

Prefer these MCP tools over shell or direct file edits. Catalog and read first. Supply the current SHA-256 for replacements, compose after writes, and instantiate only when the user intends trusted repository code to execute. If MCP is unavailable, fall back to `cobruh catalog`, `cobruh compose`, and `cobruh instantiate`.

## Install bundled skills

List and install:

```console
cobruh skills list
cobruh skills install --agent codex --scope project --project /absolute/project
```

Agents are `codex`, `claude`, `copilot`, `cursor`, or `all`. Scope defaults to `project`. Use repeated `--skill` options to filter. Identical installations are no-ops; differing content fails unless `--force` is supplied.

If installation fails, check destination parent symlinks, file permissions, conflicting content, the selected skill name, and whether `--scope user` points at the intended home directory.
