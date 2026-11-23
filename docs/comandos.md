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

### Tiempos medidos en el ensayo completo (23/11/2026, repositorio gemelo)

| Paso | Tiempo |
|---|---|
| Seis checks obligatorios de una PR (desde el push) | 22–32 s (CodeQL ≈1 min aparte) |
| `Entrega · main` hasta pedir la aprobación (checks, publicar, staging) | ≈75 s |
| Producción tras aprobar (+ panel) | ≈15 s (+ 30 s) |
| Vigilancia hasta el rojo y la incidencia (+ panel) | ≈30 s (+ 25 s) |
| Rollback tras aprobar | ≈30 s |

Resultado: PR con fallo bloqueada; B en verde y publicada como `v1.1.0`; la vigilancia abrió la
incidencia con el `KeyError`; rollback a `v1.0.0`; la vigilancia la cerró sola; arreglo publicado
como `v1.2.0` y vigilancia en verde.

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
uv run pytest -q --cov                 # 38 passed, cobertura ≈96 %
uv run python -m evaluacion.evaluar    # 11/12 (91,7 %) · umbral 80 %
```

## Bloque 2 · Demo: dos PR con un fallo quedan bloqueadas (≈30 s de checks; CodeQL ≈1 min)

Un comando por PR (`scripts/abrir-pr.sh`: rama, parche, commit, push, PR y navegador). Se lanzan
seguidas y corren a la vez:

```bash
bash scripts/abrir-pr.sh calidad       # import sin usar → solo ci / Calidad en rojo
bash scripts/abrir-pr.sh tests         # respuesta inventada → solo ci / Tests en rojo
gh pr checks respuesta-por-defecto --watch --required
gh pr view respuesta-por-defecto --json mergeStateStatus   # BLOCKED
# esperar ≈3 min al comentario de CodeRabbit (diapositiva 16) antes de cerrar
bash scripts/abrir-pr.sh cerrar        # cierra las dos y borra sus ramas
```

En la de **calidad**, **Files changed** muestra la anotación de ruff (`F401 logging imported but
unused`) en la línea del import. Si GitHub no responde: `SOLO_LOCAL=1 bash scripts/abrir-pr.sh tests`
hace lo mismo en local y enseña `2 failed` (con `calidad`, «ruff: FALLA»).

En la PR: los seis checks en paralelo, el botón de merge bloqueado y, en **Files changed**, las
anotaciones de CodeQL si las hay. También aparecen GitGuardian y CodeRabbit: son apps instaladas
en la cuenta, no workflows del repositorio (checks de terceros). CodeRabbit tarda unos tres minutos;
si la PR se cierra antes, deja «Review failed: the pull request is closed». Local: `uv run pytest -q` → `2 failed`.

Ensayado el 23/11/2026 (PR #1 del repositorio gemelo, con el `main` actual): `ci / Tests` en rojo con
`2 failed, 36 passed`, merge `BLOCKED`;
tras revertir, todo verde y merge `CLEAN`.

## Bloque 3 · Demo: la versión B pasa todo y se publica

```bash
bash scripts/abrir-pr.sh verde                                       # la versión B
gh pr checks plazo-de-atencion --watch --required                    # los seis en verde
gh pr merge plazo-de-atencion --squash --delete-branch && git pull --ff-only
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
bash scripts/abrir-pr.sh arreglo       # en local: «1 failed» con el test y «42 passed» con el arreglo; abre la PR
gh pr checks plazo-para-todas-las-prioridades --watch --required
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
bash scripts/abrir-pr.sh cerrar                    # cierra las PR de la demo que sigan abiertas
```
