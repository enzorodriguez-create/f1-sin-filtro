from flask import Flask

from config import Config
from app.extensions import db, bcrypt, oauth


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    bcrypt.init_app(app)

    oauth.init_app(app)


    # Blueprint principal
    from app.main.routes import bp as main_bp

    app.register_blueprint(
        main_bp
    )


    # Blueprint de autenticación
    from app.auth.routes import bp as auth_bp

    app.register_blueprint(
        auth_bp
    )


    return app