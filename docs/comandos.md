# S18 · Comandos de la clase, en orden

Bash (macOS, Linux o Git Bash). La demo es **nativa de GitHub**: el repositorio público
`JoseAntonioNuevo/thepower-cicd` ya tiene los entornos, la regla de `main`, CodeQL, Dependabot,
Pages y la versión A (`v1.0.0`) en producción.

La demo gira alrededor de **dos ramas preparadas**, con un cambio cada una:

| Rama | Cambio | Qué pasa |
|---|---|---|
| `plazo-de-atencion` | **Correcto**: cada respuesta incluye `sla_horas` (alta 4 h, media 24 h, baja 72 h), con un test por prioridad | Los seis checks en verde, en local y en la PR; se integra y llega a producción como `v1.1.0` |
| `respuesta-por-defecto` | **Incorrecto**: si el proveedor falla, inventa una respuesta, y deja un `import logging` sin usar | Calidad y Tests en rojo, en local y en la PR; el merge queda bloqueado |

Con cada rama se hace lo mismo: primero los checks **en local** (`scripts/comprobar.sh`, los
mismos seis de la PR) y después la **PR real** en GitHub. Primero la verde y luego la roja.

```bash
export GH_REPO=JoseAntonioNuevo/thepower-cicd
cd ~/Documents/the-power/thepower-cicd && git switch main && git pull --ff-only
ultima() { gh run list --workflow "$1" --limit 1 --json databaseId --jq '.[0].databaseId'; }
```

Pestañas abiertas antes de conectar: el repositorio, **Actions**, **Pull requests**, la release
`v1.0.0`, **Settings → Environments**, **Settings → Rules** y el panel
(`https://joseantonionuevo.github.io/thepower-cicd/`).

### Tiempos medidos en los ensayos (23/11/2026)

| Paso | Tiempo |
|---|---|
| `scripts/comprobar.sh` (seis checks en local, con la imagen de Docker en caché) | ≈10 s (`--rapido`: ≈3 s) |
| Abrir una PR con `scripts/abrir-pr.sh` | ≈10 s |
| Seis checks obligatorios de una PR | 20–30 s (CodeQL ≈1 min aparte; CodeRabbit ≈3 min) |
| `Entrega · main` hasta pedir la aprobación (checks, publicar, staging) | ≈75 s |
| Producción tras aprobar (+ panel) | ≈15 s (+ 30 s) |
| Vigilancia (+ panel) | ≈30 s (+ 25 s) |
| Rollback tras aprobar | ≈30 s |

## 0. Antes de conectar (no se proyecta)

```bash
gh auth status                                 # cuenta ACTIVA: JoseAntonioNuevo (gh auth switch --user …)
uv sync --locked
gh release list                                # v1.0.0
gh pr list --state open                        # ninguna
gh issue list --label incidente --state open   # ninguna
git ls-remote --heads origin plazo-de-atencion respuesta-por-defecto   # las dos ramas existen
docker build -q --provenance=false --build-arg APP_VERSION=version-A -t s18:A .   # respaldo local
```

Si faltan las ramas: `bash scripts/abrir-pr.sh preparar` las crea desde `main` y las sube.

## Bloque 1 · El repositorio

```bash
git ls-files
sed -n '1,30p' .github/workflows/entrega-main.yml
bash scripts/comprobar.sh                      # en main: 6/6 en verde (el punto de partida)
```

## Bloque 2 · Demo 1: un cambio correcto y otro incorrecto, en local y en la PR

### 1. El cambio correcto

```bash
git switch plazo-de-atencion
git show --stat HEAD && git diff main -- app.py   # qué cambia: SLA_HORAS y sla_horas en la respuesta
bash scripts/comprobar.sh                      # ✅ 6/6 en verde · 41 passed
bash scripts/abrir-pr.sh correcto              # abre la PR (y el navegador)
gh pr checks plazo-de-atencion --watch --required   # los seis en verde
gh pr view plazo-de-atencion --json mergeStateStatus  # CLEAN: se puede integrar (se integra en el bloque 3)
```

### 2. El cambio incorrecto

```bash
git switch respuesta-por-defecto
git diff main -- app.py                        # la «mejora»: respuesta por defecto + import logging
bash scripts/comprobar.sh                      # ❌ 2 en rojo (Calidad, Tests)
bash scripts/abrir-pr.sh incorrecto            # abre la PR (y el navegador)
gh pr checks respuesta-por-defecto --watch --required   # Calidad y Tests en rojo
gh pr view respuesta-por-defecto --json mergeStateStatus  # BLOCKED
git switch main
```

En local, `comprobar.sh` enseña la causa debajo de cada check en rojo:
``app.py:12:8: F401 `logging` imported but unused`` y los dos tests que fallan
(`test_fallo_del_proveedor_devuelve_error_y_no_inventa_una_respuesta` y
`test_el_log_de_un_fallo_guarda_el_codigo_y_el_estado`). En la PR, lo mismo: la anotación de ruff
en la línea del import (**Files changed**) y el log de **ci / Tests**.

También aparecen CodeQL, GitGuardian y CodeRabbit: no son obligatorios. CodeRabbit (diapositiva 16)
tarda unos tres minutos; no cerrar la PR roja antes. Después:

```bash
bash scripts/abrir-pr.sh cerrar incorrecto     # cierra solo la roja; la rama se queda para otra vez
```

## Bloque 3 · Demo 2: el cambio correcto se integra y se publica

```bash
gh pr merge plazo-de-atencion --squash --delete-branch && git switch main && git pull --ff-only
gh run watch "$(ultima entrega-main.yml)"
```

En la ejecución de `Entrega · main`: el grafo comprobaciones → publicar → staging → producción
y el resumen de **Publicar imagen** con el digest. Mientras espera la aprobación:

```bash
IMAGEN=ghcr.io/joseantonionuevo/thepower-cicd   # paquete público: no hace falta iniciar sesión
DIGEST="$(docker buildx imagetools inspect "$IMAGEN:$(git rev-parse HEAD)" --format '{{json .Manifest}}' | jq -r .digest)"
echo "$DIGEST"
gh attestation verify "oci://$IMAGEN@$DIGEST" --repo "$GH_REPO"
```

## Bloque 4 · Demo 3: staging y aprobación de producción

- **Staging** ya pasó: arrancó `ghcr.io/…@$DIGEST` en el runner y el smoke salió bien.
- **Producción** está en *Waiting*: **Review deployments → produccion → Approve and deploy**.
- Resultado: release `v1.1.0`, etiqueta `produccion` → ese digest, panel actualizado.

```bash
gh release view v1.1.0
curl -s https://joseantonionuevo.github.io/thepower-cicd/datos.json | jq '.releases[0].version'
```

Sin corte, en local (unos 7 s):

```bash
uv run python extras/despliegue_sin_corte.py   # sin corte: 0 fallos · con corte: ~60 fallos
```

## Bloque 5 · Demo 4: la vigilancia de producción

```bash
gh workflow run vigilancia.yml && sleep 5
gh run watch "$(ultima vigilancia.yml)"        # verde: tres peticiones, una por prioridad, todas 200
gh issue list --label incidente --state open   # ninguna
```

Qué pasa cuando falla: la incidencia real del ensayo (diapositiva 35), abierta sola por la
vigilancia cuando una versión con un fallo que los tests no cubrían llegó a producción:
<https://github.com/JoseAntonioNuevo/thepower-cicd-ensayo/issues/3>.

## Bloque 5 · Demo 5: rollback (simulacro)

Volver a `v1.0.0` sin reconstruir, comprobar que producción responde y volver a `v1.1.0`:

```bash
gh workflow run rollback.yml -f version=v1.0.0
gh run watch "$(ultima rollback.yml)"          # aprobar en «Review deployments»
gh workflow run vigilancia.yml && sleep 5 && gh run watch "$(ultima vigilancia.yml)"   # verde
gh workflow run rollback.yml -f version=v1.1.0 # y de vuelta a la versión nueva (también se aprueba)
```

## Bloque 6 · Migración compatible y restauración

```bash
uv run python extras/migracion_y_restauracion.py
```

## Si GitHub no responde

Todo lo de los bloques 1 y 2 funciona en local: `git switch <rama>` y `bash scripts/comprobar.sh`
son los mismos seis checks. Para la entrega, la imagen de respaldo:

```bash
docker run --rm -d --name api --read-only --cap-drop ALL -p 127.0.0.1:8000:8000 s18:A
bash scripts/smoke.sh http://127.0.0.1:8000 version-A
bash scripts/vigilancia.sh http://127.0.0.1:8000
docker stop api
```

## Después de la clase

```bash
bash scripts/abrir-pr.sh cerrar                # si quedó alguna PR de la demo abierta
gh release list                                # v1.1.0 en producción (o v1.0.0 si se dejó el rollback)
```

Para repetir la demo con otro grupo, `main` tiene que volver al estado de partida (una PR que
revierta el cambio correcto) y las ramas se recrean con `bash scripts/abrir-pr.sh preparar`; el
cambio correcto saldría entonces como `v1.2.0`.
