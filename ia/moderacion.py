import os
import joblib


RUTA_MODELO = os.path.join(
    os.path.dirname(__file__),
    "modelo_moderacion.pkl"
)


modelo = joblib.load(
    RUTA_MODELO
)


UMBRAL_CONFIANZA = 0.55


def clasificar_comentario(texto):

    probabilidades = modelo.predict_proba(
        [texto]
    )[0]


    probabilidad_no_ofensivo = probabilidades[0]
    probabilidad_ofensivo = probabilidades[1]


    if probabilidad_ofensivo >= UMBRAL_CONFIANZA:

        moderacion = "Ofensivo"
        confianza = probabilidad_ofensivo

    elif probabilidad_no_ofensivo >= UMBRAL_CONFIANZA:

        moderacion = "No ofensivo"
        confianza = probabilidad_no_ofensivo

    else:

        moderacion = "No concluyente"

        confianza = max(
            probabilidad_no_ofensivo,
            probabilidad_ofensivo
        )


    return moderacion, confianza