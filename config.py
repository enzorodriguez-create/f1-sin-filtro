import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-cambiar"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///f1_sin_filtro.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    GOOGLE_CLIENT_ID = os.environ.get(
        "GOOGLE_CLIENT_ID"
    )

    GOOGLE_CLIENT_SECRET = os.environ.get(
        "GOOGLE_CLIENT_SECRET"
    )