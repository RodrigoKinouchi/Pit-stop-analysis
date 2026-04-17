"""
Temporada 2026 — visualização a partir do SQLite (pit_stop_2026.db).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

from utils.constants import (
    AMATTHEIS_LOGO,
    AMATTHEIS_NEUTRAL_COLOR,
    CAR_IMAGE,
    DEFAULT_TRACK_IMAGE,
    get_drivers_names,
    track_images,
)
from utils.db_2026 import (
    _ms_to_sec_optional,
    default_db_path,
    ensure_db_ready,
    fetch_calendar,
    load_race_dataframe,
    load_season_dataframe_2026,
)


def _format_stage_option(row: sqlite3.Row) -> str:
    d = row["event_date"]
    try:
        dt = datetime.fromisoformat(d)
        d_br = dt.strftime("%d/%m/%Y")
    except ValueError:
        d_br = d
    return f"Etapa {row['stage_number']} — {row['circuit_name']} ({d_br})"


def _track_image_for_circuit(circuit_name: str) -> str:
    n = (circuit_name or "").lower()
    tid = None
    if "interlagos" in n:
        tid = 3
    elif "zilmar" in n or "cascavel" in n:
        tid = 4
    elif "velopark" in n or "nova santa rita" in n:
        tid = 8
    elif "velocitta" in n or "mogi" in n:
        tid = 2
    elif "cristais" in n or "curvelo" in n:
        tid = 9
    elif "cuiabá" in n or "cuiaba" in n or "mato grosso" in n:
        tid = 11
    elif "goiânia" in n or "goiania" in n or "ayrton senna" in n:
        tid = 1
    elif "chapecó" in n or "chapeco" in n:
        tid = 4
    elif "brasília" in n or "brasilia" in n or "nelson piquet" in n:
        tid = 12
    if tid is not None and tid in track_images:
        p = track_images[tid]
        if os.path.exists(p):
            return p
    return DEFAULT_TRACK_IMAGE


def _pilot_color_map(df: pd.DataFrame, by_team: bool) -> dict:
    m = {}
    for _, r in df.iterrows():
        p = r["Piloto"]
        if by_team:
            m[p] = r["team_color_hex"]
        else:
            m[p] = r["amattheis_color_hex"] or AMATTHEIS_NEUTRAL_COLOR
    return m


st.set_page_config(
    page_title="Temporada 2026 — Pit Stop",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    import base64

    if os.path.exists(CAR_IMAGE):
        with open(CAR_IMAGE, "rb") as img_file:
            car_b64 = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
        <style>
            .car-background-26 {{
                position: fixed; bottom: 0; right: 0; width: 400px; height: 250px;
                opacity: 0.2; z-index: -1; pointer-events: none;
                background-image: url('data:image/png;base64,{car_b64}');
                background-size: contain; background-repeat: no-repeat;
                background-position: bottom right;
            }}
        </style>
        <div class="car-background-26"></div>
        """,
            unsafe_allow_html=True,
        )
except Exception:
    pass

try:
    st.image(Image.open(AMATTHEIS_LOGO), use_container_width=True)
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)
st.title("🏁 Temporada 2026")
st.caption(
    f"Lendo SQLite: `{default_db_path()}`. "
    "Na Streamlit Cloud, gravar só em disco sem commit do `.db` perde dados no redeploy — "
    "veja o expander **Persistência** na página Entrada 2026."
)

ensure_db_ready()
cal_rows = fetch_calendar()
if not cal_rows:
    st.error("Calendário 2026 vazio. Execute `python -m utils.db_2026`.")
    st.stop()

color_mode = st.radio(
    "Padrão de cores dos pilotos:",
    ("Equipes", "Padrão Amattheis"),
    index=0,
    horizontal=True,
)
by_team = color_mode == "Equipes"

stage_labels = [_format_stage_option(r) for r in cal_rows]
idx = st.selectbox("Etapa", range(len(cal_rows)), format_func=lambda i: stage_labels[i])
stage_number = int(cal_rows[idx]["stage_number"])
circuit_name = str(cal_rows[idx]["circuit_name"])

race_type = st.selectbox("Corrida", ["Sprint", "Principal"])

img_path = _track_image_for_circuit(circuit_name)
try:
    st.image(Image.open(img_path), width=180)
except Exception:
    pass

df = load_race_dataframe(stage_number, race_type)
df_all = load_season_dataframe_2026()

if df.empty:
    st.info(
        "Nenhum pit stop gravado para esta etapa e tipo de corrida. "
        "Use a página **Entrada de dados 2026** para incluir registros."
    )
    st.stop()

pilot_color_map = _pilot_color_map(df, by_team)

if race_type == "Sprint":
    df["Pneu_Trocado"] = df["Pneu1"]
else:
    df["Pneu_Trocado"] = df[["Pneu1", "Pneu2"]].agg(lambda x: ", ".join(x.dropna().astype(str)), axis=1)

df_plot = df.copy()
df_plot["POS_numeric"] = pd.to_numeric(df_plot["POS"], errors="coerce")
df_plot = df_plot.sort_values("POS_numeric", na_position="last")

st.subheader(f"Dados: Etapa {stage_number} — {race_type} — {circuit_name}")

tabs = st.tabs(["Overview", "Amattheis", "Análise pilotos (ano)", "Análise equipes (ano)"])

with tabs[0]:
    min_p = df_plot["Tempopneu_numeric"].min()
    max_p = df_plot["Tempopneu_numeric"].max()
    y0, y1 = (None, None)
    if pd.notna(min_p) and pd.notna(max_p):
        y0, y1 = max(0, min_p - 0.5), max_p + 0.5

    fig1 = px.bar(
        df_plot,
        x="Piloto",
        y="Tempopneu_numeric",
        title="Tempo de troca de pneus (s)",
        labels={"Tempopneu_numeric": "Segundos", "Piloto": "Piloto"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
        text="Pneu_Trocado",
    )
    fig1.update_layout(title_x=0.4, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    if y0 is not None:
        fig1.update_yaxes(range=[y0, y1])
    st.plotly_chart(fig1, use_container_width=True)

    min_t = df_plot["TempoTotal_numeric"].min()
    max_t = df_plot["TempoTotal_numeric"].max()
    y0t, y1t = (None, None)
    if pd.notna(min_t) and pd.notna(max_t):
        y0t, y1t = max(0, min_t - 0.5), max_t + 0.5

    fig2 = px.bar(
        df_plot,
        x="Piloto",
        y="TempoTotal_numeric",
        title="Tempo total de pit (s)",
        labels={"TempoTotal_numeric": "Segundos", "Piloto": "Piloto"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
        text="Pneu_Trocado",
    )
    fig2.update_layout(title_x=0.4, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    if y0t is not None:
        fig2.update_yaxes(range=[y0t, y1t])
    st.plotly_chart(fig2, use_container_width=True)

    if race_type == "Sprint":
        pneu_counts = df["Pneu1"].value_counts()
        pneu_stats = {
            "TD": int(pneu_counts.get("TD", 0)),
            "TE": int(pneu_counts.get("TE", 0)),
            "DD": int(pneu_counts.get("DD", 0)),
            "DE": int(pneu_counts.get("DE", 0)),
            "ALL": int((df["Pneu1"] == "ALL").sum()),
        }
        labels = [k for k, v in pneu_stats.items() if v > 0]
        values = [pneu_stats[k] for k in labels]
        if labels:
            st.plotly_chart(
                px.pie(values=values, names=labels, title="Distribuição Pneu 1 — Sprint", hole=0.3),
                use_container_width=True,
            )
    else:
        combinacoes = {
            "TD & TE": df[((df["Pneu1"] == "TD") & (df["Pneu2"] == "TE")) | ((df["Pneu1"] == "TE") & (df["Pneu2"] == "TD"))],
            "TD & DD": df[((df["Pneu1"] == "TD") & (df["Pneu2"] == "DD")) | ((df["Pneu1"] == "DD") & (df["Pneu2"] == "TD"))],
            "TD & DE": df[((df["Pneu1"] == "TD") & (df["Pneu2"] == "DE")) | ((df["Pneu1"] == "DE") & (df["Pneu2"] == "TD"))],
            "DD & DE": df[((df["Pneu1"] == "DD") & (df["Pneu2"] == "DE")) | ((df["Pneu1"] == "DE") & (df["Pneu2"] == "DD"))],
            "DD & TE": df[((df["Pneu1"] == "DD") & (df["Pneu2"] == "TE")) | ((df["Pneu1"] == "TE") & (df["Pneu2"] == "DD"))],
            "TE & DE": df[((df["Pneu1"] == "TE") & (df["Pneu2"] == "DE")) | ((df["Pneu1"] == "DE") & (df["Pneu2"] == "TE"))],
        }
        combinacoes["ALL"] = df[df["Pneu1"] == "ALL"]
        cl, cv = [], []
        for nome, sub in combinacoes.items():
            c = len(sub)
            if c > 0:
                cl.append(nome)
                cv.append(c)
        if cl:
            st.plotly_chart(
                px.pie(values=cv, names=cl, title="Combinações de pneus — Principal", hole=0.3),
                use_container_width=True,
            )

    pos_num = pd.to_numeric(df["POS"], errors="coerce")
    sc = px.scatter(
        df.assign(POS_num=pos_num),
        x="POS_num",
        y="TempoTotal_numeric",
        title="Posição na corrida × tempo total (s)",
        labels={"POS_num": "Posição", "TempoTotal_numeric": "Tempo total (s)"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
    )
    sc.update_traces(marker=dict(size=12))
    sc.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(sc, use_container_width=True)

    sc2 = px.scatter(
        df.assign(POS_num=pos_num),
        x="POS_num",
        y="pitlap",
        title="Posição × volta do pit",
        labels={"POS_num": "Posição", "pitlap": "Volta do pit"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
    )
    sc2.update_traces(marker=dict(size=12))
    sc2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(sc2, use_container_width=True)

with tabs[1]:
    df_m = df[df["detail_level"] == "amattheis_extended"].copy()
    if df_m.empty:
        st.info(
            "Não há registros com detalhamento Amattheis nesta corrida. "
            "Grave pits dos carros do programa (métricas estendidas) em **Entrada 2026**."
        )
    else:
        cor_m = _pilot_color_map(df_m, by_team=False)
        df_m["aj"] = _ms_to_sec_optional(df_m["tempo_reacao_air_jack_ms"])
        df_m["1c"] = _ms_to_sec_optional(df_m["tempo_primeira_conexao_ms"])
        df_m["Troca1"] = _ms_to_sec_optional(df_m["tempo_troca1_ms"])
        df_m["Troca2"] = _ms_to_sec_optional(df_m["tempo_troca2_ms"])
        if race_type == "Sprint":
            df_m["TempoDeslocamento"] = df_m["Tempopneu_numeric"] - df_m["Troca1"]
        else:
            df_m["TempoDeslocamento"] = df_m["Tempopneu_numeric"] - (
                df_m["Troca1"].fillna(0) + df_m["Troca2"].fillna(0)
            )

        charts = [
            (
                px.bar(
                    df_m,
                    x="Piloto",
                    y="TempoTotal_numeric",
                    title="Tempo total",
                    labels={"TempoTotal_numeric": "s"},
                    color="Piloto",
                    color_discrete_map=cor_m,
                ),
                "tt",
            ),
            (
                px.bar(
                    df_m,
                    x="Piloto",
                    y="Tempopneu_numeric",
                    title="Troca de pneus",
                    labels={"Tempopneu_numeric": "s"},
                    color="Piloto",
                    color_discrete_map=cor_m,
                ),
                "tp",
            ),
            (
                px.bar(df_m, x="Piloto", y="aj", title="Reação Air Jack", color="Piloto", color_discrete_map=cor_m),
                "aj",
            ),
            (
                px.bar(df_m, x="Piloto", y="1c", title="1ª conexão", color="Piloto", color_discrete_map=cor_m),
                "1c",
            ),
            (
                px.bar(df_m, x="Piloto", y="Troca1", title="Troca 1", color="Piloto", color_discrete_map=cor_m),
                "t1",
            ),
        ]
        if race_type == "Principal":
            charts.append(
                (
                    px.bar(
                        df_m,
                        x="Piloto",
                        y="Troca2",
                        title="Troca 2",
                        color="Piloto",
                        color_discrete_map=cor_m,
                    ),
                    "t2",
                )
            )
        charts.append(
            (
                px.bar(
                    df_m,
                    x="Piloto",
                    y="TempoDeslocamento",
                    title="Deslocamento (troca pneus − soma trocas pistola)",
                    color="Piloto",
                    color_discrete_map=cor_m,
                ),
                "des",
            )
        )

        for i in range(0, len(charts), 2):
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(charts[i][0], use_container_width=True)
            if i + 1 < len(charts):
                with c2:
                    st.plotly_chart(charts[i + 1][0], use_container_width=True)

        st.markdown("#### Vídeos")
        any_link = False
        for _, row in df_m.iterrows():
            link = row.get("video_link")
            if pd.notna(link) and str(link).strip():
                any_link = True
                st.markdown(f"**{row['Piloto']}** — [YouTube]({link})")
        if not any_link:
            st.caption("Nenhum link cadastrado para estes registros.")

with tabs[2]:
    if df_all.empty:
        st.warning("Sem dados no SQLite para 2026.")
    else:
        names = list(get_drivers_names(2026).values())
        pick = st.multiselect("Pilotos", sorted(names), default=[])
        if pick:
            sub = df_all[df_all["pilot_name"].isin(pick)].copy()
            sub["Etapa_corrida"] = (
                "E" + sub["stage_number"].astype(str) + " " + sub["race_type"].astype(str)
            )
            st.dataframe(
                sub[
                    [
                        "Etapa_corrida",
                        "pilot_name",
                        "team_name",
                        "pit_lap",
                        "race_position",
                        "Tempopneu_numeric",
                        "TempoTotal_numeric",
                    ]
                ].rename(
                    columns={
                        "pilot_name": "Piloto",
                        "team_name": "Equipe",
                        "pit_lap": "Volta pit",
                        "race_position": "Pos",
                        "Tempopneu_numeric": "Troca pneu (s)",
                        "TempoTotal_numeric": "Total (s)",
                    }
                ),
                use_container_width=True,
            )
            figp = px.bar(
                sub,
                x="Etapa_corrida",
                y="TempoTotal_numeric",
                color="pilot_name",
                barmode="group",
                title="Tempo total por corrida (selecionados)",
            )
            st.plotly_chart(figp, use_container_width=True)
        else:
            st.caption("Selecione um ou mais pilotos.")

with tabs[3]:
    if df_all.empty or len(df_all) < 2:
        st.info("Inclua pits de mais carros/corridas para comparar equipes (box plot precisa de volume).")
    else:
        team_colors = {t: h for t, h in zip(df_all["team_name"], df_all["team_color_hex"])}
        figb = px.box(
            df_all,
            x="team_name",
            y="TempoTotal_numeric",
            color="team_name",
            color_discrete_map=team_colors,
            title="Tempo total de pit por equipe — todas as entradas 2026",
            labels={"team_name": "Equipe", "TempoTotal_numeric": "s"},
        )
        figb.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(figb, use_container_width=True)

        figbp = px.box(
            df_all,
            x="team_name",
            y="Tempopneu_numeric",
            color="team_name",
            color_discrete_map=team_colors,
            title="Troca de pneus por equipe — todas as entradas 2026",
            labels={"team_name": "Equipe", "Tempopneu_numeric": "s"},
        )
        figbp.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(figbp, use_container_width=True)
