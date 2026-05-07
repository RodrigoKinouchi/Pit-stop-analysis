from __future__ import annotations

import io
import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd


def _norm(text: str) -> str:
    s = (text or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class UploadParseResult:
    df: pd.DataFrame
    warnings: List[str]


def build_driver_lookup(drivers_rows: List) -> Dict[str, int]:
    lookup: Dict[str, int] = {}
    for d in drivers_rows:
        car = int(d["car_number"])
        pilot = str(d["pilot_name"])
        display = str(d["display_label"])
        lookup[_norm(pilot)] = car
        lookup[_norm(display)] = car

        parts = _norm(pilot).split()
        if parts:
            lookup[parts[-1]] = car  # sobrenome
            if len(parts) >= 2:
                lookup[f"{parts[0][0]} {parts[-1]}"] = car  # inicial + sobrenome
    return lookup


def _pit_report_alias(name: str) -> str:
    aliases = {
        "e elias": "enzo elias",
        "g di mauro": "gaetano di mauro",
        "r zonta": "ricardo zonta",
        "casagrande": "gabriel casagrande",
        "gui salas": "guilherme salas",
        "r barrichello": "rubens barrichello",
        "j campos": "julio campos",
        "muggiati": "zezinho muggiati",
        "a khodair": "allam khodair",
        "f massa": "felipe massa",
        "h castroneves": "helio castroneves",
        "a ibiapina": "alfredinho ibiapina",
        "leo reis": "leonardo reis",
        "r mauricio": "ricardo mauricio",
        "a leist": "arthur leist",
        "r suzuki": "rafael suzuki",
        "n piquet": "nelson piquet jr",
        "c ramos": "cesar ramos",
        "t camilo": "thiago camilo",
        "v orige": "vicente orige",
        "r guerra": "renan guerra",
        "f bartz": "felipe bartz",
        "sette camara": "sergio sette camara",
        "f baptista": "felipe baptista",
        "d serra": "daniel serra",
    }
    return aliases.get(name, name)


def _map_driver_to_car(driver_name: str, driver_lookup: Dict[str, int]) -> Optional[int]:
    key = _pit_report_alias(_norm(driver_name))
    if key in driver_lookup:
        return driver_lookup[key]
    return None


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "etapa": "stage_number",
        "corrida": "race_type",
        "carro": "car_number",
        "volta_pit": "pit_lap",
        "pitlap": "pit_lap",
        "posicao": "race_position",
        "pos": "race_position",
        "tempo_pit_s": "tempo_total",
        "tempo pit": "tempo_total",
        "tempo_total_s": "tempo_total",
    }
    out = df.copy()
    mapped = {}
    for c in out.columns:
        mapped[c] = rename.get(_norm(str(c)), c)
    out = out.rename(columns=mapped)
    return out


def parse_structured_file(file_bytes: bytes, filename: str) -> UploadParseResult:
    warnings: List[str] = []
    fn = filename.lower()
    if fn.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif fn.endswith(".xlsx") or fn.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Formato estruturado inválido. Use CSV ou Excel.")

    df = _standardize_columns(df)
    return UploadParseResult(df=df, warnings=warnings)


def extract_text_from_upload(file_bytes: bytes, filename: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    fn = filename.lower()

    if fn.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore"), warnings

    if fn.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages), warnings
        except Exception as ex:
            raise ValueError(f"Falha ao ler PDF: {ex}")

    if fn.endswith(".png") or fn.endswith(".jpg") or fn.endswith(".jpeg"):
        try:
            import pytesseract  # type: ignore
            from PIL import Image

            img = Image.open(io.BytesIO(file_bytes))
            local_tessdata = os.path.expanduser(r"~\tessdata")
            tess_config = ""
            if os.path.exists(os.path.join(local_tessdata, "por.traineddata")):
                tess_config = f'--tessdata-dir "{local_tessdata}"'
            txt = pytesseract.image_to_string(img, lang="por+eng", config=tess_config)
            warnings.append("OCR aplicado na imagem. Revise os dados antes de gravar.")
            return txt, warnings
        except Exception as ex:
            raise ValueError(
                "Não foi possível extrair texto da imagem. "
                f"Instale/configure Tesseract OCR no ambiente. Detalhe: {ex}"
            )

    raise ValueError("Formato de arquivo não suportado para extração de texto.")


def parse_pit_report_text(
    raw_text: str, driver_lookup: Dict[str, int], default_stage: Optional[int] = None
) -> UploadParseResult:
    """
    Parser tolerante a mudanças de layout:
    captura linhas no padrão:
    2026 03 SP 1 Pit1 Felipe Fraga 3.750
    """
    warnings: List[str] = []
    rows: List[dict] = []

    pattern = re.compile(
        r"^\s*(20\d{2})\s+(\d{1,2})\s+[A-Z]{2,4}\s+([12])\s+Pit\d+\s+(.+?)\s+(\d+\.\d{2,3})\s*$",
        re.IGNORECASE,
    )

    for line in (raw_text or "").splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        _, stage, corr, pilot, tempo = m.groups()
        # Evita capturar tabelas de movimento/troca que trazem numeros extras no "nome".
        if any(ch.isdigit() for ch in pilot):
            continue
        car = _map_driver_to_car(pilot, driver_lookup)
        if car is None:
            warnings.append(f"Piloto não mapeado automaticamente: {pilot}")
            continue

        rows.append(
            {
                "stage_number": int(stage) if stage else (default_stage or 0),
                "race_type": "Sprint" if str(corr) == "1" else "Principal",
                "car_number": car,
                "tempo_total": str(tempo),
                "tempo_troca_pneus": str(tempo),
                "pilot_from_report": pilot,
            }
        )

    return UploadParseResult(df=pd.DataFrame(rows), warnings=warnings)


def parse_results_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    fn = filename.lower()
    if fn.endswith((".csv", ".xlsx", ".xls")):
        parsed = parse_structured_file(file_bytes, filename).df
    else:
        txt, _ = extract_text_from_upload(file_bytes, filename)
        parsed = parse_results_text(txt)
    parsed = _standardize_columns(parsed)
    # Aceita as colunas do CSV gerado no fluxo anterior
    if "corrida" in parsed.columns and "race_type" not in parsed.columns:
        parsed["race_type"] = parsed["corrida"]
    if "pos_final" in parsed.columns and "race_position" not in parsed.columns:
        parsed["race_position"] = parsed["pos_final"]
    cols_needed = {"race_type", "car_number", "pit_lap", "race_position"}
    if not cols_needed.issubset(set(parsed.columns)):
        raise ValueError(
            "Arquivo de resultados precisa ter: race_type, car_number, pit_lap, race_position (ou pos_final)."
        )
    return parsed


def parse_results_text(raw_text: str) -> pd.DataFrame:
    """
    Parser tolerante para PDF de resultado oficial.
    Extrai: race_type, car_number, pit_lap, race_position.
    """
    rows: List[dict] = []
    race_type = "Sprint"
    for line in (raw_text or "").splitlines():
        ln = (line or "").strip()
        low = _norm(ln)
        if "2 corrida" in low or "2a corrida" in low:
            race_type = "Principal"
            continue
        if "1 corrida" in low or "1a corrida" in low:
            race_type = "Sprint"
            continue
        # Ex.: "1 293 LEONARDO REIS ... 5 1" (pos, carro, ..., in, pits)
        m = re.match(r"^\s*(\d{1,2})\s+(\d{1,3})\s+.+\s+(\d{1,2})\s+(\d)\s*$", ln)
        if not m:
            continue
        pos = int(m.group(1))
        car = int(m.group(2))
        pit_lap = int(m.group(3))
        rows.append(
            {
                "race_type": race_type,
                "car_number": car,
                "pit_lap": pit_lap,
                "race_position": pos,
            }
        )
    # Sempre devolve schema consistente, mesmo vazio
    return pd.DataFrame(rows, columns=["race_type", "car_number", "pit_lap", "race_position"])


def merge_with_results(import_df: pd.DataFrame, results_df: pd.DataFrame) -> pd.DataFrame:
    if import_df.empty:
        return import_df
    out = import_df.copy()
    key_cols = ["race_type", "car_number"]
    m = results_df[key_cols + ["pit_lap", "race_position"]].drop_duplicates(key_cols, keep="first")
    out = out.merge(m, on=key_cols, how="left", suffixes=("", "_res"))
    if "pit_lap_res" in out.columns:
        out["pit_lap"] = out.get("pit_lap").fillna(out["pit_lap_res"])
        out = out.drop(columns=["pit_lap_res"])
    if "race_position_res" in out.columns:
        out["race_position"] = out.get("race_position").fillna(out["race_position_res"])
        out = out.drop(columns=["race_position_res"])
    return out
