from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)
from almacenamiento import extension_valida, subir_imagen
from app.extensions import db
from app.models import (Usuario, Publicacion, BloquePublicacion, ImagenCarrusel)  


bp = Blueprint(
    "editor",
    __name__
)


def obtener_usuario_actual():

    datos_usuario = session.get(
        "usuario"
    )

    if not datos_usuario:

        return None


    return db.session.get(
        Usuario,
        datos_usuario["id"]
    )


@bp.route("/editor")
def editor():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if usuario.rol != "editor":

        return redirect(
            url_for(
                "main.inicio"
            )
        )

    return render_template(
        "editor/dashboard.html",
        usuario=usuario,
        seccion_activa="dashboard"
    )

@bp.route("/editor/publicaciones")
def editor_publicaciones():

    usuario = obtener_usuario_actual()

    publicaciones = Publicacion.query.filter_by(
        autor_id=usuario.id
    ).order_by(
        Publicacion.id.desc()
    ).all()

    return render_template(
        "editor/mis_publicaciones.html",
        usuario=usuario,
        publicaciones=publicaciones,
        seccion_activa="publicaciones"
    )

@bp.route(
    "/editor/crear-publicacion",
    methods=["GET", "POST"]
)
def editor_crear_publicacion():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if request.method == "POST":

        # Obtengo el título
        titulo = request.form.get(
            "titulo",
            ""
        ).strip()

        if not titulo:

            return "Tenés que ingresar un título."

        # Obtengo la portada
        portada = request.files.get(
            "imagen_portada"
        )

        imagen_portada = None

        if portada and portada.filename:

            if not extension_valida(
                portada.filename
            ):

                return "Formato de portada no válido."

            imagen_portada = subir_imagen(
                portada,
                carpeta="publicaciones"
            )

        # Compruebo si se publica o queda como borrador
        accion = request.form.get(
            "accion",
            "borrador"
        )

        if accion == "publicar":

            estado = "publicada"

        else:

            estado = "borrador"

        # Creo la publicación
        nueva_publicacion = Publicacion(
            titulo=titulo,
            imagen_portada=imagen_portada,
            estado=estado,
            autor_id=usuario.id
        )

        db.session.add(
            nueva_publicacion
        )

        # Guardo primero para obtener el ID
        db.session.commit()

        # Obtengo el orden de los bloques
        bloques_orden = request.form.get(
            "bloques_orden",
            ""
        )

        tipos_bloques = [
            tipo
            for tipo in bloques_orden.split(",")
            if tipo
        ]

        # Recorro los bloques respetando el orden
        for indice, tipo in enumerate(
            tipos_bloques,
            start=1
        ):

            # TEXTO
            if tipo == "texto":

                contenido = request.form.get(
                    f"bloque_{indice}_texto",
                    ""
                ).strip()

                if contenido:

                    nuevo_bloque = BloquePublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo="texto",
                        contenido=contenido,
                        orden=indice
                    )

                    db.session.add(
                        nuevo_bloque
                    )

            # IMAGEN
            elif tipo == "imagen":

                imagen = request.files.get(
                    f"bloque_{indice}_imagen"
                )

                if imagen and imagen.filename:

                    if extension_valida(
                        imagen.filename
                    ):

                        imagen_key = subir_imagen(
                            imagen,
                            carpeta="publicaciones/contenido"
                        )

                        nuevo_bloque = BloquePublicacion(
                            publicacion_id=nueva_publicacion.id,
                            tipo="imagen",
                            contenido=imagen_key,
                            orden=indice
                        )

                        db.session.add(
                            nuevo_bloque
                        )

            # CARRUSEL
            elif tipo == "carrusel":

                imagenes = request.files.getlist(
                    f"bloque_{indice}_carrusel"
                )

                imagenes_validas = [
                    imagen
                    for imagen in imagenes
                    if imagen and imagen.filename
                ]

                if imagenes_validas:

                    bloque_carrusel = BloquePublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo="carrusel",
                        contenido=None,
                        orden=indice
                    )

                    db.session.add(
                        bloque_carrusel
                    )

                    db.session.flush()

                    orden_imagen = 1

                    for imagen in imagenes_validas:

                        if extension_valida(
                            imagen.filename
                        ):

                            imagen_key = subir_imagen(
                                imagen,
                                carpeta="publicaciones/carruseles"
                            )

                            nueva_imagen = ImagenCarrusel(
                                bloque_id=bloque_carrusel.id,
                                imagen=imagen_key,
                                orden=orden_imagen
                            )

                            db.session.add(
                                nueva_imagen
                            )

                            orden_imagen += 1

        # Guardo bloques e imágenes
        db.session.commit()

        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )

    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario,
        seccion_activa="crear_publicacion"
    )

@bp.route("/editor/comentarios")
def editor_comentarios():

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/comentarios.html",
        usuario=usuario,
        seccion_activa="comentarios"
    )

@bp.route("/editor/categorias")
def editor_categorias():

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/categorias.html",
        usuario=usuario,
        seccion_activa="categorias"
    )

@bp.route("/editor/etiquetas")
def editor_etiquetas():

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/etiquetas.html",
        usuario=usuario,
        seccion_activa="etiquetas"
    )

@bp.route(
    "/editor/perfil",
    methods=["GET", "POST"]
)
def editor_perfil():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    return render_template(
        "editor/perfil.html",
        usuario=usuario,
        seccion_activa="perfil_editor"
    )

@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/vista-previa"
)
def editor_vista_previa_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()

    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        autor_id=usuario.id
    ).first()

    if not publicacion:

        return "Publicación no encontrada."

    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        BloquePublicacion.orden
    ).all()

    carruseles = {}

    for bloque in bloques:

        if bloque.tipo == "carrusel":

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()

            carruseles[bloque.id] = imagenes

    return render_template(
        "editor/vista_previa_publicacion.html",
        usuario=usuario,
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles,
        seccion_activa="publicaciones"
    )

@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/editar"
)
def editor_editar_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/editar_publicacion.html",
        usuario=usuario,
        id_publicacion=id_publicacion,
        seccion_activa="publicaciones"
    )