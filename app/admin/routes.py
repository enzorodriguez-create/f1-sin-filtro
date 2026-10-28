from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session
)

from app.extensions import db
from app.models import Usuario


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
        "admin/solicitudes.html",
        usuario=usuario,
        seccion_activa="solicitudes"
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

@bp.route("/admin/perfil")
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

    return render_template(
        "admin/perfil.html",
        usuario=usuario,
        seccion_activa="perfil"
    )