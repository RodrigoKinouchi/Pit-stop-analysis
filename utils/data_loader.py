"""
Funções para carregar e processar dados dos arquivos Excel ou Google Sheets
"""

import pandas as pd
from typing import Dict, List, Optional
from utils.constants import (
    PITSTOP_FILE, MATTHEIS_FILE, 
    USE_GOOGLE_SHEETS, GOOGLE_SHEETS_PITSTOP_ID, GOOGLE_SHEETS_MATTHEIS_ID,
    init_google_sheets_config
)

# Importar Google Sheets apenas se necessário
# A inicialização será feita dentro das funções quando necessário


def load_all_data() -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os dados do arquivo PITSTOP.xlsx ou Google Sheets
    
    Returns:
        Dicionário com nome da aba como chave e DataFrame como valor
    """
    # Re-inicializar configurações para garantir que está atualizado
    init_google_sheets_config()
    
    # Re-importar variáveis atualizadas
    from utils.constants import USE_GOOGLE_SHEETS, GOOGLE_SHEETS_PITSTOP_ID
    
    if USE_GOOGLE_SHEETS and GOOGLE_SHEETS_PITSTOP_ID:
        try:
            from utils.google_sheets import load_all_sheets_data
            dados = load_all_sheets_data(GOOGLE_SHEETS_PITSTOP_ID)
            return dados
        except Exception as e:
            # Se falhar ao carregar do Google Sheets, tentar Excel local como fallback
            # (sem mostrar erro, apenas usar fallback silenciosamente)
            try:
                dados = pd.read_excel(PITSTOP_FILE, sheet_name=None)
                return dados
            except Exception as excel_error:
                # Se ambos falharem, lançar erro original do Google Sheets
                raise Exception(f"Erro ao carregar dados do Google Sheets: {str(e)}. Erro ao carregar Excel local: {str(excel_error)}")
    else:
        try:
            dados = pd.read_excel(PITSTOP_FILE, sheet_name=None)
            return dados
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo {PITSTOP_FILE}: {str(e)}")


def load_mattheis_data() -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os dados do arquivo Mattheis.xlsx ou Google Sheets
    
    Returns:
        Dicionário com nome da aba como chave e DataFrame como valor
    """
    # Re-inicializar configurações para garantir que está atualizado
    init_google_sheets_config()
    
    # Re-importar variáveis atualizadas
    from utils.constants import USE_GOOGLE_SHEETS, GOOGLE_SHEETS_MATTHEIS_ID
    
    if USE_GOOGLE_SHEETS and GOOGLE_SHEETS_MATTHEIS_ID:
        try:
            from utils.google_sheets import load_all_sheets_data
            dados = load_all_sheets_data(GOOGLE_SHEETS_MATTHEIS_ID)
            return dados
        except Exception as e:
            # Se falhar ao carregar do Google Sheets, tentar Excel local como fallback
            # (sem mostrar erro, apenas usar fallback silenciosamente)
            try:
                dados = pd.read_excel(MATTHEIS_FILE, sheet_name=None)
                return dados
            except Exception as excel_error:
                # Se ambos falharem, lançar erro original do Google Sheets
                raise Exception(f"Erro ao carregar dados do Google Sheets Mattheis: {str(e)}. Erro ao carregar Excel local: {str(excel_error)}")
    else:
        try:
            dados = pd.read_excel(MATTHEIS_FILE, sheet_name=None)
            return dados
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo {MATTHEIS_FILE}: {str(e)}")


def get_season_sheets(sheets: List[str], season: int) -> List[str]:
    """
    Filtra as abas do Excel por temporada
    
    Args:
        sheets: Lista com nomes das abas
        season: Ano da temporada (ex: 2024, 2025)
    
    Returns:
        Lista filtrada de abas da temporada especificada
    """
    # Padrão esperado: abas podem conter o ano no nome ou seguir padrão E1, E2, etc.
    # Vamos assumir que:
    # - Abas de 2024 podem ter formato: "E1", "E1S", "E2", "E2S", etc. ou "2024_E1", etc.
    # - Abas de 2025 podem ter formato similar ou "2025_E1", etc.
    
    # Se a aba contém o ano explicitamente
    season_sheets = [s for s in sheets if str(season) in s]
    
    # Se não encontrou com o ano no nome, vamos usar lógica de mapeamento
    # Por padrão, temporadas antigas (2024) terão menos etapas completas
    # Vamos assumir que temporadas mais recentes têm mais dados
    
    if not season_sheets:
        # Estratégia alternativa: se não há ano no nome, usar mapeamento manual
        # ou inferir pela quantidade de etapas
        # Por enquanto, vamos retornar todas as abas e deixar o usuário configurar
        # ou usar uma lógica de separação baseada em data de criação/modificação
        pass
    
    return season_sheets


def get_season_mapping() -> Dict[int, List[str]]:
    """
    Retorna mapeamento de temporadas para abas do Excel
    Este mapeamento pode ser ajustado conforme necessário
    
    Returns:
        Dicionário com temporada como chave e lista de abas como valor
    """
    # Mapeamento padrão: assumir que abas E1 a E12 são de 2024
    # e abas E1 a E9+ são de 2025 (ou vice-versa, dependendo da estrutura real)
    # Este mapeamento deve ser ajustado baseado na estrutura real dos dados
    
    # Por padrão, vamos usar um mapeamento que separa por número de etapas
    # Temporada 2024: etapas 1-12 (E1, E1S, E2, E2S, ..., E12, E12S)
    # Temporada 2025: etapas 1-12 (E1, E1S, E2, E2S, ..., E12, E12S)
    # Como não temos o ano no nome, vamos usar um padrão baseado na ordem
    # ou na quantidade de etapas
    
    # Por enquanto, retornar um dicionário vazio para permitir configuração manual
    return {}


def filter_sheets_by_season(sheets: List[str], season: int, 
                            season_mapping: Optional[Dict[int, List[str]]] = None) -> List[str]:
    """
    Filtra abas por temporada usando mapeamento manual ou inferência
    
    Args:
        sheets: Lista com nomes das abas
        season: Ano da temporada
        season_mapping: Mapeamento manual de temporada para lista de abas (opcional)
    
    Returns:
        Lista de abas filtradas para a temporada especificada
    """
    # Se não foi fornecido mapeamento, usar o padrão
    if season_mapping is None:
        season_mapping = get_season_mapping()
    
    if season_mapping and season in season_mapping:
        # Usar mapeamento manual se fornecido
        mapped_sheets = season_mapping[season]
        # Retornar apenas as abas que existem no arquivo
        return [s for s in mapped_sheets if s in sheets]
    
    # Tentar inferir pelo nome da aba
    # Abas com ano explícito
    season_sheets = [s for s in sheets if str(season) in s]
    
    if season_sheets:
        return season_sheets
    
    # Se não encontrou, tentar padrão comum baseado na ordem
    # Ordenar as abas e dividir pela metade (assumindo 2 temporadas)
    sorted_sheets = sorted(sheets)
    
    # Se temos mapeamento em cache, usar
    if hasattr(filter_sheets_by_season, '_cache') and season in filter_sheets_by_season._cache:
        return [s for s in filter_sheets_by_season._cache[season] if s in sheets]
    
    # Estratégia: se não há mapeamento, retornar todas as abas
    # O usuário pode configurar manualmente depois
    return sorted_sheets


def get_available_seasons(sheets: List[str]) -> List[int]:
    """
    Identifica temporadas disponíveis nas abas
    
    Args:
        sheets: Lista com nomes das abas
    
    Returns:
        Lista de anos/temporadas disponíveis
    """
    seasons = set()
    
    # Procurar por anos no nome das abas
    for sheet in sheets:
        # Tentar encontrar padrão de ano (4 dígitos)
        import re
        years = re.findall(r'\b(20\d{2})\b', sheet)
        if years:
            seasons.add(int(years[0]))
    
    # Se não encontrou anos explícitos, retornar temporadas padrão
    if not seasons:
        # Por padrão, assumir 2024 e 2025
        seasons = {2024, 2025}
    
    return sorted(list(seasons))


def prepare_dataframe(df: pd.DataFrame, drivers_names: dict) -> pd.DataFrame:
    """
    Prepara o DataFrame adicionando colunas derivadas
    
    Args:
        df: DataFrame original
        drivers_names: Dicionário de mapeamento de numeral para nome do piloto
    
    Returns:
        DataFrame preparado com colunas adicionais
    """
    df = df.copy()
    
    # Adicionar coluna de piloto
    df['Piloto'] = df['Numeral'].astype(str).map(drivers_names)
    
    # Verificar se é Sprint ou Main baseado no nome da aba (será passado externamente)
    # Mas podemos adicionar outras colunas derivadas aqui
    
    return df

