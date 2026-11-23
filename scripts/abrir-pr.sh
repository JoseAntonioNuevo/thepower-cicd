#!/usr/bin/env bash
# Abre una de las PR de la demo con un solo comando, partiendo de un main limpio y al día.
#
#   bash scripts/abrir-pr.sh calidad   # ci / Calidad en rojo: un import sin usar (ruff F401)
#   bash scripts/abrir-pr.sh tests     # ci / Tests en rojo: inventa una respuesta si falla el proveedor
#   bash scripts/abrir-pr.sh verde     # los seis checks en verde: la versión B
#   bash scripts/abrir-pr.sh arreglo   # el test que faltaba (1 failed en local) y el arreglo; requiere B en main
#   bash scripts/abrir-pr.sh cerrar    # cierra las PR de la demo que sigan abiertas y borra sus ramas
#
# Variables opcionales:
#   SIN_NAVEGADOR=1  no abre la PR en el navegador al crearla.
#   SOLO_LOCAL=1     no sube nada a GitHub: crea la rama, aplica el parche, hace el commit, muestra
#                    lo que dirían ruff y pytest y vuelve a main (ensayo o respaldo si GitHub falla).
set -euo pipefail

RAMAS=(import-sin-usar respuesta-por-defecto plazo-de-atencion plazo-para-todas-las-prioridades)

uso() {
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
}

fallo() {
    echo "✗ $*" >&2
    exit 1
}

resumen_pytest() {
    # La última línea de pytest («N passed» o «N failed, M passed»), sin cortar el script si falla.
    uv run --locked pytest -q -p no:cacheprovider 2>&1 | tail -n 1 || true
}

cerrar() {
    git switch -q main
    local rama numero cerradas=0
    for rama in "${RAMAS[@]}"; do
        numero="$(gh pr list --head "$rama" --state open --json number --jq '.[0].number // empty')"
        if [[ -n "$numero" ]]; then
            gh pr close "$numero" --delete-branch
            cerradas=$((cerradas + 1))
        fi
        if git show-ref --verify --quiet "refs/heads/$rama"; then
            git branch -q -D "$rama"
        fi
    done
    echo "✓ PR de la demo cerradas: $cerradas. Estás en main."
}

[[ $# -eq 1 ]] || uso
cd "$(git rev-parse --show-toplevel)"
command -v gh >/dev/null || fallo "Falta la CLI de GitHub (gh)."

case "$1" in
    calidad)
        parche=cambios/00-import-sin-usar.patch
        rama=import-sin-usar
        titulo="Preparar el registro con el módulo logging"
        cuerpo="Importa \`logging\` para llevar más adelante el log estructurado al módulo estándar."
        esperado="solo ci / Calidad en rojo; la anotación de ruff sale en la línea del import"
        ;;
    tests)
        parche=cambios/01-pr-con-fallo.patch
        rama=respuesta-por-defecto
        titulo="Responder algo por defecto si falla el proveedor"
        cuerpo="Si el proveedor de IA no responde, devolvemos una clasificación por defecto en lugar de un error, para no dejar al usuario sin respuesta."
        esperado="solo ci / Tests en rojo (2 failed) y el merge bloqueado"
        ;;
    verde)
        parche=cambios/02-version-b.patch
        rama=plazo-de-atencion
        titulo="Añadir el plazo de atención (versión B)"
        cuerpo="Cada respuesta incluye \`sla_horas\`, el plazo de atención según la prioridad, con su test."
        esperado="los seis checks en verde; al integrarla, Entrega · main publica B y espera la aprobación"
        ;;
    arreglo)
        parche=cambios/03-test-que-faltaba.patch
        rama=plazo-para-todas-las-prioridades
        titulo="Plazo de atención para todas las prioridades"
        cuerpo="Añade el plazo de la prioridad baja y un test con las tres prioridades: el que le faltaba a la versión B."
        esperado="los seis checks en verde; al integrarla, Entrega · main publica C"
        ;;
    cerrar)
        cerrar
        exit 0
        ;;
    *) uso ;;
esac

if ! git diff --quiet || ! git diff --cached --quiet; then
    fallo "Hay cambios sin guardar. Guárdalos o descártalos antes de abrir la PR."
fi
git switch -q main
if [[ "${SOLO_LOCAL:-0}" != 1 ]]; then   # en local no se toca la red: sirve aunque GitHub no responda
    permiso="$(gh repo view --json viewerPermission --jq .viewerPermission 2>/dev/null || true)"
    if [[ "$permiso" != ADMIN && "$permiso" != MAINTAIN && "$permiso" != WRITE ]]; then
        fallo "La cuenta activa de gh no puede escribir en este repositorio (${permiso:-sin acceso}). Revisa: gh auth status · gh auth switch"
    fi
    git pull -q --ff-only
    if git ls-remote --exit-code --heads origin "$rama" >/dev/null; then
        fallo "La rama $rama ya existe en GitHub (¿la PR sigue abierta?). Ciérrala con: bash scripts/abrir-pr.sh cerrar"
    fi
fi
if git show-ref --verify --quiet "refs/heads/$rama"; then
    git branch -q -D "$rama"   # restos de un ensayo anterior: el parche la vuelve a crear igual
fi
if ! git apply --check "$parche" 2>/dev/null; then
    if [[ "$1" == arreglo ]]; then
        fallo "El arreglo se aplica sobre la versión B: integra antes la PR verde (bash scripts/abrir-pr.sh verde)."
    fi
    fallo "$parche no se aplica sobre main: main ya no está en el estado de partida de la demo."
fi

git switch -q -c "$rama"
if [[ "$1" == arreglo ]]; then
    git apply --include='tests/*' "$parche"
    echo "Solo el test nuevo:  $(resumen_pytest)"
    git apply --exclude='tests/*' "$parche"
    resultado="$(resumen_pytest)"
    echo "Con el arreglo:      $resultado"
    [[ "$resultado" != *failed* ]] || fallo "El arreglo no deja los tests en verde: revisa la rama $rama."
else
    git apply "$parche"
fi
git commit -q -am "$titulo"

if [[ "${SOLO_LOCAL:-0}" == 1 ]]; then
    if uv run --locked ruff check -q . >/dev/null 2>&1; then echo "ruff:   correcto"; else echo "ruff:   FALLA"; fi
    echo "pytest: $(resumen_pytest)"
    git switch -q main
    echo "✓ Rama $rama creada en local, sin subir nada. En CI se esperaría: $esperado."
    exit 0
fi

if ! salida="$(git push -q -u origin HEAD 2>&1)"; then   # sin el aviso «Create a pull request…» de GitHub
    echo "$salida" >&2
    git switch -q main
    fallo "No se pudo subir la rama $rama."
fi
url="$(gh pr create --base main --head "$rama" --title "$titulo" \
    --body "$cuerpo"$'\n\n'"_Parche de la demo de S18: \`$parche\`._")"
git switch -q main

echo "✓ PR abierta: $url"
echo "  Se espera: $esperado."
echo "  Seguir los checks: gh pr checks $url --watch --required"
if [[ "${SIN_NAVEGADOR:-0}" != 1 ]]; then
    gh pr view "$url" --web >/dev/null 2>&1 || true
fi
