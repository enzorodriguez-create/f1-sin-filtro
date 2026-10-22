from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    apellido = db.Column(
    db.String(100),
    nullable=False
    )     

    usuario = db.Column(
    db.String(50),
    unique=True,
    nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=True
    )

    foto = db.Column(
        db.String(500),
        nullable=True
    )

    rol = db.Column(
        db.String(20),
        nullable=False,
        default="usuario"
    )

    tipo_login = db.Column(
        db.String(20),
        nullable=False,
        default="normal"
    )

    premium = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    def guardar_password(self, password):
        self.password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

    def verificar_password(self, password):
        return bcrypt.check_password_hash(
            self.password,
            password
        )