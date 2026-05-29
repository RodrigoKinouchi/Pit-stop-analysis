"""
CSV padrão por etapa: stage{N}.csv

Formato esperado (separador `;`, decimais com vírgula):
  stage_number;race_type;car_number;pit_lap;race_position;tempo_total;
  tempo_troca_parado;tempo_troca_pneus;pneu1;pneu2;video_link

race_type: SPRINT | PRINCIPAL (case-insensitive)

Pasta base: variável de ambiente PITSTOP_STAGE_CSV_DIR ou secret Streamlit homónimo.
Arquivo: stage1.csv, stage2.csv, … na raiz dessa pasta.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

import pandas as pd


def _norm_header(s: str) -> str:
    t = (s or "").strip().lower()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9_]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t


def _br_decimal_to_dot(s: object) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    t = str(s).strip().replace(" ", "")
    if not t:
        return ""
    return t.replace(",", ".")


def default_stage_csv_dir() -> Optional[Path]:
    env = (os.environ.get("PITSTOP_STAGE_CSV_DIR") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            try:
                sec = st.secrets.get("PITSTOP_STAGE_CSV_DIR")
            except (FileNotFoundError, KeyError, AttributeError, TypeError):
                sec = None
            if sec:
                return Path(str(sec).strip()).expanduser().resolve()
    except Exception:
        pass
    return None


def stage_csv_path(stage_number: int, base_dir: Optional[Path] = None) -> Path:
    root = base_dir or default_stage_csv_dir()
    if not root:
        raise ValueError(
            "Defina a pasta dos CSVs: variável PITSTOP_STAGE_CSV_DIR ou secret Streamlit PITSTOP_STAGE_CSV_DIR."
        )
    return (root / f"stage{int(stage_number)}.csv").resolve()


def _parse_semicolon_stage_csv_text(text: str) -> pd.DataFrame:
    """
    Parser tolerante para stageX.csv com `;`.
    - Remove `;` final vazio (links YouTube com `;` no fim da linha).
    - Sprint: se o link estiver na coluna pneu2, desloca para video_link.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return pd.DataFrame()
    header_parts = lines[0].split(";")
    ncols = len(header_parts)
    rows: list[list[str]] = []
    for line in lines[1:]:
        parts = line.split(";")
        while parts and parts[-1] == "":
            parts.pop()
        if len(parts) > ncols:
            parts = parts[: ncols - 1] + [";".join(parts[ncols - 1 :])]
        if len(parts) < ncols:
            parts = parts + [""] * (ncols - len(parts))
        if len(parts) >= 11 and parts[1].strip().upper() == "SPRINT":
            p9 = parts[9].strip()
            p10 = parts[10].strip() if len(parts) > 10 else ""
            if p9.lower().startswith("http") and not p10:
                parts = parts[:9] + ["", p9]
        rows.append(parts[:ncols])
    return pd.DataFrame(rows, columns=header_parts)


def load_stage_csv_bytes(data: bytes, filename: str = "stage.csv") -> pd.DataFrame:
    """Lê CSV/bytes no formato stageX (sep `;` ou `,`)."""
    bio = __import__("io").BytesIO(data)
    df = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            bio.seek(0)
            text = bio.read().decode(enc)
        except Exception:
            continue
        first = text.splitlines()[0] if text.strip() else ""
        if ";" in first:
            cand = _parse_semicolon_stage_csv_text(text)
            if not cand.empty and cand.shape[1] >= 5:
                df = cand
                break
        for sep in (",",):
            try:
                bio.seek(0)
                cand = pd.read_csv(bio, sep=sep, encoding=enc, dtype=str)
                if cand.shape[1] >= 5:
                    df = cand
                    break
            except Exception:
                continue
        if df is not None:
            break
    if df is None or df.empty:
        raise ValueError("CSV vazio ou ilegível (esperado separador ; e colunas stage_number, race_type, …).")
    df.columns = [_norm_header(str(c)) for c in df.columns]
    return _normalize_stage_df(df)


def load_stage_csv_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return load_stage_csv_bytes(path.read_bytes(), path.name)


def _normalize_stage_df(df: pd.DataFrame) -> pd.DataFrame:
    """Garante nomes de coluna canónicos após _norm_header no cabeçalho."""
    alias = {
        "etapa": "stage_number",
        "tipo_corrida": "race_type",
        "carro": "car_number",
        "volta_pit": "pit_lap",
        "posicao": "race_position",
        "pos": "race_position",
        "link": "video_link",
    }
    out = df.copy()
    out = out.rename(columns={k: v for k, v in alias.items() if k in out.columns})
    out = out.loc[:, ~out.columns.duplicated()]
    required = {"stage_number", "race_type", "car_number", "pit_lap", "race_position", "tempo_total"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias em falta no CSV: {sorted(missing)}")
    return out


def race_type_to_app(value: object) -> str:
    s = str(value or "").strip().upper()
    if s in ("SPRINT", "S", "1"):
        return "Sprint"
    if s in ("PRINCIPAL", "MAIN", "P", "2"):
        return "Principal"
    raise ValueError(f"race_type inválido: {value!r} (use SPRINT ou PRINCIPAL)")


def row_to_app_dict(row: pd.Series) -> dict:
    """Uma linha já normalizada -> dict para upsert / formulário."""
    stg = int(float(str(row["stage_number"]).replace(",", ".")))
    rt = race_type_to_app(row["race_type"])
    car = int(float(_br_decimal_to_dot(row["car_number"])))
    lap = int(float(_br_decimal_to_dot(row["pit_lap"])))
    pos = str(row["race_position"]).strip()
    tt = _br_decimal_to_dot(row.get("tempo_total", ""))
    tp = _br_decimal_to_dot(row.get("tempo_troca_pneus", ""))
    if not tp and tt:
        tp = tt
    parado = _br_decimal_to_dot(row.get("tempo_troca_parado", ""))
    p1 = str(row.get("pneu1", "") or "").strip() or "Não registrado"
    p2 = str(row.get("pneu2", "") or "").strip() or ""
    vid = str(row.get("video_link", "") or "").strip() or ""
    notes_parts = ["stage CSV"]
    if parado:
        notes_parts.append(f"troca_parado={parado}")
    notes = "; ".join(notes_parts)
    return {
        "stage_number": stg,
        "race_type": rt,
        "car_number": car,
        "pit_lap": lap,
        "race_position": pos,
        "tempo_total_dot": tt,
        "tempo_troca_pneus_dot": tp,
        "pneu1": p1,
        "pneu2": p2 if p2 else None,
        "video_link": vid if vid else None,
        "notes": notes,
    }


def filter_stage_df(df: pd.DataFrame, stage_number: int, race_type: str) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    work["_stg"] = work["stage_number"].apply(lambda x: int(float(_br_decimal_to_dot(x))))
    work["_rt"] = work["race_type"].apply(race_type_to_app)
    m = (work["_stg"] == stage_number) & (work["_rt"] == race_type)
    return work.loc[m].drop(columns=["_stg", "_rt"], errors="ignore")


def validate_rows_for_sqlite(rows: List[dict], parse_ms) -> tuple[list[dict], list[str]]:
    """parse_ms: função str -> Optional[int] (ex.: parse_ss_mmm_to_ms)."""
    errs: list[str] = []
    ok: list[dict] = []
    for i, r in enumerate(rows, start=1):
        try:
            tt_ms = parse_ms(r["tempo_total_dot"])
            if tt_ms is None:
                errs.append(f"Linha {i}: tempo_total inválido ({r.get('tempo_total_dot')!r}).")
                continue
            tp_ms = parse_ms(r.get("tempo_troca_pneus_dot") or "")
            if tp_ms is None:
                tp_ms = tt_ms
            ok.append({**r, "tempo_total_ms": tt_ms, "tempo_troca_pneus_ms": tp_ms})
        except Exception as ex:
            errs.append(f"Linha {i}: {ex}")
    return ok, errs
