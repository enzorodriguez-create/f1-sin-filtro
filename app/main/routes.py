import requests


from flask import Blueprint, render_template
from app.models import (Publicacion,  BloquePublicacion, ImagenCarrusel)


bp = Blueprint(
    "main",
    __name__
)


@bp.route("/")
def inicio():

    # Obtengo las últimas 4
    # publicaciones publicadas
    publicaciones = Publicacion.query.filter_by(
        estado="publicada"
    ).order_by(
        Publicacion.id.desc()
    ).limit(4).all()


    # La publicación más nueva
    # va a ser la noticia principal
    publicacion_principal = None


    # Las siguientes van abajo
    publicaciones_secundarias = []


    if publicaciones:

        publicacion_principal = publicaciones[0]

        publicaciones_secundarias = publicaciones[1:4]


    return render_template(
        "index.html",
        publicacion_principal=publicacion_principal,
        publicaciones_secundarias=publicaciones_secundarias
    )


@bp.route("/noticias")
def noticias():

    return render_template(
        "noticias.html"
    )


@bp.route(
    "/post/<int:id_publicacion>"
)
def post(id_publicacion):

    # Obtengo la publicación
    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        estado="publicada"
    ).first()


    # Compruebo que exista
    if not publicacion:

        return "Publicación no encontrada."


    # Obtengo todos los bloques
    # respetando el orden en que
    # fueron creados por el editor
    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        BloquePublicacion.orden
    ).all()


    # Guardo las imágenes
    # de cada carrusel
    carruseles = {}


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            carruseles[bloque.id] = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


    return render_template(
        "post.html",
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles
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

@bp.route("/premium/suscripcion")
def suscripcion():

    return render_template(
        "suscripcion.html"
    )


@bp.route("/categorias")
def categorias():

    return render_template(
        "categorias.html"
    )