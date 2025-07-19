import streamlit as st
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from kloppy import opta
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚽ Análisis de Eventos Opta (pass + shot)")

# 📂 Subida de archivos F7 y F24
f7_file = st.file_uploader("Subí archivo F7 (alineaciones - opta_f7.xml)", type="xml")
f24_file = st.file_uploader("Subí archivo F24 (eventos - opta_f24.xml)", type="xml")

if f7_file and f24_file:
    # ✅ Cargar dataset desde archivos subidos
    dataset = opta.load(
        f7_data=f7_file,
        f24_data=f24_file,
        coordinates="opta",
        event_types=["pass", "shot"]
    )
    df = dataset.to_df()


    # 🎛️ Filtros
    st.sidebar.header("Filtros")

    tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
    jugador = st.sidebar.selectbox("Jugador", ['Todos'] + sorted(df['player_id'].dropna().unique()))
    equipo = st.sidebar.selectbox("Equipo", ['Todos'] + sorted(df['team_id'].dropna().unique()))
    min_minute, max_minute = int(df['minute'].min()), int(df['timestamp'].max())
    minutos = st.sidebar.slider("Minutos", min_minute, max_minute, (min_minute, max_minute))

    # Zona del campo (coordenadas de Opta: 0–100)
    st.sidebar.markdown("📍 Zona del campo")
    xmin = st.sidebar.slider("X min", 0, 100, 30)
    xmax = st.sidebar.slider("X max", 0, 100, 70)
    ymin = st.sidebar.slider("Y min", 0, 100, 20)
    ymax = st.sidebar.slider("Y max", 0, 100, 80)

    # Aplicar filtros
    filtered_df = df[df['event_type'] == tipo_evento]
    if jugador != 'Todos':
        filtered_df = filtered_df[filtered_df['player_id'] == jugador]
    if equipo != 'Todos':
        filtered_df = filtered_df[filtered_df['team_id'] == equipo]

    filtered_df = filtered_df[
        (filtered_df['timestamp'] >= minutos[0]) & (filtered_df['timestamp'] <= minutos[1]) &
        (filtered_df['x'] >= xmin) & (filtered_df['x'] <= xmax) &
        (filtered_df['y'] >= ymin) & (filtered_df['y'] <= ymax)
    ]

    # Mostrar resultados
    st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

    # Visualización
    pitch = Pitch(pitch_type='opta')
    fig, ax = pitch.draw(figsize=(10, 7))
    pitch.scatter(filtered_df['x'], filtered_df['y'], ax=ax, color='red', s=100, edgecolors='black')
    st.pyplot(fig)

    # Tabla de resultados
    st.dataframe(filtered_df[['player_id', 'team_id', 'timestamp']].value_counts().reset_index(name='Cantidad'))

