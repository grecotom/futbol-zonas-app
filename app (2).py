import streamlit as st
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from kloppy import statsperform
import pandas as pd

st.set_page_config(layout="wide")
st.title("⚽ Análisis de Eventos con StatsPerform (MA1 + MA3)")

# 📂 Subida de archivos MA1 y MA3
ma1_file = st.file_uploader("Subí archivo MA1 (eventos)", type="json")
ma3_file = st.file_uploader("Subí archivo MA3 (metadatos)", type="json")

if ma1_file and ma3_file:
    # ✅ Cargar datos de StatsPerform
    dataset = statsperform.load_event(
        ma1_data=ma1_file,
        ma3_data=ma3_file,
        coordinates="opta",
        pitch_length=102.5,
        pitch_width=69.0,
        event_types=["pass", "shot"]
    )

    df = dataset.to_df()

    if df.empty:
        st.warning("⚠️ El archivo se cargó, pero no hay eventos disponibles. Verificá que los archivos sean del mismo partido.")
    else:
        # 🎛️ Filtros
        st.sidebar.header("Filtros")

        tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
        jugador_id = st.sidebar.selectbox("Jugador (player_id)", ['Todos'] + sorted(df['player_id'].dropna().unique()))
        equipo_id = st.sidebar.selectbox("Equipo (team_id)", ['Todos'] + sorted(df['team_id'].dropna().unique()))
        min_minute = int(df['timestamp'].dt.total_seconds().min() // 60)
        max_minute = int(df['timestamp'].dt.total_seconds().max() // 60)
        minutos = st.sidebar.slider("Minutos", min_minute, max_minute, (min_minute, max_minute))

        st.sidebar.markdown("📍 Zona del campo")
        xmin = st.sidebar.slider("X min", 0.0, 100.0, 0.0)
        xmax = st.sidebar.slider("X max", 0.0, 100.0, 100.0)
        ymin = st.sidebar.slider("Y min", 0.0, 100.0, 0.0)
        ymax = st.sidebar.slider("Y max", 0.0, 100.0, 100.0)

        # Convertimos el tiempo en minutos
        df['minute'] = df['timestamp'].dt.total_seconds() // 60

        # Aplicar filtros
        filtered_df = df[df['event_type'] == tipo_evento]
        if jugador_id != 'Todos':
            filtered_df = filtered_df[filtered_df['player_id'] == jugador_id]
        if equipo_id != 'Todos':
            filtered_df = filtered_df[filtered_df['team_id'] == equipo_id]

        filtered_df = filtered_df[
            (filtered_df['minute'] >= minutos[0]) & (filtered_df['minute'] <= minutos[1]) &
            (filtered_df['coordinates_x'] >= xmin) & (filtered_df['coordinates_x'] <= xmax) &
            (filtered_df['coordinates_y'] >= ymin) & (filtered_df['coordinates_y'] <= ymax)
        ]

        # Mostrar resultados
        st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

        pitch = Pitch(pitch_type='opta')
        fig, ax = pitch.draw(figsize=(10, 7))
        pitch.scatter(filtered_df['coordinates_x'], filtered_df['coordinates_y'], ax=ax, color='blue', s=100, edgecolors='black')
        st.pyplot(fig)

        # Mostrar tabla con conteo por jugador
        st.dataframe(filtered_df[['player_id', 'team_id', 'minute']].value_counts().reset_index(name='Cantidad'))

