#!/usr/bin/env bash
set -euo pipefail

IP="${KALI_OFFICIAL_BIND_IP:-0.0.0.0}"
PORT="${KALI_OFFICIAL_PORT:-5000}"

if command -v kali-server-mcp >/dev/null 2>&1; then
  exec kali-server-mcp --ip "$IP" --port "$PORT"
fi

if command -v kali_server.py >/dev/null 2>&1; then
  exec kali_server.py --ip "$IP" --port "$PORT"
fi

if [ -f /opt/mcp-kali-server/kali_server.py ]; then
  exec python3 /opt/mcp-kali-server/kali_server.py --ip "$IP" --port "$PORT"
fi

if [ -f /usr/share/mcp-kali-server/kali_server.py ]; then
  exec python3 /usr/share/mcp-kali-server/kali_server.py --ip "$IP" --port "$PORT"
fi

# Upstream (clonado por git) nombra el server 'server.py'.
for p in /opt/mcp-kali-server/server.py /usr/share/mcp-kali-server/server.py; do
  if [ -f "$p" ]; then
    exec python3 "$p" --ip "$IP" --port "$PORT"
  fi
done

echo "[ERROR] No se encontró el server MCP de Kali (kali-server-mcp / kali_server.py / server.py)." >&2
exit 1
