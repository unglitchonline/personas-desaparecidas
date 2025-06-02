"""
Este script analiza las cifras de personas desaparecidas
y no localizadas en México desde una perspectiva estatal.
"""

import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from plotly.subplots import make_subplots


# Todas las gráficas de este script
# van a compartir el mismo esquema de colores.
PLOT_COLOR = "#171010"
PAPER_COLOR = "#2B2B2B"

# La fecha en la que los datos fueron recopilados.
FECHA_FUENTE = "01/06/2025"

# Este diccionario es utilizado por todas las funciones
# para poder referenciar cada entidad con su clave numérica.
ENTIDADES = {
    0: "México",
    1: "Aguascalientes",
    2: "Baja California",
    3: "Baja California Sur",
    4: "Campeche",
    5: "Coahuila",
    6: "Colima",
    7: "Chiapas",
    8: "Chihuahua",
    9: "Ciudad de México",
    10: "Durango",
    11: "Guanajuato",
    12: "Guerrero",
    13: "Hidalgo",
    14: "Jalisco",
    15: "Estado de México",
    16: "Michoacán",
    17: "Morelos",
    18: "Nayarit",
    19: "Nuevo León",
    20: "Oaxaca",
    21: "Puebla",
    22: "Querétaro",
    23: "Quintana Roo",
    24: "San Luis Potosí",
    25: "Sinaloa",
    26: "Sonora",
    27: "Tabasco",
    28: "Tamaulipas",
    29: "Tlaxcala",
    30: "Veracruz",
    31: "Yucatán",
    32: "Zacatecas",
    99: "Se desconoce",
}


# Esta lista será usada para las etiquetas del eje horizontal
# en la gráfica de comparación mensual.
MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def desaparecidos_anuales(entidad_id, xanchor="left"):
    """
    Crea una gráfica de barras mostrando la evolución anual de
    la tasa de incidencia de personas desaparecidas.

    Parameters
    ----------
    entidad_id : int
        La clave numérica de la entidad. 0 para datos a nivel nacional.

    xanchor : str
        Es la ubicación de la leyenda dentro del gráfico.
        Los posibles valores pueden ser "left" o "right".

    """

    # Cargamos el dataset de la población estimada según el CONAPO.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str})

    # Sumamos el total de población por entidad.
    pop["CVE"] = pop["CVE"].str[:2]
    pop = pop.groupby("CVE").sum(numeric_only=True)

    # Si el valor de entidad_id es 0, sumamos la población de todas las entidades.
    if entidad_id == 0:
        pop = pop.sum(axis=0)
    else:
        pop = pop.loc[f"{entidad_id:02}"]

    # Convertimos el índice a int.
    pop.index = pop.index.astype(int)

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv")

    # Filtramos por entidad. Si entidad_es 0, no hacemos filtro.
    if entidad_id != 0:
        df = df[df["CVE_ENT"] == entidad_id]

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

    # Contamos los registros de forma anual.
    df = df["FECHA_DESAPARICION"].value_counts().resample("YS").sum().to_frame("total")

    # Del índice solo necesitamos el año.
    df.index = df.index.year

    # Agregamos la población.
    df["pop"] = pop

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["total"] / df["pop"] * 100000

    # Preparamos el texto para cada observación dentro de la gráfica.
    df["texto"] = df.apply(
        lambda x: f"<b>{x['tasa']:,.2f}</b><br>({x['total']:,.0f})", axis=1
    )

    # Seleccionamos los últimos 20 años.
    df = df.tail(20)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["tasa"],
            text=df["texto"],
            name=f"Total acumulado: <b>{df['total'].sum():,.0f}</b> víctimas.<br>No incluye registros confidenciales.",
            textposition="outside",
            marker_color=df["tasa"],
            marker_colorscale="portland",
            marker_cmid=0,
            marker_line_width=0,
            textfont_size=34,
        )
    )

    fig.update_xaxes(
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=2,
        showline=True,
        showgrid=True,
        gridwidth=0.5,
        mirror=True,
        nticks=len(df) + 1,
    )

    fig.update_yaxes(
        title="Tasa bruta por cada 100,000 habitantes",
        range=[0, df["tasa"].max() * 1.1],
        ticks="outside",
        separatethousands=True,
        ticklen=10,
        title_standoff=15,
        tickcolor="#FFFFFF",
        linewidth=2,
        gridwidth=0.5,
        showline=True,
        nticks=20,
        zeroline=False,
        mirror=True,
    )

    fig.update_layout(
        legend_itemsizing="constant",
        showlegend=True,
        legend_borderwidth=1,
        legend_bordercolor="#FFFFFF",
        legend_x=0.01 if xanchor == "left" else 0.99,
        legend_y=0.98,
        legend_xanchor=xanchor,
        legend_yanchor="top",
        width=1920,
        height=1080,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=24,
        title_text=f"Evolución de la incidencia de personas desaparecidas y no localizadas en <b>{ENTIDADES[entidad_id]}</b> ({df.index.min()}-{df.index.max()})",
        title_x=0.5,
        title_y=0.965,
        margin_t=80,
        margin_r=40,
        margin_b=120,
        margin_l=140,
        title_font_size=34,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        annotations=[
            dict(
                x=0.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
            ),
            dict(
                x=0.5,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="top",
                text="Año de la desaparición",
            ),
            dict(
                x=1.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image(f"./anual_{entidad_id}.png")


def homicidios_anuales(entidad_id, xanchor="left"):
    """
    Crea una gráfica de barras mostrando la evolución anual de
    la tasa de homicidios dolosos.

    Parameters
    ----------
    entidad_id : int
        La clave numérica de la entidad. 0 para datos a nivel nacional.

    xanchor : str
        Es la ubicación de la leyenda dentro del gráfico.
        Los posibles valores pueden ser "left" o "right".

    """

    # Cargamos el dataset de la población estimada según el CONAPO.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str})

    # Sumamos el total de población por entidad.
    pop["CVE"] = pop["CVE"].str[:2]
    pop = pop.groupby("CVE").sum(numeric_only=True)

    # Si el valor de entidad_id es 0, sumamos la población de todas las entidades.
    if entidad_id == 0:
        pop = pop.sum(axis=0)
    else:
        pop = pop.loc[f"{entidad_id:02}"]

    # Convertimos el índice a int.
    pop.index = pop.index.astype(int)

    # Cargamos el dataset de víctimas (SESNSP).
    df = pd.read_csv(
        "./assets/timeseries_victimas.csv", parse_dates=["PERIODO"], index_col=0
    )

    # Filtramos por entidad. Si entidad_es 0, no hacemos filtro.
    if entidad_id != 0:
        df = df[df["CVE_ENT"] == entidad_id]

    # Seleccionamos homicidios dolosos y feminicidios.
    # Esto es con el efecto de seleccionar todas las muertes violentas.
    df = df[df["DELITO"].isin(["Homicidio doloso", "Feminicidio"])]

    # Calculamos el total de víctimas por año.
    df = df.resample("YS").sum(numeric_only=True)

    # Solo necesitamos el año para emparejar los DataFrames.
    df.index = df.index.year

    # Agregamos la población total para cada año.
    df["pop"] = pop

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["TOTAL"] / df["pop"] * 100000

    # Preparamos el texto para cada observación dentro de la gráfica.
    df["texto"] = df.apply(
        lambda x: f"<b>{x['tasa']:,.2f}</b><br>({x['TOTAL']:,.0f})", axis=1
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["tasa"],
            text=df["texto"],
            name=f"Total acumulado: <b>{df['TOTAL'].sum():,.0f}</b>",
            textposition="outside",
            marker_color=df["tasa"],
            marker_colorscale="redor",
            marker_line_width=0,
            textfont_size=40,
        )
    )

    fig.update_xaxes(
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=2,
        showline=True,
        showgrid=True,
        gridwidth=0.5,
        mirror=True,
        nticks=len(df) + 1,
    )

    fig.update_yaxes(
        title="Tasa bruta por cada 100,000 habitantes",
        range=[0, df["tasa"].max() * 1.15],
        ticks="outside",
        separatethousands=True,
        ticklen=10,
        title_standoff=15,
        tickcolor="#FFFFFF",
        linewidth=2,
        gridwidth=0.5,
        showline=True,
        nticks=20,
        zeroline=False,
        mirror=True,
    )

    fig.update_layout(
        legend_itemsizing="constant",
        showlegend=True,
        legend_borderwidth=1,
        legend_bordercolor="#FFFFFF",
        legend_x=0.01 if xanchor == "left" else 0.99,
        legend_y=0.98,
        legend_xanchor=xanchor,
        legend_yanchor="top",
        width=1920,
        height=1080,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=24,
        title_text=f"Evolución de la tasa de homicidios dolosos en <b>{ENTIDADES[entidad_id]}</b> (2015-2025)",
        title_x=0.5,
        title_y=0.965,
        margin_t=80,
        margin_r=40,
        margin_b=120,
        margin_l=130,
        title_font_size=36,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        annotations=[
            dict(
                x=0.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                text=f"Fuente: SESNSP ({FECHA_FUENTE})",
            ),
            dict(
                x=0.5,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="top",
                text="Año de registro del homicidio",
            ),
            dict(
                x=1.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image(f"./anual_homicidios_{entidad_id}.png")


def comparacion_mensual(entidad_id, año, xanchor="left"):
    """
    Crea dos gráficas de barras comparando las cifras mensuales
    de personas desaparecidas y homicidios dolosos.

    Parameters
    ----------
    entidad_id : int
        La clave numérica de la entidad. 0 para datos a nivel nacional.

    año: int
        El año que se desea graficar.

    xanchor : str
        Es la ubicación de la leyenda dentro del gráfico.
        Los posibles valores pueden ser "left" o "right".

    """

    # Cargamos el dataset de víctimas (SESNSP).
    homicidios = pd.read_csv(
        "./assets/timeseries_victimas.csv", parse_dates=["PERIODO"], index_col=0
    )

    # Filtramos por entidad. Si entidad_es 0, no hacemos filtro.
    if entidad_id != 0:
        homicidios = homicidios[homicidios["CVE_ENT"] == entidad_id]

    # Seleccionamos homicidios dolosos y feminicidios.
    # Esto es con el efecto de seleccionar todas las muertes violentas.
    homicidios = homicidios[
        homicidios["DELITO"].isin(["Homicidio doloso", "Feminicidio"])
    ]

    # Seleccionamos los registros del año de nuestro interés.
    homicidios = homicidios[homicidios.index.year == año]

    # Calculamos el total de víctimas por mes.
    homicidios = homicidios.resample("MS").sum(numeric_only=True)["TOTAL"]

    # Cargamos el dataset de personas desaparecidas.
    desaparecidos = pd.read_csv("./data.csv")

    # Filtramos por entidad. Si entidad_es 0, no hacemos filtro.
    if entidad_id != 0:
        desaparecidos = desaparecidos[desaparecidos["CVE_ENT"] == entidad_id]

    # Seleccionamos un registro por víctima.
    desaparecidos = desaparecidos.groupby("ID_VICTIMA").last()

    # Limpiamos valores confidenciales.
    desaparecidos = desaparecidos.replace("CONFIDENCIAL", np.nan)

    # Convertimos las fechas a DateTime.
    desaparecidos["FECHA_DESAPARICION"] = pd.to_datetime(
        desaparecidos["FECHA_DESAPARICION"], errors="coerce"
    )
    desaparecidos["FECHA_REGISTRO"] = pd.to_datetime(
        desaparecidos["FECHA_REGISTRO"], errors="coerce"
    )

    # Vamos a preferir la fecha de desaparición.
    # Pero cuando no esté disponible usaremos la fecha de registro.
    desaparecidos["FECHA_DESAPARICION"] = desaparecidos["FECHA_DESAPARICION"].fillna(
        desaparecidos["FECHA_REGISTRO"]
    )

    # Seleccionamos los registros del año de nuestro interés.
    desaparecidos = desaparecidos[desaparecidos["FECHA_DESAPARICION"].dt.year == año]

    # Contamos los registros por mes de ocurrencia.
    desaparecidos = (
        desaparecidos["FECHA_DESAPARICION"].value_counts().resample("MS").sum()
    )

    # Vamos a agregar dos gráficas de barras verticales.
    # Una para los homicidios y otra para las personas desaparecidas.
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=MESES,
            y=desaparecidos.values,
            text=desaparecidos.values,
            texttemplate="%{text:,.0f}",
            name=f"<b>Personas desaparecidas</b><br>Total: <b>{desaparecidos.sum():,.0f}</b>",
            textposition="outside",
            marker_color="#2196f3",
            marker_cmid=0,
            marker_line_width=0,
            textfont_size=30,
        )
    )

    fig.add_trace(
        go.Bar(
            x=MESES,
            y=homicidios.values,
            text=homicidios.values,
            texttemplate="%{text:,.0f}",
            name=f"<b>Homicidios dolosos</b><br>Total: <b>{homicidios.sum():,.0f}</b>",
            textposition="outside",
            marker_color="#ffa000",
            marker_cmid=0,
            marker_line_width=0,
            textfont_size=30,
        )
    )

    fig.update_xaxes(
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=2,
        showline=True,
        showgrid=True,
        gridwidth=0.5,
        mirror=True,
        nticks=21,
    )

    fig.update_yaxes(
        title="Número de registros mensuales",
        range=[0, homicidios.values.max() * 1.08],
        ticks="outside",
        separatethousands=True,
        ticklen=10,
        title_standoff=15,
        tickcolor="#FFFFFF",
        linewidth=2,
        gridwidth=0.5,
        showline=True,
        nticks=20,
        zeroline=False,
        mirror=True,
    )

    fig.update_layout(
        legend_itemsizing="constant",
        showlegend=True,
        legend_borderwidth=1,
        legend_bordercolor="#FFFFFF",
        legend_x=0.01 if xanchor == "left" else 0.99,
        legend_y=0.98,
        legend_xanchor=xanchor,
        legend_yanchor="top",
        width=1920,
        height=1080,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=24,
        title_text=f"Personas desaparecidas y homicidios dolosos en <b>{ENTIDADES[entidad_id]}</b> durante el {año}",
        title_x=0.5,
        title_y=0.965,
        margin_t=80,
        margin_r=40,
        margin_b=120,
        margin_l=140,
        title_font_size=36,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        annotations=[
            dict(
                x=0.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                text=f"Fuentes: RNPDNO y SESNSP ({FECHA_FUENTE})",
            ),
            dict(
                x=0.5,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="top",
                text="Mes de la desaparición / mes de registro",
            ),
            dict(
                x=1.01,
                y=-0.11,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image(f"./mensual_{entidad_id}_{año}.png")


def crear_mapa(año):
    """
    Crea un mapa choropleth y una tabla desglosando las personas
    desaparecidas y no localizadas por sexo y entidad de ocurrencia.

    Parameters
    ----------
    año : int
        El año que nos interesa graficar.

    """

    # Cargamos el dataset de la población estimada según el CONAPO.
    pop = pd.read_csv("./assets/poblacion.csv", dtype={"CVE": str})

    # Sumamos el total de población por entidad.
    pop["CVE"] = pop["CVE"].str[:2]
    pop = pop.groupby("CVE").sum(numeric_only=True)

    # Seleccionamos la población del año especificado.
    pop = pop[str(año)]

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv", dtype={"CVE_ENT": str})

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

    # Seleccionamos los registros del año de nuestro interés.
    df = df[df["FECHA_DESAPARICION"].dt.year == año]

    # Transformamos el DataFrame para que las entidades sean el índice
    # y las columnas el sexo de la víctima.
    df = df.pivot_table(
        index="CVE_ENT",
        columns="SEXO",
        values="ENTIDAD",
        aggfunc="count",
        fill_value=0,
    )

    # Calculamos el total por entidad.
    df["total"] = df.sum(axis=1)

    # Agregamos la población para cada entidad.
    df["pop"] = pop

    # Calculamos la tasa por cada 100,000 habitantes.
    df["tasa"] = df["total"] / df["pop"] * 100000

    # Ordenamos la tasa de manera descendente.
    df.sort_values("tasa", ascending=False, inplace=True)

    # Calculamos los totales nacionales.
    total_nacional = df["total"].sum()
    poblacion_nacional = pop.sum()

    # Preparamos los valores para nuestro subtítulo.
    subtitulo = f"Tasa nacional: <b>{total_nacional / poblacion_nacional * 100000:,.2f}</b> (con <b>{total_nacional:,.0f}</b> víctimas)"

    # Quitamos los valores NaN para que no interfieran con los siguientes pasos.
    df = df.dropna(axis=0)

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
    etiquetas[-1] = f"≥{etiquetas[-1]}"

    # Cargamos el GeoJSON de México.
    geojson = json.load(open("./assets/mexico.json", "r", encoding="utf-8"))

    fig = go.Figure()

    fig.add_traces(
        go.Choropleth(
            geojson=geojson,
            locations=df.index,
            z=df["tasa"],
            featureidkey="properties.CVEGEO",
            colorscale="portland",
            marker_line_color="#FFFFFF",
            marker_line_width=1.5,
            zmin=valor_min,
            zmax=valor_max,
            colorbar=dict(
                x=0.03,
                y=0.5,
                ypad=50,
                ticks="outside",
                outlinewidth=2,
                outlinecolor="#FFFFFF",
                tickvals=marcas,
                ticktext=etiquetas,
                tickwidth=3,
                tickcolor="#FFFFFF",
                ticklen=10,
            ),
        )
    )

    fig.update_geos(
        fitbounds="geojson",
        showocean=True,
        oceancolor="#082032",
        showcountries=False,
        framecolor="#FFFFFF",
        framewidth=2,
        showlakes=False,
        coastlinewidth=0,
        landcolor="#1C0A00",
    )

    fig.update_layout(
        showlegend=False,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=28,
        margin_t=80,
        margin_r=40,
        margin_b=60,
        margin_l=40,
        width=1920,
        height=1080,
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.5,
                y=1.025,
                xanchor="center",
                yanchor="top",
                text=f"Incidencia de personas desaparecidas y no localizadas en México durante el {año}",
                font_size=42,
            ),
            dict(
                x=0.0275,
                y=0.46,
                textangle=-90,
                xanchor="center",
                yanchor="middle",
                text="Tasa bruta por cada 100,000 habitantes",
            ),
            dict(
                x=0.01,
                y=-0.056,
                xanchor="left",
                yanchor="top",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
            ),
            dict(
                x=0.5,
                y=-0.056,
                xanchor="center",
                yanchor="top",
                text=subtitulo,
            ),
            dict(
                x=1.01,
                y=-0.056,
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    # Guardamos el mapa con un nombre temporal.
    fig.write_image("./1.png")

    # Ahora crearemos las tablas con el desglose por entidad.

    # Agregamos el nombre a cada entidad.
    df["nombre"] = df.index.map(lambda x: ENTIDADES[int(x)])

    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.03,
        specs=[[{"type": "table"}, {"type": "table"}]],
    )

    fig.add_trace(
        go.Table(
            columnwidth=[150, 80],
            header=dict(
                values=[
                    "<b>Entidad</b>",
                    "<b>Hombres</b>",
                    "<b>Mujeres</b>",
                    "<b>Total*</b>",
                    "<b>Tasa ↓</b>",
                ],
                font_color="#FFFFFF",
                fill_color=["#00897b", "#00897b", "#00897b", "#00897b", "#FF1E56"],
                align="center",
                height=43,
                line_width=0.8,
            ),
            cells=dict(
                values=[
                    df["nombre"][:16],
                    df["HOMBRE"][:16],
                    df["MUJER"][:16],
                    df["total"][:16],
                    df["tasa"][:16],
                ],
                fill_color=PLOT_COLOR,
                height=43,
                format=["", ",", ",", ",", ",.2f"],
                line_width=0.8,
                align=["left", "center"],
            ),
        ),
        col=1,
        row=1,
    )

    fig.add_trace(
        go.Table(
            columnwidth=[150, 80],
            header=dict(
                values=[
                    "<b>Entidad</b>",
                    "<b>Hombres</b>",
                    "<b>Mujeres</b>",
                    "<b>Total*</b>",
                    "<b>Tasa ↓</b>",
                ],
                font_color="#FFFFFF",
                fill_color=["#00897b", "#00897b", "#00897b", "#00897b", "#FF1E56"],
                align="center",
                height=43,
                line_width=0.8,
            ),
            cells=dict(
                values=[
                    df["nombre"][16:],
                    df["HOMBRE"][16:],
                    df["MUJER"][16:],
                    df["total"][16:],
                    df["tasa"][16:],
                ],
                fill_color=PLOT_COLOR,
                height=43,
                format=["", ",", ",", ",", ",.2f"],
                line_width=0.8,
                align=["left", "center"],
            ),
        ),
        col=2,
        row=1,
    )

    fig.update_layout(
        width=1920,
        height=840,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=28,
        margin_t=25,
        margin_l=40,
        margin_r=40,
        margin_b=0,
        paper_bgcolor=PAPER_COLOR,
        annotations=[
            dict(
                x=0.5,
                y=0.03,
                xanchor="center",
                yanchor="top",
                text="*El total está conformado por hombres, mujeres y víctimas con sexo no determinado.",
            ),
        ],
    )

    # Guardamos la tabla con un nombre temporal.
    fig.write_image("./2.png")

    # Vamos a usar la librería Pillow para unir ambas imágenes.
    # Primero cargamos las dos imágenes recién creadas.
    imagen1 = Image.open("./1.png")
    imagen2 = Image.open("./2.png")

    # Calculamos el ancho y alto final de nuestra imagen.
    resultado_ancho = imagen1.width
    resultado_alto = imagen1.height + imagen2.height

    # Copiamos los pixeles de ambas imágenes.
    resultado = Image.new("RGB", (resultado_ancho, resultado_alto))
    resultado.paste(im=imagen1, box=(0, 0))
    resultado.paste(im=imagen2, box=(0, imagen1.height))

    # Exportamos la nueva imagen unida y borramos las originales.
    resultado.save(f"./estatal_{año}.png")

    os.remove("./1.png")
    os.remove("./2.png")


def comparacion_anual(primer_año, segundo_año):
    """
    Crea una gráfica de barras horizontal mostrando el cambio
    porcentual de personas desaparecidas para cada entidad en México.

    Parameters
    ----------
    primre_año : int
        El año base que nos interesa comparar.

    segundo_año : int
        El año destino que nos interesa comparar.

    """

    # Cargamos el dataset de personas desaparecidas.
    df = pd.read_csv("./data.csv")

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

    # Seleccionamos los registros de los años de nuestro interés.
    df = df[df["FECHA_DESAPARICION"].dt.year.isin([primer_año, segundo_año])]

    # Transformamos el DataFrame para que las entidades sean el índice
    # y las columnas el año de ocurrencia.
    df = df.pivot_table(
        index="CVE_ENT",
        columns=df["FECHA_DESAPARICION"].dt.year,
        values="ENTIDAD",
        aggfunc="count",
        fill_value=0,
    )

    # Asignamos el nombre a las claves de entidad.
    df.index = df.index.map(ENTIDADES)

    # Calculamos el total nacional.
    df.loc["<b>Nacional</b>"] = df.sum(axis=0)

    # Calculamos el cambio porcentual.
    df["cambio"] = (df[segundo_año] - df[primer_año]) / df[primer_año] * 100

    # Preparamos el texto para cada observación.
    df["texto"] = df.apply(
        lambda x: f" <b>{x['cambio']:,.1f}%</b> ({x[primer_año]:,.0f} → {x[segundo_año]:,.0f}) ",
        axis=1,
    )

    # Ordenamos de mayor a menor basado en el cambio porcentual.
    df.sort_values("cambio", ascending=False, inplace=True)

    # Calculamos el valor máximo para ajustar el rango del eje horizontal.
    valor_max = df["cambio"].abs().max()
    valor_max = ((valor_max // 5) + 1) * 5

    # Determinamos la posición de los textos para cada barra.
    df["ratio"] = df["cambio"].abs() / valor_max
    df["texto_pos"] = df["ratio"].apply(lambda x: "inside" if x >= 0.7 else "outside")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=df.index,
            x=df["cambio"],
            text=df["texto"],
            textposition=df["texto_pos"],
            textfont_color="#FFFFFF",
            orientation="h",
            marker_color=df["cambio"],
            marker_colorscale="geyser",
            marker_cmid=0,
            marker_line_width=0,
            textfont_size=30,
        )
    )

    fig.update_xaxes(
        range=[valor_max * -1, valor_max],
        ticksuffix="%",
        ticks="outside",
        ticklen=10,
        zeroline=False,
        tickcolor="#FFFFFF",
        linewidth=2,
        showline=True,
        gridwidth=0.5,
        mirror=True,
        nticks=20,
    )

    fig.update_yaxes(
        autorange="reversed",
        ticks="outside",
        separatethousands=True,
        ticklen=10,
        tickcolor="#FFFFFF",
        linewidth=2,
        gridwidth=0.5,
        showline=True,
        mirror=True,
    )

    fig.update_layout(
        showlegend=False,
        width=1920,
        height=1920,
        font_family="Montserrat",
        font_color="#FFFFFF",
        font_size=24,
        title_text=f"Comparación de la incidencia de personas desaparecidas en México ({primer_año} vs. {segundo_año})",
        title_x=0.5,
        title_y=0.98,
        margin_t=80,
        margin_r=40,
        margin_b=120,
        margin_l=280,
        title_font_size=36,
        paper_bgcolor=PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
        annotations=[
            dict(
                x=0.99,
                y=0.0,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="bottom",
                align="left",
                bgcolor="#323232",
                bordercolor="#FFFFFF",
                borderwidth=1.5,
                borderpad=7,
                text="<b>Notas:</b><br>No incluye registros confidenciales.<br>Todas estas personas aún siguen<br>desaparecidas o no localizadas.",
            ),
            dict(
                x=0.01,
                y=-0.06,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                text=f"Fuente: RNPDNO ({FECHA_FUENTE})",
            ),
            dict(
                x=0.58,
                y=-0.06,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="top",
                text="Cambio porcentual",
            ),
            dict(
                x=1.0,
                y=-0.06,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                text="🧁 @lapanquecita",
            ),
        ],
    )

    fig.write_image("./comparacion_entidad.png")


if __name__ == "__main__":
    desaparecidos_anuales(29)
    homicidios_anuales(25)
    comparacion_mensual(25, 2024)

    crear_mapa(2024)
    comparacion_anual(2023, 2024)
