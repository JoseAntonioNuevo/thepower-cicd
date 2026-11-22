"""Genera el panel de producción: una página estática que publica GitHub Pages.

No guarda estado propio: lee de la API de GitHub lo que ya registran los workflows
(releases con su digest, ejecuciones de entrega, rollback y vigilancia, e incidentes).
Solo usa la biblioteca estándar y la CLI `gh` que trae el runner.

Uso (workflow «Panel»):  PROD_DIGEST=sha256:… python3 scripts/panel.py _site
"""

import html
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
ESTADOS = {
    "success": ("ok", "correcto"),
    "failure": ("ko", "fallo"),
    "cancelled": ("otro", "cancelado"),
    "skipped": ("otro", "omitido"),
    "waiting": ("pend", "esperando aprobación"),
    "in_progress": ("pend", "en curso"),
    "queued": ("pend", "en cola"),
}


def api(ruta: str):
    salida = subprocess.run(["gh", "api", ruta], check=True, capture_output=True, text=True)
    return json.loads(salida.stdout)


def ejecuciones(repo: str, archivo: str, cuantas: int) -> list[dict]:
    try:
        datos = api(f"repos/{repo}/actions/workflows/{archivo}/runs?per_page={cuantas}")
    except subprocess.CalledProcessError:  # el workflow aún no existe en main
        return []
    return [
        {
            "titulo": r["display_title"],
            "workflow": r["name"],
            "estado": r["conclusion"] or r["status"],
            "fecha": r["created_at"],
            "url": r["html_url"],
        }
        for r in datos["workflow_runs"]
    ]


def recoger(repo: str, prod_digest: str) -> dict:
    releases = []
    for r in api(f"repos/{repo}/releases?per_page=20"):
        encontrado = DIGEST.search(r.get("body") or "")
        releases.append(
            {
                "version": r["tag_name"],
                "url": r["html_url"],
                "fecha": r["created_at"],
                "commit": r["target_commitish"],
                "digest": encontrado.group(0) if encontrado else "",
            }
        )
    incidentes = [
        {
            "numero": i["number"],
            "titulo": i["title"],
            "abierto": i["state"] == "open",
            "fecha": i["created_at"],
            "url": i["html_url"],
        }
        for i in api(f"repos/{repo}/issues?labels=incidente&state=all&per_page=10")
        if "pull_request" not in i
    ]
    return {
        "repo": repo,
        "prod_digest": prod_digest,
        "generado": datetime.now(UTC).isoformat(),
        "releases": releases,
        "vigilancia": ejecuciones(repo, "vigilancia.yml", 24),
        "cambios": sorted(
            ejecuciones(repo, "entrega-main.yml", 8) + ejecuciones(repo, "rollback.yml", 8),
            key=lambda r: r["fecha"],
            reverse=True,
        )[:10],
        "incidentes": incidentes,
    }


# ------------------------------------------------------------------ HTML
def e(texto) -> str:
    return html.escape(str(texto), quote=True)


def fecha(iso: str) -> str:
    momento = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(MADRID)
    return momento.strftime("%d/%m/%Y %H:%M")


def estado(clave: str) -> str:
    clase, texto = ESTADOS.get(clave, ("otro", clave))
    return f'<span class="estado {clase}">{e(texto)}</span>'


def render(datos: dict) -> str:
    repo = datos["repo"]
    actual = next(
        (r for r in datos["releases"] if r["digest"] and r["digest"] == datos["prod_digest"]),
        None,
    )
    ultima = datos["vigilancia"][0] if datos["vigilancia"] else None
    abiertos = [i for i in datos["incidentes"] if i["abierto"]]

    if actual:
        produccion = (
            f'<a class="grande" href="{e(actual["url"])}">{e(actual["version"])}</a>'
            f"<p>commit <code>{e(actual['commit'][:7])}</code> · "
            f"<code>{e(actual['digest'][:19])}…</code></p>"
        )
    else:
        produccion = '<p class="grande">—</p><p>Todavía no hay una versión en producción.</p>'
    if ultima:
        vigilancia = (
            f'<p class="grande">{estado(ultima["estado"])}</p>'
            f'<p><a href="{e(ultima["url"])}">{fecha(ultima["fecha"])}</a></p>'
        )
    else:
        vigilancia = '<p class="grande">—</p><p>Sin comprobaciones todavía.</p>'
    incidentes_tarjeta = "".join(
        f'<li><a href="{e(i["url"])}">#{i["numero"]}</a> {e(i["titulo"])}</li>' for i in abiertos
    )

    cuadros = "".join(
        f'<a class="cuadro {ESTADOS.get(r["estado"], ("otro",))[0]}" href="{e(r["url"])}" '
        f'title="{fecha(r["fecha"])} · {e(ESTADOS.get(r["estado"], ("", r["estado"]))[1])}"></a>'
        for r in reversed(datos["vigilancia"])
    )
    filas_cambios = "".join(
        f"<tr><td>{fecha(r['fecha'])}</td><td>{e(r['workflow'])}</td>"
        f'<td><a href="{e(r["url"])}">{e(r["titulo"])}</a></td><td>{estado(r["estado"])}</td></tr>'
        for r in datos["cambios"]
    )
    marca = ' <span class="marca">en producción</span>'
    filas_versiones = "".join(
        f'<tr><td><a href="{e(r["url"])}">{e(r["version"])}</a>{marca if r is actual else ""}</td>'
        f"<td>{fecha(r['fecha'])}</td><td><code>{e(r['commit'][:7])}</code></td>"
        f"<td><code>{e(r['digest'][:19])}…</code></td></tr>"
        for r in datos["releases"]
    )
    filas_incidentes = "".join(
        f'<tr><td><a href="{e(i["url"])}">#{i["numero"]}</a></td><td>{e(i["titulo"])}</td>'
        f"<td>{estado('failure') if i['abierto'] else estado('success')}</td>"
        f"<td>{fecha(i['fecha'])}</td></tr>"
        for i in datos["incidentes"]
    )
    vacio = '<tr><td colspan="4" class="tenue">Nada todavía.</td></tr>'

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel de producción</title>
<style>
:root {{ --fondo:#f6f6f3; --tarjeta:#fff; --texto:#1d1d1b; --tenue:#66665f; --linea:#e3e3de;
  --ok:#1a7f37; --ko:#cf222e; --pend:#9a6700; --otro:#8c8c86; --enlace:#0b57d0; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fondo:#111213; --tarjeta:#1a1b1d;
  --texto:#ececea; --tenue:#a0a09a; --linea:#2c2d30; --ok:#3fb950; --ko:#f85149;
  --pend:#d29922; --otro:#6e6e69; --enlace:#8ab4f8; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--fondo); color:var(--texto);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:980px; margin:0 auto; padding:28px 16px 56px; }}
h1 {{ font-size:1.6rem; margin:0 0 4px; }} h2 {{ font-size:1.05rem; margin:32px 0 10px; }}
a {{ color:var(--enlace); }} code {{ font-size:.85em; }}
.tenue {{ color:var(--tenue); }}
.tarjetas {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px;
  margin-top:20px; }}
.tarjeta {{ background:var(--tarjeta); border:1px solid var(--linea); border-radius:10px;
  padding:14px 16px; }}
.tarjeta h3 {{ margin:0 0 6px; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em;
  color:var(--tenue); }}
.tarjeta p {{ margin:2px 0; }} .tarjeta ul {{ margin:4px 0 0; padding-left:18px; }}
.grande {{ font-size:1.5rem; font-weight:650; text-decoration:none; }}
.estado {{ font-weight:600; }} .ok {{ color:var(--ok); }} .ko {{ color:var(--ko); }}
.pend {{ color:var(--pend); }} .otro {{ color:var(--otro); }}
.cuadros {{ display:flex; flex-wrap:wrap; gap:4px; }}
.cuadro {{ width:18px; height:18px; border-radius:4px; background:var(--otro); }}
.cuadro.ok {{ background:var(--ok); }} .cuadro.ko {{ background:var(--ko); }}
.cuadro.pend {{ background:var(--pend); }}
.tabla {{ overflow-x:auto; background:var(--tarjeta); border:1px solid var(--linea);
  border-radius:10px; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ text-align:left; padding:8px 12px; border-bottom:1px solid var(--linea);
  white-space:nowrap; }}
th {{ font-size:.8rem; color:var(--tenue); font-weight:600; }} tr:last-child td {{ border:0; }}
.marca {{ font-size:.75rem; background:var(--ok); color:#fff; border-radius:999px;
  padding:1px 8px; margin-left:6px; }}
</style>
</head>
<body>
<main>
<h1>Panel de producción</h1>
<p class="tenue"><a href="https://github.com/{e(repo)}">{e(repo)}</a> · actualizado el
{fecha(datos["generado"])} (hora de Madrid)</p>
<p class="tenue">Demo de clase: «producción» es la imagen con la etiqueta <code>produccion</code>
en GHCR. La vigilancia la arranca cada hora y le envía peticiones ficticias.</p>

<div class="tarjetas">
  <section class="tarjeta"><h3>En producción</h3>{produccion}</section>
  <section class="tarjeta"><h3>Última vigilancia</h3>{vigilancia}</section>
  <section class="tarjeta"><h3>Incidentes abiertos</h3>
    <p class="grande {"ko" if abiertos else "ok"}">{len(abiertos)}</p>
    <ul>{incidentes_tarjeta}</ul></section>
</div>

<h2>Vigilancia · últimas comprobaciones (la más reciente a la derecha)</h2>
<div class="cuadros">{cuadros or '<span class="tenue">Sin comprobaciones todavía.</span>'}</div>

<h2>Entregas y rollbacks</h2>
<div class="tabla"><table>
<tr><th>Fecha</th><th>Workflow</th><th>Cambio</th><th>Resultado</th></tr>
{filas_cambios or vacio}
</table></div>

<h2>Versiones publicadas</h2>
<div class="tabla"><table>
<tr><th>Versión</th><th>Publicada</th><th>Commit</th><th>Digest</th></tr>
{filas_versiones or vacio}
</table></div>

<h2>Incidentes</h2>
<div class="tabla"><table>
<tr><th>Número</th><th>Título</th><th>Estado</th><th>Abierto</th></tr>
{filas_incidentes or vacio}
</table></div>
</main>
</body>
</html>
"""


def main(argv: list[str]) -> int:
    destino = Path(argv[1] if len(argv) > 1 else "_site")
    datos = recoger(os.environ["GITHUB_REPOSITORY"], os.getenv("PROD_DIGEST", ""))
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(render(datos), encoding="utf-8")
    (destino / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), "utf-8")
    print(f"Panel generado en {destino}/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
