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
    Comentario,
    PublicacionGuardada
)

from almacenamiento import (
    extension_valida,
    subir_imagen,
    borrar_imagen
)

from ia.moderacion import clasificar_comentario


bp = Blueprint(
    "perfil",
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
# SEGURIDAD USUARIO
# =====================================

@bp.before_request
def proteger_rutas_usuario():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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


    if usuario.rol != "usuario":

        return redirect(
            url_for(
                "main.inicio"
            )
        )


# =====================================
# PERFIL
# =====================================

@bp.route("/perfil")
def perfil():

    usuario = obtener_usuario_actual()


    cantidad_comentarios = Comentario.query.filter_by(
        usuario_id=usuario.id
    ).count()


    cantidad_guardados = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id
    ).count()


    comentarios_recientes = Comentario.query.filter_by(
        usuario_id=usuario.id
    ).order_by(
        Comentario.id.desc()
    ).limit(3).all()


    return render_template(
        "perfil/perfil.html",
        usuario=usuario,
        cantidad_comentarios=cantidad_comentarios,
        cantidad_guardados=cantidad_guardados,
        comentarios_recientes=comentarios_recientes
    )


# =====================================
# EDITAR PERFIL
# =====================================

@bp.route(
    "/perfil/editar",
    methods=["GET", "POST"]
)
def editar_perfil():

    usuario = obtener_usuario_actual()


    mensaje = None


    if request.method == "POST":

        exito, mensaje = actualizar_perfil_usuario(
            usuario
        )


        if exito:

            return redirect(
                url_for(
                    "perfil.perfil"
                )
            )


    return render_template(
        "perfil/editar.html",
        usuario=usuario,
        mensaje=mensaje
    )


# =====================================
# SOLICITAR EDITOR
# =====================================

@bp.route(
    "/perfil/solicitar-editor",
    methods=["GET", "POST"]
)
def solicitar_editor():

    usuario = obtener_usuario_actual()


    solicitud_pendiente = SolicitudEditor.query.filter_by(
        usuario_id=usuario.id,
        estado="pendiente"
    ).first()


    if request.method == "POST":

        if solicitud_pendiente:

            return redirect(
                url_for(
                    "perfil.solicitar_editor"
                )
            )


        motivo = request.form.get(
            "motivo",
            ""
        ).strip()


        if not motivo:

            return render_template(
                "perfil/solicitar_editor.html",
                usuario=usuario,
                solicitud_pendiente=solicitud_pendiente,
                error="Tenés que indicar por qué querés ser editor."
            )


        if len(motivo) > 500:

            return render_template(
                "perfil/solicitar_editor.html",
                usuario=usuario,
                solicitud_pendiente=solicitud_pendiente,
                error="El motivo no puede superar los 500 caracteres."
            )


        nueva_solicitud = SolicitudEditor(
            usuario_id=usuario.id,
            motivo=motivo,
            estado="pendiente"
        )


        db.session.add(
            nueva_solicitud
        )


        db.session.commit()


        return redirect(
            url_for(
                "perfil.solicitar_editor"
            )
        )


    return render_template(
        "perfil/solicitar_editor.html",
        usuario=usuario,
        solicitud_pendiente=solicitud_pendiente
    )


# =====================================
# MIS COMENTARIOS
# =====================================

@bp.route("/perfil/comentarios")
def comentarios():

    usuario = obtener_usuario_actual()


    comentarios = Comentario.query.filter_by(
        usuario_id=usuario.id
    ).order_by(
        Comentario.id.desc()
    ).all()


    return render_template(
        "perfil/comentarios.html",
        usuario=usuario,
        comentarios=comentarios
    )


# =====================================
# EDITAR COMENTARIO
# =====================================

@bp.route(
    "/perfil/comentarios/<int:id_comentario>/editar",
    methods=["GET", "POST"]
)
def editar_comentario(
    id_comentario
):

    usuario = obtener_usuario_actual()


    comentario = Comentario.query.filter_by(
        id=id_comentario,
        usuario_id=usuario.id
    ).first()


    if not comentario:

        return redirect(
            url_for(
                "perfil.comentarios"
            )
        )


    error = None


    if request.method == "POST":

        contenido = request.form.get(
            "contenido",
            ""
        ).strip()


        if not contenido:

            error = "El comentario no puede estar vacío."


        elif len(contenido) > 1000:

            error = (
                "El comentario no puede superar "
                "los 1000 caracteres."
            )


        else:

            moderacion, confianza = clasificar_comentario(
                contenido
            )


            comentario.contenido = contenido

            comentario.moderacion = moderacion

            comentario.confianza = float(
                confianza
            )


            db.session.commit()


            return redirect(
                url_for(
                    "perfil.comentarios"
                )
            )


    return render_template(
        "perfil/editar_comentario.html",
        usuario=usuario,
        comentario=comentario,
        error=error
    )


# =====================================
# ELIMINAR COMENTARIO
# =====================================

@bp.route(
    "/perfil/comentarios/<int:id_comentario>/eliminar",
    methods=["POST"]
)
def eliminar_comentario(
    id_comentario
):

    usuario = obtener_usuario_actual()


    comentario = Comentario.query.filter_by(
        id=id_comentario,
        usuario_id=usuario.id
    ).first()


    if not comentario:

        return redirect(
            url_for(
                "perfil.comentarios"
            )
        )


    db.session.delete(
        comentario
    )


    db.session.commit()


    return redirect(
        url_for(
            "perfil.comentarios"
        )
    )


# =====================================
# GUARDADOS
# =====================================

@bp.route("/perfil/guardados")
def guardados():

    usuario = obtener_usuario_actual()


    guardados = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id
    ).order_by(
        PublicacionGuardada.id.desc()
    ).all()


    return render_template(
        "perfil/guardados.html",
        usuario=usuario,
        guardados=guardados
    )


# =====================================
# GUARDAR PUBLICACIÓN
# =====================================

@bp.route(
    "/perfil/guardados/<int:id_publicacion>/guardar",
    methods=["POST"]
)
def guardar_publicacion(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    guardado_existente = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id,
        publicacion_id=id_publicacion
    ).first()


    if not guardado_existente:

        nuevo_guardado = PublicacionGuardada(
            usuario_id=usuario.id,
            publicacion_id=id_publicacion
        )


        db.session.add(
            nuevo_guardado
        )


        db.session.commit()


    return redirect(
        url_for(
            "main.post",
            id_publicacion=id_publicacion
        )
    )


# =====================================
# QUITAR GUARDADO
# =====================================

@bp.route(
    "/perfil/guardados/<int:id_publicacion>/quitar",
    methods=["POST"]
)
def quitar_publicacion_guardada(
    id_publicacion
):

    usuario = obtener_usuario_actual()


    guardado = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id,
        publicacion_id=id_publicacion
    ).first()


    if guardado:

        db.session.delete(
            guardado
        )


        db.session.commit()


    return redirect(
        url_for(
            "perfil.guardados"
        )
    )


# =====================================
# ACTUALIZAR PERFIL
# =====================================

def actualizar_perfil_usuario(
    usuario
):

    # =====================================
    # USUARIO Y EMAIL
    # =====================================

    nuevo_usuario = request.form.get(
        "usuario",
        usuario.usuario
    ).strip()


    nuevo_email = request.form.get(
        "email",
        usuario.email
    ).strip()


    usuario_existente = Usuario.query.filter(
        Usuario.usuario == nuevo_usuario,
        Usuario.id != usuario.id
    ).first()


    if usuario_existente:

        return (
            False,
            "Ya existe otro usuario con ese nombre de usuario."
        )


    email_existente = Usuario.query.filter(
        Usuario.email == nuevo_email,
        Usuario.id != usuario.id
    ).first()


    if email_existente:

        return (
            False,
            "Ya existe otro usuario con ese email."
        )


    # =====================================
    # DATOS PERSONALES
    # =====================================

    usuario.nombre = request.form.get(
        "nombre",
        usuario.nombre
    ).strip()


    usuario.apellido = request.form.get(
        "apellido",
        usuario.apellido
    ).strip()


    usuario.usuario = nuevo_usuario


    usuario.email = nuevo_email


    # =====================================
    # CONTRASEÑA
    # =====================================

    if usuario.tipo_login == "normal":

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


        if (
            password_actual
            or password_nueva
            or password_confirmacion
        ):

            if not usuario.verificar_password(
                password_actual
            ):

                return (
                    False,
                    "La contraseña actual es incorrecta."
                )


            if not password_nueva:

                return (
                    False,
                    "Tenés que ingresar una nueva contraseña."
                )


            if (
                password_nueva
                !=
                password_confirmacion
            ):

                return (
                    False,
                    "Las contraseñas nuevas no coinciden."
                )


            usuario.guardar_password(
                password_nueva
            )


    # =====================================
    # FOTO
    # =====================================

    foto = request.files.get(
        "foto"
    )


    foto_anterior = None


    if foto and foto.filename:

        if not extension_valida(
            foto.filename
        ):

            return (
                False,
                "La imagen debe ser JPG, JPEG, PNG, WEBP o GIF."
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


    return (
        True,
        "Perfil actualizado correctamente."
    )