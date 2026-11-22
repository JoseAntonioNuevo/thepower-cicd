"""El panel se genera con datos de la API de GitHub; aquí, con datos simulados."""

from scripts import panel

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def datos(prod_digest: str) -> dict:
    return {
        "repo": "alumno/thepower-cicd",
        "prod_digest": prod_digest,
        "generado": "2026-11-25T17:30:00+00:00",
        "releases": [
            {
                "version": "v1.1.0",
                "url": "https://x/v1.1.0",
                "fecha": "2026-11-25T17:20:00Z",
                "commit": "b" * 40,
                "digest": DIGEST_B,
            },
            {
                "version": "v1.0.0",
                "url": "https://x/v1.0.0",
                "fecha": "2026-11-23T10:00:00Z",
                "commit": "a" * 40,
                "digest": DIGEST_A,
            },
        ],
        "vigilancia": [
            {
                "titulo": "Vigilancia",
                "workflow": "Vigilancia · producción",
                "estado": "failure",
                "fecha": "2026-11-25T17:25:00Z",
                "url": "https://x/run/2",
            },
        ],
        "cambios": [
            {
                "titulo": "<script>alert(1)</script>",
                "workflow": "Entrega · main",
                "estado": "waiting",
                "fecha": "2026-11-25T17:20:00Z",
                "url": "https://x/run/1",
            },
        ],
        "incidentes": [
            {
                "numero": 7,
                "titulo": "Incidente: la vigilancia falla con v1.1.0",
                "abierto": True,
                "fecha": "2026-11-25T17:26:00Z",
                "url": "https://x/issues/7",
            },
        ],
    }


def test_marca_la_version_en_produccion_por_su_digest():
    pagina = panel.render(datos(DIGEST_A))
    assert 'v1.0.0</a> <span class="marca">en producción</span>' in pagina
    assert 'v1.1.0</a> <span class="marca">' not in pagina
    assert "25/11/2026 18:30" in pagina  # hora de Madrid
    assert "esperando aprobación" in pagina
    assert '<span class="estado ko">abierta</span>' in pagina


def test_escapa_el_texto_que_viene_de_github():
    pagina = panel.render(datos(DIGEST_B))
    assert "<script>" not in pagina
    assert "&lt;script&gt;" in pagina


def test_sin_nada_publicado_no_falla():
    vacio = datos("") | {"releases": [], "vigilancia": [], "cambios": [], "incidentes": []}
    pagina = panel.render(vacio)
    assert "Todavía no hay una versión en producción." in pagina


def job(nombre: str, estado: str, conclusion: str | None) -> dict:
    return {"name": nombre, "status": estado, "conclusion": conclusion}


def test_una_ejecucion_cuenta_su_resultado_aunque_el_panel_siga_en_marcha():
    vigilancia = [
        job("Peticiones sintéticas a producción", "completed", "failure"),
        job("panel / Construir el panel", "in_progress", None),
    ]
    assert panel.estado_sin_panel(vigilancia, "in_progress") == "failure"
    entrega = [
        job("comprobaciones / Tests", "completed", "success"),
        job("Producción", "completed", "success"),
        job("panel / Construir el panel", "in_progress", None),
    ]
    assert panel.estado_sin_panel(entrega, "in_progress") == "success"


def test_si_falta_algo_por_terminar_se_mantiene_el_estado_de_la_ejecucion():
    esperando = [job("Staging", "completed", "success"), job("Producción", "waiting", None)]
    assert panel.estado_sin_panel(esperando, "waiting") == "waiting"
    assert panel.estado_sin_panel([job("Staging", "completed", "timed_out")], "x") == "failure"
