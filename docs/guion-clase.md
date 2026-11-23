# S18 · Guion de la clase (90 minutos)

**Miércoles 25/11/2026 · grupo L/X · 18:30–20:00 (hora de Madrid).**
Presentación: `material/S18/presentaciones/S18-cicd-monitorizacion.pptx` (42 diapositivas).
Comandos exactos, en el mismo orden: [comandos.md](comandos.md).

La demo es **nativa de GitHub** (repositorio público `JoseAntonioNuevo/thepower-cicd`: Actions,
GHCR, environments, releases, vigilancia y panel en Pages, todo gratuito). AWS aparece solo como
«en una plataforma real» (versión completa en `material/S18/referencia-aws/`).

## La idea de la demo

Dos ramas preparadas, con un cambio cada una, y el mismo recorrido para las dos:

| Rama | Cambio | En local (`scripts/comprobar.sh`) | En la PR |
|---|---|---|---|
| `plazo-de-atencion` | **Correcto**: `sla_horas` en cada respuesta (alta 4 h, media 24 h, baja 72 h) y un test por prioridad | ✅ 6/6 · 41 passed | Seis checks en verde, merge permitido |
| `respuesta-por-defecto` | **Incorrecto**: inventa una respuesta si falla el proveedor y deja un `import logging` sin usar | ❌ Calidad y Tests | Calidad y Tests en rojo, merge bloqueado |

Primero la verde y luego la roja: en cada una, los checks **en local** y después la **PR real**.
Así se ve que la PR ejecuta exactamente lo mismo que el portátil, en una máquina limpia, y que la
regla de `main` convierte el rojo en un bloqueo. Después, la verde sigue el camino completo:
integrar → publicar → staging → aprobación → `v1.1.0` en producción → vigilancia → rollback
(como simulacro). El fallo en producción que encuentra la vigilancia se enseña con la incidencia
real del ensayo (diapositivas 35 y 37): con un cambio correcto no hay nada que encontrar.

La teoría y la demo se alternan: cada bloque termina en algo que se ve en pantalla y en una
pregunta para el grupo. La práctica posterior es **opcional** (aclaración de Laura del 04/11).

### Las diapositivas y el directo

La presentación no cambia: sus diapositivas de demo enseñan el **ensayo** del 23/11 (la versión B,
en verde pero con un fallo escondido). En directo se hace el recorrido nuevo, y cada una sirve así:

| Diapositiva | Lo que enseña | Cómo usarla en directo |
|---|---|---|
| 15 · Demo 1 | El cambio incorrecto (la respuesta inventada) y `2 failed` en Tests | Después de las dos PR: por qué falla la roja. La verde no tiene diapositiva: se ve en pantalla |
| 16 · CodeRabbit | Su revisión en un ensayo anterior: vio el problema y propuso cambiar los tests | Comparar con lo que comente hoy en la PR roja (ver bloque 2) |
| 24 · Demo 2 | El resumen de «Imagen publicada» de B en el ensayo | Los pasos son los mismos; en directo, el del cambio correcto |
| 31 · Demo 3 | B en el ensayo: en verde, aprobada como `v1.1.0` y con el plazo solo para alta y media | Contraste: «también estaba en verde». Hoy se aprueba el cambio correcto, que trae las tres prioridades y su test |
| 35 · Demo 4 | La incidencia real que abrió la vigilancia con B | Lo que pasa cuando un fallo no tiene test; en directo, la vigilancia sale en verde |
| 38 · Demo 5 | El rollback del ensayo (A → B → A → C) | En directo, simulacro: `v1.1.0` → `v1.0.0` → `v1.1.0` |

## Antes de conectar

- `gh auth status`: la cuenta **activa** debe ser `JoseAntonioNuevo`; `scripts/abrir-pr.sh` se
  para si la activa solo puede leer (`gh auth switch --user JoseAntonioNuevo`).
- Terminal con letra grande en `~/Documents/the-power/thepower-cicd`, en `main` y al día;
  `uv sync --locked` hecho. Docker arrancado e imagen local de respaldo construida (comandos.md, paso 0).
- Las dos ramas existen en GitHub (`git ls-remote --heads origin plazo-de-atencion
  respuesta-por-defecto`); si no, `bash scripts/abrir-pr.sh preparar`.
- Pestañas: el repositorio, **Actions**, **Pull requests**, la release `v1.0.0`,
  **Settings → Environments**, **Settings → Rules** y el panel en GitHub Pages.
- Estado de partida: `v1.0.0` en producción, ninguna PR ni incidencia abierta, todo en verde.
- Si GitHub no responde: los bloques 1 y 2 son iguales en local (`comprobar.sh`) y se dice abiertamente.
- Nada de credenciales, tokens ni el archivo `.env` en pantalla.

## Recorrido

| Hora | Min | Diapositivas | Qué se enseña en diapositiva | Qué se hace en vivo |
|---|---:|---|---|---|
| 18:30–18:33 | 3 | 1–2 | Objetivo; QR de **S17 (23/11)** | Responder al QR un minuto |
| 18:33–18:39 | 6 | 3–5 | **Punto de partida:** qué es CI/CD, qué es monitorizar, seis casos de uso y las métricas DORA | Preguntar cómo publican hoy y cuál de los seis casos les ha pasado |
| 18:39–18:45 | 6 | 6–9 | Caso conductor; CI y entrega continua en los workflows de la demo; entornos; la cadena commit → digest → release → `request_id` | Recorrer el repositorio y `comprobar.sh` en `main`: 6/6 en verde |
| 18:45–19:05 | 20 | 10–19 | Workflow y action; los seis workflows; los seis checks; tests con dobles; **demo 1**; CodeRabbit (16); ruleset y SHA; alternativas con precios | **Demo 1:** rama correcta → `comprobar.sh` (6/6) → PR verde; rama incorrecta → `comprobar.sh` (Calidad y Tests) → PR roja y bloqueada; CodeRabbit en la roja |
| 19:05–19:17 | 12 | 20–24 | Construir una vez; digest; GHCR; secretos; tokens del job; procedencia verificable | **Demo 2:** integrar la PR verde; `Entrega · main` publica; digest y `gh attestation verify` |
| 19:17–19:34 | 17 | 25–31 | Entrega real (25); staging y producción con aprobación; rolling; smoke; progresivos; sin corte | `extras/despliegue_sin_corte.py`; **demo 3:** aprobar producción → `v1.1.0` |
| 19:34–19:50 | 16 | 32–38 | Observabilidad; log estructurado; APM; **el fallo del ensayo** (35); error tracking; vigilancia, alerta y panel; rollback | **Demo 4:** vigilancia en verde y panel; **demo 5:** rollback a `v1.0.0` como simulacro y vuelta a `v1.1.0` |
| 19:50–19:54 | 4 | 39–40 | Migraciones expand/contract; backups, RPO/RTO y restauración | `extras/migracion_y_restauracion.py` (30 s) |
| 19:54–20:00 | 6 | 41–42 | Práctica opcional y cierre | Preguntas; recordar el QR |

La franja exacta de cada diapositiva está al principio de sus notas. **Cambio del 23/11/2026
(noche):** la demo pasa a dos ramas preparadas (correcta e incorrecta), con los checks primero en
local y luego en la PR; la historia anterior de B (verde con un fallo escondido → incidencia →
rollback → arreglo) queda como el ensayo real que enseñan las diapositivas 25, 31, 35, 37 y 38.

## Bloque a bloque

### 18:30 · Apertura (diapositivas 1–2)

- El objetivo no es «tener un pipeline», sino **poder demostrar** tres cosas: un cambio
  defectuoso no llega a desplegarse, lo desplegado es exactamente lo que se probó y se puede
  volver a una versión conocida.
- QR: evalúa la **S17 del 23/11** (Bedrock + Lambda). Un minuto para rellenarlo.
- El grupo L/X tuvo la S16 con otro profesor: la demo trae su propia API (la misma tarea de
  clasificación de incidencias ficticias).
- **Pregunta:** «¿Qué tendría que pasar para que os fiarais de desplegar un viernes a las 19:00?».

### 18:33 · Punto de partida · qué es CI/CD y qué es monitorizar (3–5)

- **3 · Qué es CI/CD.** CI (código, construir, probar), CD (publicar, desplegar) y la
  monitorización cerrando el círculo. Cada línea de «con CI/CD» es una parte de la clase.
- **4 · Qué es monitorizar.** Las cuatro señales doradas, las señales propias de una app de IA y
  el ciclo de un incidente (detectar → avisar → diagnosticar → recuperar → aprender).
- **5 · Casos de uso** y las cinco métricas DORA.
- **Preguntas:** «¿A cuál de las dos columnas se parece cómo publicáis hoy?» y «¿Cuál de los seis casos os ha pasado?».

### 18:39 · Caso conductor y bloque 1 · CI/CD y entornos (6–9)

- CI = integrar a menudo y comprobar cada cambio. La demo hace **entrega continua**: siempre hay
  una imagen validada y pasar a producción es una decisión (aprobación).
- Entornos: local, CI, staging, producción. La **misma imagen** en todos; cambia la configuración.
- La cadena: commit → comprobaciones → imagen → **digest** → release → etiqueta `produccion` →
  cada petición lleva `version` = commit.
- Honestidad: GitHub no aloja la API. Staging arranca la imagen en el runner y producción es la
  etiqueta `produccion` que ejecutaría el servidor. En AWS cambiarían esos dos jobs; el resto no.
- **En vivo:** recorrer el repositorio y lanzar `bash scripts/comprobar.sh` en `main`: los seis
  checks de la PR, en local, en unos 10 s. Todo en verde: es el punto de partida.
- **Pregunta:** «Si mañana falla una petición, ¿qué dato necesitáis para saber qué versión la atendió?».

### 18:45 · Bloque 2 · GitHub Actions (10–19)

- Workflow, evento, job, step, runner, action, `permissions`. La PR solo tiene `contents: read`.
- **Qué es una action (11):** `action.yml` con `inputs`, `outputs` y `runs`; tres tipos; runner
  de GitHub frente a runner propio.
- **Los seis checks (12–13):** Calidad, Tests, Evaluación, Imagen, Dependencias y Workflows, en
  paralelo. `scripts/comprobar.sh` ejecuta los mismos en local. CodeQL corre aparte.
- **Tests con dobles (14):** el proveedor de IA se sustituye por un doble; entrada inválida (422),
  respuesta válida y fallo del proveedor (504 sin inventar respuesta).
- **Demo 1 (15) · el mismo camino para un cambio correcto y otro incorrecto.**
  1. `git switch plazo-de-atencion` y enseñar el diff: `SLA_HORAS` con las tres prioridades y un
     test para cada una. `bash scripts/comprobar.sh` → **6/6 en verde, 41 passed**.
     `bash scripts/abrir-pr.sh correcto` → la PR, y en unos 25 s los seis checks en verde y el
     merge permitido. Mensaje: GitHub ha hecho exactamente lo mismo que el portátil, en una
     máquina limpia. No se integra todavía (bloque 3).
  2. `git switch respuesta-por-defecto` y enseñar el diff: si el proveedor falla, una respuesta
     por defecto (parece amable) y un `import logging` que se quedó sin usar.
     `bash scripts/comprobar.sh` → **Calidad y Tests en rojo**, con la causa debajo: la línea del
     import (F401) y los dos tests que esperan un 504 sin respuesta inventada.
     `bash scripts/abrir-pr.sh incorrecto` → los mismos dos checks en rojo en la PR, la anotación de
     ruff en la línea del diff y el merge **bloqueado** por la regla de `main`.
  3. Moraleja: el build y el arranque funcionan en los dos casos; lo que separa uno de otro son
     los tests y el análisis. Cada check atrapa un tipo de error distinto.
- **CodeRabbit (16):** comenta la PR roja a los ≈3 min (no cerrarla antes). La diapositiva enseña
  un ensayo en el que acertó el problema pero propuso «actualizar los tests al nuevo contrato», que
  dejaría pasar el fallo. En el ensayo de este mismo cambio (PR #19, 23/11 por la noche) pidió
  quitar el import y **propuso el arreglo correcto** («quitar la respuesta por defecto para que un
  fallo del proveedor devuelva 504»); en la verde no comentó nada. Mensaje: el revisor con IA no es
  determinista; el test sí. Decide una persona y bloquea el test. Después:
  `bash scripts/abrir-pr.sh cerrar incorrecto`.
- **Ruleset y acciones por SHA (17):** un tag se puede mover; un SHA no.
- **Alternativas (18–19):** cambia quién mantiene la máquina; las garantías de la clase no.
- **Preguntas:** «¿Por qué el fallo lo detecta un test y no el build de Docker?» y «¿Por qué el
  VPS, que parece el más barato, no es siempre la mejor opción?».

### 19:05 · Bloque 3 · Artefacto, secretos y procedencia (20–24)

- Construir **una vez**. Una etiqueta se puede mover; el digest es la huella del contenido.
  Staging, producción y el rollback usan el digest.
- Dónde vive cada dato: `.env` local, secretos de GitHub (solo `OPENROUTER_API_KEY`, opcional);
  en la imagen, nada secreto.
- **Sin claves guardadas:** cada job recibe un token temporal con los permisos que declara; la
  atestación se firma con un token OIDC de corta duración.
- **Demo 2 (24):** integrar la PR verde (`gh pr merge plazo-de-atencion --squash --delete-branch`).
  `Entrega · main` repite los checks, publica la imagen en GHCR y anota el digest;
  `gh attestation verify` demuestra quién la construyó y desde qué commit.
- **Pregunta:** «¿Qué ganamos al desplegar por digest en lugar de por la etiqueta `latest`?».

### 19:17 · Bloque 4 · Staging, producción y despliegue sin corte (25–31)

- **La entrega real del ensayo (25):** el grafo de una ejecución completa (≈2 min y medio). Se
  enseña mientras corre la de clase.
- **Staging (26):** el job descarga el digest publicado, lo arranca endurecido y pasa el smoke
  con la versión esperada. Un job verde no basta: la API tiene que responder.
- **Producción:** el environment `produccion` exige aprobación. Al aprobar, la etiqueta
  `produccion` pasa a ese digest (se comprueba) y se crea la release `v1.1.0`.
- **Progresivos (29)** y **sin corte (30):** en vivo `uv run python extras/despliegue_sin_corte.py`
  (sin corte 0 fallos; parar y arrancar ≈60).
- **Demo 3 (31):** aprobar producción en **Review deployments** y abrir la release y el panel. La
  diapositiva enseña B en el ensayo (también en verde, pero sin plazo para «baja»): es el contraste
  con el cambio de hoy, que sí trae las tres prioridades y su test.
- **Pregunta:** «¿Qué diferencia hay entre "el job está en verde" y "producción ejecuta la v1.1.0"?».

### 19:34 · Bloque 5 · Observabilidad y rollback (32–38)

- Cuatro herramientas para cuatro preguntas: logging, monitoring, APM/trazas y error tracking.
  La demo implementa logs, vigilancia sintética, alerta (incidencia) y panel; APM y error
  tracking se explican, **no se integran**.
- Log estructurado (33): una línea JSON con `request_id`, `version`, `estado`, `duracion_ms`…
- **El fallo del ensayo (35):** no se repite en directo. En el ensayo, una versión con los seis
  checks en verde fallaba con la prioridad baja (500); la vigilancia lo encontró y **abrió la
  incidencia sola**, con la versión, el digest, el `request_id` y la línea `KeyError`. Es lo que
  pasa cuando un fallo no tiene test: hoy, el cambio correcto trae un test por prioridad.
- **Demo 4 (37):** lanzar `Vigilancia · producción` contra la `v1.1.0`: tres peticiones, una por
  prioridad, todas 200; ninguna incidencia; el panel con la versión nueva.
- **Demo 5 (38) · rollback como simulacro** (la diapositiva enseña el rollback real del ensayo): `Rollback · producción` con `v1.0.0`, aprobado. Sin
  reconstruir: prueba esa imagen y le devuelve la etiqueta. Vigilancia en verde con `v1.0.0` y
  vuelta a `v1.1.0` con el mismo workflow. Los equipos ensayan el rollback antes de necesitarlo.
- **Pregunta:** «¿El rollback arregla el código?».

### 19:50 · Bloque 6 · Datos y recuperación (39–40)

- Expand → migrar → contract. **Volver a una imagen antigua no revierte los datos.**
- Backups: RPO y RTO; una copia solo vale si se ha restaurado. `extras/` lo demuestra con SQLite.
- **Pregunta:** «Si la versión nueva escribió datos en una columna nueva y volvemos a la anterior, ¿qué pasa con ellos?».

### 19:54 · Práctica y cierre (41–42)

- Práctica opcional: [ejercicio.md](ejercicio.md), gratuita en un repositorio público. Evidencias:
  una PR verde y otra roja bloqueada, digest y atestación, aprobación de producción, vigilancia y
  rollback.
- Recordar el QR de S17. Próxima sesión: S19, evaluación y testing de sistemas de IA.

## Si algo falla en directo

| Situación | Qué hacer |
|---|---|
| Un workflow tarda más de 2 minutos | Explicar el grafo o una ejecución anterior; volver al final del bloque |
| GitHub no responde (githubstatus.com) | `comprobar.sh` en las dos ramas (mismos checks) y la imagen de respaldo; decirlo |
| `abrir-pr.sh` dice que la cuenta no puede escribir | `gh auth switch --user JoseAntonioNuevo` |
| Un check falla sin motivo aparente | Leer el log, no forzarlo; **Re-run failed jobs** |
| Producción no pide aprobación | Revisar **Settings → Environments → produccion → Required reviewers** |
| Pregunta fuera de alcance (Kubernetes, Terraform…) | Responder en una frase y apuntarla para el cierre |
