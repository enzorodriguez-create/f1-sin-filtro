import os
import uuid

from flask import url_for


# Extensiones que permito subir como imagen
EXTENSIONES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif"
}


# Si no uso S3, guardo las imágenes localmente
CARPETA_LOCAL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "uploads"
)


_s3 = None


def usa_s3():

    # Compruebo si tengo configurado un bucket de S3
    return bool(
        os.environ.get("S3_BUCKET")
    )


def _cliente():

    global _s3


    if _s3 is None:

        import boto3

        from botocore.config import Config


        region = (
            os.environ.get(
                "AWS_DEFAULT_REGION"
            )
            or
            "us-east-1"
        )


        _s3 = boto3.client(
            "s3",

            region_name=region,

            endpoint_url=
                f"https://s3.{region}.amazonaws.com",

            config=Config(
                signature_version="s3v4",

                s3={
                    "addressing_style":
                        "virtual"
                }
            )
        )


    return _s3


def extension_valida(
    nombre_archivo
):

    # Compruebo que la extensión sea una imagen permitida
    return (
        os.path.splitext(
            nombre_archivo
        )[1].lower()
        in
        EXTENSIONES
    )


def subir_imagen(
    archivo,
    carpeta="portadas"
):

    # Obtengo la extensión del archivo
    ext = os.path.splitext(
        archivo.filename
    )[1].lower()


    # Creo un nombre único para evitar archivos repetidos
    key = (
        f"{carpeta}/"
        f"{uuid.uuid4().hex}"
        f"{ext}"
    )


    if usa_s3():

        # Subo la imagen al bucket de Amazon S3
        _cliente().upload_fileobj(
            archivo,

            os.environ[
                "S3_BUCKET"
            ],

            key,

            ExtraArgs={
                "ContentType":
                    archivo.mimetype
            }
        )


    else:

        # Si no tengo S3 configurado,
        # guardo la imagen localmente
        destino = os.path.join(
            CARPETA_LOCAL,
            key
        )


        os.makedirs(
            os.path.dirname(
                destino
            ),
            exist_ok=True
        )


        archivo.save(
            destino
        )


    # Devuelvo solamente la key
    # para guardarla en la base de datos
    return key


def url_imagen(key):

    if not key:
        return None


    # Si la foto ya es una URL externa,
    # por ejemplo la foto de Google,
    # la utilizo directamente
    if (
        key.startswith("http://")
        or
        key.startswith("https://")
    ):

        return key


    # Si es una key de S3,
    # genero una URL temporal
    if usa_s3():

        return _cliente().generate_presigned_url(

            "get_object",

            Params={
                "Bucket":
                    os.environ["S3_BUCKET"],

                "Key":
                    key
            },

            ExpiresIn=3600
        )


    return url_for(
        "static",
        filename=f"uploads/{key}"
    )


def borrar_imagen(key):

    if not key:
        return


    # No intento borrar una foto externa,
    # por ejemplo la foto de Google
    if (
        key.startswith("http://")
        or
        key.startswith("https://")
    ):

        return


    if usa_s3():

        _cliente().delete_object(

            Bucket=
                os.environ["S3_BUCKET"],

            Key=
                key
        )


    else:

        ruta = os.path.join(
            CARPETA_LOCAL,
            key
        )


        if os.path.exists(ruta):

            os.remove(ruta)