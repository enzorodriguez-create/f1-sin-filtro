import os
import requests

from flask import Flask, render_template, redirect, url_for, session
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bd1xd")

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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/registro")
def registro():
    return render_template("registro.html")

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
    return render_template("editor/dashboard.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

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

    session["usuario"] = {
        "nombre": info.get("name"),
        "email": info.get("email"),
        "foto": info.get("picture"),
        "rol": "usuario",
        "tipo_login": "google"
    }

    return redirect(url_for("perfil"))

@app.route("/editor/crear-publicacion")
def editor_crear_publicacion():
    usuario = session.get("usuario")
    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)