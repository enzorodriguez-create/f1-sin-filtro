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