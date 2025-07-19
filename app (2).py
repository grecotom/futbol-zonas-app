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

    # ✅ Convertir a DataFrame con método nativo
    df = dataset.to_df()

    if df.empty:
        st.warning("⚠️ No se pudieron cargar eventos con datos de jugadores o equipos. Verificá que los archivos F7 y F24 correspondan al mismo partido.")
    else:
        # 🎛️ Filtros en barra lateral
        st.sidebar.header("Filtros")

        tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
        jugador = st.sidebar.selectbox("Jugador (player_id)", ['Todos'] + sorted(df['player_id'].dropna().unique()))
        equipo = st.sidebar.selectbox("Equipo (team_id)", ['Todos'] + sorted(df['team_id'].dropna().unique()))

        # Zona del campo (Opta: 0-100)
        st.sidebar.markdown("📍 Zona del campo")
        xmin = st.sidebar.slider("X min", 0.0, 100.0, 30.0)
        xmax = st.sidebar.slider("X max", 0.0, 100.0, 70.0)
        ymin = st.sidebar.slider("Y min", 0.0, 100.0, 20.0)
        ymax = st.sidebar.slider("Y max", 0.0, 100.0, 80.0)

        # Aplicar filtros
        filtered_df = df[df['event_type'] == tipo_evento]
        if jugador != 'Todos':
            filtered_df = filtered_df[filtered_df['player_id'] == jugador]
        if equipo != 'Todos':
            filtered_df = filtered_df[filtered_df['team_id'] == equipo]

        filtered_df = filtered_df[
            (filtered_df['coordinates_x'] >= xmin) & (filtered_df['coordinates_x'] <= xmax) &
            (filtered_df['coordinates_y'] >= ymin) & (filtered_df['coordinates_y'] <= ymax)
        ]

        # Mostrar resultados
        st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

        # Visualización
        pitch = Pitch(pitch_type='opta')
        fig, ax = pitch.draw(figsize=(10, 7))
        pitch.scatter(
            filtered_df['coordinates_x'],
            filtered_df['coordinates_y'],
            ax=ax,
            color='red',
            s=100,
            edgecolors='black'
        )
        st.pyplot(fig)

        # Tabla de resumen
        st.dataframe(
            filtered_df[['player_id', 'team_id']]
            .value_counts()
            .reset_index(name='Cantidad')
        )

