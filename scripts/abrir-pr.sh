#!/usr/bin/env bash
# Las dos PR de la demo: un cambio correcto y otro incorrecto, cada uno en su rama.
#
#   bash scripts/abrir-pr.sh preparar     # antes de clase: crea y sube las dos ramas desde main
#   bash scripts/abrir-pr.sh correcto     # PR de plazo-de-atencion: los seis checks en verde
#   bash scripts/abrir-pr.sh incorrecto   # PR de respuesta-por-defecto: Calidad y Tests en rojo
#   bash scripts/abrir-pr.sh cerrar       # cierra las PR de la demo abiertas (las ramas se quedan)
#   bash scripts/abrir-pr.sh cerrar incorrecto   # solo la del cambio incorrecto
#
# En clase, para cada rama: git switch <rama> → bash scripts/comprobar.sh → abrir su PR.
# Con SIN_NAVEGADOR=1 no abre la PR en el navegador.
set -euo pipefail

uso() {
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
}

fallo() {
    echo "✗ $*" >&2
    exit 1
}

# datos CAMBIO → rama, parche, título y descripción de la PR
datos() {
    case "$1" in
        correcto)
            rama=plazo-de-atencion
            parche=cambios/cambio-correcto.patch
            titulo="Añadir el plazo de atención a cada respuesta"
            cuerpo="Cada respuesta incluye \`sla_horas\`, el plazo de atención según la prioridad (alta 4 h, media 24 h, baja 72 h), con un test para cada prioridad."
            esperado="los seis checks en verde y el merge permitido"
            ;;
        incorrecto)
            rama=respuesta-por-defecto
            parche=cambios/cambio-incorrecto.patch
            titulo="Responder algo por defecto si falla el proveedor"
            cuerpo="Si el proveedor de IA no responde, devolvemos una clasificación por defecto en lugar de un error, para no dejar al usuario sin respuesta."
            esperado="ci / Calidad (import sin usar) y ci / Tests (2 failed) en rojo y el merge bloqueado"
            ;;
        *) uso ;;
    esac
}

comprobar_permiso() {
    local permiso
    permiso="$(gh repo view --json viewerPermission --jq .viewerPermission 2>/dev/null || true)"
    if [[ "$permiso" != ADMIN && "$permiso" != MAINTAIN && "$permiso" != WRITE ]]; then
        fallo "La cuenta activa de gh no puede escribir en este repositorio (${permiso:-sin acceso}). Revisa: gh auth status · gh auth switch"
    fi
}

existe_en_github() {
    git ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1
}

preparar() {
    if ! git diff --quiet || ! git diff --cached --quiet; then
        fallo "Hay cambios sin guardar. Guárdalos o descártalos antes de preparar las ramas."
    fi
    comprobar_permiso
    git switch -q main
    git pull -q --ff-only
    local cambio
    for cambio in correcto incorrecto; do
        datos "$cambio"
        if existe_en_github "$rama"; then
            echo "• $rama ya existe en GitHub: se deja como está."
            continue
        fi
        git apply --check "$parche" 2>/dev/null \
            || fallo "$parche no se aplica sobre main: main ya no está en el estado de partida de la demo."
        if git show-ref --verify --quiet "refs/heads/$rama"; then
            git branch -q -D "$rama"   # restos locales de un ensayo: se vuelve a crear igual
        fi
        git switch -q -c "$rama"
        git apply "$parche"
        git commit -q -am "$titulo"
        if ! salida="$(git push -q -u origin HEAD 2>&1)"; then
            echo "$salida" >&2
            git switch -q main
            fallo "No se pudo subir la rama $rama."
        fi
        git switch -q main
        echo "✓ $rama creada y subida (cambio $cambio)."
    done
    echo "Listo. En clase: git switch plazo-de-atencion · bash scripts/comprobar.sh · bash scripts/abrir-pr.sh correcto"
}

abrir() {
    datos "$1"
    comprobar_permiso
    existe_en_github "$rama" || fallo "La rama $rama no está en GitHub. Créala antes con: bash scripts/abrir-pr.sh preparar"
    local abierta url checks
    abierta="$(gh pr list --head "$rama" --state open --json url --jq '.[0].url // empty')"
    [[ -z "$abierta" ]] || fallo "Ya hay una PR abierta para $rama: $abierta"
    if git show-ref --verify --quiet "refs/heads/$rama"; then
        git fetch -q origin "$rama"
        if [[ "$(git rev-parse "$rama")" != "$(git rev-parse "origin/$rama")" ]]; then
            fallo "Tu rama local $rama no coincide con la de GitHub: súbela (git push) o vuelve a la de GitHub."
        fi
    fi

    url="$(gh pr create --base main --head "$rama" --title "$titulo" \
        --body "$cuerpo"$'\n\n'"_Cambio de la demo de S18: \`$parche\`._")"

    # GitHub tarda unos segundos en registrar los checks; hasta entonces «gh pr checks --watch» termina
    # con «no checks reported». Se espera aquí (como mucho 40 s) para que el seguimiento funcione siempre.
    for _ in $(seq 1 20); do
        checks="$(gh pr checks "$url" --required --json name --jq length 2>/dev/null || echo 0)"
        [[ "${checks:-0}" -gt 0 ]] && break
        sleep 2
    done

    echo "✓ PR abierta: $url"
    echo "  Se espera: $esperado."
    echo "  Seguir los checks: gh pr checks $rama --watch --required"
    if [[ "${SIN_NAVEGADOR:-0}" != 1 ]]; then
        gh pr view "$url" --web >/dev/null 2>&1 || true
    fi
}

cerrar() {
    comprobar_permiso
    local cambio numero cerradas=0 cambios=(correcto incorrecto)
    [[ -z "${1:-}" ]] || cambios=("$1")
    for cambio in "${cambios[@]}"; do
        datos "$cambio"
        numero="$(gh pr list --head "$rama" --state open --json number --jq '.[0].number // empty')"
        if [[ -n "$numero" ]]; then
            gh pr close "$numero"
            cerradas=$((cerradas + 1))
        fi
    done
    echo "✓ PR de la demo cerradas: $cerradas. Las ramas siguen en GitHub para repetir la demo."
}

[[ $# -eq 1 || ( $# -eq 2 && "$1" == cerrar ) ]] || uso
cd "$(git rev-parse --show-toplevel)"
command -v gh >/dev/null || fallo "Falta la CLI de GitHub (gh)."

case "$1" in
    preparar) preparar ;;
    correcto | incorrecto) abrir "$1" ;;
    cerrar)
        if [[ -n "${2:-}" ]]; then datos "$2"; fi   # valida el nombre del cambio
        cerrar "${2:-}"
        ;;
    *) uso ;;
esac
