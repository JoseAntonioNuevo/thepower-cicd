#!/usr/bin/env bash
# Los seis checks de la PR, en local y sobre la rama en la que estés: lo mismo que hará GitHub.
# No se para en el primer fallo: termina con un resumen de qué pasaría en la PR.
#
#   bash scripts/comprobar.sh            # los seis (≈40 s; Imagen necesita Docker)
#   bash scripts/comprobar.sh --rapido   # solo Calidad, Tests y Evaluación (≈5 s)
#
# Diferencias con GitHub: la evaluación usa siempre las reglas de la demo (gratis), zizmor se
# ejecuta sin red y la revisión de dependencias de la PR (dependency-review) solo existe allí.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1
# Para contar caracteres y no bytes al alinear («Evaluación» lleva tilde).
[[ "$(locale charmap 2>/dev/null)" == UTF-8 ]] || export LC_ALL=en_US.UTF-8

rapido=0
case "${1:-}" in
    "") ;;
    --rapido) rapido=1 ;;
    *) echo "Uso: bash scripts/comprobar.sh [--rapido]" >&2; exit 2 ;;
esac

VERDE=$'\e[32m'; ROJO=$'\e[31m'; GRIS=$'\e[90m'; NEGRITA=$'\e[1m'; NORMAL=$'\e[0m'
if [[ ! -t 1 ]]; then VERDE=""; ROJO=""; GRIS=""; NEGRITA=""; NORMAL=""; fi

COMMIT="$(git rev-parse HEAD)"
TMP="$(mktemp -d)"
CONTENEDOR="api-comprobar-$$"
# Al salir, pase lo que pase: sin contenedor de prueba ni archivos temporales.
trap 'docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT

rojos=()
omitidos=()
n=0

# resultado NOMBRE ESTADO(ok|fallo|omitido) RESUMEN SEGUNDOS [ARCHIVO-CON-DETALLE]
resultado() {
    local nombre="$1" estado="$2" resumen="$3" segundos="$4" detalle="${5:-}" relleno
    n=$((n + 1))
    printf -v relleno '%*s' $((13 - ${#nombre})) ''   # por caracteres: «Evaluación» lleva tilde
    case "$estado" in
        ok) printf '%s %b✓%b  %s %s %b(%s s)%b\n' "$n/6" "$VERDE" "$NORMAL" "$nombre$relleno" "$resumen" "$GRIS" "$segundos" "$NORMAL" ;;
        fallo)
            printf '%s %b✗  %s %s%b %b(%s s)%b\n' "$n/6" "$ROJO$NEGRITA" "$nombre$relleno" "$resumen" "$NORMAL" "$GRIS" "$segundos" "$NORMAL"
            rojos+=("$nombre")
            if [[ -n "$detalle" && -s "$detalle" ]]; then
                sed -n '1,8p' "$detalle" | sed "s/^/       ${ROJO}│${NORMAL} /"
            fi
            ;;
        omitido)
            printf '%s %b–  %s %s%b\n' "$n/6" "$GRIS" "$nombre$relleno" "$resumen" "$NORMAL"
            omitidos+=("$nombre")
            ;;
    esac
}

RAMA="$(git branch --show-current)"
echo "${NEGRITA}Checks de la PR, en local${NORMAL} · rama ${RAMA:-(ninguna)} · commit ${COMMIT:0:7}"
echo

# 1 · Calidad: el lock de Docker sale del de uv, ruff y formato.
t0=$SECONDS
: >"$TMP/calidad"
uv export --locked --no-dev --no-emit-project --no-header --format requirements-txt 2>/dev/null \
    | diff -u requirements.lock - >/dev/null || echo "requirements.lock no coincide con uv.lock" >>"$TMP/calidad"
uv run --locked ruff check --output-format=concise . 2>/dev/null | grep -E '^[^ ].*:[0-9]+:[0-9]+:' >>"$TMP/calidad"
uv run --locked ruff format --check . 2>/dev/null | grep '^Would reformat' >>"$TMP/calidad"
if [[ -s "$TMP/calidad" ]]; then
    resultado Calidad fallo "lock, ruff y formato" $((SECONDS - t0)) "$TMP/calidad"
else
    resultado Calidad ok "lock, ruff y formato" $((SECONDS - t0))
fi

# 2 · Tests: sin red ni claves, con la cobertura mínima de la PR.
t0=$SECONDS
uv run --locked pytest -q -p no:cacheprovider --cov --cov-fail-under=90 >"$TMP/tests.log" 2>&1
estado=$?
linea="$(grep -E '^(=+ )?[0-9]+ (passed|failed)' "$TMP/tests.log" | tail -n 1 | sed -E 's/^=+ //; s/ in [0-9.]+s.*//')"
cobertura="$(awk '/^TOTAL/ {print $NF}' "$TMP/tests.log")"
if [[ $estado -eq 0 ]]; then
    resultado Tests ok "$linea · cobertura $cobertura" $((SECONDS - t0))
else
    grep -E '^FAILED|not reached' "$TMP/tests.log" | sed 's/ - .*//' >"$TMP/tests"
    resultado Tests fallo "${linea:-error al ejecutar pytest}" $((SECONDS - t0)) "$TMP/tests"
fi

# 3 · Evaluación: las 12 incidencias ficticias con un umbral del 80 %. En local, siempre las reglas.
t0=$SECONDS
env -u OPENROUTER_API_KEY uv run --locked python -m evaluacion.evaluar --umbral 0.8 >"$TMP/eval.log" 2>&1
estado=$?
linea="$(head -n 1 "$TMP/eval.log" | sed 's/^### Evaluación del clasificador · //; s/^[^0-9]*//')"
if [[ $estado -eq 0 ]]; then
    resultado Evaluación ok "$linea" $((SECONDS - t0))
else
    grep -E '❌' "$TMP/eval.log" >"$TMP/eval"
    resultado Evaluación fallo "${linea:-error al evaluar}" $((SECONDS - t0)) "$TMP/eval"
fi

if [[ $rapido -eq 1 ]]; then
    resultado Imagen omitido "(--rapido)" 0
    resultado Dependencias omitido "(--rapido)" 0
    resultado Workflows omitido "(--rapido)" 0
else
    # 4 · Imagen: se construye, arranca endurecida y pasa el smoke con su versión.
    t0=$SECONDS
    if ! docker info >/dev/null 2>&1; then
        resultado Imagen omitido "Docker no está arrancado" 0
    elif docker build -q --provenance=false --build-arg "APP_VERSION=$COMMIT" -t api:comprobacion . >"$TMP/imagen" 2>&1 \
        && docker run --rm -d --name "$CONTENEDOR" --read-only --cap-drop ALL \
            -p 127.0.0.1:8765:8000 api:comprobacion >>"$TMP/imagen" 2>&1 \
        && bash scripts/smoke.sh http://127.0.0.1:8765 "$COMMIT" >>"$TMP/imagen" 2>&1; then
        resultado Imagen ok "build, contenedor endurecido y smoke" $((SECONDS - t0))
    else
        tail -n 6 "$TMP/imagen" >"$TMP/imagen.fallo"
        resultado Imagen fallo "build, contenedor o smoke" $((SECONDS - t0)) "$TMP/imagen.fallo"
    fi
    docker rm -f "$CONTENEDOR" >/dev/null 2>&1 || true

    # 5 · Dependencias: vulnerabilidades conocidas en lo que va dentro de la imagen.
    t0=$SECONDS
    if uvx -q pip-audit==2.10.1 --requirement requirements.lock --require-hashes --disable-pip \
        --progress-spinner off >"$TMP/deps" 2>&1; then
        resultado Dependencias ok "pip-audit sin vulnerabilidades" $((SECONDS - t0))
    else
        resultado Dependencias fallo "pip-audit" $((SECONDS - t0)) "$TMP/deps"
    fi

    # 6 · Workflows: el pipeline también es código.
    t0=$SECONDS
    : >"$TMP/workflows"
    uvx -q --from actionlint-py==1.7.12.24 actionlint >>"$TMP/workflows" 2>&1 || echo "(actionlint)" >>"$TMP/workflows"
    uvx -q zizmor==1.33.1 --offline --quiet .github/workflows >"$TMP/zizmor" 2>&1 \
        || { cat "$TMP/zizmor"; echo "(zizmor)"; } >>"$TMP/workflows"
    if command -v shellcheck >/dev/null; then
        shellcheck scripts/*.sh >>"$TMP/workflows" 2>&1 || echo "(shellcheck)" >>"$TMP/workflows"
    fi
    if [[ -s "$TMP/workflows" ]]; then
        resultado Workflows fallo "actionlint, zizmor y shellcheck" $((SECONDS - t0)) "$TMP/workflows"
    else
        resultado Workflows ok "actionlint, zizmor y shellcheck" $((SECONDS - t0))
    fi
fi

echo
if [[ ${#rojos[@]} -eq 0 ]]; then
    hechos=$((6 - ${#omitidos[@]}))
    echo "${VERDE}${NEGRITA}✅ ${hechos}/${hechos} en verde${NORMAL}: la PR debería pasar sus checks."
    exit 0
fi
lista="$(printf '%s, ' "${rojos[@]}")"
lista="${lista%, }"
echo "${ROJO}${NEGRITA}❌ ${#rojos[@]} en rojo (${lista})${NORMAL}: en la PR, esos checks fallarán y el merge quedará bloqueado."
exit 1
