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
    Categoria,
    Etiqueta,
    Comentario
)


bp = Blueprint(
    "editor",
    __name__
)


# =====================================
# USUARIO ACTUAL
# =====================================

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


# =====================================
# SEGURIDAD EDITOR
# =====================================

@bp.before_request
def proteger_rutas_editor():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol == "admin":

        return redirect(
            url_for(
                "admin.admin_dashboard"
            )
        )


    if usuario.rol == "usuario":

        return redirect(
            url_for(
                "perfil.perfil"
            )
        )


    if usuario.rol != "editor":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


# =====================================
# DASHBOARD
# =====================================

@bp.route("/editor")
def editor():

    usuario = obtener_usuario_actual()


    publicaciones = Publicacion.query.filter_by(
        autor_id=usuario.id
    ).order_by(
        Publicacion.id.desc()
    ).all()


    cantidad_publicaciones = len(
        publicaciones
    )


    cantidad_publicadas = Publicacion.query.filter_by(
        autor_id=usuario.id,
        estado="publicada"
    ).count()


    cantidad_borradores = Publicacion.query.filter_by(
        autor_id=usuario.id,
        estado="borrador"
    ).count()


    ultimas_publicaciones = publicaciones[:3]


    comentarios = Comentario.query.join(
        Publicacion,
        Comentario.publicacion_id
        ==
        Publicacion.id
    ).filter(
        Publicacion.autor_id
        ==
        usuario.id
    ).order_by(
        Comentario.id.desc()
    ).all()


    cantidad_comentarios = len(
        comentarios
    )


    ultimos_comentarios = comentarios[:2]


    comentarios_por_publicacion = {}


    for publicacion in ultimas_publicaciones:

        cantidad = Comentario.query.filter_by(
            publicacion_id=publicacion.id
        ).count()


        comentarios_por_publicacion[
            publicacion.id
        ] = cantidad


    categorias_usadas = []


    for publicacion in publicaciones:

        for categoria in publicacion.categorias:

            if categoria not in categorias_usadas:

                categorias_usadas.append(
                    categoria
                )


    cantidad_categorias = len(
        categorias_usadas
    )


    etiquetas_usadas = []


    for publicacion in publicaciones:

        for etiqueta in publicacion.etiquetas:

            if etiqueta not in etiquetas_usadas:

                etiquetas_usadas.append(
                    etiqueta
                )


    cantidad_etiquetas = len(
        etiquetas_usadas
    )


    ultimo_borrador = Publicacion.query.filter_by(
        autor_id=usuario.id,
        estado="borrador"
    ).order_by(
        Publicacion.id.desc()
    ).first()


    return render_template(
        "editor/dashboard.html",

        usuario=usuario,

        cantidad_publicaciones=
            cantidad_publicaciones,

        cantidad_publicadas=
            cantidad_publicadas,

        cantidad_borradores=
            cantidad_borradores,

        cantidad_comentarios=
            cantidad_comentarios,

        cantidad_categorias=
            cantidad_categorias,

        cantidad_etiquetas=
            cantidad_etiquetas,

        categorias_usadas=
            categorias_usadas,

        etiquetas_usadas=
            etiquetas_usadas,

        ultimas_publicaciones=
            ultimas_publicaciones,

        comentarios_por_publicacion=
            comentarios_por_publicacion,

        ultimos_comentarios=
            ultimos_comentarios,

        ultimo_borrador=
            ultimo_borrador,

        seccion_activa="dashboard"
    )


# =====================================
# MIS PUBLICACIONES
# =====================================

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


# =====================================
# CREAR PUBLICACIÓN
# =====================================

@bp.route(
    "/editor/crear-publicacion",
    methods=["GET", "POST"]
)
def editor_crear_publicacion():

    usuario = obtener_usuario_actual()


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    etiquetas = Etiqueta.query.order_by(
        Etiqueta.nombre.asc()
    ).all()


    if request.method == "POST":

        titulo = request.form.get(
            "titulo",
            ""
        ).strip()


        if not titulo:

            return "Tenés que ingresar un título."


        resumen = request.form.get(
            "resumen",
            ""
        ).strip()


        categorias_ids = request.form.getlist(
            "categorias"
        )


        categorias_seleccionadas = []


        for categoria_id in categorias_ids:

            categoria = db.session.get(
                Categoria,
                int(categoria_id)
            )


            if categoria:

                categorias_seleccionadas.append(
                    categoria
                )


        etiquetas_ids = request.form.getlist(
            "etiquetas"
        )


        etiquetas_seleccionadas = []


        for etiqueta_id in etiquetas_ids:

            etiqueta = db.session.get(
                Etiqueta,
                int(etiqueta_id)
            )


            if etiqueta:

                etiquetas_seleccionadas.append(
                    etiqueta
                )


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


        accion = request.form.get(
            "accion",
            "borrador"
        )


        if accion == "publicar":

            estado = "publicada"

        else:

            estado = "borrador"


        nueva_publicacion = Publicacion(
            titulo=titulo,
            resumen=resumen,
            imagen_portada=imagen_portada,
            estado=estado,
            autor_id=usuario.id
        )


        nueva_publicacion.categorias = (
            categorias_seleccionadas
        )


        nueva_publicacion.etiquetas = (
            etiquetas_seleccionadas
        )


        if categorias_seleccionadas:

            nueva_publicacion.categoria_id = (
                categorias_seleccionadas[0].id
            )

        else:

            nueva_publicacion.categoria_id = None


        db.session.add(
            nueva_publicacion
        )


        db.session.commit()


        bloques_orden = request.form.get(
            "bloques_orden",
            ""
        )


        tipos_bloques = [
            tipo
            for tipo in bloques_orden.split(",")
            if tipo
        ]


        for indice, tipo in enumerate(
            tipos_bloques,
            start=1
        ):

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
        etiquetas=etiquetas,
        seccion_activa="crear_publicacion"
    )


# =====================================
# COMENTARIOS
# =====================================

@bp.route("/editor/comentarios")
def editor_comentarios():

    usuario = obtener_usuario_actual()


    publicaciones = Publicacion.query.filter_by(
        autor_id=usuario.id
    ).order_by(
        Publicacion.titulo.asc()
    ).all()


    comentarios = Comentario.query.join(
        Publicacion,
        Comentario.publicacion_id
        ==
        Publicacion.id
    ).filter(
        Publicacion.autor_id
        ==
        usuario.id
    ).order_by(
        Comentario.id.desc()
    ).all()


    return render_template(
        "editor/comentarios.html",
        usuario=usuario,
        comentarios=comentarios,
        publicaciones=publicaciones,
        cantidad_comentarios=len(comentarios),
        cantidad_publicaciones=len(publicaciones),
        seccion_activa="comentarios"
    )


# =====================================
# ELIMINAR COMENTARIO
# =====================================

@bp.route(
    "/editor/comentarios/<int:id_comentario>/eliminar",
    methods=["POST"]
)
def editor_eliminar_comentario(
    id_comentario
):

    usuario = obtener_usuario_actual()


    comentario = Comentario.query.join(
        Publicacion,
        Comentario.publicacion_id
        ==
        Publicacion.id
    ).filter(
        Comentario.id
        ==
        id_comentario,

        Publicacion.autor_id
        ==
        usuario.id
    ).first()


    if not comentario:

        return redirect(
            url_for(
                "editor.editor_comentarios"
            )
        )


    db.session.delete(
        comentario
    )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_comentarios"
        )
    )


# =====================================
# CATEGORÍAS
# =====================================

@bp.route(
    "/editor/categorias",
    methods=["GET", "POST"]
)
def editor_categorias():

    usuario = obtener_usuario_actual()


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


    categorias = Categoria.query.order_by(
        Categoria.id.asc()
    ).all()


    return render_template(
        "editor/categorias.html",
        usuario=usuario,
        categorias=categorias,
        seccion_activa="categorias"
    )


# =====================================
# EDITAR CATEGORÍA
# =====================================

@bp.route(
    "/editor/categorias/<int:id_categoria>/editar",
    methods=["POST"]
)
def editor_editar_categoria(
    id_categoria
):

    usuario = obtener_usuario_actual()


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


        imagen_anterior = categoria.imagen


        categoria.imagen = subir_imagen(
            imagen_archivo,
            carpeta="categorias"
        )


        if imagen_anterior:

            borrar_imagen(
                imagen_anterior
            )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_categorias"
        )
    )


# =====================================
# ELIMINAR CATEGORÍA
# =====================================

@bp.route(
    "/editor/categorias/<int:id_categoria>/eliminar",
    methods=["POST"]
)
def editor_eliminar_categoria(
    id_categoria
):

    usuario = obtener_usuario_actual()


    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return "Categoría no encontrada."


    imagen_categoria = categoria.imagen


    publicaciones = Publicacion.query.filter(
        Publicacion.categorias.any(
            Categoria.id
            ==
            categoria.id
        )
    ).all()


    for publicacion in publicaciones:

        if categoria in publicacion.categorias:

            publicacion.categorias.remove(
                categoria
            )


        if (
            publicacion.categoria_id
            ==
            categoria.id
        ):

            publicacion.categoria_id = None


    db.session.delete(
        categoria
    )


    db.session.commit()


    if imagen_categoria:

        borrar_imagen(
            imagen_categoria
        )


    return redirect(
        url_for(
            "editor.editor_categorias"
        )
    )


# =====================================
# ETIQUETAS
# =====================================

@bp.route(
    "/editor/etiquetas",
    methods=["GET", "POST"]
)
def editor_etiquetas():

    usuario = obtener_usuario_actual()


    if request.method == "POST":

        nombre = request.form.get(
            "nombre",
            ""
        ).strip()


        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()


        nombre = nombre.lstrip(
            "#"
        ).strip()


        if not nombre:

            return "Tenés que ingresar un nombre."


        etiqueta_existente = Etiqueta.query.filter_by(
            nombre=nombre
        ).first()


        if etiqueta_existente:

            return "Ya existe una etiqueta con ese nombre."


        nueva_etiqueta = Etiqueta(
            nombre=nombre,
            descripcion=descripcion
        )


        db.session.add(
            nueva_etiqueta
        )


        db.session.commit()


        return redirect(
            url_for(
                "editor.editor_etiquetas"
            )
        )


    etiquetas = Etiqueta.query.order_by(
        Etiqueta.nombre.asc()
    ).all()


    etiqueta_mas_usada = None


    if etiquetas:

        etiqueta_mas_usada = max(
            etiquetas,
            key=lambda etiqueta: len(
                etiqueta.publicaciones
            )
        )


    return render_template(
        "editor/etiquetas.html",
        usuario=usuario,
        etiquetas=etiquetas,
        etiqueta_mas_usada=etiqueta_mas_usada,
        seccion_activa="etiquetas"
    )


# =====================================
# EDITAR ETIQUETA
# =====================================

@bp.route(
    "/editor/etiquetas/<int:id_etiqueta>/editar",
    methods=["POST"]
)
def editor_editar_etiqueta(
    id_etiqueta
):

    usuario = obtener_usuario_actual()


    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return "Etiqueta no encontrada."


    nombre = request.form.get(
        "nombre",
        ""
    ).strip()


    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()


    nombre = nombre.lstrip(
        "#"
    ).strip()


    if not nombre:

        return "Tenés que ingresar un nombre."


    etiqueta_existente = Etiqueta.query.filter(
        Etiqueta.nombre == nombre,
        Etiqueta.id != id_etiqueta
    ).first()


    if etiqueta_existente:

        return "Ya existe otra etiqueta con ese nombre."


    etiqueta.nombre = nombre

    etiqueta.descripcion = descripcion


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_etiquetas"
        )
    )


# =====================================
# ELIMINAR ETIQUETA
# =====================================

@bp.route(
    "/editor/etiquetas/<int:id_etiqueta>/eliminar",
    methods=["POST"]
)
def editor_eliminar_etiqueta(
    id_etiqueta
):

    usuario = obtener_usuario_actual()


    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return "Etiqueta no encontrada."


    etiqueta.publicaciones.clear()


    db.session.delete(
        etiqueta
    )


    db.session.commit()


    return redirect(
        url_for(
            "editor.editor_etiquetas"
        )
    )


# =====================================
# PERFIL EDITOR
# =====================================

@bp.route(
    "/editor/perfil",
    methods=["GET", "POST"]
)
def editor_perfil():

    usuario = obtener_usuario_actual()


    if request.method == "POST":

        usuario.nombre = request.form.get(
            "nombre",
            usuario.nombre
        ).strip()


        usuario.apellido = request.form.get(
            "apellido",
            usuario.apellido
        ).strip()


        usuario.usuario = request.form.get(
            "usuario",
            usuario.usuario
        ).strip()


        usuario.email = request.form.get(
            "email",
            usuario.email
        ).strip()


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


        db.session.commit()


        if foto_anterior:

            borrar_imagen(
                foto_anterior
            )


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


# =====================================
# CAMBIAR CONTRASEÑA
# =====================================

@bp.route(
    "/editor/perfil/cambiar-password",
    methods=["POST"]
)
def editor_cambiar_password():

    usuario = obtener_usuario_actual()


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


# =====================================
# VISTA PREVIA
# =====================================

@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/vista-previa"
)
def editor_vista_previa_publicacion(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        autor_id=usuario.id
    ).first()


    if not publicacion:

        return redirect(
            url_for(
                "editor.editor_publicaciones"
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

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


            carruseles[
                bloque.id
            ] = imagenes


    return render_template(
        "editor/vista_previa_publicacion.html",
        usuario=usuario,
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles,
        seccion_activa="publicaciones"
    )


# =====================================
# EDITAR PUBLICACIÓN
# =====================================

@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/editar",
    methods=["GET", "POST"]
)
def editor_editar_publicacion(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        autor_id=usuario.id
    ).first()


    if not publicacion:

        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )


    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).order_by(
        BloquePublicacion.orden
    ).all()


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    etiquetas = Etiqueta.query.order_by(
        Etiqueta.nombre.asc()
    ).all()


    if request.method == "POST":

        titulo = request.form.get(
            "titulo",
            ""
        ).strip()


        if titulo:

            publicacion.titulo = titulo


        resumen = request.form.get(
            "resumen",
            ""
        ).strip()


        publicacion.resumen = resumen


        categorias_ids = request.form.getlist(
            "categorias"
        )


        categorias_seleccionadas = []


        for categoria_id in categorias_ids:

            categoria = db.session.get(
                Categoria,
                int(categoria_id)
            )


            if categoria:

                categorias_seleccionadas.append(
                    categoria
                )


        publicacion.categorias = (
            categorias_seleccionadas
        )


        if categorias_seleccionadas:

            publicacion.categoria_id = (
                categorias_seleccionadas[0].id
            )

        else:

            publicacion.categoria_id = None


        etiquetas_ids = request.form.getlist(
            "etiquetas"
        )


        etiquetas_seleccionadas = []


        for etiqueta_id in etiquetas_ids:

            etiqueta = db.session.get(
                Etiqueta,
                int(etiqueta_id)
            )


            if etiqueta:

                etiquetas_seleccionadas.append(
                    etiqueta
                )


        publicacion.etiquetas = (
            etiquetas_seleccionadas
        )


        accion = request.form.get(
            "accion",
            "borrador"
        )


        if accion == "publicar":

            publicacion.estado = "publicada"

        else:

            publicacion.estado = "borrador"


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


            portada_anterior = (
                publicacion.imagen_portada
            )


            publicacion.imagen_portada = subir_imagen(
                nueva_portada,
                carpeta="publicaciones"
            )


            if portada_anterior:

                borrar_imagen(
                    portada_anterior
                )


        for bloque in bloques:

            if bloque.tipo == "texto":

                contenido = request.form.get(
                    f"bloque_{bloque.id}_texto",
                    ""
                ).strip()


                bloque.contenido = contenido


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


                    imagen_anterior = (
                        bloque.contenido
                    )


                    bloque.contenido = subir_imagen(
                        nueva_imagen,
                        carpeta="publicaciones/contenido"
                    )


                    if imagen_anterior:

                        borrar_imagen(
                            imagen_anterior
                        )


        bloques_nuevos_orden = request.form.get(
            "bloques_nuevos_orden",
            ""
        )


        tipos_nuevos = [
            tipo
            for tipo in bloques_nuevos_orden.split(",")
            if tipo
        ]


        ultimo_orden = 0


        if bloques:

            ultimo_orden = bloques[-1].orden


        for indice, tipo in enumerate(
            tipos_nuevos,
            start=1
        ):

            nuevo_orden = (
                ultimo_orden
                +
                indice
            )


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


        db.session.commit()


        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )


    carruseles = {}


    for bloque in bloques:

        if bloque.tipo == "carrusel":

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).order_by(
                ImagenCarrusel.orden
            ).all()


            carruseles[
                bloque.id
            ] = imagenes


    return render_template(
        "editor/editar_publicacion.html",
        usuario=usuario,
        publicacion=publicacion,
        bloques=bloques,
        carruseles=carruseles,
        categorias=categorias,
        etiquetas=etiquetas,
        seccion_activa="publicaciones"
    )


# =====================================
# ELIMINAR PUBLICACIÓN
# =====================================

@bp.route(
    "/editor/publicaciones/<int:id_publicacion>/eliminar",
    methods=["POST"]
)
def editor_eliminar_publicacion(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    publicacion = Publicacion.query.filter_by(
        id=id_publicacion,
        autor_id=usuario.id
    ).first()


    if not publicacion:

        return redirect(
            url_for(
                "editor.editor_publicaciones"
            )
        )


    imagenes_a_eliminar = []


    if publicacion.imagen_portada:

        imagenes_a_eliminar.append(
            publicacion.imagen_portada
        )


    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for bloque in bloques:

        if (
            bloque.tipo == "imagen"
            and bloque.contenido
        ):

            imagenes_a_eliminar.append(
                bloque.contenido
            )


        if bloque.tipo == "carrusel":

            imagenes = ImagenCarrusel.query.filter_by(
                bloque_id=bloque.id
            ).all()


            for imagen in imagenes:

                if imagen.imagen:

                    imagenes_a_eliminar.append(
                        imagen.imagen
                    )


                db.session.delete(
                    imagen
                )


        db.session.delete(
            bloque
        )


    publicacion.categorias = []

    publicacion.etiquetas = []


    db.session.delete(
        publicacion
    )


    db.session.commit()


    for imagen in imagenes_a_eliminar:

        borrar_imagen(
            imagen
        )


    return redirect(
        url_for(
            "editor.editor_publicaciones"
        )
    )