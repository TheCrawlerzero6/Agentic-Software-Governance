# MCP Cookbook

## Purpose

Use MCP tools as optional supporting evidence when already available.

## Procedure

1. Start with local repo evidence.
2. Use MCP only for a concrete gap: external docs, PR context, internal policy, architecture notes, or notebook/document sources.
3. Record MCP source/tool name, evidence summary, and target `governance/` file.
4. Treat MCP output as supporting evidence, not a replacement for local files.

## Examples

| Gap | MCP evidence | Register in |
|---|---|---|
| Missing architecture docs in repo | internal docs connector | `evidence/documentation.md` |
| PR rationale absent locally | GitHub MCP | `decisions.md` |
| Team policy affects agent rules | knowledge base MCP | `evidence/agents.md` |

## Limits

Do not configure MCP servers, authenticate services, or access private systems unless explicitly authorized.

## Continue

If no MCP exists, record nothing unless the user expected one. Continue with local evidence.

