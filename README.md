# S18 · CI/CD y monitorización de una API de IA

Demo de la sesión 18 de AI Engineer (thePower). Una API pequeña de soporte, la de la sesión 16,
con todo lo necesario para entregarla con garantías y **solo con GitHub**:

- un cambio con errores **queda bloqueado** en la pull request (seis checks obligatorios);
- se construye **una sola imagen**; staging y producción usan **exactamente ese digest**;
- **no hay claves guardadas**: cada job usa su token temporal de GitHub;
- producción exige la **aprobación de una persona** y cada versión queda como release;
- una **vigilancia** cada hora detecta fallos, abre una incidencia y la cierra al recuperarse;
- si la versión nueva falla, se **vuelve a la anterior** reutilizando su digest.

Todo es gratuito en un repositorio público: Actions (runners estándar), GHCR, environments,
releases, atestaciones, CodeQL, Dependabot y GitHub Pages.

> **Qué es «producción» en esta demo.** GitHub no aloja la API. Staging arranca la imagen
> publicada dentro del runner y la prueba; producción es la imagen con la etiqueta `produccion`
> en GHCR (lo que ejecutaría el servidor), y la vigilancia la arranca cada hora para probarla.
> En AWS (ECS, Lambda…) solo cambiarían los jobs de staging y producción: desplegarían en el
> servicio y probarían su URL. El resto del pipeline es idéntico.

## Qué hay en el repositorio

| Ruta | Qué es |
|---|---|
| `app.py` | La API completa en un archivo: contrato, proveedores, logs y endpoints |
| `tests/` | Pruebas sin red ni claves: API, evaluación y panel |
| `evaluacion/` | 12 incidencias ficticias con su respuesta esperada y el script que mide los aciertos |
| `Dockerfile` · `requirements.lock` | Imagen con base y dependencias fijadas por digest y hash |
| `pyproject.toml` · `uv.lock` | Dependencias exactas y configuración de ruff, pytest y cobertura |
| `.github/workflows/` | Seis workflows (tabla siguiente) |
| `.github/dependabot.yml` · `.github/zizmor.yml` | Actualizaciones automáticas y auditoría de los workflows |
| `scripts/smoke.sh` | Comprobación tras desplegar: salud, versión, una clasificación y un 422 |
| `scripts/vigilancia.sh` | Vigilancia sintética: tres peticiones, una por prioridad |
| `scripts/panel.py` | Genera el panel de producción que publica GitHub Pages |
| `cambios/` | Tres parches para la clase: PR con fallo, versión B y el test que faltaba |
| `extras/` | Despliegue sin corte en local, migración compatible y prueba de restauración |
| `docs/` | Guion de clase, comandos en orden y práctica opcional |

### Los workflows

| Archivo | Cuándo | Qué hace |
|---|---|---|
| `ci-pr.yml` | Cada pull request hacia `main` | Llama a las comprobaciones. Solo lee el repositorio |
| `comprobaciones.yml` | Lo llaman la PR y la entrega | Seis jobs en paralelo, un check cada uno (tabla siguiente) |
| `entrega-main.yml` | Cada integración en `main` que cambie la imagen (`app.py`, `requirements.lock`, `Dockerfile`), o a mano | Comprobaciones → **publicar** (GHCR + atestación) → **staging** → **producción** (aprobación + release) → panel |
| `rollback.yml` | A mano, con una versión (`v1.0.0`) | Prueba esa imagen y le devuelve la etiqueta `produccion`; también pide aprobación |
| `vigilancia.yml` | Cada hora y a mano | Arranca producción, envía peticiones sintéticas, abre o cierra la incidencia |
| `panel.yml` | Al final de los tres anteriores | Publica el panel en GitHub Pages |

### Los seis checks de cada PR

| Check | Qué comprueba | Por qué |
|---|---|---|
| **Calidad** | `uv sync --locked`, que `requirements.lock` sale de `uv.lock`, `ruff check` y `ruff format` | El fallo más barato primero; CI y Docker instalan lo mismo |
| **Tests** | `pytest` con cobertura mínima del 90 % | El parche 01 lo pone en rojo |
| **Evaluación** | Aciertos sobre las 12 incidencias; mínimo 80 % | La calidad de la IA también bloquea; enlaza con S19 |
| **Imagen** | `docker build`, contenedor endurecido y `smoke.sh` | Se prueba el artefacto, no solo el código |
| **Dependencias** | `dependency-review-action` y `pip-audit` | Cadena de suministro: nada vulnerable entra con la PR |
| **Workflows** | `actionlint`, `zizmor` y `shellcheck` | El pipeline también es código y se revisa |

CodeQL (análisis de seguridad de GitHub) también se ejecuta en cada PR, pero no es obligatorio:
tarda más que el resto (≈1 min) y sus avisos se revisan en **Security**. En el ensayo del
23/11/2026 los seis checks obligatorios terminaron en unos 30 segundos.

La **evaluación** mide las reglas de la demo (gratis y deterministas: 11 de 12, porque las reglas
no entienden «iniciar sesión»). Si se añade el secreto `OPENROUTER_API_KEY`, el mismo job evalúa
el modelo real (12 llamadas de pago por ejecución). Mide al proveedor, no al endpoint: los fallos
de la API los cubren los tests, el smoke y la vigilancia.

Todas las acciones externas están fijadas al SHA completo de 40 caracteres (comprobado con
`gh api` el 23/11/2026):

| Acción | Versión | SHA |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `astral-sh/setup-uv` | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |
| `actions/dependency-review-action` | v5.0.0 | `a1d282b36b6f3519aa1f3fc636f609c47dddb294` |
| `actions/attest-build-provenance` | v4.2.2 | `4d101475d8b20a2381f78447822ac1eab6504dd8` |
| `actions/upload-pages-artifact` | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `actions/deploy-pages` | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |

## 1. Probar en local (sin cuenta de nada)

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) 0.13.7, Docker, `git`, `curl` y `jq`.

```bash
uv sync --locked                       # exactamente lo que dice uv.lock
uv run ruff check . && uv run ruff format --check .
uv run pytest --cov                    # 38 pruebas, sin red
uv run python -m evaluacion.evaluar    # 11/12 (91,7 %) · umbral 80 %
```

La API en modo demo (reglas visibles, sin coste) y las dos comprobaciones:

```bash
uv run uvicorn app:crear_app --factory --port 8000 --no-access-log
bash scripts/smoke.sh http://127.0.0.1:8000        # en otra terminal
bash scripts/vigilancia.sh http://127.0.0.1:8000
```

Cada petición deja una línea JSON. Fíjate en lo que **sí** hay (`request_id`, `version`, `ruta`,
`estado`, `duracion_ms`) y en lo que **no**: el texto de la incidencia ni ninguna clave.

La misma comprobación que hace el check «Imagen»:

```bash
docker build --provenance=false --build-arg APP_VERSION=prueba-local -t api:local .
docker run --rm -d --name api --read-only --cap-drop ALL -p 127.0.0.1:8000:8000 api:local
bash scripts/smoke.sh http://127.0.0.1:8000 prueba-local
docker logs api && docker stop api
```

## 2. Tu copia en GitHub

Copia la carpeta **fuera** de cualquier otro repositorio (dentro de otro, `git apply` ignora los
parches sin avisar) y crea el repositorio **público** sin subir nada todavía:

```bash
cp -R thepower-cicd ~/mi-cicd && cd ~/mi-cicd && rm -rf .git
git init -b main && git add -A && git commit -m "Versión A"
gh repo create mi-cicd --public --source . --remote origin
export GH_REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
YO="$(gh api user --jq .id)"
```

Antes del primer push, crea los dos entornos. Solo `main` puede desplegar y producción pide tu
aprobación (puedes aprobar tus propios despliegues):

```bash
for entorno in staging produccion; do
  if [[ $entorno == produccion ]]; then
    REVISORES="[{\"type\":\"User\",\"id\":$YO}]"
  else
    REVISORES="[]"
  fi
  gh api -X PUT "repos/$GH_REPO/environments/$entorno" --input - <<JSON
{"reviewers": $REVISORES, "prevent_self_review": false,
 "deployment_branch_policy": {"protected_branches": false, "custom_branch_policies": true}}
JSON
  gh api -X POST "repos/$GH_REPO/environments/$entorno/deployment-branch-policies" \
    -f name=main -f type=branch
done
gh api -X PUT "repos/$GH_REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false
gh api -X POST "repos/$GH_REPO/pages" -f build_type=workflow     # el panel
```

Sube la versión A y lanza la primera entrega a mano: el primer push de un repositorio no tiene
con qué compararse y el filtro de rutas de `Entrega · main` no lo lanza solo. Se queda esperando
tu aprobación para producción:

```bash
git push -u origin main
gh workflow run entrega-main.yml --ref main && sleep 5
gh run watch "$(gh run list --workflow entrega-main.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

Apruébala en la ejecución (**Review deployments → produccion → Approve**). Se crea la release
`v1.0.0` y la imagen recibe la etiqueta `produccion`.

Por último, la regla de `main`: obligar a entrar por PR con los seis checks en verde.
**Settings → Rules → Rulesets → New branch ruleset**, rama por defecto, activa *Require a pull
request before merging* (0 aprobaciones: si no, no podrías integrar tus propias PR) y *Require
status checks to pass* con `ci / Calidad`, `ci / Tests`, `ci / Evaluación`, `ci / Imagen`,
`ci / Dependencias` y `ci / Workflows` (aparecen en la lista tras la primera PR). Activa también
*Block force pushes*. En **Settings → Advanced Security** activa CodeQL (*Default setup*).

## 3. El recorrido de la clase

### 3.1 Una PR con un fallo queda bloqueada

```bash
git switch -c respuesta-por-defecto
git apply cambios/01-pr-con-fallo.patch
git commit -am "Responder algo por defecto si falla el proveedor"
git push -u origin HEAD && gh pr create --fill && gh pr checks --watch
```

El cambio parece razonable, pero inventa una respuesta cuando el proveedor falla. Dos tests lo
detectan, el check **Tests** queda en rojo y la PR no se puede integrar. Ciérrala:
`gh pr close --delete-branch`.

### 3.2 La versión B pasa todo y llega a producción

```bash
git switch main && git switch -c plazo-de-atencion
git apply cambios/02-version-b.patch
git commit -am "Añadir el plazo de atención (versión B)"
git push -u origin HEAD && gh pr create --fill && gh pr checks --watch
gh pr merge --squash --delete-branch && git switch main && git pull
```

`Entrega · main` publica B, la prueba en staging y espera tu aprobación. Al aprobar, B pasa a
producción como `v1.1.0`. Comprueba la procedencia del artefacto:

```bash
gh release view v1.1.0                                   # imagen y digest
gh attestation verify oci://ghcr.io/USUARIO/mi-cicd@sha256:… --repo "$GH_REPO"
```

### 3.3 La vigilancia encuentra un fallo que los tests no cubrían

```bash
gh workflow run vigilancia.yml && sleep 5
gh run watch "$(gh run list --workflow vigilancia.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
gh issue list --label incidente
```

La vigilancia envía una consulta de prioridad baja y B responde 500: calcula el plazo con un
diccionario al que le falta `baja`. La incidencia trae la versión, el digest y la línea de log
`excepcion` con `error_tipo: KeyError`, localizada por su `request_id`. El panel (GitHub Pages)
la muestra en rojo.

### 3.4 Rollback: la versión anterior, sin reconstruir

```bash
gh workflow run rollback.yml -f version=v1.0.0
```

Apruébalo (también es producción). El workflow prueba la imagen de `v1.0.0` y le devuelve la
etiqueta `produccion`. Lanza otra vez la vigilancia: en verde, y cierra la incidencia sola.

### 3.5 Arreglar hacia delante

```bash
git switch -c plazo-para-todas-las-prioridades
git apply --include='tests/*' cambios/03-test-que-faltaba.patch   # el test, en rojo
git apply --exclude='tests/*' cambios/03-test-que-faltaba.patch   # y el arreglo
```

## 4. Retirar

Nada cuesta dinero. Para limpiar: borra el repositorio (`gh repo delete`) y, en tu perfil,
**Packages → mi-cicd → Package settings → Delete package**.

## Plan para proteger los datos

La práctica no necesita base de datos. Si tu API la tuviera, este es el plan mínimo.

### Despliegue progresivo

| Estrategia | Qué hace | Cuándo usarla |
|---|---|---|
| **Rolling** | Arranca instancias nuevas, espera a que estén sanas y para las antiguas | Servicio pequeño; en ECS, el *circuit breaker* deshace el cambio si la tarea no arranca |
| **Blue/green** | Dos entornos completos; se prueba el nuevo y se cambia el tráfico de una vez | Cuando hay que validar antes de recibir usuarios y volver atrás al instante |
| **Canary** | Un porcentaje pequeño de tráfico real va a la versión nueva; si va bien, el resto | Cambios de riesgo con métricas fiables de error y latencia |
| **Lineal** | El tráfico se mueve en incrementos iguales | Cuando se quiere observar cada escalón |

Blue/green, canary y lineal necesitan algo que reparta el tráfico (un balanceador, Service
Connect en ECS o los porcentajes de versiones de Workers o Lambda); esta demo no despliega en
un servidor, así que no lo tiene. Plan para
producción: empezar con canary del 10 %, vigilar errores 5xx y p95 durante unos minutos,
continuar solo si no empeoran y volver al digest anterior en cuanto salte la alarma.

**Cómo se demuestra que no hay corte.** Con peticiones continuas por el mismo endpoint estable
(en producción, un balanceador como el ALB) antes, durante y después del cambio, y cero
respuestas fallidas en las tres fases. El smoke de esta demo se ejecuta al terminar: prueba que
B funciona, no que el cambio no cortó. `extras/despliegue_sin_corte.py` lo enseña en local, sin
nube ni cambios en la API: un
balanceador mínimo con readiness (B solo recibe tráfico tras responder `/health`) y drenaje (A
termina sus peticiones antes de pararse) frente a parar A y arrancar B.

```bash
uv run python extras/despliegue_sin_corte.py   # sin corte: 0 fallos · con corte: ~60 fallos
```

### Cambios de base de datos compatibles con la versión anterior

Durante un despliegue conviven la versión antigua y la nueva, y un rollback vuelve a poner
la antigua. Por eso cada cambio de esquema debe funcionar con **las dos**:

1. **Expand**: añadir lo nuevo sin quitar nada (columna opcional, tabla nueva).
2. **Migrar**: desplegar el código que escribe en lo nuevo y rellenar los datos antiguos.
3. **Contract**: retirar lo viejo solo cuando ninguna versión desplegable lo usa.

Renombrar o borrar una columna en un solo paso rompe a la versión anterior. Y **volver a
una imagen antigua no revierte una migración**: los datos escritos por B siguen ahí.

### Copias de seguridad con prueba de restauración

- Copias automáticas con retención definida (en RDS, entre 0 y 35 días; 0 las desactiva) y
  una copia manual antes de cada migración.
- Dos números acordados: cuántos datos se pueden perder (RPO) y cuánto se tarda en volver (RTO).
- **Restaurar de verdad**, de forma periódica, en una base nueva: comprobar integridad,
  número de filas y una consulta funcional. En RDS, restaurar a un punto en el tiempo crea
  una instancia nueva y no modifica la original.
- Anotar fecha, duración y resultado de cada prueba. Una copia nunca restaurada es una hipótesis.

`extras/migracion_y_restauracion.py` demuestra las tres ideas con SQLite y datos ficticios,
sin tocar la API ni AWS:

```bash
uv run python extras/migracion_y_restauracion.py
```

## Más documentación

- [Guion de la clase](docs/guion-clase.md) · [Comandos en orden](docs/comandos.md) ·
  [Práctica opcional](docs/ejercicio.md)
