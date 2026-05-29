"""Atualiza pit_lap e race_position SPRINT no stage4.csv."""
from pathlib import Path

# Classificação final da Sprint (etapa 4)
SPRINT_RACE_POSITION: dict[int, str] = {
    1: "1",
    33: "2",
    38: "3",
    19: "4",
    83: "5",
    73: "6",
    8: "7",
    51: "8",
    0: "9",
    30: "10",
    11: "11",
    7: "12",
    80: "13",
    293: "14",
    10: "15",
    85: "16",
    12: "17",
    111: "18",
    121: "19",
    29: "20",
    90: "21",
    18: "22",
    81: "23",
    22: "24",
    444: "25",
    54: "26",
    95: "27",
    301: "28",
    24: "29",
    21: "30",
    4: "DNF",
}

# car_number -> pit_lap (PDF SP26_4_P1_PIT; carro 21 = volta 9 com 49,999)
SPRINT_PIT_LAP: dict[int, int] = {
    0: 9,
    1: 9,
    4: 10,
    7: 12,
    8: 12,
    10: 10,
    11: 10,
    12: 12,
    18: 13,
    19: 12,
    21: 9,
    22: 10,
    24: 10,
    29: 13,
    30: 10,
    33: 11,
    38: 10,
    51: 12,
    54: 11,
    73: 12,
    80: 9,
    81: 9,
    83: 9,
    85: 9,
    90: 11,
    95: 10,
    111: 9,
    121: 13,
    293: 12,
    301: 9,
    444: 10,
}

# tempo total do #21 Sprint (ignora pit intermediário 42,976 na volta 10)
CAR_21_TEMPO_TOTAL = "49,999"

# Classificação final da Principal (etapa 4)
PRINCIPAL_RACE_POSITION: dict[int, str] = {
    11: "1",
    7: "2",
    121: "3",
    83: "4",
    80: "5",
    30: "6",
    73: "7",
    19: "8",
    21: "9",
    111: "10",
    33: "11",
    8: "12",
    38: "13",
    51: "14",
    85: "15",
    0: "16",
    12: "17",
    1: "18",
    293: "19",
    22: "20",
    29: "21",
    18: "22",
    90: "23",
    301: "24",
    24: "25",
    95: "26",
    54: "27",
    27: "28",
    81: "29",
    10: "DNF",
    444: "DNF",
}

# pit_lap Principal — SP26_4_P2_PITS.pdf (2ª corrida); #81 = volta 11 (56,887 s)
PRINCIPAL_PIT_LAP: dict[int, int] = {
    0: 17,
    1: 11,
    7: 13,
    8: 8,
    10: 10,
    11: 11,
    12: 14,
    18: 9,
    19: 7,
    21: 22,
    22: 8,
    24: 9,
    27: 10,
    29: 7,
    30: 16,
    33: 12,
    38: 15,
    51: 7,
    54: 7,
    73: 18,
    80: 13,
    81: 11,
    83: 11,
    85: 7,
    90: 9,
    95: 13,
    111: 12,
    121: 13,
    293: 9,
    301: 11,
    444: 9,
}


def main() -> None:
    path = Path(__file__).resolve().parent / "stage4.csv"
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    out = [lines[0]]
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(";")
        if len(parts) < 11:
            out.append(line)
            continue
        if parts[1] == "SPRINT":
            car = int(parts[2])
            lap = SPRINT_PIT_LAP.get(car)
            if lap is not None:
                parts[3] = str(lap)
            pos = SPRINT_RACE_POSITION.get(car)
            if pos is not None:
                parts[4] = pos
            if car == 21:
                parts[5] = CAR_21_TEMPO_TOTAL
            out.append(";".join(parts))
        elif parts[1] == "PRINCIPAL":
            car = int(parts[2])
            lap = PRINCIPAL_PIT_LAP.get(car)
            if lap is not None:
                parts[3] = str(lap)
            pos = PRINCIPAL_RACE_POSITION.get(car)
            if pos is not None:
                parts[4] = pos
            out.append(";".join(parts))
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
    desktop = Path(r"c:\Users\rodri\Desktop\Etapas 2026\S26E04 - Goiania\stage4.csv")
    if desktop.parent.exists():
        desktop.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
    print(f"Atualizado: {path}")


if __name__ == "__main__":
    main()
