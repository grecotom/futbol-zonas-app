import streamlit as st
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from kloppy import load_wyscout_event_data
import pandas as pd
import io
import json

st.set_page_config(layout="wide")
st.title("⚽ Análisis de Acciones por Zona y Filtros - Wyscout")

uploaded_file = st.file_uploader("Subí el archivo JSON de eventos Wyscout", type="json")

if uploaded_file:
    file_text = uploaded_file.read().decode("utf-8")
    file_io = io.StringIO(file_text)
    dataset = load_wyscout_event_data(event_data=uploaded_file)
    
    # ... el resto del código igual ...

    # Convertir eventos a DataFrame
    df = pd.DataFrame([{
        "x": e.coordinates.x if e.coordinates else None,
        "y": e.coordinates.y if e.coordinates else None,
        "event_type": e.event_type.value,
        "player": e.player.name if e.player else None,
        "team": e.team.name if e.team else None,
        "period": e.period.value if e.period else None,
        "timestamp": e.timestamp.total_seconds() if e.timestamp else None,
        "minute": int(e.timestamp.total_seconds() // 60) if e.timestamp else None,
        "match_id": dataset.metadata.match_id if dataset.metadata else "Desconocido",
    } for e in dataset.events if e.coordinates])

    # ----- FILTROS SIDEBAR -----
    st.sidebar.header("🎛️ Filtros")

    # Filtro por tipo de evento
    event_type = st.sidebar.selectbox("Tipo de evento", sorted(df['event_type'].dropna().unique()))

    # Filtro por equipo
    teams = df['team'].dropna().unique().tolist()
    team_selected = st.sidebar.selectbox("Equipo", ['Todos'] + teams)

    # Filtro por jugador
    players = df['player'].dropna().unique().tolist()
    player_selected = st.sidebar.selectbox("Jugador", ['Todos'] + players)

    # Filtro por minuto del partido
    min_minute, max_minute = int(df['minute'].min()), int(df['minute'].max())
    min_sel, max_sel = st.sidebar.slider("Minutos", min_value=min_minute, max_value=max_minute,
                                         value=(min_minute, max_minute))

    # Filtro por zona del campo
    st.sidebar.markdown("📍 Zona del campo (coordenadas Wyscout 0-100)")
    xmin = st.sidebar.slider("X min", 0, 100, 30)
    xmax = st.sidebar.slider("X max", 0, 100, 70)
    ymin = st.sidebar.slider("Y min", 0, 100, 20)
    ymax = st.sidebar.slider("Y max", 0, 100, 80)

    # ----- APLICAR FILTROS -----
    filtered_df = df[df['event_type'] == event_type]
    if team_selected != 'Todos':
        filtered_df = filtered_df[filtered_df['team'] == team_selected]
    if player_selected != 'Todos':
        filtered_df = filtered_df[filtered_df['player'] == player_selected]

    filtered_df = filtered_df[
        (filtered_df['x'] >= xmin) & (filtered_df['x'] <= xmax) &
        (filtered_df['y'] >= ymin) & (filtered_df['y'] <= ymax) &
        (filtered_df['minute'] >= min_sel) & (filtered_df['minute'] <= max_sel)
    ]

    st.subheader(f"📊 Eventos encontrados: {len(filtered_df)}")

    # ----- VISUALIZACIÓN -----
    col1, col2 = st.columns([2, 1])

    with col1:
        pitch = Pitch(pitch_type='wyscout')
        fig, ax = pitch.draw(figsize=(10, 7))
        pitch.scatter(filtered_df['x'], filtered_df['y'], ax=ax, color='red', s=100, edgecolors='black')
        st.pyplot(fig)

    with col2:
        st.dataframe(filtered_df[['player', 'team', 'minute']].value_counts().reset_index(name='cantidad'))
