import streamlit as st
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from kloppy import opta
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚽ Análisis de Eventos Opta (pass + shot) - Múltiples Partidos")

# 📂 Subida múltiple de archivos
f7_files = st.file_uploader("Subí archivos F7 (alineaciones)", type="xml", accept_multiple_files=True)
f24_files = st.file_uploader("Subí archivos F24 (eventos)", type="xml", accept_multiple_files=True)

dataframes = []

if f7_files and f24_files:
    # Indexar archivos F24 por nombre base
    f24_dict = {f.name.replace("_f24.xml", ""): f for f in f24_files}

    for f7 in f7_files:
        nombre_base = f7.name.replace("_f7.xml", "")
        if nombre_base in f24_dict:
            f24 = f24_dict[nombre_base]

            try:
                dataset = opta.load(
                    f7_data=f7,
                    f24_data=f24,
                    coordinates="opta",
                    event_types=["pass", "shot"]
                )
                df = dataset.to_df()
                df["match_id"] = nombre_base
                dataframes.append(df)
            except Exception as e:
                st.error(f"❌ Error cargando partido '{nombre_base}': {e}")
        else:
            st.warning(f"⚠️ No se encontró archivo F24 para '{nombre_base}'")

# Procesar si hay datos válidos
if dataframes:
    df = pd.concat(dataframes, ignore_index=True)

    # 🎛️ Filtros
    st.sidebar.header("Filtros")
    tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
    partidos = st.sidebar.multiselect("Partido(s)", df['match_id'].unique(), default=df['match_id'].unique())
    jugadores = ['Todos'] + sorted(df['player_id'].dropna().astype(str).unique())
    jugador = st.sidebar.selectbox("Jugador", jugadores)
    equipos = ['Todos'] + sorted(df['team_id'].dropna().astype(str).unique())
    equipo = st.sidebar.selectbox("Equipo", equipos)

    # Zona del campo
    st.sidebar.markdown("📍 Zona del campo")
    xmin = st.sidebar.slider("X min", 0, 100, 30)
    xmax = st.sidebar.slider("X max", 0, 100, 70)
    ymin = st.sidebar.slider("Y min", 0, 100, 20)
    ymax = st.sidebar.slider("Y max", 0, 100, 80)

    # Aplicar filtros
    filtered_df = df[df['event_type'] == tipo_evento]
    filtered_df = filtered_df[filtered_df['match_id'].isin(partidos)]

    if jugador != 'Todos':
        filtered_df = filtered_df[filtered_df['player_id'].astype(str) == jugador]
    if equipo != 'Todos':
        filtered_df = filtered_df[filtered_df['team_id'].astype(str) == equipo]

    filtered_df = filtered_df[
        (filtered_df['coordinates_x'] >= xmin) & (filtered_df['coordinates_x'] <= xmax) &
        (filtered_df['coordinates_y'] >= ymin) & (filtered_df['coordinates_y'] <= ymax)
    ]

    # Mostrar resultados
    st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

    pitch = Pitch(pitch_type='opta')
    fig, ax = pitch.draw(figsize=(10, 7))
    pitch.scatter(filtered_df['coordinates_x'], filtered_df['coordinates_y'], ax=ax, color='red', s=100, edgecolors='black')
    st.pyplot(fig)

    st.dataframe(
        filtered_df[['player_id', 'team_id', 'match_id']]
        .value_counts()
        .reset_index(name='Cantidad')
        .rename(columns={'player_id': 'Jugador', 'team_id': 'Equipo', 'match_id': 'Partido'})
    )
else:
    if f7_files and f24_files:
        st.warning("⚠️ No se pudieron emparejar archivos F7 y F24 correctamente.")



