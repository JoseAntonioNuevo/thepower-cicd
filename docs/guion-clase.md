# S18 · Guion de la clase (90 minutos)

**Miércoles 25/11/2026 · grupo L/X · 18:30–20:00 (hora de Madrid).**
Presentación: `material/S18/presentaciones/S18-cicd-monitorizacion.pptx` (42 diapositivas).
Comandos exactos, en el mismo orden: [comandos.md](comandos.md).

> **Cambio del 23/11/2026: demo nativa de GitHub.** La demo en directo ya no despliega en AWS:
> usa el repositorio público `JoseAntonioNuevo/thepower-cicd` con Actions, GHCR, environments,
> releases, vigilancia y panel en Pages (todo gratuito). El guion y las 42 diapositivas siguen
> ese recorrido, con resultados y capturas reales del ensayo en GitHub del 23/11. AWS aparece
> solo como «en una plataforma real» (versión completa en `material/S18/referencia-aws/`).

La teoría y la demo se alternan: cada bloque termina en algo que se ve en pantalla y en una
pregunta para el grupo. La práctica posterior es **opcional** (aclaración de Laura del 04/11).

## Antes de conectar

- Terminal con letra grande en `~/Documents/the-power/thepower-cicd`, en `main` y al día;
  `uv sync --locked` hecho. Docker arrancado e imagen local de respaldo construida (comandos.md, paso 0).
- Pestañas: el repositorio, **Actions**, **Pull requests**, la release `v1.0.0`,
  **Settings → Environments**, **Settings → Rules** y el panel en GitHub Pages.
- Estado de partida comprobado: `v1.0.0` (versión A) en producción, ninguna incidencia abierta,
  ninguna PR de la demo abierta. Las ejecuciones tardan 1–2 minutos: se lanzan en directo y,
  mientras corren, se explica el grafo o una ejecución anterior.
- Si GitHub no responde: el recorrido tiene versión local real (pytest, Docker, `vigilancia.sh`)
  y se dice abiertamente.
- Nada de credenciales, tokens ni el archivo `.env` en pantalla.

## Recorrido

| Hora | Min | Diapositivas | Qué se enseña en diapositiva | Qué se hace en vivo |
|---|---:|---|---|---|
| 18:30–18:33 | 3 | 1–2 | Objetivo; QR de **S17 (23/11)** | Responder al QR un minuto |
| 18:33–18:39 | 6 | 3–5 | **Punto de partida:** qué es CI/CD (bucle código → construir → probar → publicar → desplegar → monitorizar; sin y con CI/CD); qué es monitorizar (cuatro señales doradas, señales propias de IA, ciclo de un incidente); seis casos de uso y las cinco métricas DORA | Preguntar cómo publican hoy y cuál de los seis casos les ha pasado |
| 18:39–18:45 | 6 | 6–9 | Caso conductor: la API de S16 con garantías; CI y entrega continua en los workflows de la demo; entornos y configuración; la cadena commit → digest → release → `request_id` | Abrir el repositorio: `app.py`, `.github/workflows/`, `evaluacion/`, `scripts/` |
| 18:45–19:05 | 20 | 10–19 | Anatomía de un workflow; **qué es una action** (action.yml, tipos, runners); los seis workflows; los seis checks de la PR; tests con dobles; **CodeRabbit** como revisor con IA (16); ruleset y acciones por SHA; **alternativas** (Cloudflare Workers Builds, GitLab, CodeBuild, VPS propio) con precios | **PR con fallo**: aplicar `cambios/01`, ver los seis checks en paralelo, Tests en rojo y la PR bloqueada; esperar ≈3 min el comentario de CodeRabbit |
| 19:05–19:17 | 12 | 20–24 | Construir una vez; etiqueta frente a digest; GHCR; variables y secretos; tokens del job; procedencia verificable (atestación SLSA firmada con Sigstore) | **PR de B** en verde y merge; `Entrega · main` publica en GHCR; digest y `gh attestation verify` |
| 19:17–19:34 | 17 | 25–31 | La entrega real del ensayo (25); staging y producción con aprobación; rolling y circuit breaker (ejemplo ECS); smoke contra la API; despliegue progresivo (rolling, blue/green, canary, lineal); **cómo se demuestra un despliegue sin corte** | `extras/despliegue_sin_corte.py` (7 s); staging en verde; **aprobar producción** de B (`v1.1.0`) |
| 19:34–19:50 | 16 | 32–38 | Logging y monitoring; log estructurado (línea real de B); **APM** (cascada de spans, `trace_id` frente a `request_id`); demo 4 con la incidencia real; **error tracking** (eventos agrupados por huella); vigilancia, alerta y panel en Pages; rollback | **Vigilancia** → incidencia abierta → `request_id` → `KeyError`; panel; **rollback a v1.0.0** |
| 19:50–19:54 | 4 | 39–40 | Migraciones expand/contract; backups, RPO/RTO y restauración | `extras/migracion_y_restauracion.py` (30 s) |
| 19:54–20:00 | 6 | 41–42 | Práctica opcional, evidencias que se piden y cierre | Preguntas; recordar el QR |

**Redistribución del 23/11/2026** (demo nativa de GitHub; dos diapositivas nuevas: 16 CodeRabbit y
25 la entrega real del ensayo): la 16 (2 min) sale de la demo 1 (15, de 4 a 3 min) y de precios
(19, de 2 a 1 min); la 25 (2 min) sale de staging y producción (26) y del smoke (28), un minuto
cada una. Ningún bloque cambia de duración. Los párrafos siguientes conservan la numeración de
su fecha: desde la 16 todo sube un número y desde la 25, dos.

**Redistribución del 17/11/2026** (tres diapositivas nuevas: 27 APM, 29 error tracking, 33 despliegue
sin corte, 8 minutos): se recorta un minuto a 10 (comprobaciones de la PR), 17 (secretos), 21
(desplegar), 22 (rolling), 25 (mapa de observabilidad), 32 (progresivos), 34 (migraciones) y 37
(cierre). La franja exacta de cada diapositiva está al principio de sus notas.

**Redistribución del 20/11/2026** (tres diapositivas de punto de partida al principio: 3 qué es CI/CD, 4 qué es
monitorizar, 5 casos de uso; 6 minutos): se recorta un minuto al caso conductor (6), dos a «tres automatizaciones»
(7, que ahora repasa lo visto en la 3), uno a entornos (8), uno a la cadena (9) y uno a la demo de desplegar B (27).
Desde la 3, todas las diapositivas citadas antes del 20/11 suben tres números.

**Revisión del 20/11/2026.** Progresivos y «sin corte, cómo se demuestra» pasan del bloque 6 al bloque 4, detrás de la
verificación (ahora 27 y 28). Van antes de desplegar B (29), que debe seguir justo antes del bloque 5 porque el fallo de B
se investiga en la demo 4. Observabilidad y rollback pasan a 30–36 (19:34–19:50); el bloque 6 queda en migraciones y
backups (37–38). No cambia la duración de ninguna diapositiva; la 7 ahora sitúa CI y CD en los workflows de la demo.

## Bloque a bloque

### 18:30 · Apertura (diapositivas 1–2)

- El objetivo no es «tener un pipeline», sino **poder demostrar** tres cosas: un cambio
  defectuoso no llega a desplegarse, lo desplegado es exactamente lo que se probó y se puede
  volver a una versión conocida.
- QR: evalúa la **S17 del 23/11** (Bedrock + Lambda). Un minuto para rellenarlo; Laura insiste
  en que las respuestas son importantes.
- El grupo L/X tuvo la S16 con otro profesor: la demo trae su propia API (la misma tarea de
  clasificación de incidencias ficticias), no hace falta haber hecho la de José.
- **Pregunta:** «¿Qué tendría que pasar para que os fiarais de desplegar un viernes a las 19:00?».

### 18:33 · Punto de partida · qué es CI/CD y qué es monitorizar (3–5)

- **3 · Qué es CI/CD.** Bucle infinito: a la izquierda CI (código, construir, probar), a la derecha CD
  (publicar, desplegar) y la monitorización cerrando el círculo. Columna «sin CI/CD» frente a «con CI/CD»:
  cada línea de «con» es una parte de la clase.
- **4 · Qué es monitorizar.** Panel ilustrativo con las cuatro señales doradas (latencia, tráfico, errores,
  saturación); señales propias de una app de IA (tokens, coste, latencia del modelo, calidad → S19); ciclo de
  un incidente: detectar → avisar → diagnosticar → recuperar → aprender, que es lo que se hará en el bloque 5.
- **5 · Casos de uso.** Seis situaciones típicas con «sin» y «con» (un cambio rompe la API, cambiar de modelo,
  error de madrugada, volver atrás, factura de tokens, publicar a menudo) y las cinco métricas DORA.
- **Preguntas:** «¿A cuál de las dos columnas se parece cómo publicáis hoy?» y «¿Cuál de los seis casos os ha pasado?».

### 18:39 · Caso conductor y bloque 1 · CI/CD y entornos (6–9)

- CI = integrar a menudo y comprobar cada cambio automáticamente. CD tiene dos lecturas:
  *entrega continua* (siempre hay un artefacto listo; desplegar es una decisión) y *despliegue
  continuo* (se despliega solo). La demo hace **entrega continua**: producción exige aprobación.
- Entornos: local, CI, staging, producción. La **misma imagen** en todos; cambia la configuración.
- La cadena que conecta todo: commit → comprobaciones → imagen → **digest** → release →
  etiqueta `produccion` → cada petición lleva `version` = commit. Con ella se responde «¿qué
  código atendió esta petición?».
- Honestidad: GitHub no aloja la API. Staging arranca la imagen en el runner y producción es la
  etiqueta `produccion` que ejecutaría el servidor. En AWS cambiarían esos dos jobs; el resto no.
- **En vivo:** recorrer el repositorio (un archivo de app, tests, evaluación, seis workflows).
- **Pregunta:** «Si mañana falla una petición, ¿qué dato necesitáis para saber qué versión la atendió?».

### 18:45 · Bloque 2 · GitHub Actions (10–19)

- Workflow, evento, job, step, runner, action, `permissions`. Un job no tiene más permisos de
  los que declara: la PR solo tiene `contents: read`.
- **Qué es una action (11):** un paso reutilizable que vive en su propio repositorio y se describe
  con `action.yml`: `inputs`, `outputs` y `runs`. Tres tipos: JavaScript, contenedor y compuesta.
  Runner de GitHub (máquina limpia; gratis e ilimitado en repositorios públicos) frente a runner propio.
- Los seis checks de `comprobaciones.yml`, en paralelo: **Calidad** (lock, ruff), **Tests**
  (cobertura ≥ 90 %), **Evaluación** (≥ 80 % de aciertos; enlaza con S19), **Imagen** (build y
  smoke), **Dependencias** (dependency review y pip-audit) y **Workflows** (actionlint, zizmor,
  shellcheck). CodeQL corre aparte y no es obligatorio. Lo llaman la PR y `main`.
- Tests: el proveedor de IA se sustituye por un doble. Tres casos del enunciado: entrada
  inválida (422), respuesta válida y fallo del proveedor (504 sin inventar respuesta).
- **Demo · PR con fallo.** `cambios/01` «mejora» la API devolviendo una respuesta por defecto
  cuando el proveedor falla. Parece razonable; dos tests lo detectan. El check Tests queda en
  rojo y la regla de `main` bloquea el merge.
- **CodeRabbit (16):** app de revisión con IA instalada en la cuenta (check de terceros, no
  obligatorio). En el ensayo, en unos tres minutos resumió la PR y comentó las líneas: acertó el
  problema (dos tests rotos y un cliente que no sabe que el proveedor falló), pero propuso
  «actualizar los tests al nuevo contrato», que dejaría pasar el fallo. Decide una persona; bloquea
  el test. Dejar la PR abierta ≈3 min: si se cierra antes, CodeRabbit responde «Review failed: the
  pull request is closed».
- Acciones fijadas al SHA de 40 caracteres: un tag se puede mover; un SHA no. `zizmor` lo comprueba
  en cada PR y Dependabot propone las actualizaciones (con una semana de espera).
- **Alternativas (18–19):** Cloudflare Workers Builds, GitLab CI/CD, AWS CodeBuild + CodePipeline
  y un VPS propio. Mensaje: cambia quién mantiene la máquina; las garantías de la clase no.
- **Pregunta:** «¿Por qué el fallo lo detecta un test y no el build de Docker?».
- **Pregunta (alternativas):** «¿Por qué el VPS, que parece el más barato, no es siempre la mejor opción?».

### 19:05 · Bloque 3 · Artefacto, secretos y procedencia (20–24)

- Construir **una vez**. Una etiqueta es un nombre que puede apuntar a otra imagen; el digest es
  la huella del contenido. Staging, producción y el rollback usan el digest.
- Dónde vive cada dato: `.env` local (fuera de Git), variables y secretos de GitHub (el único
  secreto opcional es `OPENROUTER_API_KEY`, para evaluar el modelo real). En la imagen, nada secreto.
- **Sin claves guardadas:** cada job recibe un token temporal de GitHub con los permisos que
  declara (`packages: write` para publicar). La atestación se firma con un token OIDC de corta
  duración: es el mismo mecanismo que usaría AWS para dar credenciales de una hora a un rol.
- **Demo:** PR de B (`cambios/02`) con los seis checks en verde → merge → `Entrega · main` publica
  la imagen en GHCR; en el resumen, el digest. `gh attestation verify` demuestra quién la construyó
  y desde qué commit.
- **Pregunta:** «¿Qué ganamos al desplegar por digest en lugar de por la etiqueta `latest`?».

### 19:17 · Bloque 4 · Staging, producción y despliegue sin corte (25–31)

- **La entrega real (25):** captura del grafo de la ejecución de B en el ensayo (seis checks →
  publicar → staging → producción → panel, ≈2 min y medio). Se enseña mientras corre la de clase.

- **Staging:** el job descarga exactamente el digest publicado, lo arranca endurecido
  (`--read-only`, `--cap-drop ALL`) y pasa el smoke con la versión esperada. Un job verde no
  basta: la API tiene que responder y ser la versión correcta.
- **Producción:** el environment `produccion` exige aprobación. Al aprobar, la etiqueta
  `produccion` pasa a señalar el mismo digest (se comprueba) y se crea la release `v1.1.0` con
  las notas generadas. El historial queda en **Environments**.
- **Progresivos (29):** rolling, blue/green, canary, lineal. Necesitan algo que reparta el tráfico
  (balanceador, Service Connect, porcentajes de versiones); la demo no despliega en un servidor.
- **Sin corte, cómo se demuestra (30):** endpoint estable, readiness y drenaje; cero fallos antes,
  durante y después. En vivo, `uv run python extras/despliegue_sin_corte.py`: sin corte 0 fallos;
  parar y arrancar ≈60 fallos.
- **Demo (31):** aprobar producción de B y abrir la release y el panel.
- **Pregunta:** «¿Qué diferencia hay entre "el job está en verde" y "producción ejecuta B"?».

### 19:34 · Bloque 5 · Observabilidad y rollback (32–38)

- Cuatro herramientas para cuatro preguntas: logging (qué pasó en una petición), monitoring
  (cómo va el servicio), APM/trazas (dónde se va el tiempo) y error tracking (agrupar
  excepciones y avisar). La demo implementa logs, vigilancia sintética, alerta (incidencia) y
  panel; APM y error tracking se explican, **no se integran**.
- Log estructurado: una línea JSON con `request_id`, `version`, `ruta`, `estado`, `duracion_ms`,
  `proveedor_ms`. Nunca el texto del usuario ni secretos.
- **APM (34)** y **error tracking (36):** esquemas rotulados como ilustrativos; ni OpenTelemetry
  ni Sentry están integrados.
- **Demo · el fallo que los tests no cubrían (35).** Se lanza `Vigilancia · producción`: tres
  peticiones, una por prioridad. B responde 500 a la de prioridad baja. El workflow queda en rojo
  y **abre una incidencia** con la versión, el digest, el `request_id` y la línea `excepcion` con
  `KeyError`. El panel la muestra. ¿Por qué no lo vio staging? Su smoke solo prueba un caso.
- **Vigilancia, alerta y panel (37):** captura real del panel del ensayo; la alerta es la incidencia.
- **Rollback (38):** `Rollback · producción` con `v1.0.0`, aprobado. Sin reconstruir: prueba esa imagen
  y le devuelve la etiqueta. Se repite la vigilancia: verde, y la incidencia se cierra sola.
  Después, arreglar hacia delante con `cambios/03` (el test que faltaba, primero en rojo).
- **Pregunta:** «¿El rollback arregla el código?».

### 19:50 · Bloque 6 · Datos y recuperación (39–40)

- Expand → migrar → contract. Durante un despliegue y un rollback conviven dos versiones: el
  esquema debe valer para las dos. **Volver a una imagen antigua no revierte los datos.**
- Backups: RPO y RTO; una copia solo vale si se ha restaurado. `extras/` lo demuestra con SQLite.
- **Pregunta:** «Si B escribió datos en una columna nueva y volvemos a A, ¿qué pasa con ellos?».

### 19:54 · Práctica y cierre (41–42)

- Práctica opcional: [ejercicio.md](ejercicio.md), gratuita en un repositorio público.
  Evidencias: PR roja, digest y atestación, aprobación de producción, incidencia de la
  vigilancia y rollback.
- Recordar el QR de S17. Próxima sesión: S19, evaluación y testing de sistemas de IA.

## Si algo falla en directo

| Situación | Qué hacer |
|---|---|
| Un workflow tarda más de 2 minutos | Explicar el grafo o una ejecución anterior; volver al final del bloque |
| GitHub no responde (githubstatus.com) | Recorrido local equivalente (comandos.md) y decirlo |
| Un check falla sin motivo aparente | Es la demo de que «un job verde no basta»: leer el log, no forzarlo; **Re-run failed jobs** |
| Producción no pide aprobación | Revisar **Settings → Environments → produccion → Required reviewers** |
| Pregunta fuera de alcance (Kubernetes, Terraform…) | Responder en una frase y apuntarla para el cierre |
