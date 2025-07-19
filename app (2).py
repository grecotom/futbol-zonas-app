import streamlit as st
from mplsoccer import Pitch
from streamlit_drawable_canvas import st_canvas
from kloppy import opta
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("⚽ Análisis de Eventos Opta (Zona seleccionable)")

f7_file = st.file_uploader("Subí archivo F7 (alineaciones - opta_f7.xml)", type="xml")
f24_file = st.file_uploader("Subí archivo F24 (eventos - opta_f24.xml)", type="xml")

if f7_file and f24_file:
    dataset = opta.load(
        f7_data=f7_file,
        f24_data=f24_file,
        coordinates="opta",
        event_types=["pass", "shot"]
    )
    df = dataset.to_df()

    # Mapeo de nombres
    player_id_map = {
        player.player_id: player.full_name
        for team in dataset.metadata.teams
        for player in team.players
    }
    team_id_map = {
        team.team_id: team.name
        for team in dataset.metadata.teams
    }
    df["player_name"] = df["player_id"].map(player_id_map)
    df["team_name"] = df["team_id"].map(team_id_map)

    st.sidebar.header("Filtros")
    tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
    jugador = st.sidebar.selectbox("Jugador", ['Todos'] + sorted(df['player_name'].dropna().unique()))
    equipo = st.sidebar.selectbox("Equipo", ['Todos'] + sorted(df['team_name'].dropna().unique()))

    # 📐 Selección de zona con canvas
    st.subheader("🖌️ Seleccioná una zona en el campo")

    pitch = Pitch(pitch_type='opta')
    fig, ax = pitch.draw(figsize=(6, 4))
    st.pyplot(fig)

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=1,
        background_color="#ffffff",
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="rect",
        key="canvas",
    )

    # Aplicar filtros
    filtered_df = df[df['event_type'] == tipo_evento]
    if jugador != 'Todos':
        filtered_df = filtered_df[filtered_df['player_name'] == jugador]
    if equipo != 'Todos':
        filtered_df = filtered_df[filtered_df['team_name'] == equipo]

    if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
        shape = canvas_result.json_data["objects"][0]
        left = shape["left"] / 6  # Normalizamos a escala 0-100
        top = shape["top"] / 4
        width = shape["width"] / 6
        height = shape["height"] / 4

        xmin = left
        xmax = left + width
        ymin = top
        ymax = top + height

        st.markdown(f"📍 Zona seleccionada: x[{xmin:.1f}-{xmax:.1f}] y[{ymin:.1f}-{ymax:.1f}]")

        filtered_df = filtered_df[
            (filtered_df['coordinates_x'] >= xmin) & (filtered_df['coordinates_x'] <= xmax) &
            (filtered_df['coordinates_y'] >= ymin) & (filtered_df['coordinates_y'] <= ymax)
        ]

    st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

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

    st.dataframe(filtered_df[['player_name', 'team_name']].value_counts().reset_index(name='Cantidad'))



