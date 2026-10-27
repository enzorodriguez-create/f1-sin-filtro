from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session
)

from app.extensions import db
from app.models import (Usuario, Publicacion, BloquePublicacion,
    ImagenCarrusel  )  


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

    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario,
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

@bp.route("/editor/categorias")
def editor_categorias():

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/categorias.html",
        usuario=usuario,
        seccion_activa="categorias"
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

    return render_template(
        "editor/perfil.html",
        usuario=usuario,
        seccion_activa="perfil_editor"
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
    "/editor/publicaciones/<int:id_publicacion>/editar"
)
def editor_editar_publicacion(id_publicacion):

    usuario = obtener_usuario_actual()

    return render_template(
        "editor/editar_publicacion.html",
        usuario=usuario,
        id_publicacion=id_publicacion,
        seccion_activa="publicaciones"
    )