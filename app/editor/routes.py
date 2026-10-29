from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from almacenamiento import (
    extension_valida,
    subir_imagen,
    borrar_imagen
)

from app.extensions import db

from app.models import (
    Usuario,
    Publicacion,
    BloquePublicacion,
    ImagenCarrusel,
    Categoria
)


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


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    if request.method == "POST":

        # =========================
        # TÍTULO
        # =========================

        titulo = request.form.get(
            "titulo",
            ""
        ).strip()


        if not titulo:

            return "Tenés que ingresar un título."


        # =========================
        # RESUMEN
        # =========================

        resumen = request.form.get(
            "resumen",
            ""
        ).strip()


        # =========================
        # CATEGORÍA
        # =========================

        categoria_id = request.form.get(
            "categoria_id"
        )


        if categoria_id:

            categoria_id = int(
                categoria_id
            )

        else:

            categoria_id = None


        # =========================
        # PORTADA
        # =========================

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


        # =========================
        # ESTADO
        # =========================

        accion = request.form.get(
            "accion",
            "borrador"
        )


        if accion == "publicar":

            estado = "publicada"

        else:

            estado = "borrador"


        # =========================
        # CREO PUBLICACIÓN
        # =========================

        nueva_publicacion = Publicacion(
            titulo=titulo,
            resumen=resumen,
            imagen_portada=imagen_portada,
            estado=estado,
            autor_id=usuario.id,
            categoria_id=categoria_id
        )


        db.session.add(
            nueva_publicacion
        )


        db.session.commit()


        # =========================
        # ORDEN DE BLOQUES
        # =========================

        bloques_orden = request.form.get(
            "bloques_orden",
            ""
        )


        tipos_bloques = [
            tipo
            for tipo in bloques_orden.split(",")
            if tipo
        ]


        # =========================
        # GUARDO BLOQUES
        # =========================

        for indice, tipo in enumerate(
            tipos_bloques,
            start=1
        ):


            # =========================
            # TEXTO
            # =========================

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


            # =========================
            # IMAGEN
            # =========================

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


            # =========================
            # CARRUSEL
            # =========================

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


        db.session.commit()


        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )


    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario,
        categorias=categorias,
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


@bp.route(
    "/editor/categorias",
    methods=["GET", "POST"]
)
def editor_categorias():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    # =========================
    # CREAR CATEGORÍA
    # =========================

    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()


        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()


        imagen_archivo = request.files.get(
            "imagen"
        )


        if not nombre:

            return "Tenés que ingresar un nombre."


        categoria_existente = Categoria.query.filter_by(
            nombre=nombre
        ).first()


        if categoria_existente:

            return "Ya existe una categoría con ese nombre."


        imagen = None


        if (
            imagen_archivo
            and imagen_archivo.filename
        ):

            if not extension_valida(
                imagen_archivo.filename
            ):

                return "Formato de imagen no válido."


            imagen = subir_imagen(
                imagen_archivo,
                carpeta="categorias"
            )


        nueva_categoria = Categoria(
            nombre=nombre,
            descripcion=descripcion,
            imagen=imagen
        )


        db.session.add(
            nueva_categoria
        )


        db.session.commit()


        return redirect(
            url_for(
                "editor.editor_categorias"
            )
        )


    # =========================
    # LISTADO
    # =========================

    categorias = Categoria.query.order_by(
        Categoria.id.asc()
    ).all()


    return render_template(
        "editor/categorias.html",
        usuario=usuario,
        categorias=categorias,
        seccion_activa="categorias"
    )


# =========================
# EDITAR CATEGORÍA
# =========================

@bp.route(
    "/editor/categorias/<int:id_categoria>/editar",
    methods=["POST"]
)
def editor_editar_categoria(id_categoria):

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return "Categoría no encontrada."


    nombre = request.form.get(
        "nombre",
        ""
    ).strip()


    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()


    if not nombre:

        return "Tenés que ingresar un nombre."


    categoria_existente = Categoria.query.filter(
        Categoria.nombre == nombre,
        Categoria.id != id_categoria
    ).first()


    if categoria_existente:

        return "Ya existe otra categoría con ese nombre."


    categoria.nombre = nombre

    categoria.descripcion = descripcion


    # =========================
    # IMAGEN
    # =========================

    imagen_archivo = request.files.get(
        "imagen"
    )


    if (
        imagen_archivo
        and imagen_archivo.filename
    ):

        if not extension_valida(
            imagen_archivo.filename
        ):

            return "Formato de imagen no válido."


        categoria.imagen = subir_imagen(
            imagen_archivo,
            carpeta="categorias"
        )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_categorias"
        )
    )


# =========================
# ELIMINAR CATEGORÍA
# =========================

@bp.route(
    "/editor/categorias/<int:id_categoria>/eliminar",
    methods=["POST"]
)
def editor_eliminar_categoria(id_categoria):

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return "Categoría no encontrada."


    db.session.delete(
        categoria
    )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_categorias"
        )
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


    if usuario.rol != "editor":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    if request.method == "POST":

        # =========================
        # NOMBRE
        # =========================

        usuario.nombre = request.form.get(
            "nombre",
            usuario.nombre
        ).strip()


        # =========================
        # APELLIDO
        # =========================

        usuario.apellido = request.form.get(
            "apellido",
            usuario.apellido
        ).strip()


        # =========================
        # USUARIO
        # =========================

        usuario.usuario = request.form.get(
            "usuario",
            usuario.usuario
        ).strip()


        # =========================
        # EMAIL
        # =========================

        usuario.email = request.form.get(
            "email",
            usuario.email
        ).strip()


        # =========================
        # FOTO
        # =========================

        foto = request.files.get(
            "foto"
        )


        foto_anterior = None


        if foto and foto.filename:

            if not extension_valida(
                foto.filename
            ):

                return (
                    "La imagen debe ser JPG, JPEG, "
                    "PNG, WEBP o GIF."
                )


            foto_anterior = usuario.foto


            usuario.foto = subir_imagen(
                foto,
                carpeta="avatares"
            )


        # =========================
        # GUARDO CAMBIOS
        # =========================

        db.session.commit()


        if foto_anterior:

            borrar_imagen(
                foto_anterior
            )


        # =========================
        # ACTUALIZO LA SESIÓN
        # =========================

        session["usuario"] = {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "usuario": usuario.usuario,
            "email": usuario.email,
            "foto": usuario.foto,
            "rol": usuario.rol,
            "tipo_login": usuario.tipo_login,
            "premium": usuario.premium
        }


        return redirect(
            url_for(
                "editor.editor_perfil"
            )
        )


    return render_template(
        "editor/perfil.html",
        usuario=usuario,
        seccion_activa="perfil_editor"
    )


@bp.route(
    "/editor/perfil/cambiar-password",
    methods=["POST"]
)
def editor_cambiar_password():

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


    if usuario.tipo_login == "google":

        return redirect(
            url_for(
                "editor.editor_perfil"
            )
        )


    password_actual = request.form.get(
        "pass_actual",
        ""
    )


    password_nueva = request.form.get(
        "pass_nueva",
        ""
    )


    password_confirmacion = request.form.get(
        "pass_confirm",
        ""
    )


    if not usuario.verificar_password(
        password_actual
    ):

        return "La contraseña actual es incorrecta."


    if not password_nueva:

        return "Tenés que ingresar una nueva contraseña."


    if (
        password_nueva
        !=
        password_confirmacion
    ):

        return "Las contraseñas nuevas no coinciden."


    usuario.guardar_password(
        password_nueva
    )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_perfil"
        )
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
    "/editor/publicaciones/<int:id_publicacion>/editar",
    methods=["GET", "POST"]
)
def editor_editar_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    # =========================
    # GUARDAR CAMBIOS
    # =========================

    if request.method == "POST":


        # =========================
        # TÍTULO
        # =========================

        titulo = request.form.get(
            "titulo",
            ""
        ).strip()


        if titulo:

            publicacion.titulo = titulo


        # =========================
        # RESUMEN
        # =========================

        resumen = request.form.get(
            "resumen",
            ""
        ).strip()


        publicacion.resumen = resumen


        # =========================
        # CATEGORÍA
        # =========================

        categoria_id = request.form.get(
            "categoria_id"
        )


        if categoria_id:

            publicacion.categoria_id = int(
                categoria_id
            )

        else:

            publicacion.categoria_id = None


        # =========================
        # ESTADO
        # =========================

        accion = request.form.get(
            "accion",
            "borrador"
        )


        if accion == "publicar":

            publicacion.estado = "publicada"

        else:

            publicacion.estado = "borrador"


        # =========================
        # PORTADA
        # =========================

        nueva_portada = request.files.get(
            "imagen_portada"
        )


        if (
            nueva_portada
            and nueva_portada.filename
        ):

            if not extension_valida(
                nueva_portada.filename
            ):

                return "Formato de portada no válido."


            publicacion.imagen_portada = subir_imagen(
                nueva_portada,
                carpeta="publicaciones"
            )


        # =========================
        # BLOQUES EXISTENTES
        # =========================

        for bloque in bloques:


            # =========================
            # TEXTO EXISTENTE
            # =========================

            if bloque.tipo == "texto":

                contenido = request.form.get(
                    f"bloque_{bloque.id}_texto",
                    ""
                ).strip()


                bloque.contenido = contenido


            # =========================
            # IMAGEN EXISTENTE
            # =========================

            elif bloque.tipo == "imagen":

                nueva_imagen = request.files.get(
                    f"bloque_{bloque.id}_imagen"
                )


                if (
                    nueva_imagen
                    and nueva_imagen.filename
                ):

                    if not extension_valida(
                        nueva_imagen.filename
                    ):

                        return "Formato de imagen no válido."


                    bloque.contenido = subir_imagen(
                        nueva_imagen,
                        carpeta="publicaciones/contenido"
                    )


        # =========================
        # BLOQUES NUEVOS
        # =========================

        bloques_nuevos_orden = request.form.get(
            "bloques_nuevos_orden",
            ""
        )


        tipos_nuevos = [
            tipo
            for tipo in bloques_nuevos_orden.split(",")
            if tipo
        ]


        # =========================
        # ÚLTIMO ORDEN
        # =========================

        ultimo_orden = 0


        if bloques:

            ultimo_orden = bloques[-1].orden


        # =========================
        # BLOQUES NUEVOS
        # =========================

        for indice, tipo in enumerate(
            tipos_nuevos,
            start=1
        ):


            nuevo_orden = (
                ultimo_orden
                +
                indice
            )


            # =========================
            # TEXTO NUEVO
            # =========================

            if tipo == "texto":

                contenido = request.form.get(
                    f"nuevo_bloque_{indice}_texto",
                    ""
                ).strip()


                if contenido:

                    nuevo_bloque = BloquePublicacion(
                        publicacion_id=publicacion.id,
                        tipo="texto",
                        contenido=contenido,
                        orden=nuevo_orden
                    )


                    db.session.add(
                        nuevo_bloque
                    )


            # =========================
            # IMAGEN NUEVA
            # =========================

            elif tipo == "imagen":

                imagen = request.files.get(
                    f"nuevo_bloque_{indice}_imagen"
                )


                if (
                    imagen
                    and imagen.filename
                ):

                    if not extension_valida(
                        imagen.filename
                    ):

                        return "Formato de imagen no válido."


                    imagen_key = subir_imagen(
                        imagen,
                        carpeta="publicaciones/contenido"
                    )


                    nuevo_bloque = BloquePublicacion(
                        publicacion_id=publicacion.id,
                        tipo="imagen",
                        contenido=imagen_key,
                        orden=nuevo_orden
                    )


                    db.session.add(
                        nuevo_bloque
                    )


            # =========================
            # CARRUSEL NUEVO
            # =========================

            elif tipo == "carrusel":

                imagenes = request.files.getlist(
                    f"nuevo_bloque_{indice}_carrusel"
                )


                imagenes_validas = [
                    imagen
                    for imagen in imagenes
                    if imagen and imagen.filename
                ]


                if imagenes_validas:

                    bloque_carrusel = BloquePublicacion(
                        publicacion_id=publicacion.id,
                        tipo="carrusel",
                        contenido=None,
                        orden=nuevo_orden
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


        # =========================
        # GUARDO CAMBIOS
        # =========================

        db.session.commit()


        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )


    # =========================
    # CARRUSELES
    # =========================

    carruseles = {}


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


            carruseles[bloque.id] = imagenes


    # =========================
    # PÁGINA
    # =========================

    return render_template(
        "editor/editar_publicacion.html",
        usuario=usuario,
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles,
        categorias=categorias,
        seccion_activa="publicaciones"
    )


@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/eliminar",
    methods=["POST"]
)
def editor_eliminar_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        autor_id=usuario.id
    ).first()


    if not publicacion:

        return "Publicación no encontrada."


    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).all()


            for imagen in imagenes:

                db.session.delete(
                    imagen
                )


    for bloque in bloques:

        db.session.delete(
            bloque
        )


    db.session.delete(
        publicacion
    )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_publicaciones"
        )
    )