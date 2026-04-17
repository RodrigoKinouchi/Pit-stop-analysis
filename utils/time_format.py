"""
Formato de tempos: ss.mmm (segundos com três casas decimais, milissegundos).

Ex.: 12.852 → 12 segundos e 852 milissegundos.
Armazenamento recomendado no SQLite: INTEGER (milissegundos totais) para evitar erro de ponto flutuante.
"""

from __future__ import annotations

import re
from typing import Optional

_SS_MMM_PATTERN = re.compile(r"^\s*(\d+)\.(\d{1,3})\s*$")
_NR_TOKENS = frozenset(
    x.lower()
    for x in (
        "",
        "nr",
        "n/r",
        "nao registrado",
        "não registrado",
        "-",
        "—",
    )
)


def parse_ss_mmm_to_ms(value: Optional[str]) -> Optional[int]:
    """
    Converte string no formato ss.mmm para milissegundos inteiros.
    Aceita 1–3 dígitos na parte fracionária (ex.: 12.8 → 12.800 s).

    Retorna None para valores ausentes / 'não registrado' / inválidos.
    """
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in _NR_TOKENS:
        return None
    m = _SS_MMM_PATTERN.match(s)
    if not m:
        return None
    sec = int(m.group(1))
    frac = m.group(2).ljust(3, "0")[:3]
    return sec * 1000 + int(frac)


def format_ms_to_ss_mmm(ms: Optional[int]) -> Optional[str]:
    """Formata milissegundos como ss.mmm. None permanece None."""
    if ms is None:
        return None
    if ms < 0:
        raise ValueError("ms deve ser >= 0")
    sec, rem = divmod(ms, 1000)
    return f"{sec}.{rem:03d}"


def ms_to_seconds_float(ms: Optional[int]) -> Optional[float]:
    """Útil para integração com libs que esperam segundos em float."""
    if ms is None:
        return None
    return ms / 1000.0
