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
                )
                df = dataset.to_df()
                df["match_id"] = nombre_base

                # 🔄 Mapear player_id → player_name y team_id → team_name
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

                dataframes.append(df)
            except Exception as e:
                st.error(f"❌ Error cargando partido '{nombre_base}': {e}")
        else:
            st.warning(f"⚠️ No se encontró archivo F24 para '{nombre_base}'")

if dataframes:
    df = pd.concat(dataframes, ignore_index=True)

    # 🎛️ Filtros
    st.sidebar.header("Filtros")
    tipo_evento = st.sidebar.selectbox("Tipo de evento", df['event_type'].unique())
    partidos = st.sidebar.multiselect("Partido(s)", df['match_id'].unique(), default=df['match_id'].unique())
    jugadores = ['Todos'] + sorted(df['player_name'].dropna().unique())
    jugador = st.sidebar.selectbox("Jugador", jugadores)
    equipos = ['Todos'] + sorted(df['team_name'].dropna().unique())
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
        filtered_df = filtered_df[filtered_df['player_name'] == jugador]
    if equipo != 'Todos':
        filtered_df = filtered_df[filtered_df['team_name'] == equipo]

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
        filtered_df[['player_name', 'team_name']]
        .value_counts()
        .reset_index(name='Cantidad')
        .rename(columns={'player_name': 'Jugador', 'team_name': 'Equipo'})
    )
else:
    if f7_files and f24_files:
        st.warning("⚠️ No se pudieron emparejar archivos F7 y F24 correctamente.")


    # 🔁 Análisis de secuencias
    st.markdown("---")
    if st.checkbox("🔁 Mostrar análisis de secuencias"):
        st.subheader("📈 Secuencias: Recepción + Pase siguiente")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("📍 Zona de recepción (del pase 1)")
            rx_min = st.slider("Rec X min", 0, 100, 30, key="rx_min")
            rx_max = st.slider("Rec X max", 0, 100, 70, key="rx_max")
            ry_min = st.slider("Rec Y min", 0, 100, 30, key="ry_min")
            ry_max = st.slider("Rec Y max", 0, 100, 70, key="ry_max")
        with col2:
            st.markdown("🎯 Zona del siguiente pase (inicio → fin)")
            px_min = st.slider("Pase X min", 0, 100, 30, key="px_min")
            px_max = st.slider("Pase X max", 0, 100, 70, key="px_max")
            py_min = st.slider("Pase Y min", 0, 100, 30, key="py_min")
            py_max = st.slider("Pase Y max", 0, 100, 70, key="py_max")

        # Solo eventos tipo pase
        pases = df[df['event_type'] == 'PASS'].copy()

        # Ordenar por timestamp
        pases = pases.sort_values(by='timestamp')

        # Paso 1: crear un DataFrame con los pases recibidos
        pases_recibidos = pases.rename(columns={
            'receiver_player_id': 'player_id',
            'end_coordinates_x': 'rec_x',
            'end_coordinates_y': 'rec_y',
            'team_name': 'receiver_team',
            'player_name': 'receiver_name',
            'timestamp': 'rec_timestamp'
        })[['player_id', 'rec_x', 'rec_y', 'rec_timestamp', 'receiver_team', 'receiver_name']]

        # Paso 2: merge con el siguiente evento del mismo jugador
        merged = pd.merge_asof(
            pases_recibidos.sort_values("rec_timestamp"),
            pases.sort_values("timestamp"),
            by="player_id",
            left_on="rec_timestamp",
            right_on="timestamp",
            direction="forward",
            tolerance=pd.Timedelta("20s")  # por si hay separación mínima de segundos
        )

        # Filtro de zona de recepción
        cond_recepcion = (
            (merged['rec_x'] >= rx_min) & (merged['rec_x'] <= rx_max) &
            (merged['rec_y'] >= ry_min) & (merged['rec_y'] <= ry_max)
        )

        # Filtro zona del siguiente pase
        cond_pase = (
            (merged['coordinates_x'] >= px_min) & (merged['coordinates_x'] <= px_max) &
            (merged['coordinates_y'] >= py_min) & (merged['coordinates_y'] <= py_max)
        )

        secuencias = merged[cond_recepcion & cond_pase]

        # Resultado: tabla con recuento
        st.success(f"🔎 Se encontraron {len(secuencias)} secuencias que cumplen con las condiciones.")
        st.dataframe(
            secuencias.groupby(['receiver_name', 'receiver_team'])
            .size()
            .reset_index(name='Cantidad')
            .rename(columns={'receiver_name': 'Jugador', 'receiver_team': 'Equipo'})
            .sort_values(by='Cantidad', ascending=False)
        )





