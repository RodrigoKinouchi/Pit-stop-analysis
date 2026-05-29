"""Restaura pneu1/pneu2 Sprint (relatório interno) após correção de tempo_troca_parado."""
from pathlib import Path

SPRINT_PNEU1: dict[int, str] = {
    51: "DD",
    38: "TD",
    7: "TD",
    18: "TD",
    1: "DD",
    19: "TD",
    29: "TD",
    111: "TD",
    10: "TD",
    33: "TD",
    301: "DD",
    95: "TD",
    83: "TD",
    121: "TD",
    8: "TD",
    85: "TD",
    90: "TD",
    11: "TD",
    293: "DD",
    22: "TD",
    0: "DD",
    30: "TD",
    21: "TD",
    80: "TD",
    81: "TD",
    54: "DD",
    73: "DD",
    444: "TD",
    24: "TD",
    12: "TD",
    4: "TD",
}

VIDEOS: dict[int, str] = {
    30: "https://www.youtube.com/watch?v=FFAIC3lxp5U&list=PLfSetIZlzqr-4GQoXswLXJlNYvoOKVHq4&index=40",
    21: "https://www.youtube.com/watch?v=2lMteebA3YA&list=PLfSetIZlzqr-4GQoXswLXJlNYvoOKVHq4&index=39",
    54: "https://www.youtube.com/watch?v=XfNBR7GIZ28&list=PLfSetIZlzqr-4GQoXswLXJlNYvoOKVHq4&index=41",
}


def restore(path: Path) -> None:
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
            p1 = SPRINT_PNEU1.get(car, "")
            parts[8] = p1
            parts[9] = ""
            parts[10] = VIDEOS.get(car, "")
        out.append(";".join(parts))
    path.write_text("\n".join(out) + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    for p in (
        Path(r"c:\Users\rodri\Desktop\Etapas 2026\S26E04 - Goiania\stage4.csv"),
        Path(__file__).resolve().parent / "stage4.csv",
    ):
        if p.exists():
            restore(p)
            print("OK", p)
