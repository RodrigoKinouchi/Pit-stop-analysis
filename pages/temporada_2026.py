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


def _ensure_tempo_parado_column(df: pd.DataFrame) -> pd.DataFrame:
    """Garante TempoParado_numeric (coluna oficial; notes só como legado)."""
    if df.empty or "TempoParado_numeric" in df.columns:
        return df
    out = df.copy()
    if "tempo_carro_parado_ms" in out.columns:
        out["TempoParado_numeric"] = _ms_to_sec_optional(out["tempo_carro_parado_ms"])
    else:
        out["TempoParado_numeric"] = float("nan")
    return out


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
    elif "santa cruz" in n:
        tid = 4  # fallback visual próximo (sem asset dedicado)
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
st.caption(f"Lendo SQLite: `{default_db_path()}`")

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
df_all = _ensure_tempo_parado_column(load_season_dataframe_2026())

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
    st.caption(
        "Métrica principal: **tempo carro parado**. "
        "Tempo total = PIT IN→OUT · Troca de pneus = pistola (secundário)."
    )

    # 1) Tempo carro parado (prioritário)
    min_par = df_plot["TempoParado_numeric"].min()
    max_par = df_plot["TempoParado_numeric"].max()
    y0p, y1p = (None, None)
    if pd.notna(min_par) and pd.notna(max_par):
        y0p, y1p = max(0, min_par - 0.5), max_par + 0.5

    fig_par = px.bar(
        df_plot,
        x="Piloto",
        y="TempoParado_numeric",
        title="Tempo carro parado (s)",
        labels={"TempoParado_numeric": "Segundos", "Piloto": "Piloto"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
        text="Pneu_Trocado",
    )
    fig_par.update_layout(title_x=0.4, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    if y0p is not None:
        fig_par.update_yaxes(range=[y0p, y1p])
    st.plotly_chart(fig_par, use_container_width=True)

    # 2) Tempo total
    min_t = df_plot["TempoTotal_numeric"].min()
    max_t = df_plot["TempoTotal_numeric"].max()
    y0t, y1t = (None, None)
    if pd.notna(min_t) and pd.notna(max_t):
        y0t, y1t = max(0, min_t - 0.5), max_t + 0.5

    fig2 = px.bar(
        df_plot,
        x="Piloto",
        y="TempoTotal_numeric",
        title="Tempo total (PIT IN → PIT OUT) (s)",
        labels={"TempoTotal_numeric": "Segundos", "Piloto": "Piloto"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
        text="Pneu_Trocado",
    )
    fig2.update_layout(title_x=0.4, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    if y0t is not None:
        fig2.update_yaxes(range=[y0t, y1t])
    st.plotly_chart(fig2, use_container_width=True)

    # 3) Troca de pneus (secundário)
    min_p = df_plot["Tempopneu_numeric"].min()
    max_p = df_plot["Tempopneu_numeric"].max()
    y0, y1 = (None, None)
    if pd.notna(min_p) and pd.notna(max_p):
        y0, y1 = max(0, min_p - 0.5), max_p + 0.5

    fig1 = px.bar(
        df_plot,
        x="Piloto",
        y="Tempopneu_numeric",
        title="Tempo troca de pneus (s) — secundário",
        labels={"Tempopneu_numeric": "Segundos", "Piloto": "Piloto"},
        color="Piloto",
        color_discrete_map=pilot_color_map,
        text="Pneu_Trocado",
    )
    fig1.update_layout(title_x=0.4, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    if y0 is not None:
        fig1.update_yaxes(range=[y0, y1])
    st.plotly_chart(fig1, use_container_width=True)

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
        y="TempoParado_numeric",
        title="Posição na corrida × tempo carro parado (s)",
        labels={"POS_num": "Posição", "TempoParado_numeric": "Tempo carro parado (s)"},
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
                    y="TempoParado_numeric",
                    title="Tempo carro parado",
                    labels={"TempoParado_numeric": "s"},
                    color="Piloto",
                    color_discrete_map=cor_m,
                ),
                "par",
            ),
            (
                px.bar(
                    df_m,
                    x="Piloto",
                    y="TempoTotal_numeric",
                    title="Tempo total (PIT IN→OUT)",
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
                    title="Troca de pneus (secundário)",
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
        st.caption(
            "Análise prioriza **tempo carro parado**. "
            "**Tempo do piloto** = tempo total − tempo carro parado (só quando o parado existe; "
            "não se usa mais troca de pneus como substituto). "
            "Com mais de um pit na mesma corrida, usa-se o de **menor tempo total**."
        )
        w = df_all.copy()
        w["Tempo_Driver_numeric"] = w["TempoTotal_numeric"] - w["TempoParado_numeric"]

        pilotos_selecionados = st.multiselect(
            "Selecione os pilotos:",
            sorted(get_drivers_names(2026).values()),
            default=[],
        )

        if not pilotos_selecionados:
            st.caption("Selecione um ou mais pilotos.")
        else:
            dados_pilotos: list = []
            for (stg, rt), dfr in w.groupby(["stage_number", "race_type"]):
                best_idx = dfr.groupby("pilot_name")["TempoTotal_numeric"].idxmin()
                d1 = dfr.loc[best_idx].copy()

                d1["Ranking_TempoParado"] = d1["TempoParado_numeric"].rank(
                    method="min", ascending=True
                )
                d1["Ranking_TempoTotal"] = d1["TempoTotal_numeric"].rank(method="min", ascending=True)
                d1["Ranking_Tempopneu"] = d1["Tempopneu_numeric"].rank(method="min", ascending=True)
                d1["Ranking_TempoDriver"] = d1["Tempo_Driver_numeric"].rank(method="min", ascending=True)

                min_parado = d1["TempoParado_numeric"].min()
                min_total = d1["TempoTotal_numeric"].min()
                min_pneu = d1["Tempopneu_numeric"].min()
                min_driver = d1["Tempo_Driver_numeric"].min()

                nome_corrida = f"E{int(stg)} {rt}"
                sort_key = int(stg) * 10 + (1 if rt == "Principal" else 0)

                df_sel = d1[d1["pilot_name"].isin(pilotos_selecionados)]
                for _, row in df_sel.iterrows():
                    piloto = row["pilot_name"]
                    par_val = row["TempoParado_numeric"]
                    delt_par = float("nan")
                    if pd.notna(par_val) and pd.notna(min_parado):
                        delt_par = float(par_val - min_parado)
                    pneu_val = row["Tempopneu_numeric"]
                    delt_pneu = float("nan")
                    if pd.notna(pneu_val) and pd.notna(min_pneu):
                        delt_pneu = float(pneu_val - min_pneu)
                    drv_val = row["Tempo_Driver_numeric"]
                    delt_drv = float("nan")
                    if pd.notna(drv_val) and pd.notna(min_driver):
                        delt_drv = float(drv_val - min_driver)

                    dados_pilotos.append(
                        {
                            "Corrida": nome_corrida,
                            "sort_key": sort_key,
                            "Piloto": piloto,
                            "deltatempoparado": delt_par,
                            "Ranking_TempoParado": float(row["Ranking_TempoParado"])
                            if pd.notna(row["Ranking_TempoParado"])
                            else float("nan"),
                            "deltatempototal": float(row["TempoTotal_numeric"] - min_total),
                            "Ranking_TempoTotal": float(row["Ranking_TempoTotal"]),
                            "deltatempopneu": delt_pneu,
                            "Ranking_Tempopneu": float(row["Ranking_Tempopneu"])
                            if pd.notna(row["Ranking_Tempopneu"])
                            else float("nan"),
                            "deltatempodriver": delt_drv,
                            "Tempo_Driver": float(drv_val) if pd.notna(drv_val) else float("nan"),
                            "Ranking_TempoDriver": float(row["Ranking_TempoDriver"])
                            if pd.notna(row["Ranking_TempoDriver"])
                            else float("nan"),
                        }
                    )

            if not dados_pilotos:
                st.info("Nenhum dado para os pilotos selecionados nas corridas disponíveis.")
            else:
                df_pt = pd.DataFrame(dados_pilotos)
                df_pt.sort_values("sort_key", inplace=True)
                ordem_corrida = (
                    df_pt[["sort_key", "Corrida"]].drop_duplicates().sort_values("sort_key")["Corrida"].tolist()
                )

                df_par_plot = df_pt.dropna(subset=["deltatempoparado"])
                if not df_par_plot.empty:
                    fig_par = px.line(
                        df_par_plot,
                        x="Corrida",
                        y="deltatempoparado",
                        color="Piloto",
                        title="Δ tempo carro parado vs mais rápido (métrica principal)",
                        labels={"Corrida": "Corrida", "deltatempoparado": "Diferença (s)"},
                        markers=True,
                        category_orders={"Corrida": ordem_corrida},
                    )
                    fig_par.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_x=0.5
                    )
                    st.plotly_chart(fig_par, use_container_width=True)
                else:
                    st.warning("Sem tempos de carro parado válidos para o gráfico principal.")

                fig_total = px.line(
                    df_pt,
                    x="Corrida",
                    y="deltatempototal",
                    color="Piloto",
                    title="Δ tempo total (PIT IN→OUT) vs mais rápido",
                    labels={"Corrida": "Corrida", "deltatempototal": "Diferença (s)"},
                    markers=True,
                    category_orders={"Corrida": ordem_corrida},
                )
                fig_total.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_x=0.5
                )
                st.plotly_chart(fig_total, use_container_width=True)

                df_pneu_plot = df_pt.dropna(subset=["deltatempopneu"])
                if not df_pneu_plot.empty:
                    fig_pneu = px.line(
                        df_pneu_plot,
                        x="Corrida",
                        y="deltatempopneu",
                        color="Piloto",
                        title="Δ tempo troca de pneus vs mais rápido (secundário)",
                        labels={"Corrida": "Corrida", "deltatempopneu": "Diferença (s)"},
                        markers=True,
                        category_orders={"Corrida": ordem_corrida},
                    )
                    fig_pneu.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_x=0.5
                    )
                    st.plotly_chart(fig_pneu, use_container_width=True)

                df_drv_plot = df_pt.dropna(subset=["deltatempodriver"])
                if not df_drv_plot.empty:
                    fig_driver = px.line(
                        df_drv_plot,
                        x="Corrida",
                        y="deltatempodriver",
                        color="Piloto",
                        title="Δ tempo do piloto (total − parado) vs mais rápido",
                        labels={"Corrida": "Corrida", "deltatempodriver": "Diferença (s)"},
                        markers=True,
                        category_orders={"Corrida": ordem_corrida},
                    )
                    fig_driver.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_x=0.5
                    )
                    st.plotly_chart(fig_driver, use_container_width=True)

                df_pilotos_display = df_pt[
                    [
                        "Corrida",
                        "Piloto",
                        "Ranking_TempoParado",
                        "Ranking_TempoTotal",
                        "Ranking_Tempopneu",
                        "Ranking_TempoDriver",
                        "Tempo_Driver",
                    ]
                ].copy()
                df_pilotos_display["Tempo_Driver"] = df_pilotos_display["Tempo_Driver"].round(3)

                colunas = st.columns(2)
                for idx, piloto in enumerate(pilotos_selecionados):
                    df_piloto = df_pilotos_display[df_pilotos_display["Piloto"] == piloto]
                    if not df_piloto.empty:
                        with colunas[idx % 2]:
                            st.subheader(piloto)
                            st.dataframe(df_piloto, use_container_width=True)

                media_rankings = (
                    df_pt.groupby("Piloto")[
                        [
                            "Ranking_TempoParado",
                            "Ranking_TempoTotal",
                            "Ranking_Tempopneu",
                            "Ranking_TempoDriver",
                        ]
                    ]
                    .mean(numeric_only=True)
                    .reset_index()
                )
                media_rankings.rename(
                    columns={
                        "Ranking_TempoParado": "Média ranking carro parado",
                        "Ranking_TempoTotal": "Média ranking tempo total",
                        "Ranking_Tempopneu": "Média ranking troca pneus",
                        "Ranking_TempoDriver": "Média ranking tempo piloto",
                    },
                    inplace=True,
                )
                st.subheader("Média dos rankings dos pilotos selecionados")
                _mr = media_rankings.copy()
                _cols_med = (
                    "Média ranking carro parado",
                    "Média ranking tempo total",
                    "Média ranking troca pneus",
                    "Média ranking tempo piloto",
                )
                for _c in _cols_med:
                    _mr[_c] = pd.to_numeric(_mr[_c], errors="coerce").round(1)
                st.dataframe(
                    _mr,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Piloto": st.column_config.TextColumn("Piloto", alignment="center"),
                        **{
                            c: st.column_config.NumberColumn(c, format="%.1f", alignment="center")
                            for c in _cols_med
                        },
                    },
                )

with tabs[3]:
    if df_all.empty or len(df_all) < 2:
        st.info("Inclua pits de mais carros/corridas para comparar equipes (box plot precisa de volume).")
    else:
        st.caption(
            "Performance da **equipe** (métrica principal): em cada corrida usa-se o "
            "**tempo carro parado**. Δ = parado do carro − melhor parado da corrida. "
            "O tempo total (PIT IN→OUT) inclui o piloto e não entra aqui. "
            "O segundo gráfico (secundário) usa **troca de pneus comparável**: "
            "com 4 pneus, soma só os **2 mais rápidos** (evita comparação injusta vs 2 pneus)."
        )
        _excluir_equipes = {"RTR SG28 TEAM"}
        _eq = df_all[~df_all["team_name"].isin(_excluir_equipes)].copy()
        team_colors = (
            _eq.drop_duplicates(subset=["team_name"])
            .set_index("team_name")["team_color_hex"]
            .to_dict()
        )
        _pneu_col = (
            "TempopneuCmp_numeric"
            if "TempopneuCmp_numeric" in df_all.columns
            else "Tempopneu_numeric"
        )
        # Melhor da corrida considera o grid inteiro; só a exibição omite equipes excluídas.
        _per_race = df_all.groupby(["stage_number", "race_type"], as_index=False).agg(
            melhor_parado=("TempoParado_numeric", "min"),
            melhor_pneu=(_pneu_col, "min"),
        )
        _deltas = _eq.merge(_per_race, on=["stage_number", "race_type"], how="left")
        _deltas["delta_parado_s"] = _deltas["TempoParado_numeric"] - _deltas["melhor_parado"]
        _deltas["delta_pneu_s"] = _deltas[_pneu_col] - _deltas["melhor_pneu"]

        df_delta_parado = _deltas.dropna(subset=["delta_parado_s"])
        df_delta_pneu = _deltas.dropna(subset=["delta_pneu_s"])

        if len(df_delta_parado) < 2:
            st.warning(
                "Dados insuficientes para o boxplot de tempo carro parado. "
                "Grave pits com `tempo_carro_parado` no CSV (importação etapa)."
            )
        else:
            figb = px.box(
                df_delta_parado,
                x="team_name",
                y="delta_parado_s",
                color="team_name",
                color_discrete_map=team_colors,
                title="Δ tempo carro parado vs melhor da corrida — por equipe (2026)",
                labels={"team_name": "Equipe", "delta_parado_s": "Δ vs melhor (s)"},
            )
            figb.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(figb, use_container_width=True)

        if len(df_delta_pneu) < 2:
            st.warning(
                "Dados insuficientes para o boxplot de troca de pneus (delta). "
                "Corridas só com troca de pneus NR/vazia não entram."
            )
        else:
            figbp = px.box(
                df_delta_pneu,
                x="team_name",
                y="delta_pneu_s",
                color="team_name",
                color_discrete_map=team_colors,
                title="Δ troca de pneus (2 mais rápidos se 4P) — por equipe (secundário)",
                labels={"team_name": "Equipe", "delta_pneu_s": "Δ vs melhor (s)"},
            )
            figbp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(figbp, use_container_width=True)
