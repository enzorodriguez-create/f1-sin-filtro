import requests

from datetime import datetime, timezone

from flask import Blueprint, render_template

from app.models import (
    Publicacion,
    BloquePublicacion,
    ImagenCarrusel
)


bp = Blueprint(
    "main",
    __name__
)


# =====================================
# INICIO
# =====================================

@bp.route("/")
def inicio():

    # =====================================
    # PUBLICACIONES
    # =====================================

    # Obtengo las últimas 4
    # publicaciones publicadas
    publicaciones = Publicacion.query.filter_by(
        estado="publicada"
    ).order_by(
        Publicacion.id.desc()
    ).limit(4).all()


    # Guardo la publicación principal
    publicacion_principal = None


    # Guardo las publicaciones
    # que aparecen debajo
    publicaciones_secundarias = []


    if publicaciones:

        publicacion_principal = publicaciones[0]

        publicaciones_secundarias = publicaciones[1:4]


    # =====================================
    # CLASIFICACIÓN OPENF1
    # =====================================

    clasificacion = []


    # Obtengo el año actual
    anio_actual = datetime.now().year


    # Obtengo todas las carreras
    # del año actual
    url_carreras = (
        "https://api.openf1.org/v1/"
        f"sessions?year={anio_actual}"
        "&session_name=Race"
    )


    respuesta_carreras = requests.get(
        url_carreras
    )


    carreras = respuesta_carreras.json()


    # Obtengo la fecha y hora actual
    ahora = datetime.now(
        timezone.utc
    )


    # Guardo solamente las carreras
    # que ya finalizaron
    carreras_finalizadas = []


    for carrera in carreras:

        fecha_fin = carrera.get(
            "date_end"
        )


        if fecha_fin:

            fecha_fin = datetime.fromisoformat(
                fecha_fin
            )


            if fecha_fin <= ahora:

                carreras_finalizadas.append(
                    carrera
                )


    # Ordeno las carreras desde
    # la más reciente
    carreras_finalizadas.sort(
        key=lambda carrera:
            carrera["date_end"],
        reverse=True
    )


    # Compruebo que exista al menos
    # una carrera finalizada
    if carreras_finalizadas:

        ultima_carrera = (
            carreras_finalizadas[0]
        )


        session_key = ultima_carrera.get(
            "session_key"
        )


        # Obtengo la clasificación
        # del campeonato después
        # de la última carrera
        url_clasificacion = (
            "https://api.openf1.org/v1/"
            "championship_drivers"
            f"?session_key={session_key}"
        )


        respuesta_clasificacion = requests.get(
            url_clasificacion
        )


        datos_clasificacion = (
            respuesta_clasificacion.json()
        )


        # Obtengo los pilotos
        # de esa misma carrera
        url_pilotos = (
            "https://api.openf1.org/v1/"
            "drivers"
            f"?session_key={session_key}"
        )


        respuesta_pilotos = requests.get(
            url_pilotos
        )


        pilotos = respuesta_pilotos.json()


        # Recorro la clasificación
        for posicion in datos_clasificacion:

            numero_piloto = posicion.get(
                "driver_number"
            )


            # Guardo el piloto encontrado
            piloto_encontrado = None


            # Busco los datos
            # correspondientes al piloto
            for piloto in pilotos:

                if (
                    piloto.get(
                        "driver_number"
                    )
                    == numero_piloto
                ):

                    piloto_encontrado = piloto


            # Compruebo que encontré
            # los datos del piloto
            if piloto_encontrado:

                clasificacion.append({

                    "posicion":
                        posicion.get(
                            "position_current"
                        ),

                    "puntos":
                        posicion.get(
                            "points_current"
                        ),

                    "nombre":
                        piloto_encontrado.get(
                            "broadcast_name"
                        ),

                    "equipo":
                        piloto_encontrado.get(
                            "team_name"
                        )

                })


    # Ordeno los pilotos
    # según su posición
    clasificacion.sort(
        key=lambda piloto:
            piloto["posicion"]
    )


    # Muestro solamente
    # los primeros 5
    clasificacion = clasificacion[:5]


    return render_template(
        "index.html",
        publicacion_principal=publicacion_principal,
        publicaciones_secundarias=publicaciones_secundarias,
        clasificacion=clasificacion
    )


# =====================================
# NOTICIAS
# =====================================

@bp.route("/noticias")
def noticias():

    # Obtengo todas las
    # publicaciones publicadas
    publicaciones = Publicacion.query.filter_by(
        estado="publicada"
    ).order_by(
        Publicacion.id.desc()
    ).all()


    return render_template(
        "noticias.html",
        publicaciones=publicaciones
    )


# =====================================
# PUBLICACIÓN
# =====================================

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


# =====================================
# CALENDARIO
# =====================================

@bp.route("/calendario")
def calendario():

    url = (
        "https://api.openf1.org/v1/"
        "meetings?year=2026"
    )


    respuesta = requests.get(
        url
    )


    carreras = respuesta.json()


    # Traduzco los tipos
    # de circuito
    tipos_circuito = {

        "Permanent":
            "Permanente",

        "Street":
            "Callejero",

        "Temporary":
            "Temporal",

        "Temporary - Street":
            "Temporal - Callejero"

    }


    # Recorro las carreras
    # obtenidas de OpenF1
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


# =====================================
# PREMIUM
# =====================================

@bp.route("/premium")
def premium():

    return render_template(
        "premium.html"
    )


# =====================================
# SUSCRIPCIÓN
# =====================================

@bp.route("/premium/suscripcion")
def suscripcion():

    return render_template(
        "suscripcion.html"
    )


# =====================================
# CATEGORÍAS
# =====================================

@bp.route("/categorias")
def categorias():

    return render_template(
        "categorias.html"
    )