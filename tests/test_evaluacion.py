"""Tests de la evaluación. Sin red ni claves: usan las reglas de la demo o un doble."""

import asyncio
import json

import httpx
import pytest

from app import Clasificacion, ErrorProveedor, ProveedorDemo, ProveedorOpenRouter
from evaluacion.evaluar import (
    CASOS,
    Resultado,
    cargar_casos,
    crear_proveedor,
    evaluar,
    informe,
    main,
    resumir,
)


class DobleCaido:
    modelo = "doble-caido"

    async def clasificar(self, texto: str) -> Clasificacion:
        raise ErrorProveedor("proveedor_timeout", 504)


def test_el_conjunto_es_coherente():
    casos = cargar_casos()
    assert len(casos) >= 10
    # Cubre todas las categorías y prioridades: si no, una regresión podría pasar sin verse.
    assert {c["categoria"] for c in casos} == {"acceso", "facturacion", "tecnico", "consulta"}
    assert {c["prioridad"] for c in casos} == {"alta", "media", "baja"}


@pytest.mark.parametrize(
    ("linea", "mensaje"),
    [
        ('{"id": "a", "texto": "x", "categoria": "inventada", "prioridad": "alta"}', "etiqueta"),
        ('{"id": "a", "texto": "x", "categoria": "acceso", "prioridad": "baja"}\n' * 2, "repetid"),
    ],
)
def test_un_conjunto_incoherente_se_rechaza(tmp_path, linea, mensaje):
    ruta = tmp_path / "casos.jsonl"
    ruta.write_text(linea, encoding="utf-8")
    with pytest.raises(ValueError, match=mensaje):
        cargar_casos(ruta)


def test_resumir_cuenta_aciertos_por_campo_y_errores():
    resultados = [
        Resultado("a", ("acceso", "media"), ("acceso", "media"), None, 1.0),
        Resultado("b", ("acceso", "media"), ("acceso", "alta"), None, 1.0),
        Resultado("c", ("consulta", "baja"), None, "proveedor_timeout", 2.0),
    ]
    assert resumir(resultados) == {
        "total": 3,
        "aciertos": 1,
        "categoria": 2,
        "prioridad": 1,
        "errores": 1,
        "ms": 4.0,
    }


def test_un_fallo_del_proveedor_cuenta_como_error_y_no_como_acierto():
    casos = cargar_casos()[:2]
    resultados = asyncio.run(evaluar(DobleCaido(), casos))
    assert [r.error for r in resultados] == ["proveedor_timeout", "proveedor_timeout"]
    assert not any(r.acierto for r in resultados)
    assert "error `proveedor_timeout`" in informe(resultados, resumir(resultados), "x", 0.8)


def test_las_reglas_de_la_demo_superan_el_umbral(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    resumen_github = tmp_path / "resumen.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumen_github))
    assert main([]) == 0
    texto = resumen_github.read_text(encoding="utf-8")
    assert "`reglas-demo`" in texto
    assert "11/12" in texto  # las reglas no entienden «iniciar sesión»: un fallo real
    assert "::error" not in capsys.readouterr().out


def test_por_debajo_del_umbral_la_evaluacion_falla(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert main(["--umbral", "1"]) == 1
    assert "::error title=Evaluación por debajo del umbral::" in capsys.readouterr().out


def test_un_umbral_fuera_de_rango_se_rechaza():
    with pytest.raises(SystemExit):
        main(["--umbral", "0"])


def test_con_clave_se_evalua_el_modelo_real_sin_llamarlo_aqui(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-sintetica")
    monkeypatch.setenv("OPENROUTER_MODEL", "modelo-simulado")
    cliente = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    proveedor = crear_proveedor(cliente)
    assert isinstance(proveedor, ProveedorOpenRouter)
    assert proveedor.modelo == "modelo-simulado"
    monkeypatch.delenv("OPENROUTER_API_KEY")
    assert isinstance(crear_proveedor(cliente), ProveedorDemo)
    asyncio.run(cliente.aclose())


def test_los_casos_son_json_de_una_linea():
    for linea in CASOS.read_text(encoding="utf-8").splitlines():
        assert set(json.loads(linea)) == {"id", "texto", "categoria", "prioridad"}
