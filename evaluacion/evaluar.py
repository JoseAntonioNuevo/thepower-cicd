"""Evaluación del clasificador: incidencias ficticias con su respuesta esperada y un umbral.

Los tests comprueban que el código hace lo que dice; la evaluación mide **cuánto acierta**.
Se ejecuta en cada pull request (job «Evaluación») y bloquea la integración si los aciertos
bajan del umbral.

- Sin el secreto OPENROUTER_API_KEY evalúa el clasificador de reglas de la demo: gratis y
  determinista. Es lo que ocurre en clase y en las PR que llegan desde un fork.
- Con el secreto evalúa el modelo real con el mismo conjunto (una llamada de pago por caso).

Se evalúa al proveedor (`clasificar`), no al endpoint: mide la calidad de la clasificación.
Los fallos de la API los cubren los tests, el smoke y la vigilancia.

Uso: uv run python -m evaluacion.evaluar [--umbral 0.8]
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from app import ErrorProveedor, Proveedor, ProveedorDemo, ProveedorOpenRouter, config_openrouter

CASOS = Path(__file__).with_name("casos.jsonl")
CATEGORIAS = {"acceso", "facturacion", "tecnico", "consulta"}
PRIORIDADES = {"alta", "media", "baja"}


@dataclass(frozen=True)
class Resultado:
    id: str
    esperado: tuple[str, str]
    obtenido: tuple[str, str] | None  # None si el proveedor falló
    error: str | None
    ms: float

    @property
    def acierto(self) -> bool:
        return self.obtenido == self.esperado


def cargar_casos(ruta: Path = CASOS) -> list[dict]:
    """Lee el conjunto y comprueba que es coherente antes de gastar una sola llamada."""
    casos = [json.loads(linea) for linea in ruta.read_text("utf-8").splitlines() if linea.strip()]
    ids = [caso["id"] for caso in casos]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay identificadores de caso repetidos")
    for caso in casos:
        if caso["categoria"] not in CATEGORIAS or caso["prioridad"] not in PRIORIDADES:
            raise ValueError(f"El caso {caso['id']} tiene una etiqueta que no existe")
    return casos


async def evaluar(proveedor: Proveedor, casos: list[dict]) -> list[Resultado]:
    """Un caso cada vez: son pocas llamadas y así no saturamos al proveedor."""
    resultados = []
    for caso in casos:
        inicio = time.perf_counter()
        try:
            clasificacion = await proveedor.clasificar(caso["texto"])
            obtenido, error = (clasificacion.categoria, clasificacion.prioridad), None
        except ErrorProveedor as fallo:
            # Un fallo del proveedor cuenta como error: no se inventa una respuesta.
            obtenido, error = None, fallo.codigo
        resultados.append(
            Resultado(
                id=caso["id"],
                esperado=(caso["categoria"], caso["prioridad"]),
                obtenido=obtenido,
                error=error,
                ms=round((time.perf_counter() - inicio) * 1000, 1),
            )
        )
    return resultados


def resumir(resultados: list[Resultado]) -> dict:
    def coincide(r: Resultado, campo: int) -> bool:
        return r.obtenido is not None and r.obtenido[campo] == r.esperado[campo]

    return {
        "total": len(resultados),
        "aciertos": sum(r.acierto for r in resultados),
        "categoria": sum(coincide(r, 0) for r in resultados),
        "prioridad": sum(coincide(r, 1) for r in resultados),
        "errores": sum(r.error is not None for r in resultados),
        "ms": round(sum(r.ms for r in resultados), 1),
    }


def porcentaje(valor: float) -> str:
    """0.917 -> «91,7 %»; 0.8 -> «80 %» (formato español)."""
    return f"{valor * 100:.1f}".removesuffix(".0").replace(".", ",") + " %"


def informe(resultados: list[Resultado], resumen: dict, modelo: str, umbral: float) -> str:
    """Tabla en Markdown: GitHub la muestra en el resumen de la ejecución."""
    tasa = resumen["aciertos"] / resumen["total"]
    estado = "✅" if tasa >= umbral else "❌"
    origen = (
        "reglas de la demo: gratis y deterministas"
        if modelo == ProveedorDemo.modelo
        else "modelo real a través de OpenRouter"
    )
    lineas = [
        f"### Evaluación del clasificador · {estado} {resumen['aciertos']}/{resumen['total']} "
        f"({porcentaje(tasa)}) · umbral {porcentaje(umbral)}",
        "",
        f"Proveedor evaluado: `{modelo}` ({origen}).",
        "",
        "| Caso | Esperado | Obtenido | |",
        "|---|---|---|---|",
    ]
    for r in resultados:
        obtenido = " · ".join(r.obtenido) if r.obtenido else f"error `{r.error}`"
        marca = "✅" if r.acierto else "❌"
        lineas.append(f"| `{r.id}` | {' · '.join(r.esperado)} | {obtenido} | {marca} |")
    lineas += [
        "",
        f"Categoría: {resumen['categoria']}/{resumen['total']} · "
        f"Prioridad: {resumen['prioridad']}/{resumen['total']} · "
        f"Errores del proveedor: {resumen['errores']} · "
        f"Tiempo: {str(resumen['ms']).replace('.', ',')} ms",
        "",
    ]
    return "\n".join(lineas)


def crear_proveedor(cliente: httpx.AsyncClient) -> Proveedor:
    clave, modelo, ruta = config_openrouter()
    if not clave:
        return ProveedorDemo()
    return ProveedorOpenRouter(clave, modelo, ruta, cliente)


async def ejecutar(umbral: float) -> int:
    casos = cargar_casos()
    async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as cliente:
        proveedor = crear_proveedor(cliente)
        resultados = await evaluar(proveedor, casos)
    resumen = resumir(resultados)
    texto = informe(resultados, resumen, proveedor.modelo, umbral)
    print(texto)
    if ruta := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(ruta, "a", encoding="utf-8") as resumen_github:
            resumen_github.write(texto)
    tasa = resumen["aciertos"] / resumen["total"]
    if tasa < umbral:
        # Esta línea la convierte GitHub en una anotación roja en la PR.
        print(
            f"::error title=Evaluación por debajo del umbral::{porcentaje(tasa)} de aciertos; "
            f"el mínimo es {porcentaje(umbral)}"
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--umbral", type=float, default=0.8, help="aciertos mínimos (0–1)")
    args = parser.parse_args(argv)
    if not 0 < args.umbral <= 1:
        parser.error("el umbral debe estar entre 0 y 1")
    return asyncio.run(ejecutar(args.umbral))


if __name__ == "__main__":
    sys.exit(main())
