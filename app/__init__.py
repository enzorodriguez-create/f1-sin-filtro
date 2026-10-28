from flask import Flask

from config import Config
from app.extensions import db, bcrypt, oauth
from almacenamiento import url_imagen, usa_s3


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)


    # =========================
    # EXTENSIONES
    # =========================

    db.init_app(app)

    bcrypt.init_app(app)

    oauth.init_app(app)


    # =========================
    # BLUEPRINT PRINCIPAL
    # =========================

    from app.main.routes import bp as main_bp

    app.register_blueprint(
        main_bp
    )


    # =========================
    # BLUEPRINT AUTENTICACIÓN
    # =========================

    from app.auth.routes import bp as auth_bp

    app.register_blueprint(
        auth_bp
    )


    # =========================
    # BLUEPRINT PERFIL
    # =========================

    from app.perfil.routes import bp as perfil_bp

    app.register_blueprint(
        perfil_bp
    )


    # =========================
    # BLUEPRINT EDITOR
    # =========================

    from app.editor.routes import bp as editor_bp

    app.register_blueprint(
        editor_bp
    )


    # =========================
    # BLUEPRINT ADMINISTRADOR
    # =========================

    from app.admin.routes import bp as admin_bp

    app.register_blueprint(
        admin_bp
    )


    # =========================
    # FUNCIONES PARA TEMPLATES
    # =========================

    @app.context_processor
    def funciones_para_plantillas():

        return {
            "url_imagen": url_imagen,
            "usa_s3": usa_s3()
        }


    return app