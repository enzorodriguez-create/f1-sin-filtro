from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from app.extensions import db

from app.models import (
    Usuario,
    SolicitudEditor,
    Publicacion,
    Comentario,
    Categoria,
    Etiqueta,
    BloquePublicacion,
    ImagenCarrusel,
    PublicacionGuardada
)

from almacenamiento import (
    extension_valida,
    subir_imagen,
    borrar_imagen
)


bp = Blueprint(
    "admin",
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
# DASHBOARD
# =====================================

@bp.route("/admin")
def admin_dashboard():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    cantidad_usuarios = Usuario.query.count()


    cantidad_editores = Usuario.query.filter_by(
        rol="editor"
    ).count()


    cantidad_publicaciones = Publicacion.query.count()


    cantidad_comentarios = Comentario.query.count()


    cantidad_solicitudes = SolicitudEditor.query.filter_by(
        estado="pendiente"
    ).count()


    solicitudes_recientes = (
        db.session.query(
            SolicitudEditor,
            Usuario
        )
        .join(
            Usuario,
            SolicitudEditor.usuario_id
            ==
            Usuario.id
        )
        .filter(
            SolicitudEditor.estado
            ==
            "pendiente"
        )
        .order_by(
            SolicitudEditor.id.desc()
        )
        .limit(3)
        .all()
    )


    usuarios_recientes = Usuario.query.order_by(
        Usuario.id.desc()
    ).limit(3).all()


    cantidad_categorias = Categoria.query.count()


    cantidad_etiquetas = Etiqueta.query.count()


    cantidad_publicadas = Publicacion.query.filter_by(
        estado="publicada"
    ).count()


    cantidad_borradores = Publicacion.query.filter_by(
        estado="borrador"
    ).count()


    return render_template(
        "admin/dashboard.html",

        usuario=usuario,

        cantidad_usuarios=cantidad_usuarios,
        cantidad_editores=cantidad_editores,
        cantidad_publicaciones=cantidad_publicaciones,
        cantidad_comentarios=cantidad_comentarios,
        cantidad_solicitudes=cantidad_solicitudes,

        solicitudes_recientes=solicitudes_recientes,
        usuarios_recientes=usuarios_recientes,

        cantidad_categorias=cantidad_categorias,
        cantidad_etiquetas=cantidad_etiquetas,
        cantidad_publicadas=cantidad_publicadas,
        cantidad_borradores=cantidad_borradores,

        seccion_activa="dashboard"
    )


# =====================================
# USUARIOS
# =====================================

@bp.route("/admin/usuarios")
def admin_usuarios():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    usuarios = Usuario.query.order_by(
        Usuario.id.desc()
    ).all()


    cantidad_usuarios = len(
        usuarios
    )


    cantidad_editores = Usuario.query.filter_by(
        rol="editor"
    ).count()


    cantidad_premium = Usuario.query.filter_by(
        premium=True
    ).count()


    cantidad_usuarios_normales = Usuario.query.filter_by(
        rol="usuario"
    ).count()


    return render_template(
        "admin/usuarios.html",

        usuario=usuario,
        usuarios=usuarios,

        cantidad_usuarios=cantidad_usuarios,
        cantidad_editores=cantidad_editores,
        cantidad_premium=cantidad_premium,
        cantidad_usuarios_normales=cantidad_usuarios_normales,

        seccion_activa="usuarios"
    )


# =====================================
# CAMBIAR ROL
# =====================================

@bp.route(
    "/admin/usuarios/<int:id_usuario>/rol",
    methods=["POST"]
)
def admin_cambiar_rol(
    id_usuario
):

    admin = obtener_usuario_actual()

    if not admin:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if admin.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    usuario = db.session.get(
        Usuario,
        id_usuario
    )


    if not usuario:

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    if usuario.id == admin.id:

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    nuevo_rol = request.form.get(
        "rol",
        ""
    )


    roles_validos = [
        "usuario",
        "editor",
        "admin"
    ]


    if nuevo_rol in roles_validos:

        usuario.rol = nuevo_rol

        db.session.commit()


    return redirect(
        url_for(
            "admin.admin_usuarios"
        )
    )


# =====================================
# ELIMINAR USUARIO
# =====================================

@bp.route(
    "/admin/usuarios/<int:id_usuario>/eliminar",
    methods=["POST"]
)
def admin_eliminar_usuario(
    id_usuario
):

    admin = obtener_usuario_actual()

    if not admin:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if admin.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    usuario = db.session.get(
        Usuario,
        id_usuario
    )


    if not usuario:

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    if usuario.rol == "admin":

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    tiene_publicaciones = Publicacion.query.filter_by(
        autor_id=usuario.id
    ).first()


    tiene_comentarios = Comentario.query.filter_by(
        usuario_id=usuario.id
    ).first()


    if (
        tiene_publicaciones
        or
        tiene_comentarios
    ):

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    guardados = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id
    ).all()


    for guardado in guardados:

        db.session.delete(
            guardado
        )


    solicitudes = SolicitudEditor.query.filter_by(
        usuario_id=usuario.id
    ).all()


    for solicitud in solicitudes:

        db.session.delete(
            solicitud
        )


    foto_usuario = usuario.foto


    db.session.delete(
        usuario
    )


    db.session.commit()


    if foto_usuario:

        borrar_imagen(
            foto_usuario
        )


    return redirect(
        url_for(
            "admin.admin_usuarios"
        )
    )


# =====================================
# NOTIFICACIONES
# =====================================

@bp.context_processor
def notificaciones_admin():

    solicitudes_pendientes = SolicitudEditor.query.filter_by(
        estado="pendiente"
    ).count()


    return {
        "solicitudes_pendientes":
            solicitudes_pendientes
    }


# =====================================
# SOLICITUDES
# =====================================

@bp.route("/admin/solicitudes")
def admin_solicitudes():

    admin = obtener_usuario_actual()

    if not admin:

        return redirect(
            url_for(
                "auth.login"
            )
        )

    if admin.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    solicitudes = (
        db.session.query(
            SolicitudEditor,
            Usuario
        )
        .join(
            Usuario,
            SolicitudEditor.usuario_id
            ==
            Usuario.id
        )
        .order_by(
            SolicitudEditor.id.desc()
        )
        .all()
    )


    return render_template(
        "admin/solicitudes.html",
        usuario=admin,
        solicitudes=solicitudes,
        seccion_activa="solicitudes"
    )


# =====================================
# APROBAR SOLICITUD
# =====================================

@bp.route(
    "/admin/solicitudes/<int:id_solicitud>/aprobar",
    methods=["POST"]
)
def aprobar_solicitud_editor(
    id_solicitud
):

    admin = obtener_usuario_actual()


    if not admin or admin.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    solicitud = db.session.get(
        SolicitudEditor,
        id_solicitud
    )


    if not solicitud:

        return redirect(
            url_for(
                "admin.admin_solicitudes"
            )
        )


    usuario = db.session.get(
        Usuario,
        solicitud.usuario_id
    )


    if usuario:

        usuario.rol = "editor"

        solicitud.estado = "aprobada"

        db.session.commit()


    return redirect(
        url_for(
            "admin.admin_solicitudes"
        )
    )


# =====================================
# RECHAZAR SOLICITUD
# =====================================

@bp.route(
    "/admin/solicitudes/<int:id_solicitud>/rechazar",
    methods=["POST"]
)
def rechazar_solicitud_editor(
    id_solicitud
):

    admin = obtener_usuario_actual()


    if not admin or admin.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    solicitud = db.session.get(
        SolicitudEditor,
        id_solicitud
    )


    if solicitud:

        solicitud.estado = "rechazada"

        db.session.commit()


    return redirect(
        url_for(
            "admin.admin_solicitudes"
        )
    )


# =====================================
# PUBLICACIONES
# =====================================

@bp.route("/admin/publicaciones")
def admin_publicaciones():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    publicaciones = Publicacion.query.order_by(
        Publicacion.id.desc()
    ).all()


    autores_publicaciones = {}

    autores = []

    autores_ids = []


    for publicacion in publicaciones:

        autor = db.session.get(
            Usuario,
            publicacion.autor_id
        )


        autores_publicaciones[
            publicacion.id
        ] = autor


        if (
            autor
            and autor.id not in autores_ids
        ):

            autores.append(
                autor
            )

            autores_ids.append(
                autor.id
            )


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    cantidad_publicaciones = len(
        publicaciones
    )


    cantidad_publicadas = Publicacion.query.filter_by(
        estado="publicada"
    ).count()


    cantidad_borradores = Publicacion.query.filter_by(
        estado="borrador"
    ).count()


    return render_template(
        "admin/publicaciones.html",

        usuario=usuario,
        publicaciones=publicaciones,

        autores=autores,

        autores_publicaciones=
            autores_publicaciones,

        categorias=categorias,

        cantidad_publicaciones=
            cantidad_publicaciones,

        cantidad_publicadas=
            cantidad_publicadas,

        cantidad_borradores=
            cantidad_borradores,

        seccion_activa="publicaciones"
    )


# =====================================
# ELIMINAR PUBLICACIÓN
# =====================================

@bp.route(
    "/admin/publicaciones/<int:id_publicacion>/eliminar",
    methods=["POST"]
)
def admin_eliminar_publicacion(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    publicacion = db.session.get(
        Publicacion,
        id_publicacion
    )


    if not publicacion:

        return redirect(
            url_for(
                "admin.admin_publicaciones"
            )
        )


    imagenes_a_eliminar = []


    if publicacion.imagen_portada:

        imagenes_a_eliminar.append(
            publicacion.imagen_portada
        )


    comentarios = Comentario.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for comentario in comentarios:

        db.session.delete(
            comentario
        )


    guardados = PublicacionGuardada.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for guardado in guardados:

        db.session.delete(
            guardado
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
            "admin.admin_publicaciones"
        )
    )


# =====================================
# CATEGORÍAS
# =====================================

@bp.route(
    "/admin/categorias",
    methods=["GET", "POST"]
)
def admin_categorias():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


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

            return (
                "Tenés que ingresar "
                "un nombre."
            )


        categoria_existente = Categoria.query.filter_by(
            nombre=nombre
        ).first()


        if categoria_existente:

            return (
                "Ya existe una categoría "
                "con ese nombre."
            )


        imagen = None


        if (
            imagen_archivo
            and imagen_archivo.filename
        ):

            if not extension_valida(
                imagen_archivo.filename
            ):

                return (
                    "Formato de imagen "
                    "no válido."
                )


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
                "admin.admin_categorias"
            )
        )


    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    cantidad_categorias = len(
        categorias
    )


    cantidad_publicaciones = Publicacion.query.count()


    usos_categorias = {}


    categoria_mas_usada = None

    mayor_cantidad = 0


    for categoria in categorias:

        cantidad = Publicacion.query.filter(
            Publicacion.categorias.any(
                Categoria.id
                ==
                categoria.id
            )
        ).count()


        usos_categorias[
            categoria.id
        ] = cantidad


        if cantidad > mayor_cantidad:

            mayor_cantidad = cantidad

            categoria_mas_usada = categoria


    return render_template(
        "admin/categorias.html",

        usuario=usuario,
        categorias=categorias,

        cantidad_categorias=
            cantidad_categorias,

        cantidad_publicaciones=
            cantidad_publicaciones,

        usos_categorias=
            usos_categorias,

        categoria_mas_usada=
            categoria_mas_usada,

        mayor_cantidad=
            mayor_cantidad,

        seccion_activa="categorias"
    )


# =====================================
# EDITAR CATEGORÍA
# =====================================

@bp.route(
    "/admin/categorias/<int:id_categoria>/editar",
    methods=["POST"]
)
def admin_editar_categoria(
    id_categoria
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return redirect(
            url_for(
                "admin.admin_categorias"
            )
        )


    nombre = request.form.get(
        "nombre",
        ""
    ).strip()


    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()


    if not nombre:

        return (
            "Tenés que ingresar "
            "un nombre."
        )


    categoria_existente = Categoria.query.filter(
        Categoria.nombre == nombre,
        Categoria.id != id_categoria
    ).first()


    if categoria_existente:

        return (
            "Ya existe otra categoría "
            "con ese nombre."
        )


    categoria.nombre = nombre

    categoria.descripcion = descripcion


    imagen_archivo = request.files.get(
        "imagen"
    )


    imagen_anterior = None


    if (
        imagen_archivo
        and imagen_archivo.filename
    ):

        if not extension_valida(
            imagen_archivo.filename
        ):

            return (
                "Formato de imagen "
                "no válido."
            )


        imagen_anterior = categoria.imagen


        categoria.imagen = subir_imagen(
            imagen_archivo,
            carpeta="categorias"
        )


    db.session.commit()


    if imagen_anterior:

        borrar_imagen(
            imagen_anterior
        )


    return redirect(
        url_for(
            "admin.admin_categorias"
        )
    )


# =====================================
# ELIMINAR CATEGORÍA
# =====================================

@bp.route(
    "/admin/categorias/<int:id_categoria>/eliminar",
    methods=["POST"]
)
def admin_eliminar_categoria(
    id_categoria
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    categoria = db.session.get(
        Categoria,
        id_categoria
    )


    if not categoria:

        return redirect(
            url_for(
                "admin.admin_categorias"
            )
        )


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
            "admin.admin_categorias"
        )
    )


# =====================================
# ETIQUETAS
# =====================================

@bp.route(
    "/admin/etiquetas",
    methods=["GET", "POST"]
)
def admin_etiquetas():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


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

            return (
                "Tenés que ingresar "
                "un nombre."
            )


        etiqueta_existente = Etiqueta.query.filter_by(
            nombre=nombre
        ).first()


        if etiqueta_existente:

            return (
                "Ya existe una etiqueta "
                "con ese nombre."
            )


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
                "admin.admin_etiquetas"
            )
        )


    etiquetas = Etiqueta.query.order_by(
        Etiqueta.nombre.asc()
    ).all()


    cantidad_etiquetas = len(
        etiquetas
    )


    usos_etiquetas = {}


    etiqueta_mas_usada = None

    mayor_cantidad_etiqueta = 0


    for etiqueta in etiquetas:

        cantidad = Publicacion.query.filter(
            Publicacion.etiquetas.any(
                Etiqueta.id
                ==
                etiqueta.id
            )
        ).count()


        usos_etiquetas[
            etiqueta.id
        ] = cantidad


        if cantidad > mayor_cantidad_etiqueta:

            mayor_cantidad_etiqueta = cantidad

            etiqueta_mas_usada = etiqueta


    return render_template(
        "admin/etiquetas.html",

        usuario=usuario,
        etiquetas=etiquetas,

        cantidad_etiquetas=
            cantidad_etiquetas,

        usos_etiquetas=
            usos_etiquetas,

        etiqueta_mas_usada=
            etiqueta_mas_usada,

        mayor_cantidad_etiqueta=
            mayor_cantidad_etiqueta,

        seccion_activa="etiquetas"
    )


# =====================================
# EDITAR ETIQUETA
# =====================================

@bp.route(
    "/admin/etiquetas/<int:id_etiqueta>/editar",
    methods=["POST"]
)
def admin_editar_etiqueta(
    id_etiqueta
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return redirect(
            url_for(
                "admin.admin_etiquetas"
            )
        )


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

        return (
            "Tenés que ingresar "
            "un nombre."
        )


    etiqueta_existente = Etiqueta.query.filter(
        Etiqueta.nombre == nombre,
        Etiqueta.id != id_etiqueta
    ).first()


    if etiqueta_existente:

        return (
            "Ya existe otra etiqueta "
            "con ese nombre."
        )


    etiqueta.nombre = nombre

    etiqueta.descripcion = descripcion


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_etiquetas"
        )
    )


# =====================================
# ELIMINAR ETIQUETA
# =====================================

@bp.route(
    "/admin/etiquetas/<int:id_etiqueta>/eliminar",
    methods=["POST"]
)
def admin_eliminar_etiqueta(
    id_etiqueta
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    etiqueta = db.session.get(
        Etiqueta,
        id_etiqueta
    )


    if not etiqueta:

        return redirect(
            url_for(
                "admin.admin_etiquetas"
            )
        )


    publicaciones = Publicacion.query.filter(
        Publicacion.etiquetas.any(
            Etiqueta.id
            ==
            etiqueta.id
        )
    ).all()


    for publicacion in publicaciones:

        if etiqueta in publicacion.etiquetas:

            publicacion.etiquetas.remove(
                etiqueta
            )


    db.session.delete(
        etiqueta
    )


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_etiquetas"
        )
    )


# =====================================
# COMENTARIOS
# =====================================

@bp.route("/admin/comentarios")
def admin_comentarios():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    comentarios = Comentario.query.order_by(
        Comentario.fecha.desc()
    ).all()


    publicaciones = Publicacion.query.order_by(
        Publicacion.titulo.asc()
    ).all()


    cantidad_comentarios = len(
        comentarios
    )


    cantidad_publicaciones = Publicacion.query.count()


    return render_template(
        "admin/comentarios.html",

        usuario=usuario,

        comentarios=comentarios,

        publicaciones=publicaciones,

        cantidad_comentarios=
            cantidad_comentarios,

        cantidad_publicaciones=
            cantidad_publicaciones,

        seccion_activa="comentarios"
    )


# =====================================
# ELIMINAR COMENTARIO
# =====================================

@bp.route(
    "/admin/comentarios/<int:id_comentario>/eliminar",
    methods=["POST"]
)
def admin_eliminar_comentario(
    id_comentario
):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    comentario = db.session.get(
        Comentario,
        id_comentario
    )


    if not comentario:

        return redirect(
            url_for(
                "admin.admin_comentarios"
            )
        )


    db.session.delete(
        comentario
    )


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_comentarios"
        )
    )


# =====================================
# ANALÍTICAS
# =====================================

@bp.route("/admin/analiticas")
def admin_analiticas():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    # =====================================
    # ESTADÍSTICAS GENERALES
    # =====================================

    cantidad_usuarios = Usuario.query.count()


    cantidad_premium = Usuario.query.filter_by(
        premium=True
    ).count()


    cantidad_publicaciones = Publicacion.query.count()


    cantidad_comentarios = Comentario.query.count()


    cantidad_publicadas = Publicacion.query.filter_by(
        estado="publicada"
    ).count()


    cantidad_borradores = Publicacion.query.filter_by(
        estado="borrador"
    ).count()


    # =====================================
    # CATEGORÍAS MÁS USADAS
    # =====================================

    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    categorias_uso = []


    maximo_categoria = 0


    for categoria in categorias:

        cantidad = Publicacion.query.filter(
            Publicacion.categorias.any(
                Categoria.id
                ==
                categoria.id
            )
        ).count()


        categorias_uso.append(
            {
                "categoria": categoria,
                "cantidad": cantidad
            }
        )


        if cantidad > maximo_categoria:

            maximo_categoria = cantidad


    categorias_uso.sort(
        key=lambda item: item["cantidad"],
        reverse=True
    )


    categorias_uso = categorias_uso[:4]


    # =====================================
    # ETIQUETAS MÁS USADAS
    # =====================================

    etiquetas = Etiqueta.query.order_by(
        Etiqueta.nombre.asc()
    ).all()


    etiquetas_uso = []


    for etiqueta in etiquetas:

        cantidad = Publicacion.query.filter(
            Publicacion.etiquetas.any(
                Etiqueta.id
                ==
                etiqueta.id
            )
        ).count()


        etiquetas_uso.append(
            {
                "etiqueta": etiqueta,
                "cantidad": cantidad
            }
        )


    etiquetas_uso.sort(
        key=lambda item: item["cantidad"],
        reverse=True
    )


    etiquetas_uso = etiquetas_uso[:4]


    # =====================================
    # RENDIMIENTO DE EDITORES
    # =====================================

    editores = Usuario.query.filter_by(
        rol="editor"
    ).order_by(
        Usuario.nombre.asc()
    ).all()


    rendimiento_editores = []


    for editor in editores:

        publicaciones_editor = Publicacion.query.filter_by(
            autor_id=editor.id
        ).count()


        publicadas_editor = Publicacion.query.filter_by(
            autor_id=editor.id,
            estado="publicada"
        ).count()


        borradores_editor = Publicacion.query.filter_by(
            autor_id=editor.id,
            estado="borrador"
        ).count()


        rendimiento_editores.append(
            {
                "editor": editor,
                "total": publicaciones_editor,
                "publicadas": publicadas_editor,
                "borradores": borradores_editor
            }
        )


    rendimiento_editores.sort(
        key=lambda item: item["total"],
        reverse=True
    )


    return render_template(
        "admin/analiticas.html",

        usuario=usuario,

        cantidad_usuarios=cantidad_usuarios,
        cantidad_premium=cantidad_premium,
        cantidad_publicaciones=cantidad_publicaciones,
        cantidad_comentarios=cantidad_comentarios,
        cantidad_publicadas=cantidad_publicadas,
        cantidad_borradores=cantidad_borradores,

        categorias_uso=categorias_uso,
        maximo_categoria=maximo_categoria,

        etiquetas_uso=etiquetas_uso,

        rendimiento_editores=rendimiento_editores,

        seccion_activa="analiticas"
    )


# =====================================
# PERFIL ADMIN
# =====================================

@bp.route(
    "/admin/perfil",
    methods=["GET", "POST"]
)
def admin_perfil():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    if request.method == "POST":

        usuario.nombre = request.form.get(
            "nombre",
            ""
        ).strip()


        usuario.apellido = request.form.get(
            "apellido",
            ""
        ).strip()


        usuario.usuario = request.form.get(
            "usuario",
            ""
        ).strip()


        usuario.email = request.form.get(
            "email",
            ""
        ).strip()


        foto = request.files.get(
            "foto"
        )


        foto_anterior = None


        if (
            foto
            and foto.filename
        ):

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
                "admin.admin_perfil"
            )
        )


    return render_template(
        "admin/perfil.html",
        usuario=usuario,
        seccion_activa="perfil"
    )


# =====================================
# CAMBIAR CONTRASEÑA
# =====================================

@bp.route(
    "/admin/perfil/cambiar-password",
    methods=["POST"]
)
def admin_cambiar_password():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "admin":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


    password_actual = request.form.get(
        "password_actual",
        ""
    )


    password_nueva = request.form.get(
        "password_nueva",
        ""
    )


    password_confirmacion = request.form.get(
        "password_confirmacion",
        ""
    )


    if not usuario.verificar_password(
        password_actual
    ):

        return (
            "La contraseña actual "
            "es incorrecta."
        )


    if (
        password_nueva
        !=
        password_confirmacion
    ):

        return (
            "Las contraseñas nuevas "
            "no coinciden."
        )


    usuario.guardar_password(
        password_nueva
    )


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_perfil"
        )
    )