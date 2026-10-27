import requests

from flask import Blueprint, render_template


bp = Blueprint(
    "main",
    __name__
)


@bp.route("/")
def inicio():

    return render_template(
        "index.html"
    )


@bp.route("/noticias")
def noticias():

    return render_template(
        "noticias.html"
    )


@bp.route("/post")
def post():

    return render_template(
        "post.html"
    )


@bp.route("/calendario")
def calendario():

    url = "https://api.openf1.org/v1/meetings?year=2026"

    respuesta = requests.get(url)

    carreras = respuesta.json()


    tipos_circuito = {
        "Permanent": "Permanente",
        "Street": "Callejero",
        "Temporary": "Temporal",
        "Temporary - Street": "Temporal - Callejero"
    }


    for carrera in carreras:

        tipo_original = carrera.get(
            "circuit_type",
            ""
        )

        carrera["tipo_es"] = tipos_circuito.get(
            tipo_original,
            tipo_original
        )


    return render_template(
        "calendario.html",
        carreras=carreras
    )


@bp.route("/premium")
def premium():

    return render_template(
        "premium.html"
    )


@bp.route("/categorias")
def categorias():

    return render_template(
        "categorias.html"
    )