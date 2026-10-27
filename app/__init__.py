from flask import Flask

from config import Config
from app.extensions import db, bcrypt, oauth


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    bcrypt.init_app(app)

    oauth.init_app(app)


    # Importo el Blueprint principal
    from app.main.routes import bp as main_bp

    # Registro el Blueprint
    app.register_blueprint(
        main_bp
    )


    return app