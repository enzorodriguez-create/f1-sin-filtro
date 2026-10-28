import os

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request
)

from app.extensions import db, oauth
from app.models import Usuario


bp = Blueprint(
    "auth",
    __name__
)

google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)


def guardar_usuario_en_session(usuario):

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


@bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        usuario = Usuario.query.filter_by(
            email=email
        ).first()


        if (
            usuario
            and usuario.verificar_password(
                password
            )
        ):

            guardar_usuario_en_session(
                usuario
            )


            if usuario.rol == "admin":

                return redirect(
                    "/admin"
                )


            elif usuario.rol == "editor":

                return redirect(
                    "/editor"
                )


            else:

                return redirect(
                    url_for(
                        "main.inicio"
                    )
                )


        return render_template(
    "login.html",
    error="Email o contraseña incorrectos."
)


    return render_template(
        "login.html"
    )


@bp.route(
    "/registro",
    methods=["GET", "POST"]
)
def registro():

    if request.method == "POST":

        nombre = request.form.get(
            "nombre"
        )

        apellido = request.form.get(
            "apellido"
        )

        nombre_usuario = request.form.get(
            "usuario"
        )

        email = request.form.get(
            "email"
        )

        password = request.form.get(
            "password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )


        if password != confirm_password:

            return "Las contraseñas no coinciden."


        email_existente = Usuario.query.filter_by(
            email=email
        ).first()


        if email_existente:

            return "El email ya está registrado."


        usuario_existente = Usuario.query.filter_by(
            usuario=nombre_usuario
        ).first()


        if usuario_existente:

            return "El nombre de usuario ya está registrado."


        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            usuario=nombre_usuario,
            email=email,
            rol="usuario",
            tipo_login="normal",
            premium=False
        )


        nuevo_usuario.guardar_password(
            password
        )


        db.session.add(
            nuevo_usuario
        )

        db.session.commit()


        return redirect(
            url_for(
                "auth.login"
            )
        )


    return render_template(
        "registro.html"
    )


@bp.route("/logout")
def logout():

    session.pop(
        "usuario",
        None
    )

    return redirect(
        url_for(
            "main.inicio"
        )
    )

@bp.route("/auth/google")
def login_google():

    return google.authorize_redirect(
        url_for(
            "auth.callback_google",
            _external=True
        )
    )


@bp.route("/auth/google/callback")
def callback_google():

    token = google.authorize_access_token()

    info = token["userinfo"]

    email = info.get("email")

    usuario = Usuario.query.filter_by(
        email=email
    ).first()


    if usuario is None:

        nuevo_usuario = Usuario(
            nombre=info.get("given_name")
            or info.get("name"),
            apellido=info.get("family_name")
            or "",
            usuario=email.split("@")[0],
            email=email,
            password=None,
            foto=info.get("picture"),
            rol="usuario",
            tipo_login="google",
            premium=False
        )

        db.session.add(
            nuevo_usuario
        )

        db.session.commit()

        usuario = nuevo_usuario


    guardar_usuario_en_session(
        usuario
    )


    return redirect(
        url_for(
            "main.inicio"
        )
    )