"""
Funções auxiliares para temporada 2025
"""

from utils.constants import calendario_2025, etapas_2025, circuit_names, track_images, DEFAULT_TRACK_IMAGE
from typing import Optional, Tuple
import os


def get_corrida_info(numero_corrida: int) -> dict:
    """
    Retorna informações sobre uma corrida específica de 2025
    
    Args:
        numero_corrida: Número da corrida (1-23)
    
    Returns:
        Dicionário com informações da corrida
    """
    if numero_corrida in calendario_2025:
        return calendario_2025[numero_corrida]
    return {}


def get_tipo_corrida_2025(numero_corrida: int) -> str:
    """
    Retorna o tipo de corrida (Sprint ou Principal) para 2025
    
    Args:
        numero_corrida: Número da corrida (1-23)
    
    Returns:
        'Sprint' ou 'Principal'
    """
    info = get_corrida_info(numero_corrida)
    return info.get('tipo', 'Principal')


def get_circuito_2025(numero_corrida: int) -> Optional[str]:
    """
    Retorna o nome do circuito para uma corrida de 2025
    
    Args:
        numero_corrida: Número da corrida (1-23)
    
    Returns:
        Nome do circuito ou None
    """
    info = get_corrida_info(numero_corrida)
    if 'circuito' in info:
        return info['circuito']
    # Se não tem circuito específico, tentar pela etapa
    if 'etapa' in info:
        etapa = info['etapa']
        if etapa in etapas_2025:
            return etapas_2025[etapa]
    # Etapa 1 (corrida especial)
    if numero_corrida == 1:
        return etapas_2025[1]
    return None


def get_track_image_2025(numero_corrida: int) -> str:
    """
    Retorna o caminho da imagem do circuito para uma corrida de 2025
    
    Args:
        numero_corrida: Número da corrida (1-23)
    
    Returns:
        Caminho da imagem do circuito
    """
    circuito = get_circuito_2025(numero_corrida)
    if circuito and circuito in circuit_names:
        track_id = circuit_names[circuito]
        image_path = track_images.get(track_id, DEFAULT_TRACK_IMAGE)
        # Verificar se o arquivo existe
        if os.path.exists(image_path):
            return image_path
    
    # Tentar com nome do circuito diretamente
    if circuito:
        # Tentar encontrar imagem com nome do circuito
        circuit_lower = circuito.lower().replace(' ', '_')
        possible_paths = [
            f"images/{circuit_lower}.png",
            f"images/{circuito.lower()}.png",
            f"images/{circuito}.png"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    return DEFAULT_TRACK_IMAGE


def get_nome_corrida_2025(numero_corrida: int) -> str:
    """
    Retorna o nome formatado da corrida (ex: "Corrida 3 - Principal Etapa 2")
    
    Args:
        numero_corrida: Número da corrida (1-23)
    
    Returns:
        Nome formatado da corrida
    """
    info = get_corrida_info(numero_corrida)
    tipo = info.get('tipo', 'Principal')
    
    if numero_corrida == 1:
        return f"Corrida {numero_corrida} - {tipo} (Etapa 1 - Especial)"
    
    etapa = info.get('etapa', None)
    if etapa:
        return f"Corrida {numero_corrida} - {tipo} Etapa {etapa}"
    
    return f"Corrida {numero_corrida} - {tipo}"


def get_nome_aba_formatado(nome_aba: str) -> str:
    """
    Converte nome de aba (ex: "E4S") para formato legível (ex: "Corrida 6 - Sprint Etapa 4")
    
    Args:
        nome_aba: Nome da aba do Excel (ex: "E1", "E1S", "E4S", etc.)
    
    Returns:
        Nome formatado para exibição
    """
    numero_corrida = parse_corrida_name(nome_aba)
    if numero_corrida:
        return get_nome_corrida_2025(numero_corrida)
    return nome_aba


def parse_corrida_name(nome_aba: str) -> Optional[int]:
    """
    Tenta extrair o número da corrida do nome da aba
    
    Args:
        nome_aba: Nome da aba do Excel (ex: "E1S", "E2", "Corrida3", etc.)
    
    Returns:
        Número da corrida ou None se não conseguir identificar
    """
    import re
    
    # Tentar padrão "Corrida X" ou "C X"
    match = re.search(r'[Cc]orrida\s*(\d+)', nome_aba, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Tentar padrão "E X" ou "E XS"
    match = re.search(r'E\s*(\d+)', nome_aba, re.IGNORECASE)
    if match:
        etapa = int(match.group(1))
        is_sprint = 'S' in nome_aba.upper()
        
        # Mapear etapa para número de corrida
        # Etapa 1: corrida 1 (especial)
        if etapa == 1:
            return 1
        
        # Outras etapas: Sprint = (etapa-1)*2, Principal = (etapa-1)*2+1
        if is_sprint:
            return (etapa - 1) * 2
        else:
            return (etapa - 1) * 2 + 1
    
    return None

