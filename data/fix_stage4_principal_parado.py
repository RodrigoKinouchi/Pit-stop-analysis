"""tempo_troca_parado — Principal etapa 4 (corrida 2 / Pit1)."""
from pathlib import Path

PRINCIPAL_PARADO: dict[int, str] = {
    111: "6,710",
    8: "7,880",
    29: "7,970",
    22: "8,340",
    121: "8,690",
    19: "8,810",
    21: "8,970",
    27: "10,150",
    30: "10,180",
    0: "10,190",
    11: "9,8",
    33: "10,290",
    73: "10,310",
    10: "10,780",
    18: "10,850",
    83: "10,940",
    54: "11,000",
    80: "11,090",
    7: "11,250",
    38: "12,590",
    12: "13,440",
    293: "13,840",
    24: "14,250",
    301: "15,070",
    444: "22,250",
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
        if parts[1] == "PRINCIPAL":
            car = int(parts[2])
            parado = PRINCIPAL_PARADO.get(car)
            if parado is not None:
                parts[6] = parado
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
