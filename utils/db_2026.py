"""
SQLite — temporada 2026: esquema canônico + seed de calendário, equipes e pilotos.

Arquivo padrão: <raiz_do_projeto>/data/pitstop_2026.db (caminho absoluto, não depende do cwd).

Caminho alternativo (ordem de prioridade):
1) Variável de ambiente PITSTOP_2026_DB
2) Streamlit secrets: PITSTOP_2026_DB (ex.: deploy na nuvem)

Persistência no Streamlit Community Cloud
-----------------------------------------
O disco do contêiner é EFÊMERO: a cada redeploy (novo push) o app é clonado do Git
e o sistema de arquivos local é recriado. Um SQLite criado só em runtime
(data/pitstop_2026.db) NÃO volta, a menos que o ficheiro exista no repositório
(commit + push) ou use um banco externo (Postgres, etc.).

Opções para não perder dados: fazer commit do .db após gravações; usar backup
(download na página de entrada); hospedar o app noutro sítio com disco persistente;
ou migrar para base de dados gerida (Supabase/Neon + URL nas secrets).
"""

from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple

import pandas as pd

from utils.season_2026_data import (
    CALENDAR_2026,
    EQUIPES_COR_2026,
    EQUIPES_PILOTOS_2026,
    GUEST_DRIVERS_2026,
    AMATTHEIS_EXTENDED_PIT_NUMBERS_2026,
    amattheis_viz_color_for,
    apply_stage_team_overrides,
    normalize_team_name,
    parse_driver_label,
    team_chart_color,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def default_db_path() -> Path:
    env = os.environ.get("PITSTOP_2026_DB", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            try:
                sec = st.secrets.get("PITSTOP_2026_DB")
            except (FileNotFoundError, KeyError, AttributeError, TypeError):
                sec = None
            if sec:
                return Path(str(sec).strip()).expanduser().resolve()
    except Exception:
        pass
    return (_PROJECT_ROOT / "data" / "pitstop_2026.db").resolve()

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_2026 (
    stage_number INTEGER PRIMARY KEY CHECK (stage_number BETWEEN 1 AND 12),
    city TEXT NOT NULL,
    circuit_name TEXT NOT NULL,
    event_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teams_2026 (
    team_name TEXT PRIMARY KEY,
    chart_color_name TEXT NOT NULL,
    chart_color_hex TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS drivers_2026 (
    car_number INTEGER PRIMARY KEY,
    display_label TEXT NOT NULL,
    pilot_name TEXT NOT NULL,
    team_name TEXT NOT NULL REFERENCES teams_2026(team_name) ON UPDATE CASCADE,
    amattheis_color_name TEXT,
    amattheis_color_hex TEXT NOT NULL,
    is_amattheis_extended INTEGER NOT NULL DEFAULT 0 CHECK (is_amattheis_extended IN (0, 1))
);

-- Eventos de pit stop (entrada via formulário Streamlit)
CREATE TABLE IF NOT EXISTS pit_stop_events_2026 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    stage_number INTEGER NOT NULL REFERENCES calendar_2026(stage_number),
    race_type TEXT NOT NULL CHECK (race_type IN ('Sprint', 'Principal')),
    car_number INTEGER NOT NULL REFERENCES drivers_2026(car_number),
    pit_lap INTEGER NOT NULL,
    race_position TEXT NOT NULL,
    pneu1 TEXT,
    pneu2 TEXT,
    tempo_troca_pneus_ms INTEGER,
    tempo_total_ms INTEGER NOT NULL,
    tempo_reacao_air_jack_ms INTEGER,
    tempo_primeira_conexao_ms INTEGER,
    tempo_troca1_ms INTEGER,
    tempo_troca2_ms INTEGER,
    video_link TEXT,
    notes TEXT,
    detail_level TEXT NOT NULL DEFAULT 'standard'
        CHECK (detail_level IN ('standard', 'amattheis_extended'))
);

CREATE INDEX IF NOT EXISTS idx_pit_events_stage_race
    ON pit_stop_events_2026 (stage_number, race_type);
CREATE INDEX IF NOT EXISTS idx_pit_events_car
    ON pit_stop_events_2026 (car_number);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pit_natural_2026
    ON pit_stop_events_2026 (stage_number, race_type, car_number, pit_lap);
"""


def get_db_path(custom: Optional[Path] = None) -> Path:
    if custom is not None:
        return Path(custom).expanduser().resolve()
    return default_db_path()


def init_db(db_path: Optional[Path] = None) -> Path:
    """Cria diretório, aplica DDL e metadados de versão."""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )
        conn.commit()
    return path


def seed_reference_data(
    db_path: Optional[Path] = None,
    *,
    wipe_all: bool = False,
) -> Path:
    """
    Popula calendar_2026, teams_2026, drivers_2026 a partir de season_2026_data.

    Por padrão faz apenas upsert (não apaga pit_stop_events_2026).
    wipe_all=True remove TODOS os eventos e referências e recria do zero (uso dev).
    """
    path = init_db(db_path)
    team_names = sorted(set(EQUIPES_PILOTOS_2026.values()) | set(GUEST_DRIVERS_2026.values()))

    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        if wipe_all:
            conn.execute("DELETE FROM pit_stop_events_2026")
            conn.execute("DELETE FROM drivers_2026")
            conn.execute("DELETE FROM teams_2026")
            conn.execute("DELETE FROM calendar_2026")

        cur = conn.cursor()
        for st in CALENDAR_2026:
            cur.execute(
                """
                INSERT INTO calendar_2026 (stage_number, city, circuit_name, event_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(stage_number) DO UPDATE SET
                    city = excluded.city,
                    circuit_name = excluded.circuit_name,
                    event_date = excluded.event_date
                """,
                (st.stage_number, st.city, st.circuit_name, st.event_date.isoformat()),
            )

        for t in team_names:
            cname, chex = team_chart_color(t)
            cur.execute(
                """
                INSERT INTO teams_2026 (team_name, chart_color_name, chart_color_hex)
                VALUES (?, ?, ?)
                ON CONFLICT(team_name) DO UPDATE SET
                    chart_color_name = excluded.chart_color_name,
                    chart_color_hex = excluded.chart_color_hex
                """,
                (t, cname, chex),
            )

        grid = {**EQUIPES_PILOTOS_2026, **GUEST_DRIVERS_2026}
        for label, team in sorted(grid.items(), key=lambda x: parse_driver_label(x[0])[0]):
            num, pname = parse_driver_label(label)
            acss, ahex = amattheis_viz_color_for(label, num)
            ext = 1 if num in AMATTHEIS_EXTENDED_PIT_NUMBERS_2026 else 0
            cur.execute(
                """
                INSERT INTO drivers_2026 (
                    car_number, display_label, pilot_name, team_name,
                    amattheis_color_name, amattheis_color_hex, is_amattheis_extended
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(car_number) DO UPDATE SET
                    display_label = excluded.display_label,
                    pilot_name = excluded.pilot_name,
                    team_name = excluded.team_name,
                    amattheis_color_name = excluded.amattheis_color_name,
                    amattheis_color_hex = excluded.amattheis_color_hex,
                    is_amattheis_extended = excluded.is_amattheis_extended
                """,
                (num, label, pname, team, acss, ahex, ext),
            )

        conn.commit()
    return path


@contextmanager
def connect(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def ensure_db_ready(db_path: Optional[Path] = None) -> Path:
    """Garante DDL aplicado e referências (calendário/pilotos/equipes) alinhadas ao Python."""
    path = init_db(db_path)
    # Sempre ressincroniza com utils.season_2026_data (upsert; não apaga pit_stop_events_2026).
    seed_reference_data(path, wipe_all=False)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _sanitize_corrupted_tire_times(conn)
        conn.commit()
    return path


def count_pit_events_2026(db_path: Optional[Path] = None) -> int:
    """Quantidade de registros em pit_stop_events_2026 (0 se o ficheiro não existir)."""
    path = get_db_path(db_path)
    if not path.exists():
        return 0
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        r = conn.execute("SELECT COUNT(*) FROM pit_stop_events_2026").fetchone()
        return int(r[0]) if r else 0


def fetch_calendar(db_path: Optional[Path] = None) -> List[sqlite3.Row]:
    ensure_db_ready(db_path)
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT stage_number, city, circuit_name, event_date "
            "FROM calendar_2026 ORDER BY stage_number"
        )
        return cur.fetchall()


def fetch_drivers(db_path: Optional[Path] = None) -> List[sqlite3.Row]:
    ensure_db_ready(db_path)
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT car_number, display_label, pilot_name, team_name, "
            "is_amattheis_extended FROM drivers_2026 ORDER BY car_number"
        )
        return cur.fetchall()


def fetch_driver(car_number: int, db_path: Optional[Path] = None) -> Optional[sqlite3.Row]:
    ensure_db_ready(db_path)
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM drivers_2026 WHERE car_number = ?", (car_number,)
        )
        return cur.fetchone()


def _normalize_sqlite_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    pandas.read_sql a partir do SQLite em alguns ambientes (ex.: Linux / Python 3.13)
    devolve nomes em minúsculas para colunas não citadas com AS explícito.
    Padroniza nomes usados nas páginas (Pneu1, Pneu2, etc.).
    """
    if df.empty:
        return df
    rename: dict[str, str] = {}
    lower_to_canonical = {
        "pneu1": "Pneu1",
        "pneu2": "Pneu2",
    }
    for c in df.columns:
        key = str(c).lower()
        if key in lower_to_canonical and c != lower_to_canonical[key]:
            rename[c] = lower_to_canonical[key]
    return df.rename(columns=rename) if rename else df


_PARADO_NOTES_RE = re.compile(r"troca_parado\s*=\s*([\d,\.]+)", re.I)
# Pneu Rap típico Stock Car: ~1,5–4 s; acima disso costuma ser dado errado ou outra métrica.
_MAX_TIRE_RAP_MS = 8000


def _parado_sec_from_notes(notes: object) -> float:
    if notes is None or (isinstance(notes, float) and pd.isna(notes)):
        return float("nan")
    m = _PARADO_NOTES_RE.search(str(notes))
    if not m:
        return float("nan")
    return float(m.group(1).replace(",", "."))


def _sanitize_tire_ms(pneu_ms: object, total_ms: object) -> Optional[int]:
    """
    Descarta troca de pneus inválida (ex.: cópia acidental do tempo total na importação).
  """
    if pneu_ms is None or (isinstance(pneu_ms, float) and pd.isna(pneu_ms)):
        return None
    if pd.isna(pneu_ms):
        return None
    p = int(pneu_ms)
    if p <= 0 or p > _MAX_TIRE_RAP_MS:
        return None
    if total_ms is not None and not (isinstance(total_ms, float) and pd.isna(total_ms)) and not pd.isna(total_ms):
        t = int(total_ms)
        if t > 0 and (p >= t * 0.5 or abs(p - t) <= 50):
            return None
    return p


def _sanitize_corrupted_tire_times(conn: sqlite3.Connection) -> int:
    """Limpa no SQLite pneus que são cópia do tempo total (dados legados)."""
    cur = conn.execute(
        """
        UPDATE pit_stop_events_2026
        SET tempo_troca_pneus_ms = NULL
        WHERE tempo_troca_pneus_ms IS NOT NULL
          AND tempo_total_ms IS NOT NULL
          AND (
            tempo_troca_pneus_ms <= 0
            OR tempo_troca_pneus_ms > ?
            OR tempo_troca_pneus_ms >= tempo_total_ms * 0.5
            OR ABS(tempo_troca_pneus_ms - tempo_total_ms) <= 50
          )
        """
        ,
        (_MAX_TIRE_RAP_MS,),
    )
    return cur.rowcount


def _enrich_pit_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Colunas numéricas usadas nas páginas (inclui tempo parado vindo das notas do CSV)."""
    df = _normalize_sqlite_column_names(df.copy())
    df["Numeral"] = df["car_number"]
    df["Piloto"] = df["pilot_name"]
    df["POS"] = df["race_position"]
    df["pitlap"] = df["pit_lap"]
    tire_ms = df.apply(
        lambda r: _sanitize_tire_ms(r.get("tempo_troca_pneus_ms"), r.get("tempo_total_ms")),
        axis=1,
    )
    df["Tempopneu_numeric"] = _ms_to_sec_optional(tire_ms)
    df["TempoTotal_numeric"] = df["tempo_total_ms"].astype(float) / 1000.0
    df["TempoTotal"] = df["TempoTotal_numeric"]
    df["Tempopneu"] = df["Tempopneu_numeric"]
    if "notes" in df.columns:
        df["TempoParado_numeric"] = df["notes"].map(_parado_sec_from_notes)
    else:
        df["TempoParado_numeric"] = float("nan")
    return df


def _ms_to_sec_optional(series: pd.Series) -> pd.Series:
    """Converte milissegundos em segundos (float); NULL vira NaN."""

    def one(v: Any) -> float:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return float("nan")
        if pd.isna(v):
            return float("nan")
        return float(v) / 1000.0

    return series.apply(one)


def _apply_team_overrides_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ajusta equipe/cor por regras pontuais e sincroniza hex com season_2026_data."""
    if df.empty or "team_name" not in df.columns:
        return df
    out = df.copy()
    stg = out["stage_number"].astype(int)
    car = out["car_number"].astype(int)
    for i in out.index:
        team = apply_stage_team_overrides(int(stg.at[i]), int(car.at[i]), str(out.at[i, "team_name"]))
        out.at[i, "team_name"] = normalize_team_name(team)
        if "team_color_hex" in out.columns:
            _, chex = team_chart_color(team)
            out.at[i, "team_color_hex"] = chex
    return out


def load_race_dataframe(
    stage_number: int,
    race_type: str,
    db_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Uma corrida (etapa + Sprint/Principal) no formato próximo ao usado nas páginas 2024/2025.
    """
    ensure_db_ready(db_path)
    q = """
        SELECT p.id, p.stage_number, p.race_type, p.car_number, p.pit_lap, p.race_position,
               p.pneu1, p.pneu2,
               p.tempo_troca_pneus_ms, p.tempo_total_ms,
               p.tempo_reacao_air_jack_ms, p.tempo_primeira_conexao_ms,
               p.tempo_troca1_ms, p.tempo_troca2_ms,
               p.video_link, p.notes, p.detail_level,
               d.pilot_name, d.display_label, d.team_name, d.is_amattheis_extended,
               d.amattheis_color_hex,
               t.chart_color_hex AS team_color_hex
        FROM pit_stop_events_2026 p
        JOIN drivers_2026 d ON d.car_number = p.car_number
        JOIN teams_2026 t ON t.team_name = d.team_name
        WHERE p.stage_number = ? AND p.race_type = ?
        ORDER BY p.pit_lap, p.car_number
    """
    with connect(db_path) as conn:
        df = pd.read_sql_query(q, conn, params=[stage_number, race_type])
    if df.empty:
        return df
    df = _enrich_pit_df_columns(df)
    df["corrida_label"] = f"Etapa {stage_number} — {race_type}"
    return _apply_team_overrides_df(df)


def load_season_dataframe_2026(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Todos os pit stops gravados na temporada 2026 (SQLite)."""
    ensure_db_ready(db_path)
    q = """
        SELECT p.id, p.stage_number, p.race_type, p.car_number, p.pit_lap, p.race_position,
               p.pneu1, p.pneu2,
               p.tempo_troca_pneus_ms, p.tempo_total_ms,
               p.tempo_reacao_air_jack_ms, p.tempo_primeira_conexao_ms,
               p.tempo_troca1_ms, p.tempo_troca2_ms,
               p.video_link, p.notes, p.detail_level,
               d.pilot_name, d.display_label, d.team_name, d.is_amattheis_extended,
               d.amattheis_color_hex,
               t.chart_color_hex AS team_color_hex
        FROM pit_stop_events_2026 p
        JOIN drivers_2026 d ON d.car_number = p.car_number
        JOIN teams_2026 t ON t.team_name = d.team_name
        ORDER BY p.stage_number, p.race_type, p.pit_lap, p.car_number
    """
    with connect(db_path) as conn:
        df = pd.read_sql_query(q, conn)
    if df.empty:
        return df
    df = _enrich_pit_df_columns(df)
    df["corrida_label"] = (
        "E" + df["stage_number"].astype(str) + " " + df["race_type"].astype(str)
    )
    return _apply_team_overrides_df(df)


def fetch_pit_events(
    stage_number: Optional[int] = None,
    race_type: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[sqlite3.Row]:
    ensure_db_ready(db_path)
    q = (
        "SELECT p.*, d.display_label AS driver_label "
        "FROM pit_stop_events_2026 p "
        "JOIN drivers_2026 d ON d.car_number = p.car_number WHERE 1=1"
    )
    params: List[Any] = []
    if stage_number is not None:
        q += " AND p.stage_number = ?"
        params.append(stage_number)
    if race_type is not None:
        q += " AND p.race_type = ?"
        params.append(race_type)
    q += " ORDER BY p.stage_number, p.race_type, p.pit_lap, p.car_number"
    with connect(db_path) as conn:
        cur = conn.execute(q, params)
        return cur.fetchall()


def delete_pit_event(event_id: int, db_path: Optional[Path] = None) -> bool:
    ensure_db_ready(db_path)
    with sqlite3.connect(get_db_path(db_path)) as conn:
        cur = conn.execute("DELETE FROM pit_stop_events_2026 WHERE id = ?", (event_id,))
        conn.commit()
        return cur.rowcount > 0


def upsert_pit_stop_event(
    *,
    stage_number: int,
    race_type: str,
    car_number: int,
    pit_lap: int,
    race_position: str,
    pneu1: Optional[str],
    pneu2: Optional[str],
    tempo_troca_pneus_ms: Optional[int],
    tempo_total_ms: int,
    tempo_reacao_air_jack_ms: Optional[int],
    tempo_primeira_conexao_ms: Optional[int],
    tempo_troca1_ms: Optional[int],
    tempo_troca2_ms: Optional[int],
    video_link: Optional[str],
    notes: Optional[str],
    detail_level: str,
    db_path: Optional[Path] = None,
) -> Tuple[int, str]:
    """
    Insere ou atualiza pelo índice único (etapa, tipo de corrida, carro, volta do pit).
    Retorna (id, 'inserted'|'updated').
    """
    ensure_db_ready(db_path)
    cols = (
        stage_number,
        race_type,
        car_number,
        pit_lap,
        race_position,
        pneu1,
        pneu2,
        tempo_troca_pneus_ms,
        tempo_total_ms,
        tempo_reacao_air_jack_ms,
        tempo_primeira_conexao_ms,
        tempo_troca1_ms,
        tempo_troca2_ms,
        video_link,
        notes,
        detail_level,
    )
    sql_insert = """
        INSERT INTO pit_stop_events_2026 (
            stage_number, race_type, car_number, pit_lap, race_position,
            pneu1, pneu2, tempo_troca_pneus_ms, tempo_total_ms,
            tempo_reacao_air_jack_ms, tempo_primeira_conexao_ms, tempo_troca1_ms, tempo_troca2_ms,
            video_link, notes, detail_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(stage_number, race_type, car_number, pit_lap) DO UPDATE SET
            race_position = excluded.race_position,
            pneu1 = excluded.pneu1,
            pneu2 = excluded.pneu2,
            tempo_troca_pneus_ms = excluded.tempo_troca_pneus_ms,
            tempo_total_ms = excluded.tempo_total_ms,
            tempo_reacao_air_jack_ms = excluded.tempo_reacao_air_jack_ms,
            tempo_primeira_conexao_ms = excluded.tempo_primeira_conexao_ms,
            tempo_troca1_ms = excluded.tempo_troca1_ms,
            tempo_troca2_ms = excluded.tempo_troca2_ms,
            video_link = excluded.video_link,
            notes = excluded.notes,
            detail_level = excluded.detail_level,
            updated_at = datetime('now')
    """
    path = get_db_path(db_path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute(
            "SELECT id FROM pit_stop_events_2026 WHERE stage_number = ? AND race_type = ? "
            "AND car_number = ? AND pit_lap = ?",
            (stage_number, race_type, car_number, pit_lap),
        )
        existed = cur.fetchone()
        conn.execute(sql_insert, cols)
        conn.commit()
        cur2 = conn.execute(
            "SELECT id FROM pit_stop_events_2026 WHERE stage_number = ? AND race_type = ? "
            "AND car_number = ? AND pit_lap = ?",
            (stage_number, race_type, car_number, pit_lap),
        )
        row = cur2.fetchone()
        eid = int(row[0]) if row else 0
        action = "updated" if existed else "inserted"
        return eid, action


if __name__ == "__main__":
    p = seed_reference_data()
    print(f"SQLite 2026 inicializado e referências carregadas em: {p.resolve()}")
