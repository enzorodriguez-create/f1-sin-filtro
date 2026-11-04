import requests

from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from app.extensions import db

from app.models import (
    Publicacion,
    BloquePublicacion,
    ImagenCarrusel,
    Categoria,
    Etiqueta,
    Comentario
)

from ia.moderacion import clasificar_comentario


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

    publicaciones = Publicacion.query.filter_by(
        estado="publicada"
    ).order_by(
        Publicacion.id.desc()
    ).limit(4).all()


    publicacion_principal = None

    publicaciones_secundarias = []


    if publicaciones:

        publicacion_principal = publicaciones[0]

        publicaciones_secundarias = publicaciones[1:4]


    # =====================================
    # CLASIFICACIÓN OPENF1
    # =====================================

    clasificacion = []


    anio_actual = datetime.now().year


    url_carreras = (
        "https://api.openf1.org/v1/"
        f"sessions?year={anio_actual}"
        "&session_name=Race"
    )


    respuesta_carreras = requests.get(
        url_carreras
    )


    carreras = respuesta_carreras.json()


    ahora = datetime.now(
        timezone.utc
    )


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


    carreras_finalizadas.sort(
        key=lambda carrera:
            carrera["date_end"],
        reverse=True
    )


    if carreras_finalizadas:

        ultima_carrera = (
            carreras_finalizadas[0]
        )


        session_key = ultima_carrera.get(
            "session_key"
        )


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


        url_pilotos = (
            "https://api.openf1.org/v1/"
            "drivers"
            f"?session_key={session_key}"
        )


        respuesta_pilotos = requests.get(
            url_pilotos
        )


        pilotos = respuesta_pilotos.json()


        for posicion in datos_clasificacion:

            numero_piloto = posicion.get(
                "driver_number"
            )


            piloto_encontrado = None


            for piloto in pilotos:

                if (
                    piloto.get(
                        "driver_number"
                    )
                    == numero_piloto
                ):

                    piloto_encontrado = piloto


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


    clasificacion.sort(
        key=lambda piloto:
            piloto["posicion"]
    )


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
    "/post/<int:id_publicacion>",
    methods=["GET", "POST"]
)
def post(id_publicacion):

    # =====================================
    # PUBLICACIÓN
    # =====================================

    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        estado="publicada"
    ).first()


    if not publicacion:

        return "Publicación no encontrada."


    # =====================================
    # NUEVO COMENTARIO
    # =====================================

    if request.method == "POST":

        datos_usuario = session.get(
            "usuario"
        )


        if not datos_usuario:

            return redirect(
                url_for(
                    "auth.login"
                )
            )


        contenido = request.form.get(
            "comment",
            ""
        ).strip()


        if contenido:

            moderacion, confianza = clasificar_comentario(
                contenido
            )


            nuevo_comentario = Comentario(
                contenido=contenido,
                usuario_id=datos_usuario["id"],
                publicacion_id=publicacion.id,
                moderacion=moderacion,
                confianza=float(confianza)
            )


            db.session.add(
                nuevo_comentario
            )


            db.session.commit()


        return redirect(
            url_for(
                "main.post",
                id_publicacion=publicacion.id
            )
        )


    # =====================================
    # BLOQUES
    # =====================================

    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        BloquePublicacion.orden
    ).all()


    # =====================================
    # CARRUSELES
    # =====================================

    carruseles = {}


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            carruseles[bloque.id] = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


    # =====================================
    # COMENTARIOS
    # =====================================

    comentarios = Comentario.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        Comentario.id.desc()
    ).all()


    return render_template(
        "post.html",
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles,
        comentarios=comentarios
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

    categorias = Categoria.query.order_by(
        Categoria.id.asc()
    ).all()


    return render_template(
        "categorias.html",
        categorias=categorias
    )


# =====================================
# PUBLICACIONES POR CATEGORÍA
# =====================================

@bp.route(
    "/categorias/<int:id_categoria>"
)
def publicaciones_categoria(id_categoria):

    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return "Categoría no encontrada."


    publicaciones = Publicacion.query.filter(
        Publicacion.estado == "publicada",
        Publicacion.categorias.any(
            Categoria.id == id_categoria
        )
    ).order_by(
        Publicacion.id.desc()
    ).all()


    return render_template(
        "publicaciones_categoria.html",
        categoria=categoria,
        publicaciones=publicaciones
    )


# =====================================
# PUBLICACIONES POR ETIQUETA
# =====================================

@bp.route(
    "/etiquetas/<int:id_etiqueta>"
)
def publicaciones_etiqueta(id_etiqueta):

    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return "Etiqueta no encontrada."


    publicaciones = Publicacion.query.filter(
        Publicacion.estado == "publicada",
        Publicacion.etiquetas.any(
            Etiqueta.id == id_etiqueta
        )
    ).order_by(
        Publicacion.id.desc()
    ).all()


    return render_template(
        "publicaciones_etiqueta.html",
        etiqueta=etiqueta,
        publicaciones=publicaciones
    )