import pickle

import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    train_test_split
)

from sklearn.pipeline import (
    FeatureUnion,
    Pipeline
)


# =========================
# PARÁMETROS
# =========================

PORCENTAJE_PRUEBA = 0.2

SEMILLA = 42

USAR_PALABRAS = True

NGRAMAS_PALABRAS = (
    1,
    2
)

USAR_CARACTERES = True

NGRAMAS_CARACTERES = (
    2,
    5
)

QUITAR_ACENTOS = True

SUBLINEAR_TF = True

VALORES_C = [
    0.1,
    0.5,
    1,
    5,
    10,
    50
]

BALANCEAR_CLASES = True

PLIEGUES_VALIDACION = 5

UMBRAL_CONFIANZA = 0.55


# =========================
# CASOS BORDE
# =========================

CASOS_BORDE = [

    (
        "Ferrari hizo una estrategia horrible",
        "No ofensivo"
    ),

    (
        "Leclerc manejó muy mal hoy",
        "No ofensivo"
    ),

    (
        "No estoy de acuerdo con esa opinión",
        "No ofensivo"
    ),

    (
        "La carrera fue un desastre",
        "No ofensivo"
    ),

    (
        "Ese piloto tuvo una carrera pésima",
        "No ofensivo"
    ),

    (
        "No comparto para nada lo que decís",
        "No ofensivo"
    ),

    (
        "Ferrari volvió a hacer todo mal",
        "No ofensivo"
    ),

    (
        "La estrategia fue malísima",
        "No ofensivo"
    ),

    (
        "No me gustó nada lo que hizo Verstappen",
        "No ofensivo"
    ),

    (
        "Ese comentario no tiene mucho sentido",
        "No ofensivo"
    ),

    (
        "Ferrari son todos unos pelotudos",
        "Ofensivo"
    ),

    (
        "Sos un imbécil si pensás eso",
        "Ofensivo"
    ),

    (
        "Callate pelotudo no entendés nada",
        "Ofensivo"
    ),

    (
        "No entendés una mierda de Fórmula 1",
        "Ofensivo"
    ),

    (
        "Qué boludo sos",
        "Ofensivo"
    ),

    (
        "Ese piloto es un tarado",
        "Ofensivo"
    ),

    (
        "Dejá de decir pelotudeces",
        "Ofensivo"
    ),

    (
        "Sos un salame",
        "Ofensivo"
    ),

    (
        "ANDATE A LA MIERDA",
        "Ofensivo"
    ),

    (
        "sos un pelotud0",
        "Ofensivo"
    ),

    (
        "q boludo sos",
        "Ofensivo"
    ),

    (
        "sos un idi0ta",
        "Ofensivo"
    ),

    (
        "Qué maravilla Ferrari, otra vez arruinando una carrera",
        "No ofensivo"
    ),

    (
        "Genial estrategia, perdieron veinte segundos",
        "No ofensivo"
    ),

    (
        "Sí claro, sos un genio pelotudo",
        "Ofensivo"
    ),

    (
        "Muy buena opinión campeón, no entendés una mierda",
        "Ofensivo"
    )

]

# =========================
# CARGO DATOS
# =========================

df = pd.read_csv(
    "comentarios_moderacion.csv"
)

df = df.dropna()

df = df.drop_duplicates(
    subset="text"
)


print(
    f"Comentarios cargados: {len(df)} "
    f"({df['label'].value_counts().to_dict()})"
)


# =========================
# ENTRENAMIENTO Y PRUEBA
# =========================

X_train, X_test, y_train, y_test = (
    train_test_split(
        df["text"],
        df["label"],
        test_size=PORCENTAJE_PRUEBA,
        stratify=df["label"],
        random_state=SEMILLA
    )
)


# =========================
# TF-IDF
# =========================

extractores = []


if USAR_PALABRAS:

    extractores.append(
        (
            "palabras",

            TfidfVectorizer(
                lowercase=True,
                strip_accents=(
                    "unicode"
                    if QUITAR_ACENTOS
                    else None
                ),
                ngram_range=NGRAMAS_PALABRAS,
                sublinear_tf=SUBLINEAR_TF
            )
        )
    )


if USAR_CARACTERES:

    extractores.append(
        (
            "caracteres",

            TfidfVectorizer(
                lowercase=True,
                strip_accents=(
                    "unicode"
                    if QUITAR_ACENTOS
                    else None
                ),
                analyzer="char_wb",
                ngram_range=NGRAMAS_CARACTERES,
                sublinear_tf=SUBLINEAR_TF
            )
        )
    )


# =========================
# MODELO
# =========================

pipeline = Pipeline([

    (
        "features",
        FeatureUnion(
            extractores
        )
    ),

    (
        "clf",
        LogisticRegression(
            max_iter=1000,
            class_weight=(
                "balanced"
                if BALANCEAR_CLASES
                else None
            )
        )
    )

])


# =========================
# BUSCO MEJOR C
# =========================

cv = StratifiedKFold(
    n_splits=PLIEGUES_VALIDACION,
    shuffle=True,
    random_state=SEMILLA
)


search = GridSearchCV(
    pipeline,
    {
        "clf__C": VALORES_C
    },
    cv=cv,
    scoring="f1_macro",
    n_jobs=-1
)


search.fit(
    X_train,
    y_train
)


print(
    "\nMejor C:",
    search.best_params_["clf__C"]
)

print(
    "F1 en validación cruzada:",
    round(
        search.best_score_,
        3
    )
)


# =========================
# EVALUACIÓN
# =========================

y_pred = search.predict(
    X_test
)


exactitud = accuracy_score(
    y_test,
    y_pred
)


print(
    "\nExactitud en prueba:",
    round(
        exactitud,
        3
    )
)


print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "No ofensivo",
            "Ofensivo"
        ]
    )
)


print(
    "Matriz de confusión:"
)


matriz = confusion_matrix(
    y_test,
    y_pred
)


print(
    matriz
)


# =========================
# GUARDO MODELO
# =========================

model = search.best_estimator_


model.fit(
    df["text"],
    df["label"]
)


with open(
    "modelo_moderacion.pkl",
    "wb"
) as file:

    pickle.dump(
        model,
        file
    )


# =========================
# CLASIFICAR
# =========================

def clasificar(texto):

    prob_ofensivo = model.predict_proba(
        [texto]
    )[0][1]


    confianza = max(
        prob_ofensivo,
        1 - prob_ofensivo
    )


    if confianza < UMBRAL_CONFIANZA:

        etiqueta = "No concluyente"

    elif prob_ofensivo >= 0.5:

        etiqueta = "Ofensivo"

    else:

        etiqueta = "No ofensivo"


    return (
        etiqueta,
        prob_ofensivo,
        confianza
    )


# =========================
# CASOS BORDE
# =========================

print(
    "\nCASOS BORDE"
)

print(
    "-" * 70
)


for texto, esperado in CASOS_BORDE:

    obtenido, prob, confianza = (
        clasificar(
            texto
        )
    )


    print(
        texto
    )

    print(
        "Esperado:",
        esperado
    )

    print(
        "Obtenido:",
        obtenido
    )

    print(
        "Probabilidad ofensivo:",
        f"{prob:.1%}"
    )

    print(
        "Confianza:",
        f"{confianza:.1%}"
    )

    print(
        "-" * 70
    )


print(
    "\nModelo guardado en modelo_moderacion.pkl"
)