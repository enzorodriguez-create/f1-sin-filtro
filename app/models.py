from app.extensions import db, bcrypt


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


class SolicitudEditor(db.Model):

    __tablename__ = "solicitudes_editor"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    motivo = db.Column(
        db.String(500),
        nullable=False
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="pendiente"
    )


# =========================
# PUBLICACIÓN - CATEGORÍA
# =========================

publicacion_categoria = db.Table(
    "publicacion_categoria",

    db.Column(
        "publicacion_id",
        db.Integer,
        db.ForeignKey("publicaciones.id"),
        primary_key=True
    ),

    db.Column(
        "categoria_id",
        db.Integer,
        db.ForeignKey("categorias.id"),
        primary_key=True
    )
)


class Publicacion(db.Model):

    __tablename__ = "publicaciones"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titulo = db.Column(
        db.String(200),
        nullable=False
    )

    resumen = db.Column(
        db.String(255),
        nullable=True
    )

    imagen_portada = db.Column(
        db.String(500),
        nullable=True
    )

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="borrador"
    )

    autor_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id"),
        nullable=True
    )

    categoria = db.relationship(
        "Categoria"
    )

    categorias = db.relationship(
        "Categoria",
        secondary=publicacion_categoria
    )


class BloquePublicacion(db.Model):

    __tablename__ = "bloques_publicacion"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    publicacion_id = db.Column(
        db.Integer,
        db.ForeignKey("publicaciones.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    contenido = db.Column(
        db.Text,
        nullable=True
    )

    orden = db.Column(
        db.Integer,
        nullable=False
    )


class ImagenCarrusel(db.Model):

    __tablename__ = "imagenes_carrusel"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    bloque_id = db.Column(
        db.Integer,
        db.ForeignKey("bloques_publicacion.id"),
        nullable=False
    )

    imagen = db.Column(
        db.String(500),
        nullable=False
    )

    orden = db.Column(
        db.Integer,
        nullable=False
    )


class Categoria(db.Model):

    __tablename__ = "categorias"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(255),
        nullable=True
    )

    imagen = db.Column(
        db.String(500),
        nullable=True
    )