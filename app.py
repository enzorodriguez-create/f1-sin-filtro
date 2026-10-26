import os
import requests

from flask import Flask, render_template, redirect, url_for, session, request
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Usuario, bcrypt

load_dotenv()

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bd1xd")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///f1_sin_filtro.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
bcrypt.init_app(app)

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_password(password):

            session["usuario"] = {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "rol": usuario.rol,
                "premium": usuario.premium
            }

            return redirect(url_for("inicio"))

        return "Email o contraseña incorrectos."

    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        usuario = request.form.get("usuario")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return "Las contraseñas no coinciden."

        email_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if email_existente:
            return "El email ya está registrado."

        usuario_existente = Usuario.query.filter_by(
            usuario=usuario
        ).first()

        if usuario_existente:
            return "El nombre de usuario ya está registrado."

        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            usuario=usuario,
            email=email,
            rol="usuario",
            tipo_login="normal",
            premium=False
        )

        nuevo_usuario.guardar_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("registro.html")

@app.route("/logout")
def logout():

    session.pop("usuario", None)

    return redirect(url_for("inicio"))

@app.route("/noticias")
def noticias():
    return render_template("noticias.html")

@app.route("/post")
def post():
    return render_template("post.html")

@app.route("/perfil")
def perfil():
    usuario = session.get("usuario")


    return render_template("perfil/perfil.html", usuario=usuario)

@app.route("/calendario")
def calendario():

    url = "https://api.openf1.org/v1/meetings?year=2026"

    respuesta = requests.get(url)

    carreras = respuesta.json()

    tipos_circuito = {
        "Permanent": "Permanente",
        "Street": "Callejero",
        "Temporary": "Temporal",
        "Temporary - Street": "Temporal - Callejero"
    }

    for carrera in carreras:

        tipo_original = carrera.get("circuit_type", "")

        carrera["tipo_es"] = tipos_circuito.get(
            tipo_original,
            tipo_original
        )

    return render_template(
        "calendario.html",
        carreras=carreras
    )
@app.route("/premium")
def premium():
    return render_template("premium.html")

@app.route("/editor")
def editor():

    usuario = session.get("usuario")

    return render_template(
        "editor/dashboard.html",
        usuario=usuario,
        seccion_activa="dashboard"
    )

@app.route("/perfil/editar")
def editar_perfil():
    return render_template("perfil/editar.html")

@app.route("/perfil/comentarios")
def mis_comentarios():
    return render_template("perfil/comentarios.html")

@app.route("/perfil/guardados")
def guardados():
    return render_template("perfil/guardados.html")

@app.route("/perfil/etiquetas")
def etiquetas_guardadas():
    return render_template("perfil/etiquetas.html")

@app.route("/categorias")
def categorias():
    return render_template("categorias.html")

@app.route("/premium/suscripcion")
def suscripcion():
    return render_template("suscripcion.html")

@app.route("/auth/google")
def login_google():
    return google.authorize_redirect(
        url_for("callback_google", _external=True)
    )


@app.route("/auth/google/callback")
def callback_google():

    token = google.authorize_access_token()

    info = token["userinfo"]

    email = info.get("email")

    usuario = Usuario.query.filter_by(
        email=email
    ).first()


    if usuario is None:

        nuevo_usuario = Usuario(
            nombre=info.get("given_name") or info.get("name"),
            apellido=info.get("family_name") or "",
            usuario=email.split("@")[0],
            email=email,
            password=None,
            foto=info.get("picture"),
            rol="usuario",
            tipo_login="google",
            premium=False
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        usuario = nuevo_usuario


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

    return redirect(url_for("inicio"))

@app.route("/editor/crear-publicacion")
def editor_crear_publicacion():

    usuario = session.get("usuario")

    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario,
        seccion_activa="crear"
    )

@app.route("/editor/publicaciones")
def editor_publicaciones():

    usuario = session.get("usuario")

    return render_template(
        "editor/mis_publicaciones.html",
        usuario=usuario,
        seccion_activa="publicaciones"
    )

@app.route("/editor/publicaciones/<int:id_publicacion>/editar")
def editor_editar_publicacion(id_publicacion):

    usuario = session.get("usuario")

    return render_template(
        "editor/editar_publicacion.html",
        usuario=usuario,
        id_publicacion=id_publicacion,
        seccion_activa="publicaciones"
    )

@app.route("/editor/comentarios")
def editor_comentarios():

    usuario = session.get("usuario")

    return render_template(
        "editor/comentarios.html",
        usuario=usuario,
        seccion_activa="comentarios"
    )

@app.route("/editor/categorias")
def editor_categorias():

    usuario = session.get("usuario")

    return render_template(
        "editor/categorias.html",
        usuario=usuario,
        seccion_activa="categorias"
    )

@app.route("/editor/etiquetas")
def editor_etiquetas():

    usuario = session.get("usuario")

    return render_template(
        "editor/etiquetas.html",
        usuario=usuario,
        seccion_activa="etiquetas"
    )

@app.route("/editor/perfil")
def editor_perfil():

    usuario = session.get("usuario")

    return render_template(
        "editor/perfil.html",
        usuario=usuario,
        seccion_activa="perfil_editor"
    )

@app.route("/admin")
def admin():

    usuario = session.get("usuario")

    return render_template(
        "admin/dashboard.html",
        usuario=usuario,
        seccion_activa="dashboard"
    )

@app.route("/admin/usuarios")
def admin_usuarios():

    usuario = session.get("usuario")

    return render_template(
        "admin/usuarios.html",
        usuario=usuario,
        seccion_activa="usuarios"
    )

@app.route("/admin/solicitudes")
def admin_solicitudes():

    usuario = session.get("usuario")

    return render_template(
        "admin/solicitudes.html",
        usuario=usuario,
        seccion_activa="solicitudes"
    )

@app.route("/admin/publicaciones")
def admin_publicaciones():

    usuario = session.get("usuario")

    return render_template(
        "admin/publicaciones.html",
        usuario=usuario,
        seccion_activa="publicaciones"
    )

@app.route("/admin/categorias")
def admin_categorias():

    usuario = session.get("usuario")

    return render_template(
        "admin/categorias.html",
        usuario=usuario,
        seccion_activa="categorias"
    )

@app.route("/admin/etiquetas")
def admin_etiquetas():

    usuario = session.get("usuario")

    return render_template(
        "admin/etiquetas.html",
        usuario=usuario,
        seccion_activa="etiquetas"
    )

@app.route("/admin/comentarios")
def admin_comentarios():

    usuario = session.get("usuario")

    return render_template(
        "admin/comentarios.html",
        usuario=usuario,
        seccion_activa="comentarios"
    )

@app.route("/admin/analiticas")
def admin_analiticas():

    usuario = session.get("usuario")

    return render_template(
        "admin/analiticas.html",
        usuario=usuario,
        seccion_activa="analiticas"
    )

@app.route("/admin/perfil")
def admin_perfil():

    usuario = session.get("usuario")

    return render_template(
        "admin/perfil.html",
        usuario=usuario,
        seccion_activa="perfil"
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5001)