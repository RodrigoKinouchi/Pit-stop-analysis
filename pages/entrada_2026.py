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
from utils.import_2026 import (
    build_driver_lookup,
    extract_text_from_upload,
    merge_with_results,
    parse_pit_report_text,
    parse_results_file,
    parse_structured_file,
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
st.caption(
    "Tempos em **ss.mmm** (ex.: 12.852 = 12 s e 852 ms). "
    f"Banco SQLite: `{default_db_path()}` (env `PITSTOP_2026_DB` ou secret homónimo)."
)

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

drivers = fetch_drivers()
car_options = [int(d["car_number"]) for d in drivers]
driver_lookup = build_driver_lookup(drivers)


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

mode = st.radio(
    "Modo de entrada",
    ["Manual", "Upload em lote (CSV/Excel/Relatório)"],
    horizontal=True,
)

if mode == "Manual":
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
else:
    st.subheader("Upload em lote")
    st.caption(
        "Aceita CSV/Excel já estruturado, ou PDF/TXT/imagem com OCR para extrair linhas do relatório de pit."
    )
    template_df = pd.DataFrame(
        [
            {
                "stage_number": stage_number,
                "race_type": race_type,
                "car_number": 1,
                "pit_lap": 5,
                "race_position": 7,
                "tempo_total": "9.340",
                "tempo_troca_pneus": "9.340",
                "pneu1": "Não registrado",
                "pneu2": "",
                "video_link": "",
                "notes": "modelo",
            }
        ]
    )
    st.download_button(
        "Baixar template CSV",
        template_df.to_csv(index=False).encode("utf-8"),
        file_name="template_entrada_2026.csv",
        mime="text/csv",
    )
    data_file = st.file_uploader(
        "Arquivo principal (CSV/Excel/PDF/TXT/PNG/JPG)",
        type=["csv", "xlsx", "xls", "pdf", "txt", "png", "jpg", "jpeg"],
    )
    result_file = st.file_uploader(
        "Arquivo opcional de resultados (para preencher posição e pit lap)",
        type=["csv", "xlsx", "xls", "pdf", "txt", "png", "jpg", "jpeg"],
    )

    df_import = pd.DataFrame()
    parse_warnings: List[str] = []
    if data_file:
        raw = data_file.getvalue()
        name = data_file.name.lower()
        try:
            if name.endswith((".csv", ".xlsx", ".xls")):
                parsed = parse_structured_file(raw, data_file.name)
                df_import = parsed.df
                parse_warnings.extend(parsed.warnings)
            else:
                txt, warns = extract_text_from_upload(raw, data_file.name)
                parse_warnings.extend(warns)
                parsed = parse_pit_report_text(txt, driver_lookup, default_stage=stage_number)
                df_import = parsed.df
                parse_warnings.extend(parsed.warnings)
        except Exception as ex:
            st.error(f"Falha ao ler arquivo principal: {ex}")

    if not df_import.empty and result_file is not None:
        try:
            results_df = parse_results_file(result_file.getvalue(), result_file.name)
            df_import = merge_with_results(df_import, results_df)
        except Exception as ex:
            st.error(f"Falha ao aplicar arquivo de resultados: {ex}")

    if parse_warnings:
        uniq_warns = []
        seen_w = set()
        for w in parse_warnings:
            if w not in seen_w:
                uniq_warns.append(w)
                seen_w.add(w)
        st.warning("Avisos de parsing:\n- " + "\n- ".join(uniq_warns[:15]))

    if not df_import.empty:
        if "stage_number" not in df_import.columns:
            df_import["stage_number"] = stage_number
        if "race_type" not in df_import.columns:
            df_import["race_type"] = race_type

        required_cols = ["stage_number", "race_type", "car_number", "pit_lap", "race_position", "tempo_total"]
        for c in required_cols:
            if c not in df_import.columns:
                df_import[c] = None
        if "tempo_troca_pneus" not in df_import.columns:
            df_import["tempo_troca_pneus"] = df_import["tempo_total"]
        if "pneu1" not in df_import.columns:
            df_import["pneu1"] = "Não registrado"
        if "pneu2" not in df_import.columns:
            df_import["pneu2"] = None
        if "video_link" not in df_import.columns:
            df_import["video_link"] = None
        if "notes" not in df_import.columns:
            df_import["notes"] = "Importado em lote"

        st.dataframe(df_import, use_container_width=True)

        errors: List[str] = []
        valid_rows = []
        for idx, r in df_import.iterrows():
            row_id = idx + 1
            try:
                stg = int(r["stage_number"])
                rtype = str(r["race_type"]).strip()
                if rtype not in ("Sprint", "Principal", "Main"):
                    errors.append(f"Linha {row_id}: race_type inválido ({rtype}).")
                    continue
                if rtype == "Main":
                    rtype = "Principal"
                car = int(r["car_number"])
                lap = int(r["pit_lap"])
                pos = str(r["race_position"]).strip() if pd.notna(r["race_position"]) else "DNF"
                t_total = parse_ss_mmm_to_ms(str(r["tempo_total"]))
                if t_total is None:
                    errors.append(f"Linha {row_id}: tempo_total inválido ({r['tempo_total']}).")
                    continue
                t_pneu = parse_ss_mmm_to_ms(str(r["tempo_troca_pneus"]))
                valid_rows.append(
                    {
                        "stage_number": stg,
                        "race_type": rtype,
                        "car_number": car,
                        "pit_lap": lap,
                        "race_position": pos,
                        "tempo_total_ms": t_total,
                        "tempo_troca_pneus_ms": t_pneu,
                        "pneu1": str(r.get("pneu1", "Não registrado")),
                        "pneu2": (str(r.get("pneu2")).strip() or None) if pd.notna(r.get("pneu2")) else None,
                        "video_link": (str(r.get("video_link")).strip() or None)
                        if pd.notna(r.get("video_link"))
                        else None,
                        "notes": (str(r.get("notes")).strip() or "Importado em lote")
                        if pd.notna(r.get("notes"))
                        else "Importado em lote",
                    }
                )
            except Exception as ex:
                errors.append(f"Linha {row_id}: erro de validação ({ex}).")

        if errors:
            st.error("Erros encontrados no lote:")
            st.code("\n".join(errors[:50]))
        else:
            if st.button("Gravar lote no SQLite", type="primary"):
                inserted = 0
                updated = 0
                failed = 0
                for row in valid_rows:
                    try:
                        _, action = upsert_pit_stop_event(
                            stage_number=row["stage_number"],
                            race_type=row["race_type"],
                            car_number=row["car_number"],
                            pit_lap=row["pit_lap"],
                            race_position=row["race_position"],
                            pneu1=row["pneu1"],
                            pneu2=row["pneu2"],
                            tempo_troca_pneus_ms=row["tempo_troca_pneus_ms"],
                            tempo_total_ms=row["tempo_total_ms"],
                            tempo_reacao_air_jack_ms=None,
                            tempo_primeira_conexao_ms=None,
                            tempo_troca1_ms=None,
                            tempo_troca2_ms=None,
                            video_link=row["video_link"],
                            notes=row["notes"],
                            detail_level="standard",
                        )
                        if action == "inserted":
                            inserted += 1
                        else:
                            updated += 1
                    except Exception:
                        failed += 1
                st.success(
                    f"Lote processado: inseridos={inserted}, atualizados={updated}, falhas={failed}."
                )
                st.rerun()

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
