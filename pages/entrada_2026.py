"""
Entrada de pit stops — temporada 2026 (SQLite).

Tempos no formato ss.mmm (ex.: 12.852). Mesma etapa + tipo de corrida + carro + volta do pit
substitui o registro anterior.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from utils.db_2026 import (
    delete_pit_event,
    ensure_db_ready,
    fetch_calendar,
    fetch_drivers,
    fetch_driver,
    fetch_pit_events,
    upsert_pit_stop_event,
)
from utils.time_format import format_ms_to_ss_mmm, parse_ss_mmm_to_ms

st.set_page_config(
    page_title="Entrada 2026 — Pit Stop",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

PNEU_OPTIONS = ["TD", "TE", "DD", "DE", "ALL", "Não registrado"]


def _format_stage_row(row: sqlite3.Row) -> str:
    d = row["event_date"]
    try:
        dt = datetime.fromisoformat(d)
        d_br = dt.strftime("%d/%m/%Y")
    except ValueError:
        d_br = d
    return f"Etapa {row['stage_number']} — {row['circuit_name']} ({d_br})"


def _parse_time_field(raw: str, label: str) -> Tuple[bool, Optional[str], Optional[int]]:
    raw = (raw or "").strip()
    if not raw or raw.lower() in ("nr", "n/r", "não registrado", "nao registrado"):
        return True, "", None
    ms = parse_ss_mmm_to_ms(raw)
    if ms is None:
        return False, f"{label}: use ss.mmm (ex.: 12.852) ou deixe em branco / NR.", None
    return True, "", ms


ensure_db_ready()

st.title("📝 Entrada de dados — Temporada 2026")
st.caption("Tempos em **ss.mmm** (ex.: 12.852 = 12 s e 852 ms). Dados gravados em SQLite (`data/pitstop_2026.db`).")

cal_rows = fetch_calendar()
if not cal_rows:
    st.error("Calendário 2026 vazio. Execute: `python -m utils.db_2026`")
    st.stop()

stage_labels = [_format_stage_row(r) for r in cal_rows]
stage_pick = st.selectbox("Etapa", range(len(cal_rows)), format_func=lambda i: stage_labels[i])
stage_number = int(cal_rows[stage_pick]["stage_number"])

race_type = st.selectbox("Corrida", ["Sprint", "Principal"])

drivers = fetch_drivers()
car_options = [int(d["car_number"]) for d in drivers]


def _label_car(n: int) -> str:
    for d in drivers:
        if int(d["car_number"]) == n:
            return str(d["display_label"])
    return str(n)


car_number = st.selectbox("Piloto / carro", car_options, format_func=_label_car)

drv = fetch_driver(car_number)
is_ext = bool(drv and drv["is_amattheis_extended"])

col_a, col_b, col_c = st.columns(3)
with col_a:
    pit_lap = st.number_input("Volta do pit", min_value=1, value=1, step=1)
with col_b:
    race_position = st.text_input("Posição na corrida", value="1", help="Número ou DNF")
with col_c:
    st.metric("Nível de detalhe", "Amattheis (estendido)" if is_ext else "Padrão (grid)")

pneu1 = st.selectbox("Pneu 1", PNEU_OPTIONS)
if race_type == "Principal":
    pneu2 = st.selectbox("Pneu 2", PNEU_OPTIONS)
else:
    pneu2 = None

st.subheader("Tempos (ss.mmm ou NR)")

c1, c2 = st.columns(2)
with c1:
    tt_pneu_raw = st.text_input("Troca de pneus (tempo)", placeholder="12.852 ou NR")
with c2:
    tt_total_raw = st.text_input("Tempo total *", placeholder="obrigatório")

tempo_reacao_raw = ""
tempo_1c_raw = ""
tempo_t1_raw = ""
tempo_t2_raw = ""
video_link = ""
notes = ""

if is_ext:
    st.markdown("**Segmentos Amattheis**")
    e1, e2 = st.columns(2)
    with e1:
        tempo_reacao_raw = st.text_input("Reação Air Jack", placeholder="NR")
        tempo_1c_raw = st.text_input("1ª conexão", placeholder="NR")
    with e2:
        tempo_t1_raw = st.text_input("Troca 1 (pistola e encaixe)", placeholder="NR")
        if race_type == "Principal":
            tempo_t2_raw = st.text_input("Troca 2 (pistola e encaixe)", placeholder="NR")
    video_link = st.text_input("Link do vídeo (opcional)", "")
    notes = st.text_area("Observações (opcional)", "")

detail_level = "amattheis_extended" if is_ext else "standard"

if st.button("Gravar pit stop", type="primary"):
    err: List[str] = []
    ok_t, msg, tempo_troca_pneus_ms_v = _parse_time_field(tt_pneu_raw, "Troca de pneus")
    if not ok_t:
        err.append(msg or "")

    ok_t, msg, tempo_total_ms_v = _parse_time_field(tt_total_raw, "Tempo total")
    if not ok_t:
        err.append(msg or "")
    elif tempo_total_ms_v is None:
        err.append("Tempo total é obrigatório (ss.mmm).")

    tr_aj = t_1c = t_t1 = t_t2 = None
    if is_ext:
        seg_fields = [
            ("Reação Air Jack", tempo_reacao_raw),
            ("1ª conexão", tempo_1c_raw),
            ("Troca 1", tempo_t1_raw),
        ]
        parsed_seg = []
        for label, raw in seg_fields:
            o, m, v = _parse_time_field(raw, label)
            if not o:
                err.append(m or "")
            parsed_seg.append(v)
        tr_aj, t_1c, t_t1 = parsed_seg
        if race_type == "Principal":
            o, m, v = _parse_time_field(tempo_t2_raw, "Troca 2")
            if not o:
                err.append(m or "")
            t_t2 = v
    else:
        tr_aj = t_1c = t_t1 = t_t2 = None

    err = [x for x in err if x]

    if err:
        for e in err:
            st.warning(e)
        st.error("Corrija os campos indicados antes de gravar.")
    else:
        try:
            eid, action = upsert_pit_stop_event(
                stage_number=stage_number,
                race_type=race_type,
                car_number=car_number,
                pit_lap=int(pit_lap),
                race_position=race_position.strip(),
                pneu1=pneu1,
                pneu2=pneu2,
                tempo_troca_pneus_ms=tempo_troca_pneus_ms_v,
                tempo_total_ms=tempo_total_ms_v,
                tempo_reacao_air_jack_ms=tr_aj,
                tempo_primeira_conexao_ms=t_1c,
                tempo_troca1_ms=t_t1,
                tempo_troca2_ms=t_t2,
                video_link=video_link.strip() or None,
                notes=notes.strip() or None,
                detail_level=detail_level,
            )
            st.success(f"Registro {'atualizado' if action == 'updated' else 'inserido'} (id={eid}).")
            st.rerun()
        except Exception as ex:
            st.error(f"Erro ao gravar: {ex}")

st.markdown("---")
st.subheader("Registros nesta etapa e corrida")

evs = fetch_pit_events(stage_number=stage_number, race_type=race_type)
if not evs:
    st.info("Nenhum pit gravado para esta seleção.")
else:
    rows = []
    for e in evs:
        rows.append(
            {
                "id": e["id"],
                "volta": e["pit_lap"],
                "carro": e["car_number"],
                "piloto": e["driver_label"],
                "pos": e["race_position"],
                "t_pneu": format_ms_to_ss_mmm(e["tempo_troca_pneus_ms"]),
                "total": format_ms_to_ss_mmm(e["tempo_total_ms"]),
                "detalhe": e["detail_level"],
            }
        )
    df_show = pd.DataFrame(rows)
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    del_id = st.number_input("Excluir registro (id)", min_value=0, value=0, step=1)
    if st.button("Excluir por id"):
        if del_id <= 0:
            st.warning("Informe o id da coluna acima.")
        elif delete_pit_event(int(del_id)):
            st.success(f"Registro {del_id} removido.")
            st.rerun()
        else:
            st.error("Id não encontrado.")
