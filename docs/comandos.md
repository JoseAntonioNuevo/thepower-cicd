# S18 · Comandos de la clase, en orden

Bash (macOS, Linux o Git Bash). La demo es **nativa de GitHub**: el repositorio público
`JoseAntonioNuevo/thepower-cicd` ya tiene los entornos, la regla de `main`, CodeQL, Dependabot,
Pages y la versión A (`v1.0.0`) en producción. Cada momento tiene también una versión **local**
por si GitHub no responde.

```bash
export GH_REPO=JoseAntonioNuevo/thepower-cicd
cd ~/Documents/the-power/thepower-cicd && git switch main && git pull --ff-only
ultima() { gh run list --workflow "$1" --limit 1 --json databaseId --jq '.[0].databaseId'; }
```

Pestañas abiertas antes de conectar: el repositorio, **Actions**, **Pull requests**, la release
`v1.0.0`, **Settings → Environments**, **Settings → Rules** y el panel
(`https://joseantonionuevo.github.io/thepower-cicd/`).

## 0. Antes de conectar (no se proyecta)

```bash
uv sync --locked
gh run list --limit 5                          # la última entrega en verde
gh release list                                # v1.0.0
gh issue list --label incidente --state open   # ninguna
docker build -q --provenance=false --build-arg APP_VERSION=version-A -t s18:A .   # respaldo local
```

## Bloque 1 · El repositorio

```bash
git ls-files
sed -n '1,30p' .github/workflows/entrega-main.yml
```

## Bloque 2 · Las comprobaciones en local

```bash
uv export --locked --no-dev --no-emit-project --no-header --format requirements-txt | diff -u requirements.lock -
uv run ruff check . && uv run ruff format --check .
uv run pytest -q --cov                 # 36 passed, cobertura ≈96 %
uv run python -m evaluacion.evaluar    # 11/12 (91,7 %) · umbral 80 %
```

## Bloque 2 · Demo: una PR con un fallo queda bloqueada (≈1,5 min de checks)

```bash
git switch -c respuesta-por-defecto
git apply cambios/01-pr-con-fallo.patch
git commit -qam "Responder algo por defecto si falla el proveedor"
git push -u origin HEAD
gh pr create --fill
gh pr checks --watch                   # ci / Tests en rojo; el resto en verde
gh pr view --json mergeStateStatus     # BLOCKED
gh pr close --delete-branch && git switch main
```

En la PR: los seis checks en paralelo, el botón de merge bloqueado y, en **Files changed**, las
anotaciones de CodeQL si las hay. Local: `uv run pytest -q` → `2 failed`.

## Bloque 3 · Demo: la versión B pasa todo y se publica

```bash
git switch -c plazo-de-atencion
git apply cambios/02-version-b.patch
git commit -qam "Añadir el plazo de atención (versión B)"
git push -u origin HEAD && gh pr create --fill && gh pr checks --watch   # todo verde
gh pr merge --squash --delete-branch && git switch main && git pull --ff-only
gh run watch "$(ultima entrega-main.yml)"
```

En la ejecución de `Entrega · main`: el grafo comprobaciones → publicar → staging → producción
y el resumen de **Publicar imagen** con el digest. Mientras espera la aprobación:

```bash
IMAGEN=ghcr.io/joseantonionuevo/thepower-cicd   # paquete público: no hace falta iniciar sesión
DIGEST_B="$(docker buildx imagetools inspect "$IMAGEN:$(git rev-parse HEAD)" --format '{{json .Manifest}}' | jq -r .digest)"
echo "$DIGEST_B"
gh attestation verify "oci://$IMAGEN@$DIGEST_B" --repo "$GH_REPO"
```

## Bloque 4 · Demo: staging y aprobación de producción

- **Staging** ya pasó: arrancó `ghcr.io/…@$DIGEST_B` en el runner y el smoke salió bien.
- **Producción** está en *Waiting*: **Review deployments → produccion → Approve and deploy**.
- Resultado: release `v1.1.0`, etiqueta `produccion` → digest de B, panel actualizado.

```bash
gh release view v1.1.0
```

Sin corte, en local (unos 7 s):

```bash
uv run python extras/despliegue_sin_corte.py   # sin corte: 0 fallos · con corte: ~60 fallos
```

## Bloque 5 · Demo: la vigilancia detecta el fallo de B

```bash
gh workflow run vigilancia.yml && sleep 5
gh run watch "$(ultima vigilancia.yml)"        # termina en rojo (≈40 s)
gh issue list --label incidente                # incidencia abierta automáticamente
gh issue view "$(gh issue list --label incidente --json number --jq '.[0].number')"
```

En la incidencia: versión `v1.1.0`, digest, la petición «Tengo una duda sobre los horarios» con
HTTP 500, su `request_id` y la línea `excepcion` con `error_tipo: KeyError`. En el panel, la
vigilancia en rojo y una incidencia abierta.

Local, el mismo hallazgo:

```bash
git switch -q --detach origin/main             # main ya contiene B
docker build -q --provenance=false --build-arg APP_VERSION=version-B -t s18:B .
docker run --rm -d --name api --read-only --cap-drop ALL -p 127.0.0.1:8000:8000 s18:B
bash scripts/vigilancia.sh http://127.0.0.1:8000           # falla 1 de 3
docker logs api 2>&1 | grep PEGA-EL-REQUEST-ID
docker stop api && git switch -q main
```

## Bloque 5 · Demo: rollback a v1.0.0

```bash
gh workflow run rollback.yml -f version=v1.0.0
gh run watch "$(ultima rollback.yml)"          # aprobar en «Review deployments»
gh workflow run vigilancia.yml && sleep 5 && gh run watch "$(ultima vigilancia.yml)"   # verde
gh issue list --label incidente --state closed --limit 1   # cerrada con «Recuperado»
```

Arreglar hacia delante (el test que faltaba, primero en rojo):

```bash
git switch -c plazo-para-todas-las-prioridades
git apply --include='tests/*' cambios/03-test-que-faltaba.patch && uv run pytest -q   # 1 failed
git apply --exclude='tests/*' cambios/03-test-que-faltaba.patch && uv run pytest -q   # todo verde
git commit -qam "Plazo de atención para todas las prioridades" && git push -u origin HEAD
gh pr create --fill && gh pr checks --watch
```

Si da tiempo: integrar, aprobar `v1.2.0` y lanzar la vigilancia (verde).

## Bloque 6 · Migración compatible y restauración

```bash
uv run python extras/migracion_y_restauracion.py
```

## Después de la clase · dejar el repositorio listo para la siguiente vez

Producción debe volver a A con un rollback (no reescribiendo la historia):

```bash
gh workflow run rollback.yml -f version=v1.0.0     # si quedó B en producción
gh pr list --state open                            # cerrar las PR de la demo que sigan abiertas
```
