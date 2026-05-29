"""
Temporada 2026 — visualização a partir do SQLite (pit_stop_2026.db).
"""

from __future__ import annotations

import os
import re
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


_PARADO_NOTES_RE = re.compile(r"troca_parado\s*=\s*([\d,\.]+)", re.I)


def _parado_sec_from_notes(notes: object) -> float:
    """Extrai segundos de `troca_parado=` nas notas (import CSV etapa)."""
    if notes is None or (isinstance(notes, float) and pd.isna(notes)):
        return float("nan")
    m = _PARADO_NOTES_RE.search(str(notes))
    if not m:
        return float("nan")
    return float(m.group(1).replace(",", "."))


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
        st.caption(
            "**Tempo do piloto** = tempo total − **tempo parado** (`troca_parado=` nas notas, quando existir). "
            "Se não houver parado registrado, usa-se **total − troca de pneus** (mesma ideia da temporada 2024). "
            "Com mais de um pit na mesma corrida, usa-se o de **menor tempo total**."
        )
        w = df_all.copy()
        w["troca_parado_s"] = w["notes"].map(_parado_sec_from_notes)
        parado_ok = w["troca_parado_s"].notna()
        w["Tempo_Driver_numeric"] = w["TempoTotal_numeric"] - w["troca_parado_s"].where(
            parado_ok, w["Tempopneu_numeric"]
        )

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

                d1["Ranking_TempoTotal"] = d1["TempoTotal_numeric"].rank(method="min", ascending=True)
                d1["Ranking_Tempopneu"] = d1["Tempopneu_numeric"].rank(method="min", ascending=True)
                d1["Ranking_TempoDriver"] = d1["Tempo_Driver_numeric"].rank(method="min", ascending=True)

                min_total = d1["TempoTotal_numeric"].min()
                min_pneu = d1["Tempopneu_numeric"].min()
                min_driver = d1["Tempo_Driver_numeric"].min()

                nome_corrida = f"E{int(stg)} {rt}"
                sort_key = int(stg) * 10 + (1 if rt == "Principal" else 0)

                df_sel = d1[d1["pilot_name"].isin(pilotos_selecionados)]
                for _, row in df_sel.iterrows():
                    piloto = row["pilot_name"]
                    pneu_val = row["Tempopneu_numeric"]
                    delt_pneu = float("nan")
                    if pd.notna(pneu_val) and pd.notna(min_pneu):
                        delt_pneu = float(pneu_val - min_pneu)

                    dados_pilotos.append(
                        {
                            "Corrida": nome_corrida,
                            "sort_key": sort_key,
                            "Piloto": piloto,
                            "deltatempototal": float(row["TempoTotal_numeric"] - min_total),
                            "Ranking_TempoTotal": float(row["Ranking_TempoTotal"]),
                            "deltatempopneu": delt_pneu,
                            "Ranking_Tempopneu": float(row["Ranking_Tempopneu"])
                            if pd.notna(row["Ranking_Tempopneu"])
                            else float("nan"),
                            "deltatempodriver": float(row["Tempo_Driver_numeric"] - min_driver),
                            "Tempo_Driver": float(row["Tempo_Driver_numeric"]),
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

                fig_total = px.line(
                    df_pt,
                    x="Corrida",
                    y="deltatempototal",
                    color="Piloto",
                    title="Diferença do tempo total em relação ao mais rápido",
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
                        title="Diferença do tempo de troca de pneus em relação ao mais rápido",
                        labels={"Corrida": "Corrida", "deltatempopneu": "Diferença (s)"},
                        markers=True,
                        category_orders={"Corrida": ordem_corrida},
                    )
                    fig_pneu.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", title_x=0.5
                    )
                    st.plotly_chart(fig_pneu, use_container_width=True)
                else:
                    st.warning("Sem tempos de troca de pneus válidos para o gráfico de pneus (NR em todas as corridas?).")

                fig_driver = px.line(
                    df_pt,
                    x="Corrida",
                    y="deltatempodriver",
                    color="Piloto",
                    title="Diferença do tempo do piloto em relação ao mais rápido",
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
                        ["Ranking_TempoTotal", "Ranking_Tempopneu", "Ranking_TempoDriver"]
                    ]
                    .mean(numeric_only=True)
                    .reset_index()
                )
                media_rankings.rename(
                    columns={
                        "Ranking_TempoTotal": "Média ranking tempo total",
                        "Ranking_Tempopneu": "Média ranking tempo pneus",
                        "Ranking_TempoDriver": "Média ranking tempo piloto",
                    },
                    inplace=True,
                )
                st.subheader("Média dos rankings dos pilotos selecionados")
                _mr = media_rankings.copy()
                _cols_med = (
                    "Média ranking tempo total",
                    "Média ranking tempo pneus",
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
                        "Média ranking tempo total": st.column_config.NumberColumn(
                            "Média ranking tempo total",
                            format="%.1f",
                            alignment="center",
                        ),
                        "Média ranking tempo pneus": st.column_config.NumberColumn(
                            "Média ranking tempo pneus",
                            format="%.1f",
                            alignment="center",
                        ),
                        "Média ranking tempo piloto": st.column_config.NumberColumn(
                            "Média ranking tempo piloto",
                            format="%.1f",
                            alignment="center",
                        ),
                    },
                )

with tabs[3]:
    if df_all.empty or len(df_all) < 2:
        st.info("Inclua pits de mais carros/corridas para comparar equipes (box plot precisa de volume).")
    else:
        st.caption(
            "Performance da **equipe**: em cada corrida (etapa + Sprint ou Principal), usa-se o "
            "**tempo parado** (`tempo_troca_parado` no CSV). Calcula-se o **menor** parado da corrida e "
            "**Δ = parado do carro − esse melhor**. O tempo total do pit lane inclui o piloto e "
            "não entra aqui. O segundo gráfico mantém o mesmo critério para **troca de pneus**."
        )
        team_colors = (
            df_all.drop_duplicates(subset=["team_name"])
            .set_index("team_name")["team_color_hex"]
            .to_dict()
        )
        _per_race = df_all.groupby(["stage_number", "race_type"], as_index=False).agg(
            melhor_parado=("TempoParado_numeric", "min"),
            melhor_pneu=("Tempopneu_numeric", "min"),
        )
        _deltas = df_all.merge(_per_race, on=["stage_number", "race_type"], how="left")
        _deltas["delta_parado_s"] = _deltas["TempoParado_numeric"] - _deltas["melhor_parado"]
        _deltas["delta_pneu_s"] = _deltas["Tempopneu_numeric"] - _deltas["melhor_pneu"]

        df_delta_parado = _deltas.dropna(subset=["delta_parado_s"])
        df_delta_pneu = _deltas.dropna(subset=["delta_pneu_s"])

        if len(df_delta_parado) < 2:
            st.warning(
                "Dados insuficientes para o boxplot de tempo parado. "
                "Grave pits com `tempo_troca_parado` no CSV (importação etapa)."
            )
        else:
            figb = px.box(
                df_delta_parado,
                x="team_name",
                y="delta_parado_s",
                color="team_name",
                color_discrete_map=team_colors,
                title="Delta do tempo parado vs melhor da corrida — por equipe (2026)",
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
                title="Delta da troca de pneus vs melhor da corrida — por equipe (2026)",
                labels={"team_name": "Equipe", "delta_pneu_s": "Δ vs melhor (s)"},
            )
            figbp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(figbp, use_container_width=True)
