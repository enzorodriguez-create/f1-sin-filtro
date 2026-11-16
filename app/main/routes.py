import requests

from datetime import datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort
)

from app.extensions import db

from app.models import (
    Usuario,
    Publicacion,
    BloquePublicacion,
    ImagenCarrusel,
    Categoria,
    Etiqueta,
    Comentario,
    PagoPremium
)

from ia.moderacion import clasificar_comentario

from pagos import (
    usa_mercadopago,
    crear_preferencia,
    obtener_pago
)


bp = Blueprint(
    "main",
    __name__
)


# =====================================
# SEGURIDAD VISTAS PÚBLICAS
# =====================================

@bp.before_request
def proteger_vistas_publicas():

    datos_usuario = session.get(
        "usuario"
    )


    if not datos_usuario:

        return None


    usuario = db.session.get(
        Usuario,
        datos_usuario["id"]
    )


    if not usuario:

        return None


    if usuario.rol == "editor":

        return redirect(
            url_for(
                "editor.editor"
            )
        )


    if usuario.rol == "admin":

        return redirect(
            url_for(
                "admin.admin_dashboard"
            )
        )


    return None


# =====================================
# INICIO
# =====================================

@bp.route("/")
def inicio():

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


    clasificacion = []


    try:

        anio_actual = datetime.now().year


        url_carreras = (
            "https://api.openf1.org/v1/"
            f"sessions?year={anio_actual}"
            "&session_name=Race"
        )


        respuesta_carreras = requests.get(
            url_carreras,
            timeout=10
        )


        respuesta_carreras.raise_for_status()


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
                url_clasificacion,
                timeout=10
            )


            respuesta_clasificacion.raise_for_status()


            datos_clasificacion = (
                respuesta_clasificacion.json()
            )


            url_pilotos = (
                "https://api.openf1.org/v1/"
                "drivers"
                f"?session_key={session_key}"
            )


            respuesta_pilotos = requests.get(
                url_pilotos,
                timeout=10
            )


            respuesta_pilotos.raise_for_status()


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
                        ==
                        numero_piloto
                    ):

                        piloto_encontrado = piloto

                        break


                if piloto_encontrado:

                    posicion_actual = posicion.get(
                        "position_current"
                    )


                    if posicion_actual is not None:

                        clasificacion.append({

                            "posicion":
                                posicion_actual,

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


    except (
        requests.RequestException,
        ValueError,
        TypeError,
        KeyError
    ):

        clasificacion = []


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


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    categoria_seleccionada = request.args.get(
        "categoria",
        type=int
    )


    busqueda = request.args.get(
        "buscar",
        ""
    ).strip()


    if categoria_seleccionada:

        publicaciones_filtradas = []


        for publicacion in publicaciones:

            for categoria in publicacion.categorias:

                if categoria.id == categoria_seleccionada:

                    publicaciones_filtradas.append(
                        publicacion
                    )


        publicaciones = publicaciones_filtradas


    if busqueda:

        texto_busqueda = busqueda.lower()

        publicaciones_filtradas = []


        for publicacion in publicaciones:

            titulo = (
                publicacion.titulo
                or ""
            ).lower()


            resumen = (
                publicacion.resumen
                or ""
            ).lower()


            if (
                texto_busqueda in titulo
                or
                texto_busqueda in resumen
            ):

                publicaciones_filtradas.append(
                    publicacion
                )


        publicaciones = publicaciones_filtradas


    return render_template(
        "noticias.html",
        publicaciones=publicaciones,
        categorias=categorias,
        categoria_seleccionada=categoria_seleccionada,
        busqueda=busqueda
    )


# =====================================
# PUBLICACIÓN
# =====================================

@bp.route(
    "/post/<int:id_publicacion>",
    methods=["GET", "POST"]
)
def post(
    id_publicacion
):

    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        estado="publicada"
    ).first()


    if not publicacion:

        return "Publicación no encontrada."


    autor = db.session.get(
        Usuario,
        publicacion.autor_id
    )


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
                confianza=float(
                    confianza
                )
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


    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        BloquePublicacion.orden
    ).all()


    carruseles = {}


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            carruseles[
                bloque.id
            ] = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


    comentarios = Comentario.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        Comentario.id.desc()
    ).all()


    otras_publicaciones = Publicacion.query.filter(
        Publicacion.estado
        ==
        "publicada",

        Publicacion.id
        !=
        publicacion.id
    ).order_by(
        Publicacion.id.desc()
    ).limit(3).all()


    return render_template(
        "post.html",
        publicacion=publicacion,
        autor=autor,
        bloques=bloques,
        carruseles=carruseles,
        comentarios=comentarios,
        otras_publicaciones=otras_publicaciones
    )


# =====================================
# CALENDARIO
# =====================================

@bp.route("/calendario")
def calendario():

    carreras = []


    try:

        url = (
            "https://api.openf1.org/v1/"
            "meetings?year=2026"
        )


        respuesta = requests.get(
            url,
            timeout=10
        )


        respuesta.raise_for_status()


        carreras = respuesta.json()


        tipos_circuito = {

            "Permanent":
                "Permanente",

            "Street":
                "Callejero",

            "Temporary":
                "Temporal",

            "Temporary - Street":
                "Temporal - Callejero",

            "Temporary - Road":
                "Temporal - Ruta"

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


    except (
        requests.RequestException,
        ValueError,
        TypeError
    ):

        carreras = []


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
# COMPRAR PREMIUM
# =====================================

@bp.route(
    "/premium/comprar",
    methods=["POST"]
)
def comprar_premium():

    datos_usuario = session.get(
        "usuario"
    )


    if not datos_usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    usuario = db.session.get(
        Usuario,
        datos_usuario["id"]
    )


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.premium:

        flash(
            "Tu cuenta ya tiene acceso Premium."
        )

        return redirect(
            url_for(
                "main.premium"
            )
        )


    if not usa_mercadopago():

        flash(
            "Mercado Pago no está configurado."
        )

        return redirect(
            url_for(
                "main.suscripcion"
            )
        )


    pago = PagoPremium(
        usuario_id=usuario.id,
        precio=5000.0
    )


    db.session.add(
        pago
    )

    db.session.commit()


    try:

        link_pago = crear_preferencia(
            pago,
            url_retorno=url_for(
                "main.resultado_pago",
                _external=True
            ),
            url_webhook=url_for(
                "main.webhook_mercadopago",
                _external=True
            )
        )


    except Exception as error:

        print(
            f"[MP] {error}",
            flush=True
        )

        flash(
            "No se pudo iniciar el pago con Mercado Pago."
        )

        return redirect(
            url_for(
                "main.suscripcion"
            )
        )


    return redirect(
        link_pago
    )


# =====================================
# ACTUALIZAR PAGO PREMIUM
# =====================================

def actualizar_pago_premium(
    pago_mercadopago
):

    pago = db.session.get(
        PagoPremium,
        int(
            pago_mercadopago.get(
                "external_reference"
            )
            or 0
        )
    )


    if not pago:

        return None


    pago.estado = pago_mercadopago[
        "status"
    ]

    pago.payment_id = str(
        pago_mercadopago[
            "id"
        ]
    )


    if pago.estado == "approved":

        usuario = db.session.get(
            Usuario,
            pago.usuario_id
        )


        if usuario:

            usuario.premium = True


    db.session.commit()


    return pago


# =====================================
# RESULTADO DEL PAGO
# =====================================

@bp.route("/pago/resultado")
def resultado_pago():

    datos_usuario = session.get(
        "usuario"
    )


    if not datos_usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    payment_id = request.args.get(
        "payment_id"
    )


    pago_mercadopago = (
        obtener_pago(
            payment_id
        )
        if payment_id
        and payment_id != "null"
        else None
    )


    if pago_mercadopago is None:

        flash(
            "El pago no se completó."
        )

        return redirect(
            url_for(
                "main.suscripcion"
            )
        )


    pago = actualizar_pago_premium(
        pago_mercadopago
    )


    if (
        not pago
        or pago.usuario_id
        != datos_usuario["id"]
    ):

        abort(
            404,
            description="Pago no encontrado"
        )


    if pago.estado == "approved":

        usuario = db.session.get(
            Usuario,
            datos_usuario["id"]
        )


        if usuario:

            datos_usuario[
                "premium"
            ] = usuario.premium

            session[
                "usuario"
            ] = datos_usuario


    mensajes = {

        "approved":
            "¡Pago aprobado! Tu cuenta ya es Premium.",

        "pending":
            "El pago quedó pendiente.",

        "in_process":
            "El pago se está procesando."

    }


    flash(
        mensajes.get(
            pago.estado,
            f"El pago fue rechazado ({pago.estado})."
        )
    )


    return redirect(
        url_for(
            "main.premium"
        )
    )


# =====================================
# WEBHOOK MERCADO PAGO
# =====================================

@bp.route(
    "/pago/webhook",
    methods=["POST"]
)
def webhook_mercadopago():

    datos = (
        request.get_json(
            silent=True
        )
        or {}
    )


    tipo = (
        datos.get(
            "type"
        )
        or request.args.get(
            "type"
        )
        or request.args.get(
            "topic"
        )
    )


    payment_id = (
        (
            datos.get(
                "data"
            )
            or {}
        ).get(
            "id"
        )
        or request.args.get(
            "data.id"
        )
        or request.args.get(
            "id"
        )
    )


    if (
        tipo == "payment"
        and payment_id
    ):

        pago_mercadopago = obtener_pago(
            payment_id
        )


        if pago_mercadopago:

            actualizar_pago_premium(
                pago_mercadopago
            )


    return "", 200


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
def publicaciones_categoria(
    id_categoria
):

    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return "Categoría no encontrada."


    publicaciones = Publicacion.query.filter(
        Publicacion.estado
        ==
        "publicada",

        Publicacion.categorias.any(
            Categoria.id
            ==
            id_categoria
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
def publicaciones_etiqueta(
    id_etiqueta
):

    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return "Etiqueta no encontrada."


    publicaciones = Publicacion.query.filter(
        Publicacion.estado
        ==
        "publicada",

        Publicacion.etiquetas.any(
            Etiqueta.id
            ==
            id_etiqueta
        )
    ).order_by(
        Publicacion.id.desc()
    ).all()


    return render_template(
        "publicaciones_etiqueta.html",
        etiqueta=etiqueta,
        publicaciones=publicaciones
    )