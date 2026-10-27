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
from almacenamiento import extension_valida, subir_imagen, borrar_imagen


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


    return render_template(
        "perfil/perfil.html",
        usuario=usuario
    )

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

@bp.route("/perfil/comentarios")
def mis_comentarios():

    return render_template(
        "perfil/comentarios.html"
    )


@bp.route("/perfil/guardados")
def guardados():

    return render_template(
        "perfil/guardados.html"
    )


@bp.route("/perfil/etiquetas")
def etiquetas_guardadas():

    return render_template(
        "perfil/etiquetas.html"
    )

def actualizar_perfil_usuario(usuario):

    usuario.nombre = request.form.get(
        "nombre",
        usuario.nombre
    )

    usuario.apellido = request.form.get(
        "apellido",
        usuario.apellido
    )

    usuario.usuario = request.form.get(
        "usuario",
        usuario.usuario
    )

    usuario.email = request.form.get(
        "email",
        usuario.email
    )


    foto = request.files.get(
        "foto"
    )


    if foto and foto.filename:

        if not extension_valida(
            foto.filename
        ):

            return False, "La imagen debe ser JPG, JPEG, PNG, WEBP o GIF."


        foto_anterior = usuario.foto


        usuario.foto = subir_imagen(
            foto,
            carpeta="avatares"
        )


        db.session.commit()


        borrar_imagen(
            foto_anterior
        )

    else:

        db.session.commit()


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


    return True, "Perfil actualizado correctamente."