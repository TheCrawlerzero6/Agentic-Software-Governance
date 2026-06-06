# Docker Cookbook

## Purpose

Use Docker files as local configuration evidence without starting services.

## Safe Evidence

- `Dockerfile*`
- `compose*.yml`, `compose*.yaml`
- `docker-compose*.yml`, `docker-compose*.yaml`
- Existing docs that mention Docker

## Procedure

1. Read Docker/Compose files as text first.
2. If permissions are `herramientas` and user authorizes, run `docker compose config`.
3. Record service names, image/build context, ports, volumes, networks, env variable names, databases, queues, workers, and external dependencies.
4. Compare Docker configuration with README/docs when available.

## Register

- Runtime services and dependencies: `evidence/code.md` and `system-context.md`.
- Documentation mismatch: `evidence/documentation.md`.
- Decisions implied by platform/runtime: `decisions.md`.

## Limits

Do not start/stop services, delete volumes, run `prune`, `exec` into containers, or use `sudo`.

## Continue

If Docker is absent, record `no encontrado` and continue. Docker absence is not itself a risk unless docs/config imply it should exist.

