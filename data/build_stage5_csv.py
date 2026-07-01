"""Gera stage5.csv — Etapa 05 Cuiabá (Principal; Sprint sem pit)."""
from pathlib import Path

HEADER = (
    "stage_number;race_type;car_number;pit_lap;race_position;"
    "tempo_total;tempo_troca_parado;tempo_troca_pneus;pneu1;pneu2;video_link"
)

# (car, pos, pit_lap, tempo_total, parado, pneus, p1, p2)
# tempo_total = duração pit lane (col. preta Chronon, segundos com vírgula).
# Massa #19: 1º pit volta 6 (2º pit volta 21 — fora deste CSV).
# Kohl #95: 3 pits no relatório; usamos volta 9 (pit principal da análise).
# Muggiati #38: volta 7 sem duração no print — tempo_total em branco.
PRINCIPAL = [
    (33, "1", 9, "70,372", "8,310", "2,19", "DD", "TD"),
    (1, "2", 8, "71,034", "8,810", "3,03", "DD", "TD"),
    (29, "3", 9, "71,906", "8,900", "2,50", "DD", "TD"),
    (111, "4", 9, "71,522", "8,720", "3,03", "DD", "TD"),
    (7, "5", 9, "72,577", "10,090", "3,22", "DD", "TD"),
    (121, "6", 8, "70,955", "9,030", "2,94", "DD", "TD"),
    (90, "7", 9, "70,937", "8,620", "3,37", "DD", "TD"),
    (0, "8", 7, "71,514", "10,130", "2,91", "DD", "TD"),
    (6, "9", 7, "70,749", "8,680", "2,65", "DD", "TD"),
    (21, "10", 9, "71,158", "9,250", "2,62", "DD", "TD"),
    (293, "11", 8, "77,576", "15,720", "3,63", "DD", "TD"),
    (85, "12", 7, "70,341", "8,150", "2,94", "DD", "TD"),
    (72, "13", 7, "71,427", "8,650", "2,90", "DD", "TD"),
    (27, "14", 7, "72,259", "10,060", "2,59", "DD", "TD"),
    (22, "15", 8, "72,279", "10,090", "2,97", "DD", "TD"),
    (301, "16", 7, "72,477", "11,060", "3,03", "DD", "TD"),
    (12, "17", 9, "72,468", "9,970", "2,72", "DD", "TD"),
    (83, "18", 7, "72,939", "10,500", "3,12", "TE", "DE"),
    (51, "19", 14, "71,203", "8,840", "2,40", "DD", "TD"),
    (8, "20", 14, "76,117", "15,340", "2,72", "DD", "TD"),
    (19, "21", 6, "59,894", "8,280", "2,85", "DD", "TD"),
    (95, "22", 9, "71,971", "9,780", "4,00", "DD", "TD"),
    (73, "23", 9, "70,904", "8,250", "2,84", "DD", "TD"),
    (11, "NC", 7, "70,545", "8,500", "2,78", "DD", "TD"),
    (18, "NC", 7, "71,079", "8,400", "2,50", "DD", "TD"),
    (38, "NC", 7, "", "13,100", "3,96", "TE", "DE"),
]


def row(car: int, pos: str, lap: int, total: str, parado: str, pneus: str, p1: str, p2: str) -> str:
    return f"5;PRINCIPAL;{car};{lap};{pos};{total};{parado};{pneus};{p1};{p2};"


def main() -> None:
    out = Path(__file__).resolve().parent / "stage5.csv"
    lines = [HEADER] + [row(*r) for r in PRINCIPAL]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(PRINCIPAL)} pits)")


if __name__ == "__main__":
    main()
