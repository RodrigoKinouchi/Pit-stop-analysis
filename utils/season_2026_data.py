"""
Dados de referência — Stock Car 2026: calendário, grid (piloto/equipe) e cores para gráficos.

Os tempos de pit stop no app 2026 usam o formato ss.mmm; veja utils.time_format.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

# --- Calendário (12 etapas, 2026) ---
@dataclass(frozen=True)
class Stage2026:
    stage_number: int
    city: str
    circuit_name: str
    event_date: date


CALENDAR_2026: Tuple[Stage2026, ...] = (
    Stage2026(1, "Curvelo/MG", "Circuito dos Cristais", date(2026, 3, 8)),
    Stage2026(2, "Cascavel/PR", "Autódromo Zilmar Beux", date(2026, 3, 29)),
    Stage2026(3, "São Paulo/SP", "Autódromo de Interlagos", date(2026, 4, 26)),
    Stage2026(4, "Goiânia/GO", "Autódromo Internacional Ayrton Senna", date(2026, 5, 17)),
    Stage2026(5, "Cuiabá/MT", "Autódromo Internacional de Mato Grosso", date(2026, 6, 13)),
    Stage2026(6, "Mogi Guaçu/SP", "Autódromo Velocitta", date(2026, 7, 26)),
    Stage2026(7, "Cascavel/PR", "Autódromo Zilmar Beux", date(2026, 8, 9)),
    Stage2026(8, "Chapecó/SC", "Autódromo Internacional de Chapecó", date(2026, 9, 6)),
    Stage2026(9, "Brasília/DF", "Autódromo Internacional Nelson Piquet", date(2026, 9, 27)),
    Stage2026(10, "Goiânia/GO", "Autódromo Internacional Ayrton Senna", date(2026, 10, 18)),
    Stage2026(11, "Nova Santa Rita/SP", "Velopark", date(2026, 11, 15)),
    Stage2026(12, "São Paulo/SP", "Autódromo de Interlagos", date(2026, 12, 13)),
)

# Grid: chave de exibição "número - nome" → equipe (como divulgado)
EQUIPES_PILOTOS_2026: Dict[str, str] = {
    "11 - Gaetano Di Mauro": "EUROFARMA RC",
    "1 - Felipe Fraga": "EUROFARMA RC",
    "4 - Julio Campos": "TMG RACING",
    "83 - Gabriel Casagrande": "VOGEL MOTORSPORT",
    "29 - Daniel Serra": "BLAU MOTORSPORT",
    "7 - Sergio Sette Camara": "TEAM RC",
    "293 - Leonardo Reis": "CAR RACING",
    "8 - Rafael Suzuki": "SCUDERIA BANDEIRAS",
    "111 - Rubens Barrichello": "SCUDERIA BANDEIRAS SPORTS",
    "38 - Zezinho Muggiati": "TEAM RC",
    "21 - Thiago Camilo": "MERCADO LIVRE RACING TEAM",
    "73 - Enzo Elias": "TMG RACING",
    "81 - Arthur Leist": "CROWN RACING",
    "12 - Lucas Foresti": "VOGEL MOTORSPORT",
    "30 - Cesar Ramos": "MERCADO LIVRE RACING TEAM",
    "85 - Guilherme Salas": "VALDA-CAVALEIRO SPORTS",
    "19 - Felipe Massa": "TMG RACING",
    "444 - Vicente Orige": "STERLING RACING",
    "33 - Nelson Piquet Jr": "SCUDERIA BANDEIRAS",
    "0 - Caca Bueno": "SCUDERIA CHIARELLI",
    "18 - Allam Khodair": "BLAU MOTORSPORT",
    "301 - Rafael Reis": "CAR RACING",
    "51 - Atila Abreu": "SCUDERIA BANDEIRAS SPORT",
    "80 - Alfredinho Ibiapina": "FULL TIME GAZOO RACING",
    "27 - Renan Guerra": "AMATTHEIS",
    "6 - Helio Castroneves": "MERCADO LIVRE RACING TEAM",
    "10 - Ricardo Zonta": "FULL TIME GAZOO RACING",
    "22 - Andre Moraes Jr": "SCUDERIA CHIARELLI",
    "95 - Lucas Kohl": "CROWN RACING",
    "90 - Ricardo Mauricio": "VALDA-CAVALEIRO SPORTS",
    "24 - Felipe Bartz": "RTR SG28 TEAM",
    "97 - Bruna Tomaselli": "RTR SG28",
    "121 - Felipe Baptista": "STERLING RACING",
}

# Cores por equipe (nome CSS); complemento para nomes que aparecem no grid mas não na lista original
EQUIPES_COR_2026: Dict[str, str] = {
    "MERCADO LIVRE RACING TEAM": "yellow",
    "MERCADO LIVRE RACING": "yellow",
    "EUROFARMA RC": "greenyellow",
    "VALDA-CAVALEIRO SPORTS": "darkgreen",
    "FULL TIME GAZOO RACING": "crimson",
    "CAR RACING": "orange",
    "TEAM RC": "red",
    "VOGEL MOTORSPORT": "grey",
    "TMG RACING": "darkgreen",
    "RTR SG28 TEAM": "navy",
    "SCUDERIA CHIARELLI": "seashell",
    "RTR SG28": "crimson",
    "BLAU MOTORSPORT": "blue",
    "CROWN RACING": "black",
    "STERLING RACING": "white",
    "SCUDERIA BANDEIRAS SPORTS": "silver",
    "SCUDERIA BANDEIRAS": "lightblue",
    "SCUDERIA BANDEIRAS SPORT": "silver",
    "AMATTHEIS": "navy",
}

# Mapa Amattheis (visualização): destaque para pilotos do programa; demais podem usar neutro no app
PILOTOS_COR_AMATTHEIS_2026: Dict[str, str] = {
    "0 - Caca Bueno": "silver",
    "6 - Helio Castroneves": "green",
    "5 - Denis Navarro": "silver",
    "4 - Julio Campos": "silver",
    "7 - Joao Paulo de Oliveira": "silver",
    "8 - Rafael Suzuki": "silver",
    "9 - Arthur Gama": "silver",
    "10 - Ricardo Zonta": "silver",
    "11 - Gaetano Di Mauro": "silver",
    "12 - Lucas Foresti": "dimgrey",
    "18 - Allam Khodair": "silver",
    "19 - Felipe Massa": "silver",
    "21 - Thiago Camilo": "red",
    "73 - Enzo Elias": "silver",
    "29 - Daniel Serra": "silver",
    "30 - Cesar Ramos": "yellow",
    "33 - Nelson Piquet Jr": "silver",
    "38 - Zezinho Mugiatti": "silver",
    "44- Bruno Baptista": "silver",
    "51 - Atila Abreu": "silver",
    "81 - Arthur Leist": "silver",
    "83 - Gabriel Casagrande": "purple",
    "85 - Guilherme Salas": "silver",
    "1 - Felipe Fraga": "silver",
    "90 - Ricardo Mauricio": "silver",
    "95 - Lucas Kohl": "silver",
    "101 - Gianluca Petecof": "silver",
    "111 - Rubens Barrichello": "silver",
    "121 - Felipe Baptista": "silver",
    "27 - Renan Guerra": "dodgerblue",
}

# Pilotos com telemetria manual estendida (mesmo conjunto acordado para 2026)
AMATTHEIS_EXTENDED_PIT_NUMBERS_2026: frozenset = frozenset({21, 30, 6, 27, 12, 83})

# Nomes CSS → hex (sem dependência de matplotlib)
CSS_NAMED_COLOR_HEX: Dict[str, str] = {
    "yellow": "#FFFF00",
    "greenyellow": "#ADFF2F",
    "darkgreen": "#006400",
    "crimson": "#DC143C",
    "orange": "#FFA500",
    "red": "#FF0000",
    "grey": "#808080",
    "gray": "#808080",
    "navy": "#000080",
    "seashell": "#FFF5EE",
    "blue": "#0000FF",
    "black": "#000000",
    "white": "#FFFFFF",
    "silver": "#C0C0C0",
    "lightblue": "#ADD8E6",
    "green": "#008000",
    "dimgrey": "#696969",
    "dimgray": "#696969",
    "dodgerblue": "#1E90FF",
    "purple": "#800080",
}

NEUTRAL_AMATTHEIS_CHART_HEX = "#5A5A5A"


def css_name_to_hex(name: str) -> str:
    key = name.strip().lower()
    return CSS_NAMED_COLOR_HEX.get(key, "#808080")


def parse_driver_label(label: str) -> Tuple[int, str]:
    """'21 - Thiago Camilo' → (21, 'Thiago Camilo')."""
    parts = label.split(" - ", 1)
    if len(parts) != 2:
        raise ValueError(f"Label de piloto inválido: {label!r}")
    return int(parts[0].strip()), parts[1].strip()


def amattheis_viz_color_for(label: str, car_number: int) -> Tuple[Optional[str], str]:
    """
    Retorna (nome_cor_css_ou_None, hex).
    Faz match por label exato ou pelo mesmo número do carro na tabela Amattheis.
    """
    if label in PILOTOS_COR_AMATTHEIS_2026:
        n = PILOTOS_COR_AMATTHEIS_2026[label]
        return n, css_name_to_hex(n)
    prefix = f"{car_number} -"
    for k, v in PILOTOS_COR_AMATTHEIS_2026.items():
        if k.startswith(prefix):
            return v, css_name_to_hex(v)
    return None, NEUTRAL_AMATTHEIS_CHART_HEX


def team_chart_color(team_name: str) -> Tuple[str, str]:
    """(nome_css, hex) para a equipe; fallback cinza."""
    css = EQUIPES_COR_2026.get(team_name)
    if css is None:
        return "grey", "#808080"
    return css, css_name_to_hex(css)


def all_driver_labels_sorted() -> List[str]:
    return sorted(EQUIPES_PILOTOS_2026.keys(), key=lambda x: parse_driver_label(x)[0])
