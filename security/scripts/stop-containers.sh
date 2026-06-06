#!/bin/bash
# Pentesting para Desarrolladores — detiene kali + browser (libera recursos).
# Se ejecuta al terminar una auditoría (auto-stop) o cuando el dev lo pide.
# NO detiene gateway ni mongodb: siguen corriendo para conservar tu historial.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE="$PROJECT_DIR/docker-compose.yml"

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "stop-containers: Docker no disponible, nada que detener." >&2
  exit 0
fi

if docker compose version >/dev/null 2>&1; then
  docker compose -f "$COMPOSE" stop kali browser 2>/dev/null
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f "$COMPOSE" stop kali browser 2>/dev/null
fi

# Fallback explícito por nombre.
docker stop pentesting-kali pentesting-browser >/dev/null 2>&1

echo "stop-containers: kali y browser detenidos (gateway y mongodb siguen activos)." >&2
exit 0
