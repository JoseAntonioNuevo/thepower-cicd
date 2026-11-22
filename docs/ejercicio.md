# Práctica opcional S18 · Pipeline de CI/CD con tests automáticos

Enunciado original (29/09/2026): automatiza las pruebas, la construcción y el despliegue de una
pequeña API de IA. Un cambio con errores debe quedar bloqueado antes de desplegarse. Demuestra
además cómo detectar un fallo y volver a una versión anterior en un entorno de pruebas.

La práctica es **opcional** (aclaración de la escuela del 04/11). Este repositorio es una solución
completa de referencia y **gratuita**: todo funciona en un repositorio público de GitHub, sin
nube ni tarjeta. Puedes partir de él o de tu propia API de la sesión 16. Usa solo incidencias
ficticias. Dedicación orientativa: 4–6 horas.

## Pasos

1. **API y configuración.** FastAPI con `/health` y un endpoint de IA. Configuración local
   (`.env`, fuera de Git) y en GitHub (secretos y variables). Ningún modelo ni clave en el código.
2. **Tests sin APIs de pago.** Con un doble del proveedor: entrada inválida, respuesta válida y
   fallo del proveedor. `uv run pytest` debe pasar sin red.
3. **CI en cada pull request.** Dependencias bloqueadas (`uv sync --locked`), análisis (ruff),
   pytest con cobertura mínima y `docker build` con smoke del contenedor. Ese workflow solo lee
   el repositorio (`permissions: contents: read`).
4. **Evaluación.** Un conjunto fijo de casos con su respuesta esperada y un umbral de aciertos
   que también bloquea la PR.
5. **Bloqueo demostrado.** Una PR con un fallo deliberado queda roja y no se puede integrar
   (regla de `main` con los checks obligatorios). Guarda captura o enlace.
6. **Acciones por SHA.** Cada `uses:` externo con el SHA completo de 40 caracteres de un commit
   verificado y la versión en un comentario. `zizmor` en el CI para comprobarlo.
7. **Publicar desde main.** Repite las comprobaciones sobre el commit integrado; si pasan,
   construye una vez, publica en GHCR con el token del job y registra el digest y una
   atestación de procedencia (`gh attestation verify`).
8. **Entornos.** `staging` y `produccion` solo admiten `main`; producción exige aprobación.
   Ambos usan el digest publicado, sin reconstruir, y comprueban `/health` y una petición funcional.
9. **Observar.** Logs con `request_id`, versión, duración y estado, sin secretos. Una vigilancia
   programada que, si falla, abre una incidencia con el `request_id` del error.
10. **Rollback.** Lleva una segunda versión a producción y vuelve a la anterior con su digest.
    Repite la comprobación.
11. **Datos.** En el README: despliegue progresivo, cambios de base de datos compatibles con la
    versión anterior y copias con prueba de restauración (no hace falta añadir una base de datos).

## Entrega

Enlace al repositorio con los workflows, los tests y evidencias: PR bloqueada, digest publicado
y atestación, aprobación de producción, incidencia abierta por la vigilancia y rollback. Se
valoran el bloqueo de cambios defectuosos, el uso del mismo artefacto, que no haya claves
guardadas y la recuperación comprobable.

**Ampliación opcional:** despliega la imagen en un servicio real (en AWS, ECS o Lambda con OIDC
en lugar de claves) y apunta el smoke y la vigilancia a su URL; o una migración compatible y una
restauración con datos ficticios (`extras/`). Nunca sobre producción real.

## Comprobación rápida antes de entregar

- [ ] La PR defectuosa está en rojo y su workflow solo tiene `contents: read`.
- [ ] El digest de producción es el que publicó `Entrega · main` para ese commit.
- [ ] `gh attestation verify` acepta la imagen de producción.
- [ ] Un `workflow_dispatch` de rollback desde otra rama no llega a desplegar.
- [ ] Después del rollback, `/health` y `/clasificar` responden con la versión esperada.
- [ ] Ningún log contiene el texto de la incidencia ni una clave.
