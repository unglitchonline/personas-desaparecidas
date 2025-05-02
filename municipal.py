"""
Este script analiza las cifras de personas desaparecidas
y no localizadas en México desde una perspectiva municipal.
"""

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Todas las gráficas de este script
# van a compartir el mismo esquema de colores.
PLOT_COLOR = "#171010"
PAPER_COLOR = "#2B2B2B"

# La fecha en la que los datos fueron recopilados.
FECHA_FUENTE = "01/05/2025"


def crear_mapa(año):
    """
    Crea un mapa choropleth con la tasa de incidencia bruta para cada municipio.

    Parameters
    ----------
    año: int
        El año que se desea graficar.

    """

    # Cargamos el dataset de población por municipio.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str}, index_col=0)

    # Seleccionamos el año de nuestro interés.
    pop = pop[str(año)]

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv", dtype={"CVE_ENT": str, "CVE_MUN": str})

    # Seleccionamos un registro por víctima.
    df = df.groupby("ID_VICTIMA").last()

    # Limpiamos valores confidenciales.
    df = df.replace("CONFIDENCIAL", np.nan)

    # Convertimos las fechas a DateTime.
    df["FECHA_DESAPARICION"] = pd.to_datetime(df["FECHA_DESAPARICION"], errors="coerce")
    df["FECHA_REGISTRO"] = pd.to_datetime(df["FECHA_REGISTRO"], errors="coerce")

    # Vamos a preferir la fecha de desaparición.
    # Pero cuando no esté disponible usaremos la fecha de registro.
    df["FECHA_DESAPARICION"] = df["FECHA_DESAPARICION"].fillna(df["FECHA_REGISTRO"])

    # Seleccionamos solo registros del año de nuestro interés.
    df = df[df["FECHA_DESAPARICION"].dt.year == año]

    # Unimos los identificadores de entidad y municipio.
    # para crear el identificador único.
    df["CVE"] = df["CVE_ENT"] + df["CVE_MUN"]

    # Contamos los registros por municipio.
    df = df["CVE"].value_counts().to_frame("total")

    # Agregamos la población a cada municipio con registros.
    df["pop"] = pop

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["total"] / df["pop"] * 100000

    # Calculamos los totaales nacionales.
    total_nacional = df["total"].sum()
    poblacion_nacional = pop.sum()

    # Preparamos los valores para nuestro subtítulo.
    subtitulo = f"Tasa nacional: <b>{total_nacional / poblacion_nacional * 100000:,.1f}</b> (con <b>{total_nacional:,.0f}</b> víctimas)"

    # Quitamos los valores NaN para que no interfieran con los siguientes pasos.
    df = df.dropna(axis=0)

    # Calculamos algunas estadísticas descriptivas.
    estadisticas = [
        "Estadísticas descriptivas",
        "<b>(tasa bruta)</b>",
        f"Media: <b>{df['tasa'].mean():,.1f}</b>",
        f"Mediana: <b>{df['tasa'].median():,.1f}</b>",
        f"DE: <b>{df['tasa'].std():,.1f}</b>",
        f"25%: <b>{df['tasa'].quantile(0.25):,.1f}</b>",
        f"75%: <b>{df['tasa'].quantile(0.75):,.1f}</b>",
        f"95%: <b>{df['tasa'].quantile(0.95):,.1f}</b>",
        f"Máximo: <b>{df['tasa'].max():,.1f}</b>",
    ]

    estadisticas = "<br>".join(estadisticas)

    # Determinamos los valores mínimos y máximos para nuestra escala.
    # Para el valor máximo usamos el 95 percentil para mitigar los
    # efectos de valores atípicos.
    valor_min = df["tasa"].min()
    valor_max = df["tasa"].quantile(0.95)

    # Vamos a crear nuestra escala con 13 intervalos.
    marcas = np.linspace(valor_min, valor_max, 13)
    etiquetas = list()

    for item in marcas:
        if item >= 10:
            etiquetas.append(f"{item:,.0f}")
        else:
            etiquetas.append(f"{item:,.1f}")

    # A la última etiqueta le agregamos el símbolo de 'mayor o igual que'.
    etiquetas[-1] = f"≥{valor_max:,.0f}"

    # Cargamos el GeoJSON de municipios de México.
    geojson = json.loads(open("./assets/municipios.json", "r", encoding="utf-8").read())

    fig = go.Figure()

    # Configuramos nuestro mapa Choropleth con todas las variables antes definidas.
    fig.add_traces(
        go.Choropleth(
            geojson=geojson,
            locations=df.index,
            z=df["tasa"],
            featureidkey="properties.CVEGEO",
            colorscale="portland",
            marker_line_color="#FFFFFF",
            marker_line_width=1,
            zmin=valor_min,
            zmax=valor_max,
            colorbar=dict(
                x=0.035,
                y=0.5,
                thickness=150,
                ypad=400,
                ticks="outside",
                outlinewidth=5,
                outlinecolor="#FFFFFF",
                tickvals=marcas,
                ticktext=etiquetas,
                tickwidth=5,
                tickcolor="#FFFFFF",
                ticklen=30,
                tickfont_size=80,
            ),
        )
    )

    # Vamos a sobreponer otro mapa Choropleth, el cual
    # tiene el único propósito de mostrar la división política
    # de las entidades federativas.

    # Cargamos el archivo GeoJSON de México.
    geojson_borde = json.loads(
        open("./assets/mexico.json", "r", encoding="utf-8").read()
    )

    # Este mapa tiene mucho menos personalización.
    # Lo único que necesitamos es que muestre los contornos
    # de cada entidad.
    fig.add_traces(
        go.Choropleth(
            geojson=geojson_borde,
            locations=[f"{i:02}" for i in range(1, 33)],
            z=[1 for _ in range(32)],
            featureidkey="properties.CVEGEO",
            colorscale=["hsla(0, 0, 0, 0)", "hsla(0, 0, 0, 0)"],
            marker_line_color="#FFFFFF",
            marker_line_width=4,
            showscale=False,
        )
    )

    # Personalizamos algunos aspectos del mapa, como el color del oceáno
    # y el del terreno.
    fig.update_geos(
        fitbounds="geojson",
        showocean=True,
        oceancolor="#092635",
        showcountries=False,
        framecolor="#FFFFFF",
        framewidth=5,
        showlakes=False,
        coastlinewidth=0,
        landcolor="#000000",
    )

    # Agregamos las anotaciones correspondientes.
    fig.update_layout(
        showlegend=False,
        font_family="Montserrat",
        font_color="#FFFFFF",
        margin_t=50,
        margin_r=100,
        margin_b=30,
        margin_l=100,
        width=7680,
        height=4320,
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.5,
                y=0.985,
                xanchor="center",
                yanchor="top",
                text=f"Tasas de incidencia de <b>personas desaparecidas</b> en México por municipio de ocurrencia ({año})",
                font_size=140,
            ),
            dict(
                x=0.02,
                y=0.49,
                textangle=-90,
                xanchor="center",
                yanchor="middle",
                text="Tasa bruta por cada 100,000 habitantes",
                font_size=100,
            ),
            dict(
                x=0.98,
                y=0.9,
                xanchor="right",
                yanchor="top",
                text=estadisticas,
                align="left",
                borderpad=30,
                bordercolor="#FFFFFF",
                bgcolor="#000000",
                borderwidth=5,
                font_size=120,
            ),
            dict(
                x=0.01,
                y=-0.003,
                xanchor="left",
                yanchor="bottom",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
                font_size=120,
            ),
            dict(
                x=0.5,
                y=-0.003,
                xanchor="center",
                yanchor="bottom",
                text=subtitulo,
                font_size=120,
            ),
            dict(
                x=1.0,
                y=-0.003,
                xanchor="right",
                yanchor="bottom",
                text="🧁 @lapanquecita",
                font_size=120,
            ),
        ],
    )

    # El nombre del archivo llevará el año como sufijo.
    fig.write_image(f"./municipal_{año}.png")


def tasa_municipios(año):
    """
    Crea una tabla desglosando los 30 municipios con mayor
    tasa bruta de incidencia de personas desaparecidas.

    Parameters
    ----------
    año: int
        El año que se desea graficar.

    """

    # Cargamos el dataset de población por municipio.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str}, index_col=0)

    # Juntamos el nombre del municipio con el de su respectiva entdiad.
    pop["nombre"] = pop["Municipio"] + ", " + pop["Entidad"]

    # Seleccinamos solo las dos columnas que utilizaremos.
    pop = pop[["nombre", str(año)]]

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv", dtype={"CVE_ENT": str, "CVE_MUN": str})

    # Seleccionamos un registro por víctima.
    df = df.groupby("ID_VICTIMA").last()

    # Limpiamos valores confidenciales.
    df = df.replace("CONFIDENCIAL", np.nan)

    # Convertimos las fechas a DateTime.
    df["FECHA_DESAPARICION"] = pd.to_datetime(df["FECHA_DESAPARICION"], errors="coerce")
    df["FECHA_REGISTRO"] = pd.to_datetime(df["FECHA_REGISTRO"], errors="coerce")

    # Vamos a preferir la fecha de desaparición.
    # Pero cuando no esté disponible usaremos la fecha de registro.
    df["FECHA_DESAPARICION"] = df["FECHA_DESAPARICION"].fillna(df["FECHA_REGISTRO"])

    # Seleccionamos solo registros del año de nuestro interés.
    df = df[df["FECHA_DESAPARICION"].dt.year == año]

    # Unimos los identificadores de entidad y municipio.
    # para crear el identificador único.
    df["CVE"] = df["CVE_ENT"] + df["CVE_MUN"]

    # Contamos los registros por municipio.
    df = df["CVE"].value_counts().to_frame("total")

    # Unimos ambos DataFrames.
    df = df.join(pop)

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["total"] / df[str(año)] * 100000

    # Seleccionamos municipios con al menos 50,000 habitantes.
    # Esto es para evitar valores atípicos donde la poblacion
    # es muy pequeña y resulta en tasas muy grandes.
    df = df[df[str(año)] >= 50000]

    # Ordenamos los resultados por la tasa de mayor a menor.
    df.sort_values("tasa", ascending=False, inplace=True)

    # Reseteamos el índice y solo escogemos el top 30.
    df.reset_index(inplace=True)
    df.index += 1
    df = df.head(30)

    subtitulo = "Municipios con al menos 50k habs."

    fig = go.Figure()

    # Vamos a crear una tabla con 4 columnas.
    fig.add_trace(
        go.Table(
            columnwidth=[40, 220, 80, 100],
            header=dict(
                values=[
                    "<b>Pos.</b>",
                    "<b>Municipio, Entidad</b>",
                    "<b>No. Casos</b>",
                    "<b>Tasa 100k habs. ↓</b>",
                ],
                font_color="#FFFFFF",
                fill_color=["#00897b", "#00897b", "#00897b", "#ff3d00"],
                line_width=0.75,
                align="center",
                height=43,
            ),
            cells=dict(
                values=[df.index, df["nombre"], df["total"], df["tasa"]],
                line_width=0.75,
                fill_color=PLOT_COLOR,
                height=43,
                format=["", "", ",.0f", ",.2f"],
                align=["center", "left", "center"],
            ),
        )
    )

    fig.update_layout(
        showlegend=False,
        width=1280,
        height=1600,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=25,
        margin_t=180,
        margin_l=40,
        margin_r=40,
        margin_b=0,
        title_x=0.5,
        title_y=0.95,
        title_font_size=40,
        title_text=f"Los 30 municipios de México con la mayor<br><b>tasa bruta</b> de <b>personas desaparecidas</b> ({año})",
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.015,
                y=0.02,
                xanchor="left",
                yanchor="top",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
            ),
            dict(
                x=0.57,
                y=0.02,
                xanchor="center",
                yanchor="top",
                text=subtitulo,
            ),
            dict(
                x=1.01,
                y=0.02,
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image("./tabla_tasa.png")


def absolutos_municipios(año):
    """
    Crea una tabla desglosando los 30 municipios con mayor
    incidencia de personas desaparecidas.

    Parameters
    ----------
    año: int
        El año que se desea graficar.

    """

    # Cargamos el dataset de población por municipio.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str}, index_col=0)

    # Juntamos el nombre del municipio con el de su respectiva entdiad.
    pop["nombre"] = pop["Municipio"] + ", " + pop["Entidad"]

    # Seleccinamos solo las dos columnas que utilizaremos.
    pop = pop[["nombre", str(año)]]

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv", dtype={"CVE_ENT": str, "CVE_MUN": str})

    # Seleccionamos un registro por víctima.
    df = df.groupby("ID_VICTIMA").last()

    # Limpiamos valores confidenciales.
    df = df.replace("CONFIDENCIAL", np.nan)

    # Convertimos las fechas a DateTime.
    df["FECHA_DESAPARICION"] = pd.to_datetime(df["FECHA_DESAPARICION"], errors="coerce")
    df["FECHA_REGISTRO"] = pd.to_datetime(df["FECHA_REGISTRO"], errors="coerce")

    # Vamos a preferir la fecha de desaparición.
    # Pero cuando no esté disponible usaremos la fecha de registro.
    df["FECHA_DESAPARICION"] = df["FECHA_DESAPARICION"].fillna(df["FECHA_REGISTRO"])

    # Seleccionamos solo registros del año de nuestro interés.
    df = df[df["FECHA_DESAPARICION"].dt.year == año]

    # Unimos los identificadores de entidad y municipio.
    # para crear el identificador único.
    df["CVE"] = df["CVE_ENT"] + df["CVE_MUN"]

    # Contamos los registros por municipio.
    df = df["CVE"].value_counts().to_frame("total")

    # Unimos ambos DataFrames.
    df = df.join(pop)

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["total"] / df[str(año)] * 100000

    # Ordenamos los resultados por el total de mayor a menor.
    df.sort_values("total", ascending=False, inplace=True)

    # Reseteamos el índice y solo escogemos el top 30.
    df.reset_index(inplace=True)
    df.index += 1
    df = df.head(30)

    # En este caso no usaremos el subtítulo.
    subtitulo = ""

    fig = go.Figure()

    # Vamos a crear una tabla con 4 columnas.
    fig.add_trace(
        go.Table(
            columnwidth=[40, 220, 80, 100],
            header=dict(
                values=[
                    "<b>Pos.</b>",
                    "<b>Municipio, Entidad</b>",
                    "<b>No. Casos ↓</b>",
                    "<b>Tasa 100k habs.</b>",
                ],
                font_color="#FFFFFF",
                fill_color=["#00897b", "#00897b", "#ff3d00", "#00897b"],
                line_width=0.75,
                align="center",
                height=43,
            ),
            cells=dict(
                values=[df.index, df["nombre"], df["total"], df["tasa"]],
                line_width=0.75,
                fill_color=PLOT_COLOR,
                height=43,
                format=["", "", ",.0f", ",.2f"],
                align=["center", "left", "center"],
            ),
        )
    )

    fig.update_layout(
        showlegend=False,
        width=1280,
        height=1600,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=25,
        margin_t=180,
        margin_l=40,
        margin_r=40,
        margin_b=0,
        title_x=0.5,
        title_y=0.95,
        title_font_size=40,
        title_text=f"Los 30 municipios de México con la mayor<br><b>incidencia</b> de <b>personas desaparecidas</b> ({año})",
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.015,
                y=0.02,
                xanchor="left",
                yanchor="top",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
            ),
            dict(
                x=0.57,
                y=0.02,
                xanchor="center",
                yanchor="top",
                text=subtitulo,
            ),
            dict(
                x=1.01,
                y=0.02,
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image("./tabla_absolutos.png")


if __name__ == "__main__":
    crear_mapa(2024)
    tasa_municipios(2024)
    absolutos_municipios(2024)
