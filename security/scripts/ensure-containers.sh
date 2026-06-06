#!/bin/bash
# Pentesting para Desarrolladores — asegura que el entorno local esté arriba.
# Levanta los 4 contenedores (kali, browser, gateway, mongodb) con docker compose
# y espera a que kali + browser estén healthy.
#
# Salida:
#   exit 0  -> kali y browser healthy (listo para auditar)
#   exit 1  -> no se pudieron levantar (el flujo debe detenerse)
#
# Idempotente: si ya están healthy, retorna 0 de inmediato.
# La primera ejecución puede tardar (compila las imágenes de kali/browser).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE="$PROJECT_DIR/docker-compose.yml"

_health() { docker inspect --format '{{.State.Health.Status}}' "$1" 2>/dev/null; }

# 0: ¿ya están healthy?
if [ "$(_health pentesting-kali)" = "healthy" ] && [ "$(_health pentesting-browser)" = "healthy" ]; then
  echo "ensure-containers: kali y browser ya están healthy" >&2
  exit 0
fi

# 1: Docker instalado
if ! command -v docker >/dev/null 2>&1; then
  echo "ensure-containers: Docker no está instalado. Instala Docker Desktop y reintenta." >&2
  exit 1
fi

# 2: Docker corriendo
if ! docker info >/dev/null 2>&1; then
  echo "ensure-containers: Docker no está corriendo. Inícialo (Docker Desktop) y reintenta." >&2
  exit 1
fi

# 3: docker compose disponible
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "ensure-containers: ni 'docker compose' ni 'docker-compose' disponibles" >&2
  exit 1
fi

# 4: Levantar el stack (compila si hace falta la primera vez)
echo "ensure-containers: levantando el entorno (docker compose up -d)..." >&2
$DC -f "$COMPOSE" up -d 2>&1 | tail -20 >&2 || { echo "ensure-containers: 'up -d' falló" >&2; exit 1; }

# 5: Esperar healthcheck de kali + browser (max ~120s)
for i in $(seq 1 24); do
  sleep 5
  if [ "$(_health pentesting-kali)" = "healthy" ] && [ "$(_health pentesting-browser)" = "healthy" ]; then
    echo "ensure-containers: kali y browser healthy" >&2
    exit 0
  fi
done

echo "ensure-containers: no llegaron a healthy a tiempo. kali=$(_health pentesting-kali) browser=$(_health pentesting-browser)" >&2
echo "ensure-containers: revisa 'docker compose logs kali browser'." >&2
exit 1
