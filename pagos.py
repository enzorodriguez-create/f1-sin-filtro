"""
Cobros con Mercado Pago usando Checkout Pro.

Flujo:

1. crear_preferencia():
   Le indico a Mercado Pago qué se está pagando
   y a qué URL tiene que volver.

2. Redirijo al usuario a la página de pago
   de Mercado Pago.

3. Cuando termina el pago,
   Mercado Pago vuelve a /pago/resultado.

4. obtener_pago():
   Consulto el pago directamente a la API
   para comprobar su estado real.

No confío solamente en el estado enviado
por la URL porque podría modificarse manualmente.
"""

import os


_sdk = None


def usa_mercadopago():

    return bool(
        os.environ.get(
            "MP_ACCESS_TOKEN"
        )
    )


def _cliente():

    global _sdk


    if _sdk is None:

        import mercadopago


        _sdk = mercadopago.SDK(
            os.environ[
                "MP_ACCESS_TOKEN"
            ]
        )


    return _sdk


def crear_preferencia(
    pago,
    url_retorno,
    url_webhook=None
):

    """
    Crea la preferencia de Mercado Pago
    para activar F1 Sin Filtro Premium.

    Devuelve el link de pago.
    """

    datos = {

        "items": [

            {
                "id": "premium",
                "title": "F1 Sin Filtro Premium",
                "quantity": 1,
                "unit_price": float(
                    pago.precio
                ),
                "currency_id": os.environ.get(
                    "MP_MONEDA",
                    "ARS"
                )
            }

        ],

        # Guardo el ID del pago de mi base
        # para identificarlo cuando Mercado Pago responda.
        "external_reference": str(
            pago.id
        ),

        "back_urls": {

            "success":
                url_retorno,

            "failure":
                url_retorno,

            "pending":
                url_retorno

        }

    }


    # Mercado Pago solamente permite
    # auto_return con una URL HTTPS pública.
    if url_retorno.startswith(
        "https://"
    ):

        datos[
            "auto_return"
        ] = "approved"


    # El webhook también necesita HTTPS.
    if (
        url_webhook
        and
        url_webhook.startswith(
            "https://"
        )
    ):

        datos[
            "notification_url"
        ] = url_webhook


    resultado = (
        _cliente()
        .preference()
        .create(
            datos
        )
    )


    if resultado[
        "status"
    ] not in (
        200,
        201
    ):

        raise RuntimeError(
            "Mercado Pago respondió "
            f"{resultado['status']}: "
            f"{resultado['response']}"
        )


    return resultado[
        "response"
    ][
        "init_point"
    ]


def obtener_pago(
    payment_id
):

    """
    Consulta el pago real en Mercado Pago.

    Devuelve los datos del pago
    o None si no pudo obtenerse.
    """

    resultado = (
        _cliente()
        .payment()
        .get(
            payment_id
        )
    )


    if resultado[
        "status"
    ] != 200:

        return None


    return resultado[
        "response"
    ]