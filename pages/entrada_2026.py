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
    default_db_path,
    delete_pit_event,
    ensure_db_ready,
    fetch_calendar,
    fetch_drivers,
    fetch_driver,
    fetch_pit_events,
    upsert_pit_stop_event,
)
from utils.stage_csv_2026 import (
    filter_stage_df,
    load_stage_csv_bytes,
    row_to_app_dict,
    validate_rows_for_sqlite,
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

_db_path = default_db_path()
if _db_path.exists():
    st.download_button(
        label="Descarregar backup",
        data=_db_path.read_bytes(),
        file_name="pitstop_2026_backup.db",
        mime="application/x-sqlite3",
        key="download_sqlite_backup",
    )

cal_rows = fetch_calendar()
if not cal_rows:
    st.error("Calendário 2026 vazio. Execute: `python -m utils.db_2026`")
    st.stop()

stage_labels = [_format_stage_row(r) for r in cal_rows]
stage_pick = st.selectbox("Etapa", range(len(cal_rows)), format_func=lambda i: stage_labels[i])
stage_number = int(cal_rows[stage_pick]["stage_number"])

race_type = st.selectbox("Corrida", ["Sprint", "Principal"])

MODE_OPTS = ("Manual", "CSV da etapa")
mode = st.radio("Modo de entrada", MODE_OPTS, horizontal=True, key="ent26_mode_simple")

if mode == MODE_OPTS[1]:
    st.subheader("CSV da etapa")
    up_csv = st.file_uploader(
        "Envie o ficheiro stageX.csv (ex.: stage1.csv)",
        type=["csv"],
        key="ent26_stage_csv_upload",
    )
    if st.button("Carregar CSV", key="ent26_load_upload"):
        if up_csv is None:
            st.error("Escolha um ficheiro CSV primeiro.")
        else:
            try:
                st.session_state["ent26_stage_df"] = load_stage_csv_bytes(up_csv.getvalue(), up_csv.name)
                st.success("CSV carregado.")
                st.rerun()
            except Exception as ex:
                st.error(str(ex))

    sdf = st.session_state.get("ent26_stage_df")
    if sdf is not None and not sdf.empty:
        sub = filter_stage_df(sdf, stage_number, race_type)
        st.caption(f"{len(sub)} linha(s) para etapa **{stage_number}** e **{race_type}**.")
        st.dataframe(sub, use_container_width=True, hide_index=True)
        if sub.empty:
            st.info("Nenhuma linha neste CSV para a etapa e tipo de corrida selecionados.")
        else:
            ix_list = list(sub.index)

            def _row_preview(i: int) -> str:
                r = sub.loc[ix_list[i]]
                return (
                    f"#{r['car_number']} | pit volta {r['pit_lap']} | pos {r['race_position']} "
                    f"| total {r['tempo_total']}"
                )

            sel_i = st.selectbox(
                "Escolher linha para copiar ao formulário manual",
                range(len(ix_list)),
                format_func=_row_preview,
                key="ent26_stage_row_pick",
            )
            if st.button("Aplicar linha ao manual", key="ent26_apply_row"):
                st.session_state["ent26_prefill"] = row_to_app_dict(sub.loc[ix_list[sel_i]])
                st.session_state["ent26_mode_simple"] = MODE_OPTS[0]
                st.rerun()

            if st.button("Gravar todas as linhas filtradas no SQLite", type="primary", key="ent26_batch_csv"):
                rows = [row_to_app_dict(sub.loc[i]) for i in ix_list]
                ok_rows, errs = validate_rows_for_sqlite(rows, parse_ss_mmm_to_ms)
                if errs:
                    st.error("Erros de validação:\n- " + "\n- ".join(errs[:40]))
                else:
                    inserted = updated = failed = 0
                    for r in ok_rows:
                        drv_r = fetch_driver(r["car_number"])
                        is_ext_r = bool(drv_r and drv_r["is_amattheis_extended"])
                        dl = "amattheis_extended" if is_ext_r else "standard"
                        p2 = r["pneu2"] if r["race_type"] == "Principal" else None
                        try:
                            _, action = upsert_pit_stop_event(
                                stage_number=r["stage_number"],
                                race_type=r["race_type"],
                                car_number=r["car_number"],
                                pit_lap=r["pit_lap"],
                                race_position=r["race_position"],
                                pneu1=r["pneu1"],
                                pneu2=p2,
                                tempo_troca_pneus_ms=r["tempo_troca_pneus_ms"],
                                tempo_total_ms=r["tempo_total_ms"],
                                tempo_reacao_air_jack_ms=None,
                                tempo_primeira_conexao_ms=None,
                                tempo_troca1_ms=None,
                                tempo_troca2_ms=None,
                                video_link=r.get("video_link"),
                                notes=r.get("notes"),
                                detail_level=dl,
                            )
                            if action == "inserted":
                                inserted += 1
                            else:
                                updated += 1
                        except Exception:
                            failed += 1
                    st.success(
                        f"Lote CSV: inseridos={inserted}, atualizados={updated}, falhas={failed}."
                    )
                    st.rerun()

_prefill = st.session_state.pop("ent26_prefill", None)

drivers = fetch_drivers()
car_options = [int(d["car_number"]) for d in drivers]


def _label_car(n: int) -> str:
    for d in drivers:
        if int(d["car_number"]) == n:
            return str(d["display_label"])
    return str(n)


def _pneu_ix(name: Optional[str]) -> int:
    if name and name in PNEU_OPTIONS:
        return PNEU_OPTIONS.index(name)
    return PNEU_OPTIONS.index("Não registrado")


_car_ix = 0
if _prefill:
    try:
        _car_ix = car_options.index(int(_prefill["car_number"]))
    except ValueError:
        st.warning(
            f"Carro {_prefill['car_number']} não está no calendário de pilotos; ajuste a seleção."
        )
        _car_ix = 0

car_number = st.selectbox("Piloto / carro", car_options, format_func=_label_car, index=_car_ix)

drv = fetch_driver(car_number)
is_ext = bool(drv and drv["is_amattheis_extended"])

_pit_def = int(_prefill["pit_lap"]) if _prefill else 1
_pos_def = str(_prefill["race_position"]) if _prefill else "1"

col_a, col_b, col_c = st.columns(3)
with col_a:
    pit_lap = st.number_input("Volta do pit", min_value=1, value=_pit_def, step=1)
with col_b:
    race_position = st.text_input(
        "Posição na corrida",
        value=_pos_def,
        help="Número ou DNF / DQ",
    )
with col_c:
    st.metric("Nível de detalhe", "Amattheis (estendido)" if is_ext else "Padrão (grid)")

_p1_ix = _pneu_ix(str(_prefill["pneu1"])) if _prefill else _pneu_ix("TD")
pneu1 = st.selectbox("Pneu 1", PNEU_OPTIONS, index=_p1_ix)
if race_type == "Principal":
    _p2_raw = str(_prefill["pneu2"]) if _prefill and _prefill.get("pneu2") else None
    _p2_ix = _pneu_ix(_p2_raw)
    pneu2 = st.selectbox("Pneu 2", PNEU_OPTIONS, index=_p2_ix)
else:
    pneu2 = None

st.subheader("Tempos (ss.mmm ou NR)")

_tt_p_def = ""
_tt_tot_def = ""
if _prefill:
    _tt_p_def = str(_prefill.get("tempo_troca_pneus_dot") or "")
    _tt_tot_def = str(_prefill.get("tempo_total_dot") or "")

c1, c2 = st.columns(2)
with c1:
    tt_pneu_raw = st.text_input("Troca de pneus (tempo)", value=_tt_p_def, placeholder="12.852 ou NR")
with c2:
    tt_total_raw = st.text_input("Tempo total *", value=_tt_tot_def, placeholder="obrigatório")

tempo_reacao_raw = ""
tempo_1c_raw = ""
tempo_t1_raw = ""
tempo_t2_raw = ""
_vid_def = str(_prefill["video_link"]) if _prefill and _prefill.get("video_link") else ""
_notes_def = str(_prefill["notes"]) if _prefill and _prefill.get("notes") else ""

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
    video_link = st.text_input("Link do vídeo (opcional)", value=_vid_def)
    notes = st.text_area("Observações (opcional)", value=_notes_def)
else:
    video_link = st.text_input("Link do vídeo (opcional)", value=_vid_def)
    notes = st.text_area("Observações (opcional)", value=_notes_def)

detail_level = "amattheis_extended" if is_ext else "standard"

if mode == MODE_OPTS[0]:
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
