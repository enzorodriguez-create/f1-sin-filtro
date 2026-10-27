from flask import Blueprint, render_template


bp = Blueprint(
    "main",
    __name__
)


@bp.route("/")
def inicio():

    return render_template(
        "index.html"
    )


@bp.route("/noticias")
def noticias():

    return render_template(
        "noticias.html"
    )


@bp.route("/post")
def post():

    return render_template(
        "post.html"
    )


@bp.route("/calendario")
def calendario():

    return render_template(
        "calendario.html"
    )


@bp.route("/premium")
def premium():

    return render_template(
        "premium.html"
    )


@bp.route("/categorias")
def categorias():

    return render_template(
        "categorias.html"
    )