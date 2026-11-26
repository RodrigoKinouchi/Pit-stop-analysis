"""Gera stage10.csv (Cascavel) a partir do Excel CAS + Chronon P1/P2 + resultados."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import openpyxl
import pdfplumber

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "stage10.csv"
DETALHE = ROOT / "stage10_principal_pneus_detalhe.csv"

XLSX = Path(r"C:\Users\rodri\Downloads\Etapa_10_CAS_PitStop.xlsx")
P1_PITS = Path(r"C:\Users\rodri\Downloads\SP26_10_P1_PITS.pdf")
P2_PITS = Path(r"C:\Users\rodri\Downloads\SP26_10_P2_PITS.pdf")
P1_RES = Path(r"C:\Users\rodri\Downloads\SP26_10_P1_RES_ALT.pdf")
P2_RES = Path(r"C:\Users\rodri\Downloads\RESULTADO_-_2a_CORRIDA.pdf")

HEADER = (
    "stage_number;race_type;car_number;pit_lap;race_position;tempo_total;"
    "tempo_carro_parado;tempo_troca_pneus;pneu1;pneu2;video_link"
)


def fmt(v: float | None) -> str:
    if v is None:
        return ""
    return f"{float(v):.3f}".replace(".", ",")


def pt_to_sec(s: str | None) -> float | None:
    if not s:
        return None
    if ":" in s:
        m, rest = s.split(":", 1)
        return round(float(m) * 60 + float(rest), 3)
    return round(float(s), 3)


def parse_chronon(pdf: Path) -> list[dict]:
    rows: list[dict] = []
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            for line in (page.extract_text() or "").splitlines():
                m = re.search(
                    r"^(\d+)\s+.+?\s+(\d+)\s+(\d{1,2}:\d{2}:\d{2}\.\d+)(?:\s+(\d+:\d{2}\.\d+|\d+\.\d+))?\s*$",
                    line.strip(),
                )
                if not m:
                    continue
                car, lap, tod, pt = m.groups()
                rows.append(
                    {
                        "car": int(car),
                        "lap": int(lap),
                        "tod": tod,
                        "pt": pt_to_sec(pt),
                    }
                )
    return rows


def parse_results(pdf: Path) -> dict[int, str]:
    """Pos final por carro (número ou NC)."""
    text = ""
    with pdfplumber.open(pdf) as doc:
        for page in doc.pages:
            text += (page.extract_text() or "") + "\n"
    pos: dict[int, str] = {}
    # Classificados: "1 1 FELIPE..." / "23 95 LUCAS..."
    for m in re.finditer(
        r"(?m)^(\d+)\s+(\d+)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]",
        text,
    ):
        pos[int(m.group(2))] = m.group(1)
    # Não classificados: "21 THIAGO..." sem pos numérica no início da secção
    # Heurística: linhas "# DRIVER" após "Not classified"
    nc_zone = False
    for line in text.splitlines():
        if "Not classified" in line or "Não classificado" in line:
            nc_zone = True
            continue
        if nc_zone:
            m = re.match(r"^(\d+)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", line.strip())
            if m:
                car = int(m.group(1))
                if car not in pos:
                    pos[car] = "NC"
    return pos


def sheet_rows(wb, name: str) -> list[tuple]:
    return [tuple(r) for r in wb[name].iter_rows(values_only=True)][1:]


def pick_chronon(rows: list[dict], car: int, parado: float | None) -> dict | None:
    cands = [r for r in rows if r["car"] == car and r["pt"] is not None]
    if not cands:
        cands = [r for r in rows if r["car"] == car]
    if not cands:
        return None
    if parado is not None and len(cands) > 1:
        # Preferir pit cujo total seja coerente com parado (total >> parado).
        # Em desastres, total ≈ parado + deslocamento ainda maior.
        scored = sorted(
            cands,
            key=lambda r: (
                0 if (r["pt"] is not None and r["pt"] > parado + 20) else 1,
                abs((r["pt"] or 0) - (parado + 55)),  # pit lane Cascavel ~60s
                r["tod"],
            ),
        )
        return scored[0]
    return sorted(cands, key=lambda r: r["tod"])[0]


def main() -> None:
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    p1 = parse_chronon(P1_PITS)
    p2 = parse_chronon(P2_PITS)
    pos1 = parse_results(P1_RES)
    pos2 = parse_results(P2_RES)

    # Sprint: parado
    sprint_par: dict[int, tuple[float, str | None]] = {}
    for pos, car, parado, pneu in sheet_rows(wb, "Corr 1 - Tempo Pit"):
        if car is None:
            continue
        sprint_par[int(car)] = (float(parado), (str(pneu).strip() if pneu else None))

    sprint_pneus: dict[int, tuple[float, str]] = {}
    for row in sheet_rows(wb, "Corr 1 - Pneus"):
        car = int(row[1])
        de, dd, td, te, rap, lado = row[2:8]
        times = []
        sides = []
        for lab, v in (("DE", de), ("DD", dd), ("TD", td), ("TE", te)):
            if v is not None:
                times.append(float(v))
                sides.append(lab)
        if not times and rap is not None:
            times = [float(rap)]
            sides = [str(lado).strip()] if lado else ["?"]
        sprint_pneus[car] = (sum(times), sides[0] if sides else (str(lado) if lado else ""))

    # Principal: parado
    prin_par: dict[int, tuple[float, str | None]] = {}
    for pos, car, parado, pneus in sheet_rows(wb, "Corr 2 - Tempo Pit"):
        if car is None:
            continue
        prin_par[int(car)] = (float(parado), (str(pneus).strip() if pneus else None))

    prin_pneus: dict[int, tuple[float, list[tuple[str, float]], str, str]] = {}
    for row in sheet_rows(wb, "Corr 2 - Pneus"):
        car = int(row[1])
        de, dd, td, te, rap, lado = row[2:8]
        pairs: list[tuple[str, float]] = []
        for lab, v in (("DE", de), ("DD", dd), ("TD", td), ("TE", te)):
            if v is not None:
                pairs.append((lab, float(v)))
        if not pairs and rap is not None:
            pairs = [("?", float(rap))]
        full = sum(v for _, v in pairs)
        if len(pairs) >= 2:
            p1n, p2n = pairs[0][0], pairs[1][0]
        elif len(pairs) == 1:
            p1n, p2n = pairs[0][0], ""
        else:
            p1n, p2n = "Não registrado", ""
        # Se 2 lados típicos DD,TD
        if {p[0] for p in pairs} == {"DD", "TD"}:
            p1n, p2n = "DD", "TD"
        prin_pneus[car] = (full, pairs, p1n, p2n)

    out: list[dict] = []
    detalhe_rows: list[dict] = []

    for car, (parado, lado) in sorted(sprint_par.items()):
        hit = pick_chronon(p1, car, parado)
        pneu_sum, pneu_side = sprint_pneus.get(car, (None, lado or ""))
        if pneu_side and not lado:
            lado = pneu_side
        out.append(
            {
                "stage_number": "10",
                "race_type": "SPRINT",
                "car_number": str(car),
                "pit_lap": str(hit["lap"]) if hit else "",
                "race_position": pos1.get(car, "NC"),
                "tempo_total": fmt(hit["pt"]) if hit and hit["pt"] is not None else "",
                "tempo_carro_parado": fmt(parado),
                "tempo_troca_pneus": fmt(pneu_sum),
                "pneu1": (lado or pneu_side or "Não registrado"),
                "pneu2": "",
                "video_link": "",
            }
        )
        if hit is None:
            print(f"WARN Sprint #{car}: sem Chronon")

    for car, (parado, lados) in sorted(prin_par.items()):
        hit = pick_chronon(p2, car, parado)
        if car in prin_pneus:
            full, pairs, p1n, p2n = prin_pneus[car]
            detalhe = "|".join(f"{lab}:{v:.3f}" for lab, v in pairs)
            detalhe_rows.append({"car_number": car, "pneus_detalhe": detalhe})
        else:
            full, p1n, p2n = None, "Não registrado", ""
            # fallback lados do sheet parado
            if lados and "," in lados:
                a, b = [x.strip() for x in lados.split(",", 1)]
                p1n, p2n = a, b
        out.append(
            {
                "stage_number": "10",
                "race_type": "PRINCIPAL",
                "car_number": str(car),
                "pit_lap": str(hit["lap"]) if hit else "",
                "race_position": pos2.get(car, "NC"),
                "tempo_total": fmt(hit["pt"]) if hit and hit["pt"] is not None else "",
                "tempo_carro_parado": fmt(parado),
                "tempo_troca_pneus": fmt(full),
                "pneu1": p1n,
                "pneu2": p2n,
                "video_link": "",
            }
        )
        if hit is None:
            print(f"WARN Principal #{car}: sem Chronon")

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER.split(";"), delimiter=";")
        w.writeheader()
        w.writerows(out)

    with DETALHE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["car_number", "pneus_detalhe"], delimiter=";")
        w.writeheader()
        w.writerows(detalhe_rows)

    n_s = sum(1 for r in out if r["race_type"] == "SPRINT")
    n_p = sum(1 for r in out if r["race_type"] == "PRINCIPAL")
    print(f"Wrote {OUT.name}: Sprint={n_s} Principal={n_p} total={len(out)}")
    print(f"Wrote {DETALHE.name}: {len(detalhe_rows)} detalhe")
    for r in out[:3] + out[n_s : n_s + 3]:
        print(
            f"  {r['race_type']} #{r['car_number']}: lap={r['pit_lap']} "
            f"pos={r['race_position']} tot={r['tempo_total']} "
            f"par={r['tempo_carro_parado']} pneu={r['tempo_troca_pneus']} "
            f"{r['pneu1']}/{r['pneu2']}"
        )


if __name__ == "__main__":
    main()
