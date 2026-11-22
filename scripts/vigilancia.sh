#!/usr/bin/env bash
# Vigilancia sintética: peticiones representativas contra una API en marcha, como las que haría
# un servicio de monitorización. El smoke prueba UN caso justo después de desplegar; la
# vigilancia recorre las tres prioridades y se repite cada hora contra producción.
#   bash scripts/vigilancia.sh http://127.0.0.1:8000 [informe.md]
# Escribe una tabla Markdown en la salida estándar (y en el informe, si se indica).
# Sale con 1 si alguna petición falla o no cumple el contrato.
set -euo pipefail

BASE="${1:?Uso: bash scripts/vigilancia.sh http://host:puerto [informe.md]}"
INFORME="${2:-/dev/null}"
respuesta="$(mktemp)"
trap 'rm -f "$respuesta"' EXIT

# Salud: reintenta mientras el contenedor termina de arrancar.
salud="$(curl --fail-with-body -sS --retry 20 --retry-all-errors --retry-delay 2 \
  --connect-timeout 5 --max-time 10 "$BASE/health")"
version="$(jq -r '.version' <<<"$salud")"

# Incidencias ficticias, una por prioridad (con las reglas de la demo: alta, media y baja).
casos=(
  "El servicio está caído para todos"
  "No puedo entrar en mi cuenta ficticia"
  "Tengo una duda sobre los horarios"
)

fallos=0
filas=()
for texto in "${casos[@]}"; do
  cuerpo="$(jq -nc --arg texto "$texto" '{texto: $texto}')"
  medida="$(curl -sS -o "$respuesta" -w '%{http_code} %{time_total}' --connect-timeout 5 \
    --max-time 40 -X POST "$BASE/clasificar" -H 'Content-Type: application/json' -d "$cuerpo")"
  estado="${medida%% *}"
  ms="$(awk -v s="${medida##* }" 'BEGIN { printf "%d", s * 1000 }')"
  request_id="$(jq -r '.request_id // "-"' "$respuesta" 2>/dev/null || echo "-")"
  if [[ "$estado" == "200" ]] && jq -e '
      (.resultado.categoria | IN("acceso", "facturacion", "tecnico", "consulta")) and
      (.resultado.prioridad | IN("alta", "media", "baja")) and
      (.resultado.respuesta | type == "string" and length > 0)' "$respuesta" >/dev/null 2>&1; then
    resultado="✅ $(jq -r '.resultado.categoria + " · " + .resultado.prioridad' "$respuesta")"
  else
    fallos=$((fallos + 1))
    resultado="❌ $(jq -r '.error // "fuera de contrato"' "$respuesta" 2>/dev/null || echo "no es JSON")"
    # GitHub muestra esta línea como anotación roja en la ejecución.
    echo "::error title=Vigilancia::«$texto» respondió HTTP $estado (request_id $request_id)"
  fi
  filas+=("| $texto | $estado | $resultado | $ms ms | \`$request_id\` |")
done

if ((fallos == 0)); then
  titular="✅ las ${#casos[@]} peticiones responden"
else
  titular="❌ fallan $fallos de ${#casos[@]} peticiones"
  ((fallos == 1)) && titular="❌ falla 1 de ${#casos[@]} peticiones"
fi
{
  echo "### Vigilancia · versión \`${version:0:12}\` · $titular"
  echo
  echo "| Petición (ficticia) | HTTP | Resultado | Tiempo | request_id |"
  echo "|---|---|---|---|---|"
  printf '%s\n' "${filas[@]}"
  echo
} | tee -a "$INFORME"

((fallos == 0))
