from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from app.extensions import db
from app.models import Usuario, SolicitudEditor
from almacenamiento import (
    extension_valida,
    subir_imagen
)


bp = Blueprint(
    "admin",
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


    return render_template(
        "admin/dashboard.html",
        usuario=usuario,
        seccion_activa="dashboard"
    )

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


    return render_template(
        "admin/usuarios.html",
        usuario=usuario,
        seccion_activa="usuarios"
    )

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
        .all()
    )


    return render_template(
        "admin/solicitudes.html",
        usuario=admin,
        solicitudes=solicitudes,
        seccion_activa="solicitudes"
    )

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

        # Cambio el rol del usuario a editor
        usuario.rol = "editor"


        # Marco la solicitud como aprobada
        solicitud.estado = "aprobada"


        db.session.commit()


    return redirect(
        url_for(
            "admin.admin_solicitudes"
        )
    )

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


    return render_template(
        "admin/publicaciones.html",
        usuario=usuario,
        seccion_activa="publicaciones"
    )

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


        # =========================
        # NOMBRE
        # =========================

        usuario.nombre = request.form.get(
            "nombre",
            ""
        ).strip()


        # =========================
        # APELLIDO
        # =========================

        usuario.apellido = request.form.get(
            "apellido",
            ""
        ).strip()


        # =========================
        # USUARIO
        # =========================

        usuario.usuario = request.form.get(
            "usuario",
            ""
        ).strip()


        # =========================
        # EMAIL
        # =========================

        usuario.email = request.form.get(
            "email",
            ""
        ).strip()


        # =========================
        # FOTO
        # =========================

        foto = request.files.get(
            "foto"
        )


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


            usuario.foto = subir_imagen(
                foto,
                carpeta="avatares"
            )


        # =========================
        # GUARDO CAMBIOS
        # =========================

        db.session.commit()


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
                "admin.admin_perfil"
            )
        )


    return render_template(
        "admin/perfil.html",
        usuario=usuario,
        seccion_activa="perfil"
    )

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


    # Compruebo la contraseña actual
    if not usuario.verificar_password(
        password_actual
    ):

        return "La contraseña actual es incorrecta."


    # Compruebo que las nuevas coincidan
    if (
        password_nueva
        !=
        password_confirmacion
    ):

        return "Las contraseñas nuevas no coinciden."


    # Guardo la nueva contraseña
    usuario.guardar_password(
        password_nueva
    )


    db.session.commit()


    return redirect(
        url_for(
            "admin.admin_perfil"
        )
    )