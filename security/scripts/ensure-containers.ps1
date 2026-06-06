# Pentesting para Desarrolladores — asegura el entorno local (Windows / PowerShell).
# Levanta los 4 contenedores y espera a que kali + browser estén healthy.
# Salida: exit 0 listo · exit 1 no se pudo.

$ProjectDir = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $ProjectDir "docker-compose.yml"

function Get-Health($name) {
  try { docker inspect --format '{{.State.Health.Status}}' $name 2>$null } catch { "" }
}

if ((Get-Health "pentesting-kali") -eq "healthy" -and (Get-Health "pentesting-browser") -eq "healthy") {
  Write-Error "ensure-containers: kali y browser ya están healthy"; exit 0
}

try { docker info | Out-Null } catch {
  Write-Error "ensure-containers: Docker no está corriendo. Inícialo (Docker Desktop) y reintenta."; exit 1
}

Write-Error "ensure-containers: levantando el entorno (docker compose up -d)..."
docker compose -f $Compose up -d
if (-not $?) { Write-Error "ensure-containers: 'up -d' falló"; exit 1 }

for ($i = 0; $i -lt 24; $i++) {
  Start-Sleep -Seconds 5
  if ((Get-Health "pentesting-kali") -eq "healthy" -and (Get-Health "pentesting-browser") -eq "healthy") {
    Write-Error "ensure-containers: kali y browser healthy"; exit 0
  }
}
Write-Error "ensure-containers: no llegaron a healthy a tiempo. Revisa 'docker compose logs kali browser'."
exit 1
