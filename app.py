from flask import Flask, render_template
import requests


app = Flask(__name__)


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
    return render_template("perfil/perfil.html")

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
    return render_template("editor.html")

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)