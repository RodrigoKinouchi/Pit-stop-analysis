"""Preenche tempo_troca_pneus no stage4.csv (tabela Pit1 — col. 10)."""
from pathlib import Path

# car_number -> tempo (vírgula decimal); corrida 1=SPRINT, 2=PRINCIPAL
SPRINT_PNEUS: dict[int, str] = {
    51: "2,40",
    12: "2,63",
    33: "2,63",
    10: "3,18",
    83: "2,78",
    30: "2,87",
    29: "2,88",
    11: "2,91",
    38: "3,00",
    22: "3,00",
    7: "3,00",
    21: "3,09",
    85: "3,10",
    1: "3,16",
    54: "3,25",
    18: "3,28",
    19: "3,34",
    95: "3,37",
    301: "3,41",
    121: "3,43",
    90: "3,53",
    0: "3,59",
    4: "3,63",
    111: "3,72",
    80: "3,78",
    293: "3,78",
    444: "3,81",
    81: "4,06",
    73: "4,25",
    24: "7,03",
    8: "3,50",
}

PRINCIPAL_PNEUS: dict[int, str] = {
    111: "2,28",
    29: "2,56",
    22: "2,60",
    21: "2,75",
    54: "2,75",
    73: "2,75",
    30: "2,78",
    27: "2,79",
    18: "2,85",
    0: "2,87",
    12: "2,94",
    83: "3,03",
    301: "3,06",
    19: "3,12",
    293: "3,28",
    38: "3,35",
    7: "3,50",
    80: "3,56",
    24: "3,72",
}


def fix(path: Path) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    out = [lines[0]]
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(";")
        while len(parts) < 11:
            parts.append("")
        car = int(parts[2])
        if parts[1] == "SPRINT":
            t = SPRINT_PNEUS.get(car)
            if t:
                parts[7] = t
        elif parts[1] == "PRINCIPAL":
            t = PRINCIPAL_PNEUS.get(car)
            if t:
                parts[7] = t
        out.append(";".join(parts))
    path.write_text("\n".join(out) + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    for p in (
        Path(r"c:\Users\rodri\Desktop\Etapas 2026\S26E04 - Goiania\stage4.csv"),
        Path(__file__).resolve().parent / "stage4.csv",
    ):
        if p.exists():
            fix(p)
            print("OK", p)
