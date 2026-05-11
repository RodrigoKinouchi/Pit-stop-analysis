"""
Constantes e dicionários utilizados no aplicativo Pit Stop Report
"""

# Dicionário de nomes dos pilotos (2024 - padrão)
drivers_names = {
    '121': 'Felipe Baptista',
    '91': 'Eduardo Barrichello',
    '4': 'Julio Campos',
    '19': 'Felipe Massa',
    '10': 'Ricardo Zonta',
    '44': 'Bruno Baptista',
    '83': 'Gabriel Casagrande',
    '8': 'Rafael Suzuki',
    '29': 'Daniel Serra',
    '28': 'Enzo Elias',
    '111': 'Rubens Barrichello',
    '21': 'Thiago Camilo',
    '90': 'Ricardo Mauricio',
    '33': 'Nelson Piquet Jr',
    '88': 'Felipe Fraga',
    '30': 'Cesar Ramos',
    '85': 'Guilherme Salas',
    '11': 'Gaetano Di Mauro',
    '51': 'Atila Abreu',
    '81': 'Arthur Leist',
    '12': 'Lucas Foresti',
    '101': 'Gianluca Petecof',
    '0': 'Caca Bueno',
    '120': 'Vitor Baptista',
    '38': 'Zezinho Muggiati',
    '18': 'Allam Khodair',
    '95': 'Lucas Kohl',
    '80': 'Marcos Gomes',
    '35': 'Gabriel Robe',
    '99': 'Luan Lopes',
    '37': 'Raphael Teixeira'
}

# Dicionário de nomes dos pilotos (2025)
# Lista completa da temporada 2025
drivers_names_2025 = {
    '88': 'Felipe Fraga',
    '11': 'Gaetano di Mauro',
    '21': 'Thiago Camilo',
    '85': 'Guilherme Salas',
    '73': 'Enzo Elias',
    '81': 'Arthur Leist',
    '83': 'Gabriel Casagrande',
    '8': 'Rafael Suzuki',
    '33': 'Nelson Piquet Jr',
    '4': 'Julio Campos',
    '121': 'Felipe Baptista',
    '101': 'Gianluca Petecof',
    '30': 'Cesar Ramos',
    '111': 'Rubens Barrichello',
    '29': 'Daniel Serra',
    '7': 'Joao Paulo de Oliveira',
    '51': 'Atila Abreu',
    '18': 'Allam Khodair',
    '90': 'Ricardo Mauricio',
    '12': 'Lucas Foresti',
    '19': 'Felipe Massa',
    '0': 'Caca Bueno',
    '10': 'Ricardo Zonta',
    '9': 'Arthur Gama',
    '44': 'Bruno Baptista',
    '5': 'Denis Navarro',
    '38': 'Zezinho Muggiati',
    '6': 'Helio Castroneves',
    '95': 'Lucas Kohl',
    '301': 'Rafael Reis',
    '444': 'Vicente Orige'
}

# Função para obter dicionário de pilotos por temporada
def get_drivers_names(season: int = 2024):
    """Retorna dicionário de pilotos para a temporada especificada"""
    if season == 2025:
        return drivers_names_2025
    if season == 2026:
        from utils.season_2026_data import EQUIPES_PILOTOS_2026, parse_driver_label

        d = {}
        for lab in EQUIPES_PILOTOS_2026:
            num, name = parse_driver_label(lab)
            d[str(num)] = name
        return d
    return drivers_names


def _team_info_2026() -> dict:
    """Número do carro → nome canónico da equipe (Stock Car 2026)."""
    from utils.season_2026_data import EQUIPES_PILOTOS_2026, parse_driver_label

    out: dict = {}
    for label, team in EQUIPES_PILOTOS_2026.items():
        num, _ = parse_driver_label(label)
        out[num] = team
    return out


# Dicionário de informações dos times (2024)
team_info = {
    121: 'Crown',
    91: 'Mobil Ale',
    4: 'Pole',
    19: 'TMG Racing',
    10: 'RCM Motorsport',
    44: 'RCM Motorsport',
    83: 'AMattheis Vogel',
    8: 'TMG Racing',
    29: 'Eurofarma',
    28: 'Crown',
    111: 'Mobil Ale',
    21: 'Ipiranga Racing',
    90: 'Eurofarma',
    33: 'Cavaleiro',
    88: 'Blau',
    30: 'Ipiranga Racing',
    85: 'KTF Racing',
    11: 'Cavaleiro',
    51: 'Pole',
    81: 'Full Time',
    12: 'AMattheis Vogel',
    101: 'Full Time',
    0: 'KTF Sports',
    120: 'Scuderia',
    38: 'KTF Racing',
    18: 'Blau',
    95: 'Garra',
    35: 'Garra'
}

# Dicionário de informações dos times (2025)
team_info_2025 = {
    0: 'Chiarelli',
    4: 'Crown Racing',
    5: 'Full Time/Cavaleiro',
    6: 'Amattheis',
    7: 'Full Time',
    8: 'TMG Racing',
    9: 'Full Time',
    10: 'RCM Motorsport',
    11: 'Eurofarma',
    12: 'AMattheis Vogel',
    18: 'Blau',
    19: 'TMG Racing',
    21: 'Ipiranga Racing',
    29: 'Blau',
    30: 'Ipiranga Racing',
    33: 'Scuderia Bandeiras Sports',
    38: 'Car Racing Sterling',
    44: 'RCM Motorsport',
    51: 'Scuderia Bandeiras',
    73: 'Scuderia Bandeiras',
    83: 'AMattheis Vogel',
    85: 'Cavaleiro',
    88: 'Eurofarma',
    90: 'Cavaleiro',
    95: 'Chiarelli',
    101: 'Car Racing KTF',
    111: 'Full Time/Cavaleiro',
    121: 'Car Racing KTF',
    301: 'Car Racing Sterling',
    444: 'Scuderia Bandeiras Sports'
}

# Função para obter dicionário de times por temporada
def get_team_info(season: int = 2024):
    """Retorna dicionário de times para a temporada especificada"""
    if season == 2025:
        return team_info_2025
    if season == 2026:
        return _team_info_2026()
    return team_info

# Dicionário de cores por equipe (2025)
team_colors_2025 = {
    'Chiarelli': '#FFD700',  # Dourado
    'Crown Racing': '#D3D3D3',  # Cinza Claro
    'Full Time/Cavaleiro': '#FFFFFF',  # Branco
    'Amattheis': '#00008B',  # Azul Escuro
    'Full Time': '#FF69B4',  # Rosa
    'TMG Racing': '#00FF00',  # Verde
    'RCM Motorsport': '#FF0000',  # Vermelho
    'Eurofarma': '#B8860B',  # Amarelo Escuro
    'AMattheis Vogel': '#696969',  # Cinza escuro
    'Blau': '#0000FF',  # Azul
    'Ipiranga Racing': '#FFFF00',  # Amarelo
    'Scuderia Bandeiras Sports': '#800080',  # Roxo
    'Car Racing Sterling': '#FF8C00',  # Laranja
    'Scuderia Bandeiras': '#1C1C1C',  # Preto (ajustado para melhor contraste no tema Dark)
    'Cavaleiro': '#90EE90',  # Verde Claro
    'Car Racing KTF': '#FF6347'  # Laranja (Tomato - diferente da Sterling)
}

# Esquema de cores personalizado Amattheis (pilotos destacados, demais cinza)
AMATTHEIS_NEUTRAL_COLOR = '#5A5A5A'
amattheis_color_scheme_2025 = {
    '6': '#008000',   # Helio Castroneves - Verde
    '12': '#D3D3D3',  # Lucas Foresti - Cinza Claro
    '21': '#FF0000',  # Thiago Camilo - Vermelho
    '30': '#FFFF00',  # Cesar Ramos - Amarelo
    '83': '#800080'   # Gabriel Casagrande - Roxo
}

# Função para obter cor de um piloto baseado na equipe
def get_pilot_color_by_team(numeral, season: int = 2025):
    """Retorna a cor do piloto baseado na equipe"""
    team_dict = get_team_info(season)
    numeral_int = int(numeral) if isinstance(numeral, (int, float, str)) and str(numeral).isdigit() else None
    if numeral_int is None:
        return None
    
    team_name = team_dict.get(numeral_int)
    if not team_name:
        return None
    if season == 2026:
        from utils.season_2026_data import team_chart_color

        _, chex = team_chart_color(team_name)
        return chex
    return team_colors_2025.get(team_name)

# Função para criar dicionário de cores por piloto (nome do piloto -> cor)
def get_pilot_color_map(df=None, season: int = 2025):
    """Cria um dicionário mapeando nome do piloto para cor da equipe
    
    Args:
        df: DataFrame (não usado, mantido para compatibilidade)
        season: Temporada (2024, 2025 ou 2026)
    
    Returns:
        dict: Dicionário mapeando nome do piloto para cor da equipe
    """
    team_dict = get_team_info(season)
    drivers_dict = get_drivers_names(season)
    color_map = {}
    
    for numeral_str, pilot_name in drivers_dict.items():
        numeral_int = int(numeral_str) if numeral_str.isdigit() else None
        if numeral_int is None:
            continue
        team_name = team_dict.get(numeral_int)
        if not team_name:
            continue
        if season == 2026:
            from utils.season_2026_data import team_chart_color

            _, chex = team_chart_color(team_name)
            color_map[pilot_name] = chex
        elif team_name in team_colors_2025:
            color_map[pilot_name] = team_colors_2025[team_name]

    return color_map


def get_amattheis_color_map(season: int = 2025):
    """Retorna mapa de cores no padrão Amattheis (pilotos destacados, demais cinza)"""
    if season == 2026:
        from utils.season_2026_data import (
            EQUIPES_PILOTOS_2026,
            amattheis_viz_color_for,
            parse_driver_label,
        )

        color_map = {}
        for label in EQUIPES_PILOTOS_2026:
            num, name = parse_driver_label(label)
            _, hexv = amattheis_viz_color_for(label, num)
            color_map[name] = hexv
        return color_map

    drivers_dict = get_drivers_names(season)
    color_map = {}
    for numeral_str, pilot_name in drivers_dict.items():
        color_map[pilot_name] = amattheis_color_scheme_2025.get(numeral_str, AMATTHEIS_NEUTRAL_COLOR)

    return color_map

# Dicionário de imagens dos circuitos
track_images = {
    1: "images/goiania.png",
    2: "images/velocitta.png",
    3: "images/Interlagos.png",
    4: "images/cascavel.png",
    5: "images/bh.png",
    6: "images/Interlagos.png",
    7: "images/el_pinar.png",
    8: "images/velopark.png",
    9: "images/curvelo.png",  # Será criado se necessário
    10: "images/campogrande.png",  # Será criado se necessário
    11: "images/cuiaba.png",  # Será criado se necessário
    12: "images/brasilia.png"  # Será criado se necessário
}

# Mapeamento de circuitos por nome
circuit_names = {
    'Interlagos': 3,
    'Cascavel': 4,
    'Velopark': 8,
    'Velocitta': 2,
    'Curvelo': 9,
    'Campo Grande': 10,
    'Cuiaba': 11,
    'Brasilia': 12
}

# Imagem padrão caso não encontre
DEFAULT_TRACK_IMAGE = "images/Interlagos.png"

# Imagem do carro para background
CAR_IMAGE = "images/carroipiranga.png"

# Dicionário de cores por piloto (Grupo Mattheis)
cor_por_piloto = {
    '12': '#808080',  # Cinza
    '18': '#008000',  # Verde
    '21': '#FF0000',  # Vermelho
    '30': '#FFFF00',  # Amarelo
    '83': '#800080',  # Roxo
    '88': '#0000FF'   # Azul
}

# Dicionário de nomes dos pilotos do grupo Mattheis (2024)
mattheis_names_2024 = {
    '83': 'Gabriel Casagrande',
    '21': 'Thiago Camilo',
    '88': 'Felipe Fraga',
    '30': 'Cesar Ramos',
    '12': 'Lucas Foresti',
    '18': 'Allam Khodair'
}

# Dicionário de nomes dos pilotos do grupo Mattheis (2025)
mattheis_names_2025 = {
    '12': 'Lucas Foresti',
    '21': 'Thiago Camilo',
    '30': 'Cesar Ramos',
    '83': 'Gabriel Casagrande',
    '6': 'Helio Castroneves'
}

# Pilotos com métricas estendidas de pit (Amattheis) — 2026; grid em utils.season_2026_data
def _build_mattheis_names_2026():
    from utils.season_2026_data import (
        AMATTHEIS_EXTENDED_PIT_NUMBERS_2026,
        EQUIPES_PILOTOS_2026,
        parse_driver_label,
    )
    out = {}
    for label in EQUIPES_PILOTOS_2026:
        num, name = parse_driver_label(label)
        if num in AMATTHEIS_EXTENDED_PIT_NUMBERS_2026:
            out[str(num)] = name
    return out


mattheis_names_2026 = _build_mattheis_names_2026()

# Manter compatibilidade com código antigo
mattheis_names = mattheis_names_2024

# Configurações de arquivos
PITSTOP_FILE = "PITSTOP.xlsx"
MATTHEIS_FILE = "Mattheis.xlsx"
COVER_IMAGE = "images/CAPAPITSTOP.JPG"
AMATTHEIS_LOGO = "images/amattheis.png"

# Configurações do Google Sheets (IDs das planilhas)
# Configure via Streamlit Secrets ou variáveis de ambiente
# Valores padrão - serão sobrescritos se estiverem nos secrets

# Função para extrair ID da URL do Google Sheets
def extract_sheet_id(url_or_id: str) -> str:
    """
    Extrai o ID da planilha de uma URL do Google Sheets ou retorna o ID diretamente
    
    Args:
        url_or_id: URL completa ou ID da planilha
    
    Returns:
        ID da planilha (sem /edit ou outros parâmetros)
    """
    if not url_or_id:
        return None
    
    # Se contém /d/, extrair o ID (formato URL completa)
    if '/d/' in url_or_id:
        parts = url_or_id.split('/d/')
        if len(parts) > 1:
            id_part = parts[1].split('/')[0].split('?')[0].split('#')[0]
            return id_part
    
    # Se contém /edit, remover tudo depois (incluindo ? e #)
    if '/edit' in url_or_id:
        id_part = url_or_id.split('/edit')[0]
        return id_part.split('?')[0].split('#')[0]
    
    # Se contém ? ou #, remover parâmetros
    if '?' in url_or_id or '#' in url_or_id:
        id_part = url_or_id.split('?')[0].split('#')[0]
        return id_part
    
    # Se já é apenas o ID, retornar
    return url_or_id

# IDs das planilhas (extrair apenas o ID se for URL completa)
# Os IDs abaixo contêm /edit?gid=0#gid=0 no final, a função extract_sheet_id vai remover
GOOGLE_SHEETS_PITSTOP_ID = extract_sheet_id("1GDsLICxqRN_Sp4xY_CMQAviT7h4T3-MS41ud9ym3844/edit?gid=0#gid=0")
GOOGLE_SHEETS_MATTHEIS_ID = extract_sheet_id("1dEMDePVYxdzQwO31icmGI2WSG8g80mg0tptL71QXrP4/edit?gid=0#gid=0")
USE_GOOGLE_SHEETS = True

# Função para verificar se há credenciais válidas do Google Sheets
def has_google_credentials():
    """Verifica se há credenciais válidas do Google Sheets configuradas"""
    try:
        import streamlit as st
        import os
        # Verificar se há credenciais no Streamlit Secrets
        if hasattr(st, 'secrets'):
            try:
                creds_json = st.secrets.get("GOOGLE_CREDENTIALS", None)
                if creds_json:
                    return True
            except (AttributeError, FileNotFoundError, KeyError):
                pass
        # Verificar se há arquivo local de credenciais
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if os.path.exists(creds_path):
            return True
        return False
    except Exception:
        return False

# Função para inicializar configurações do Google Sheets (chamada quando necessário)
def init_google_sheets_config():
    """Inicializa configurações do Google Sheets a partir dos secrets"""
    global GOOGLE_SHEETS_PITSTOP_ID, GOOGLE_SHEETS_MATTHEIS_ID, USE_GOOGLE_SHEETS
    try:
        import streamlit as st
        # Verificar se secrets existe e tem os valores
        if hasattr(st, 'secrets'):
            if 'GOOGLE_SHEETS_PITSTOP_ID' in st.secrets:
                pitstop_id = st.secrets['GOOGLE_SHEETS_PITSTOP_ID']
                if pitstop_id:
                    GOOGLE_SHEETS_PITSTOP_ID = extract_sheet_id(pitstop_id)
            if 'GOOGLE_SHEETS_MATTHEIS_ID' in st.secrets:
                mattheis_id = st.secrets['GOOGLE_SHEETS_MATTHEIS_ID']
                if mattheis_id:
                    GOOGLE_SHEETS_MATTHEIS_ID = extract_sheet_id(mattheis_id)
            if 'USE_GOOGLE_SHEETS' in st.secrets:
                USE_GOOGLE_SHEETS = st.secrets['USE_GOOGLE_SHEETS']
        
        # Se USE_GOOGLE_SHEETS está True mas não há credenciais, desabilitar automaticamente
        if USE_GOOGLE_SHEETS and not has_google_credentials():
            USE_GOOGLE_SHEETS = False
    except (AttributeError, FileNotFoundError, ImportError, KeyError):
        # Se não há secrets configurados, verificar se há credenciais locais
        if USE_GOOGLE_SHEETS and not has_google_credentials():
            USE_GOOGLE_SHEETS = False
    except Exception:
        # Qualquer outro erro, desabilitar Google Sheets se não houver credenciais
        if USE_GOOGLE_SHEETS and not has_google_credentials():
            USE_GOOGLE_SHEETS = False

# Calendário 2025 - Mapeamento de corridas
# Cada etapa (exceto a 1ª) tem 2 corridas: Sprint e Principal
calendario_2025 = {
    1: {'tipo': 'Sprint', 'pontuacao': {i: 16 - i for i in range(1, 16)}},  # Corrida especial - Etapa 1
    2: {'tipo': 'Sprint', 'etapa': 2, 'circuito': 'Cascavel'},
    3: {'tipo': 'Principal', 'etapa': 2, 'circuito': 'Cascavel'},
    4: {'tipo': 'Sprint', 'etapa': 3, 'circuito': 'Velopark'},
    5: {'tipo': 'Principal', 'etapa': 3, 'circuito': 'Velopark'},
    6: {'tipo': 'Sprint', 'etapa': 4, 'circuito': 'Velocitta'},
    7: {'tipo': 'Principal', 'etapa': 4, 'circuito': 'Velocitta'},
    8: {'tipo': 'Sprint', 'etapa': 5, 'circuito': 'Curvelo'},
    9: {'tipo': 'Principal', 'etapa': 5, 'circuito': 'Curvelo'},
    10: {'tipo': 'Sprint', 'etapa': 6, 'circuito': 'Cascavel'},
    11: {'tipo': 'Principal', 'etapa': 6, 'circuito': 'Cascavel'},
    12: {'tipo': 'Sprint', 'etapa': 7, 'circuito': 'Velocitta'},
    13: {'tipo': 'Principal', 'etapa': 7, 'circuito': 'Velocitta'},
    14: {'tipo': 'Sprint', 'etapa': 8, 'circuito': 'Velocitta'},
    15: {'tipo': 'Principal', 'etapa': 8, 'circuito': 'Velocitta'},
    16: {'tipo': 'Sprint', 'etapa': 9, 'circuito': 'Campo Grande'},
    17: {'tipo': 'Principal', 'etapa': 9, 'circuito': 'Campo Grande'},
    18: {'tipo': 'Sprint', 'etapa': 10, 'circuito': 'Cuiaba'},
    19: {'tipo': 'Principal', 'etapa': 10, 'circuito': 'Cuiaba'},
    20: {'tipo': 'Sprint', 'etapa': 11, 'circuito': 'Brasilia'},
    21: {'tipo': 'Principal', 'etapa': 11, 'circuito': 'Brasilia'},
    22: {'tipo': 'Sprint', 'etapa': 12, 'circuito': 'Interlagos'},
    23: {'tipo': 'Principal', 'etapa': 12, 'circuito': 'Interlagos'}
}

# Mapeamento de etapas para circuitos 2025
etapas_2025 = {
    1: 'Interlagos',
    2: 'Cascavel',
    3: 'Velopark',
    4: 'Velocitta',
    5: 'Curvelo',
    6: 'Cascavel',
    7: 'Velocitta',
    8: 'Velocitta',
    9: 'Campo Grande',
    10: 'Cuiaba',
    11: 'Brasilia',
    12: 'Interlagos'
}

