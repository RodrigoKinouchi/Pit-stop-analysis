"""Corrige tempo_troca_parado Sprint etapa 4; limpa tempo_troca_pneus até tabela de pneus."""
from pathlib import Path

# Tabela Pit1 corrida 1 (Sprint) — tempo parado em segundos
SPRINT_PARADO: dict[int, str] = {
    51: "3,570",
    11: "3,590",
    18: "3,780",
    19: "3,840",
    1: "3,910",
    10: "3,940",
    33: "3,970",
    22: "4,000",
    29: "4,040",
    38: "4,070",
    7: "4,090",
    83: "4,100",
    8: "4,160",
    111: "4,410",
    30: "4,430",
    4: "4,660",
    85: "4,680",
    0: "4,720",
    301: "4,780",
    121: "4,850",
    90: "4,900",
    293: "4,900",
    21: "4,940",
    80: "4,970",
    54: "5,090",
    81: "5,120",
    95: "5,220",
    73: "5,840",
    444: "7,470",
    24: "7,870",
    12: "10,000",
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
        if parts[1] == "SPRINT":
            car = int(parts[2])
            parado = SPRINT_PARADO.get(car)
            if parado:
                parts[6] = parado
            parts[7] = ""  # tempo_troca_pneus: aguardando tabela correta
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
