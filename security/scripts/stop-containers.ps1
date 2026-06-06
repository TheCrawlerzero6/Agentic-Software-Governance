# Pentesting para Desarrolladores — detiene kali + browser (Windows / PowerShell).
# gateway y mongodb siguen corriendo para conservar el historial.

$ProjectDir = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $ProjectDir "docker-compose.yml"

try { docker info | Out-Null } catch {
  Write-Error "stop-containers: Docker no disponible, nada que detener."; exit 0
}

docker compose -f $Compose stop kali browser 2>$null
docker stop pentesting-kali pentesting-browser 2>$null | Out-Null
Write-Error "stop-containers: kali y browser detenidos (gateway y mongodb siguen activos)."
exit 0
