"""
Módulo para integração com Google Sheets
Gerencia leitura e escrita de dados no Google Sheets
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from typing import Dict, List, Optional
import os

# Escopos necessários para a API do Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_google_sheets_client():
    """
    Cria e retorna cliente autenticado do Google Sheets
    
    Returns:
        Cliente gspread autenticado
    """
    try:
        # Verificar se as credenciais estão configuradas no Streamlit Secrets
        creds_json = None
        try:
            if hasattr(st, 'secrets'):
                creds_json = st.secrets.get("GOOGLE_CREDENTIALS", None)
        except (AttributeError, FileNotFoundError, KeyError):
            # Se não há secrets configurados, continuar para tentar arquivo local
            pass
        
        if creds_json:
            # Usar credenciais do Streamlit Secrets
            import json
            if isinstance(creds_json, str):
                creds_dict = json.loads(creds_json)
            else:
                creds_dict = creds_json
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            # Tentar carregar de arquivo local (para desenvolvimento)
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
            if os.path.exists(creds_path):
                creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            else:
                raise Exception(
                    "Credenciais do Google não encontradas. "
                    "Configure GOOGLE_CREDENTIALS no Streamlit Secrets ou crie credentials.json. "
                    "Veja GOOGLE_SHEETS_SETUP.md para instruções."
                )
        
        return gspread.authorize(creds)
    except AttributeError:
        # Se st.secrets não está disponível (fora do Streamlit)
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            return gspread.authorize(creds)
        else:
            raise Exception(
                "Credenciais do Google não encontradas. "
                "Crie credentials.json ou configure via Streamlit Secrets."
            )


def load_sheet_data(spreadsheet_id: str, sheet_name: str) -> pd.DataFrame:
    """
    Carrega dados de uma aba específica do Google Sheets
    
    Args:
        spreadsheet_id: ID da planilha do Google Sheets
        sheet_name: Nome da aba
    
    Returns:
        DataFrame com os dados da aba
    """
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Se a aba não existe, criar
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        # Obter todos os valores
        values = worksheet.get_all_values()
        
        if not values or len(values) < 2:
            # Se não há dados ou apenas cabeçalho, retornar DataFrame vazio
            return pd.DataFrame()
        
        # Primeira linha são os cabeçalhos
        headers = values[0]
        data = values[1:]
        
        # Criar DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {str(e)}")
        raise


def save_sheet_data(spreadsheet_id: str, sheet_name: str, df: pd.DataFrame, 
                    clear_first: bool = True) -> bool:
    """
    Salva DataFrame em uma aba do Google Sheets
    
    Args:
        spreadsheet_id: ID da planilha do Google Sheets
        sheet_name: Nome da aba
        df: DataFrame a ser salvo
        clear_first: Se True, limpa a aba antes de salvar
    
    Returns:
        True se salvou com sucesso, False caso contrário
    """
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            if clear_first:
                worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            # Se a aba não existe, criar
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        # Preparar dados para upload
        # Converter DataFrame para lista de listas
        values = [df.columns.tolist()]  # Cabeçalhos
        values.extend(df.values.tolist())  # Dados
        
        # Atualizar planilha
        worksheet.update('A1', values)
        
        return True
    
    except Exception as e:
        # Não mostrar erro aqui, deixar o código chamador tratar
        # st.error(f"Erro ao salvar dados no Google Sheets: {str(e)}")
        return False


def load_all_sheets_data(spreadsheet_id: str) -> Dict[str, pd.DataFrame]:
    """
    Carrega todas as abas de uma planilha do Google Sheets
    
    Args:
        spreadsheet_id: ID da planilha do Google Sheets
    
    Returns:
        Dicionário com nome da aba como chave e DataFrame como valor
    """
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        
        dados = {}
        for worksheet in worksheets:
            sheet_name = worksheet.title
            try:
                values = worksheet.get_all_values()
                
                # Incluir abas mesmo que tenham apenas cabeçalho (para permitir adicionar dados depois)
                if values:
                    if len(values) > 1:
                        # Aba com dados
                        headers = values[0]
                        data = values[1:]
                        df = pd.DataFrame(data, columns=headers)
                        dados[sheet_name] = df
                    elif len(values) == 1:
                        # Aba apenas com cabeçalho (vazia mas válida)
                        headers = values[0]
                        df = pd.DataFrame(columns=headers)
                        dados[sheet_name] = df
            except Exception as e:
                # Se houver erro ao carregar uma aba específica, pular e continuar com as outras
                # Isso evita que um erro em uma aba impeça o carregamento das demais
                continue
        
        return dados
    
    except Exception as e:
        # Não mostrar erro aqui, deixar o código chamador tratar (fallback para Excel)
        # st.error(f"Erro ao carregar planilhas do Google Sheets: {str(e)}")
        raise


def get_sheet_names(spreadsheet_id: str) -> List[str]:
    """
    Retorna lista de nomes das abas de uma planilha
    
    Args:
        spreadsheet_id: ID da planilha do Google Sheets
    
    Returns:
        Lista com nomes das abas
    """
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        return [ws.title for ws in worksheets]
    
    except Exception as e:
        st.error(f"Erro ao obter nomes das abas: {str(e)}")
        return []

