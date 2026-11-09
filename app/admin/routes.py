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


    # =====================================
    # ESTADÍSTICAS
    # =====================================

    cantidad_usuarios = Usuario.query.count()


    cantidad_editores = Usuario.query.filter_by(
        rol="editor"
    ).count()


    cantidad_publicaciones = Publicacion.query.count()


    cantidad_comentarios = Comentario.query.count()


    cantidad_solicitudes = SolicitudEditor.query.filter_by(
        estado="pendiente"
    ).count()


    # =====================================
    # SOLICITUDES RECIENTES
    # =====================================

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


    # =====================================
    # USUARIOS RECIENTES
    # =====================================

    usuarios_recientes = Usuario.query.order_by(
        Usuario.id.desc()
    ).limit(3).all()


    # =====================================
    # RESUMEN DEL PORTAL
    # =====================================

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


    # =====================================
    # NO MODIFICO MI PROPIO ROL
    # =====================================

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


    # =====================================
    # PROTEJO CUENTAS ADMIN
    # =====================================

    if usuario.rol == "admin":

        return redirect(
            url_for(
                "admin.admin_usuarios"
            )
        )


    # =====================================
    # COMPRUEBO PUBLICACIONES
    # =====================================

    tiene_publicaciones = Publicacion.query.filter_by(
        autor_id=usuario.id
    ).first()


    # =====================================
    # COMPRUEBO COMENTARIOS
    # =====================================

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


    # =====================================
    # GUARDADOS
    # =====================================

    guardados = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id
    ).all()


    for guardado in guardados:

        db.session.delete(
            guardado
        )


    # =====================================
    # SOLICITUDES
    # =====================================

    solicitudes = SolicitudEditor.query.filter_by(
        usuario_id=usuario.id
    ).all()


    for solicitud in solicitudes:

        db.session.delete(
            solicitud
        )


    # =====================================
    # FOTO
    # =====================================

    foto_usuario = usuario.foto


    # =====================================
    # ELIMINO USUARIO
    # =====================================

    db.session.delete(
        usuario
    )


    db.session.commit()


    # =====================================
    # ELIMINO FOTO
    # =====================================

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


    # =====================================
    # PUBLICACIONES
    # =====================================

    publicaciones = Publicacion.query.order_by(
        Publicacion.id.desc()
    ).all()


    # =====================================
    # AUTORES
    # =====================================

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


    # =====================================
    # CATEGORÍAS
    # =====================================

    categorias = Categoria.query.order_by(
        Categoria.nombre.asc()
    ).all()


    # =====================================
    # ESTADÍSTICAS
    # =====================================

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

        autores_publicaciones=autores_publicaciones,

        categorias=categorias,

        cantidad_publicaciones=cantidad_publicaciones,

        cantidad_publicadas=cantidad_publicadas,

        cantidad_borradores=cantidad_borradores,

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


    # =====================================
    # IMÁGENES A ELIMINAR
    # =====================================

    imagenes_a_eliminar = []


    if publicacion.imagen_portada:

        imagenes_a_eliminar.append(
            publicacion.imagen_portada
        )


    # =====================================
    # COMENTARIOS
    # =====================================

    comentarios = Comentario.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for comentario in comentarios:

        db.session.delete(
            comentario
        )


    # =====================================
    # PUBLICACIONES GUARDADAS
    # =====================================

    guardados = PublicacionGuardada.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for guardado in guardados:

        db.session.delete(
            guardado
        )


    # =====================================
    # BLOQUES
    # =====================================

    bloques = BloquePublicacion.query.filter_by(
        publicacion_id=publicacion.id
    ).all()


    for bloque in bloques:


        # =====================================
        # IMAGEN DE BLOQUE
        # =====================================

        if (
            bloque.tipo == "imagen"
            and bloque.contenido
        ):

            imagenes_a_eliminar.append(
                bloque.contenido
            )


        # =====================================
        # CARRUSEL
        # =====================================

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


    # =====================================
    # CATEGORÍAS Y ETIQUETAS
    # =====================================

    publicacion.categorias = []

    publicacion.etiquetas = []


    # =====================================
    # ELIMINO PUBLICACIÓN
    # =====================================

    db.session.delete(
        publicacion
    )


    db.session.commit()


    # =====================================
    # ELIMINO IMÁGENES
    # =====================================

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

@bp.route("/admin/categorias")
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


    return render_template(
        "admin/categorias.html",
        usuario=usuario,
        seccion_activa="categorias"
    )


# =====================================
# ETIQUETAS
# =====================================

@bp.route("/admin/etiquetas")
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


    return render_template(
        "admin/etiquetas.html",
        usuario=usuario,
        seccion_activa="etiquetas"
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


    return render_template(
        "admin/comentarios.html",
        usuario=usuario,
        seccion_activa="comentarios"
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


    return render_template(
        "admin/analiticas.html",
        usuario=usuario,
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


        # =====================================
        # NOMBRE
        # =====================================

        usuario.nombre = request.form.get(
            "nombre",
            ""
        ).strip()


        # =====================================
        # APELLIDO
        # =====================================

        usuario.apellido = request.form.get(
            "apellido",
            ""
        ).strip()


        # =====================================
        # USUARIO
        # =====================================

        usuario.usuario = request.form.get(
            "usuario",
            ""
        ).strip()


        # =====================================
        # EMAIL
        # =====================================

        usuario.email = request.form.get(
            "email",
            ""
        ).strip()


        # =====================================
        # FOTO
        # =====================================

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


        # =====================================
        # GUARDO CAMBIOS
        # =====================================

        db.session.commit()


        # =====================================
        # ELIMINO FOTO ANTERIOR
        # =====================================

        if foto_anterior:

            borrar_imagen(
                foto_anterior
            )


        # =====================================
        # ACTUALIZO SESIÓN
        # =====================================

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


    # =====================================
    # CONTRASEÑA ACTUAL
    # =====================================

    if not usuario.verificar_password(
        password_actual
    ):

        return (
            "La contraseña actual "
            "es incorrecta."
        )


    # =====================================
    # CONTRASEÑAS NUEVAS
    # =====================================

    if (
        password_nueva
        !=
        password_confirmacion
    ):

        return (
            "Las contraseñas nuevas "
            "no coinciden."
        )


    # =====================================
    # GUARDO NUEVA CONTRASEÑA
    # =====================================

    usuario.guardar_password(
        password_nueva
    )


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_perfil"
        )
    )