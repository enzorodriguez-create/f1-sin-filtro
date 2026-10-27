import os
import requests

from flask import Flask, render_template, redirect, url_for, session, request, flash
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, Usuario,  SolicitudEditor, Publicacion, BloquePublicacion, ImagenCarrusel, bcrypt
from almacenamiento import (
    extension_valida,
    subir_imagen,
    url_imagen,
    borrar_imagen,
    usa_s3
)

load_dotenv()

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bd1xd")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///f1_sin_filtro.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Limito las imágenes a un máximo de 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

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

def guardar_usuario_en_session(usuario):

    # Guardo en la sesión los datos principales del usuario
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


def obtener_usuario_actual():

    # Obtengo los datos guardados en la sesión
    datos_usuario = session.get("usuario")

    if not datos_usuario:
        return None

    # Busco al usuario real en la base de datos
    return db.session.get(
        Usuario,
        datos_usuario["id"]
    )


def actualizar_perfil_usuario(usuario):

    # Actualizo los datos del formulario
    usuario.nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    usuario.apellido = request.form.get(
        "apellido",
        ""
    ).strip()

    usuario.usuario = request.form.get(
        "usuario",
        ""
    ).strip()

    usuario.email = request.form.get(
        "email",
        ""
    ).strip()


    # Obtengo la foto enviada
    foto = request.files.get("foto")


    if foto and foto.filename:

        # Compruebo que sea una extensión permitida
        if not extension_valida(foto.filename):

            return (
                False,
                "La imagen debe ser JPG, JPEG, PNG, WEBP o GIF."
            )


        # Guardo la foto anterior
        foto_anterior = usuario.foto


        # Subo la nueva foto a S3
        usuario.foto = subir_imagen(
            foto,
            carpeta="avatares"
        )


        # Guardo primero la nueva key en la base
        db.session.commit()


        # Después elimino la imagen anterior
        borrar_imagen(
            foto_anterior
        )


    else:

        # Si no cambia la foto,
        # guardo solamente los otros datos
        db.session.commit()


    # Actualizo también la sesión
    guardar_usuario_en_session(
        usuario
    )


    return (
        True,
        "Perfil actualizado correctamente."
    )

@app.before_request
def proteger_rutas_por_rol():

    usuario = obtener_usuario_actual()

    ruta = request.path


    # Protejo todas las rutas de administrador
    if ruta.startswith("/admin"):

        if not usuario:

            return redirect(
                url_for("login")
            )

        if usuario.rol != "admin":

            return redirigir_segun_rol(
                usuario
            )


    # Protejo todas las rutas de editor
    if ruta.startswith("/editor"):

        if not usuario:

            return redirect(
                url_for("login")
            )

        if usuario.rol != "editor":

            return redirigir_segun_rol(
                usuario
            )


    # Protejo todas las rutas privadas del usuario
    if ruta.startswith("/perfil"):

        if not usuario:

            return redirect(
                url_for("login")
            )

        if usuario.rol != "usuario":

            return redirigir_segun_rol(
                usuario
            )
        
def redirigir_segun_rol(usuario):

    if usuario.rol == "admin":

        return redirect(
            url_for("admin")
        )

    if usuario.rol == "editor":

        return redirect(
            url_for("editor")
        )

    return redirect(
        url_for("perfil")
    )



@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and usuario.verificar_password(password):

            guardar_usuario_en_session(
                usuario
            )

            if usuario.rol == "admin":

                return redirect(
                    url_for("admin")
                )

            elif usuario.rol == "editor":

                return redirect(
                    url_for("editor")
                )

            else:

                return redirect(
                    url_for("inicio")
                )

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

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for("login")
        )


    return render_template(
        "perfil/perfil.html",
        usuario=usuario
    )

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

@app.route(
    "/perfil/editar",
    methods=["GET", "POST"]
)
def editar_perfil():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        correcto, mensaje = actualizar_perfil_usuario(
            usuario
        )


        if not correcto:

            return mensaje


        return redirect(
            url_for("perfil")
        )


    return render_template(
        "perfil/editar.html",
        usuario=usuario
    )

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


    guardar_usuario_en_session(
        usuario
    )


    return redirect(
        url_for("inicio")
    )

@app.route(
    "/editor/crear-publicacion",
    methods=["GET", "POST"]
)
def editor_crear_publicacion():

    usuario = obtener_usuario_actual()


    if request.method == "POST":

        # Obtengo el título
        titulo = request.form.get(
            "titulo",
            ""
        ).strip()


        if not titulo:

            return "Tenés que ingresar un título."


        # Obtengo la portada
        portada = request.files.get(
            "imagen_portada"
        )


        imagen_portada = None


        # Compruebo si se seleccionó una portada
        if portada and portada.filename:

            if not extension_valida(
                portada.filename
            ):

                return "Formato de portada no válido."


            imagen_portada = subir_imagen(
                portada,
                carpeta="publicaciones"
            )


        # Obtengo qué botón se utilizó
        accion = request.form.get(
            "accion",
            "borrador"
        )


        if accion == "publicar":

            estado = "publicada"

        else:

            estado = "borrador"


        # Creo la publicación
        nueva_publicacion = Publicacion(
            titulo=titulo,
            imagen_portada=imagen_portada,
            estado=estado,
            autor_id=usuario.id
        )


        db.session.add(
            nueva_publicacion
        )


        # Guardo primero para obtener el id
        db.session.commit()


        # Obtengo el orden enviado desde JavaScript
        bloques_orden = request.form.get(
            "bloques_orden",
            ""
        )


        tipos_bloques = [
            tipo
            for tipo in bloques_orden.split(",")
            if tipo
        ]


        # Recorro cada bloque respetando el orden
        for indice, tipo in enumerate(
            tipos_bloques,
            start=1
        ):


            # =========================
            # TEXTO
            # =========================

            if tipo == "texto":

                contenido = request.form.get(
                    f"bloque_{indice}_texto",
                    ""
                ).strip()


                if contenido:

                    nuevo_bloque = BloquePublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo="texto",
                        contenido=contenido,
                        orden=indice
                    )


                    db.session.add(
                        nuevo_bloque
                    )


            # =========================
            # IMAGEN
            # =========================

            elif tipo == "imagen":

                imagen = request.files.get(
                    f"bloque_{indice}_imagen"
                )


                if imagen and imagen.filename:

                    if not extension_valida(
                        imagen.filename
                    ):

                        continue


                    imagen_key = subir_imagen(
                        imagen,
                        carpeta="publicaciones/contenido"
                    )


                    nuevo_bloque = BloquePublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo="imagen",
                        contenido=imagen_key,
                        orden=indice
                    )


                    db.session.add(
                        nuevo_bloque
                    )


            # =========================
            # CARRUSEL
            # =========================

            elif tipo == "carrusel":

                imagenes = request.files.getlist(
                    f"bloque_{indice}_carrusel"
                )


                imagenes_validas = [
                    imagen
                    for imagen in imagenes
                    if imagen and imagen.filename
                ]


                if imagenes_validas:

                    bloque_carrusel = BloquePublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo="carrusel",
                        contenido=None,
                        orden=indice
                    )


                    db.session.add(
                        bloque_carrusel
                    )


                    # Obtengo el id del bloque sin cerrar la transacción
                    db.session.flush()


                    orden_imagen = 1


                    for imagen in imagenes_validas:

                        if not extension_valida(
                            imagen.filename
                        ):

                            continue


                        imagen_key = subir_imagen(
                            imagen,
                            carpeta="publicaciones/carruseles"
                        )


                        nueva_imagen = ImagenCarrusel(
                            bloque_id=bloque_carrusel.id,
                            imagen=imagen_key,
                            orden=orden_imagen
                        )


                        db.session.add(
                            nueva_imagen
                        )


                        orden_imagen += 1


        # Guardo todos los bloques e imágenes
        db.session.commit()


        return redirect(
            url_for("editor_publicaciones")
        )


    return render_template(
        "editor/crear_publicacion.html",
        usuario=usuario,
        seccion_activa="crear_publicacion"
    )

@app.route(
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

@app.route("/editor/publicaciones")
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

@app.route(
    "/editor/perfil",
    methods=["GET", "POST"]
)
def editor_perfil():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        correcto, mensaje = actualizar_perfil_usuario(
            usuario
        )


        if not correcto:

            return mensaje


        return redirect(
            url_for("editor_perfil")
        )


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

    admin = obtener_usuario_actual()


    if not admin:

        return redirect(
            url_for("login")
        )


    if admin.rol != "admin":

        return redirect(
            url_for("inicio")
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

@app.route(
    "/admin/solicitudes/<int:id_solicitud>/aprobar",
    methods=["POST"]
)
def aprobar_solicitud_editor(
    id_solicitud
):

    admin = obtener_usuario_actual()


    if not admin or admin.rol != "admin":

        return redirect(
            url_for("inicio")
        )


    solicitud = db.session.get(
        SolicitudEditor,
        id_solicitud
    )


    if not solicitud:

        return redirect(
            url_for(
                "admin_solicitudes"
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
            "admin_solicitudes"
        )
    )

@app.route(
    "/admin/solicitudes/<int:id_solicitud>/rechazar",
    methods=["POST"]
)
def rechazar_solicitud_editor(
    id_solicitud
):

    admin = obtener_usuario_actual()


    if not admin or admin.rol != "admin":

        return redirect(
            url_for("inicio")
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
            "admin_solicitudes"
        )
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

@app.route(
    "/admin/perfil",
    methods=["GET", "POST"]
)
def admin_perfil():

    usuario = obtener_usuario_actual()

    if not usuario:

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        correcto, mensaje = actualizar_perfil_usuario(
            usuario
        )


        if not correcto:

            return mensaje


        return redirect(
            url_for("admin_perfil")
        )


    return render_template(
        "admin/perfil.html",
        usuario=usuario,
        seccion_activa="perfil"
    )

@app.context_processor
def funciones_para_plantillas():

    return {
        "url_imagen":
            url_imagen,

        "usa_s3":
            usa_s3()
    }

@app.route(
    "/perfil/solicitar-editor",
    methods=["GET", "POST"]
)
def solicitar_editor():

    # Obtengo al usuario que inició sesión
    usuario = obtener_usuario_actual()


    if not usuario:

        return redirect(
            url_for("login")
        )


    # Solo un usuario normal puede solicitar ser editor
    if usuario.rol != "usuario":

        return redirect(
            url_for("perfil")
        )


    # Compruebo si ya tiene una solicitud pendiente
    solicitud_pendiente = SolicitudEditor.query.filter_by(
        usuario_id=usuario.id,
        estado="pendiente"
    ).first()


    if request.method == "POST":

        # Evito que mande varias solicitudes pendientes
        if solicitud_pendiente:

            return redirect(
                url_for("solicitar_editor")
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
            url_for("solicitar_editor")
        )


    return render_template(
        "perfil/solicitar_editor.html",
        usuario=usuario,
        solicitud_pendiente=solicitud_pendiente
    )

if __name__ == "__main__":

    with app.app_context():

        db.create_all()


        # Compruebo si ya existe una cuenta de administrador
        admin_existente = Usuario.query.filter_by(
            rol="admin"
        ).first()


        # Si no existe, creo una cuenta de administrador
        if not admin_existente:

            admin = Usuario(
                nombre="Administrador",
                apellido="F1 Sin Filtro",
                usuario="admin",
                email="admin@f1sinfiltro.com",
                rol="admin",
                tipo_login="normal",
                premium=False
            )


            admin.guardar_password(
                "Admin123"
            )


            db.session.add(
                admin
            )

            db.session.commit()


            print(
                "Cuenta de administrador creada."
            )


    app.run(
        debug=True,
        port=5001
    )