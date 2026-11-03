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


bp = Blueprint(
    "perfil",
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


@bp.route("/perfil")
def perfil():

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    # =========================
    # CANTIDAD DE COMENTARIOS
    # =========================

    cantidad_comentarios = Comentario.query.filter_by(
        usuario_id=usuario.id
    ).count()


    # =========================
    # PUBLICACIONES GUARDADAS
    # =========================

    cantidad_guardados = PublicacionGuardada.query.filter_by(
        usuario_id=usuario.id
    ).count()


    # =========================
    # ACTIVIDAD RECIENTE
    # =========================

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


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


    if usuario.rol != "usuario":

        return redirect(
            url_for(
                "perfil.perfil"
            )
        )


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


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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
def editar_comentario(id_comentario):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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


    if request.method == "POST":

        contenido = request.form.get(
            "contenido",
            ""
        ).strip()


        if contenido:

            comentario.contenido = contenido

            db.session.commit()


            return redirect(
                url_for(
                    "perfil.comentarios"
                )
            )


    return render_template(
        "perfil/editar_comentario.html",
        comentario=comentario
    )


# =====================================
# ELIMINAR COMENTARIO
# =====================================

@bp.route(
    "/perfil/comentarios/<int:id_comentario>/eliminar",
    methods=["POST"]
)
def eliminar_comentario(id_comentario):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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
def guardar_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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
# QUITAR PUBLICACIÓN GUARDADA
# =====================================

@bp.route(
    "/perfil/guardados/<int:id_publicacion>/quitar",
    methods=["POST"]
)
def quitar_publicacion_guardada(id_publicacion):

    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for(
                "auth.login"
            )
        )


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
# ETIQUETAS
# =====================================

@bp.route("/perfil/etiquetas")
def etiquetas_guardadas():

    return render_template(
        "perfil/etiquetas.html"
    )


# =====================================
# ACTUALIZAR PERFIL
# =====================================

def actualizar_perfil_usuario(usuario):

    # =========================
    # DATOS PERSONALES
    # =========================

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


    # =========================
    # CAMBIO DE CONTRASEÑA
    # =========================

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
                False,
                "La imagen debe ser JPG, JPEG, PNG, WEBP o GIF."
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


    return (
        True,
        "Perfil actualizado correctamente."
    )