"""
Módulo de Agregações

Este módulo contém funções para agregar dados de alarmes por diferentes
critérios (severidade, equipamento, teleobjeto, etc).
"""

import pandas as pd
from typing import List, Dict, Any


def agregar_por_severidade(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega dados de alarmes por severidade.
    
    Parâmetros:
        dataframe: DataFrame com dados de alarmes
                   Deve conter colunas: severidade_nome, duracao_minutos
    
    Retorna:
        DataFrame agregado por severidade com totais e percentuais
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'severidade_nome': ['Crítica', 'Alta', 'Crítica'],
        ...     'duracao_minutos': [100, 50, 200]
        ... })
        >>> df_agregado = agregar_por_severidade(df)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Agrupar por severidade
    agregado = dataframe.groupby('severidade_nome').agg({
        'duracao_minutos': 'sum'
    }).reset_index()
    
    # Calcular percentual
    total = agregado['duracao_minutos'].sum()
    agregado['percentual'] = (agregado['duracao_minutos'] / total * 100).round(2)
    
    # Ordenar por duração
    agregado = agregado.sort_values('duracao_minutos', ascending=False)
    
    return agregado


def agregar_por_equipamento(
    dataframe: pd.DataFrame, 
    top_n: int = 10
) -> pd.DataFrame:
    """
    Agrega dados de alarmes por equipamento.
    
    Parâmetros:
        dataframe: DataFrame com dados de alarmes
                   Deve conter colunas: equipamento_nome, duracao_minutos
        top_n: Número de top equipamentos a retornar (padrão: 10)
    
    Retorna:
        DataFrame agregado por equipamento com métricas
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'equipamento_nome': ['Inv01', 'Inv02', 'Inv01'],
        ...     'duracao_minutos': [100, 50, 200]
        ... })
        >>> df_agregado = agregar_por_equipamento(df, top_n=2)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Agrupar por equipamento
    agregado = dataframe.groupby('equipamento_nome').agg({
        'duracao_minutos': ['sum', 'mean', 'count']
    }).reset_index()
    
    # Renomear colunas
    agregado.columns = [
        'equipamento_nome', 
        'duracao_total', 
        'duracao_media', 
        'quantidade'
    ]
    
    # Ordenar por duração total
    agregado = agregado.sort_values('duracao_total', ascending=False)
    
    # Retornar top N
    return agregado.head(top_n)


def agregar_por_teleobjeto(
    dataframe: pd.DataFrame, 
    top_n: int = 10
) -> pd.DataFrame:
    """
    Agrega dados de alarmes por teleobjeto.
    
    Parâmetros:
        dataframe: DataFrame com dados de alarmes
                   Deve conter colunas: teleobjeto_nome, duracao_minutos
        top_n: Número de top teleobjetos a retornar (padrão: 10)
    
    Retorna:
        DataFrame agregado por teleobjeto com métricas
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'teleobjeto_nome': ['Temp01', 'Temp02', 'Temp01'],
        ...     'duracao_minutos': [100, 50, 200]
        ... })
        >>> df_agregado = agregar_por_teleobjeto(df, top_n=2)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Agrupar por teleobjeto
    agregado = dataframe.groupby('teleobjeto_nome').agg({
        'duracao_minutos': ['sum', 'mean', 'count']
    }).reset_index()
    
    # Renomear colunas
    agregado.columns = [
        'teleobjeto_nome', 
        'duracao_total', 
        'duracao_media', 
        'quantidade'
    ]
    
    # Ordenar por duração total
    agregado = agregado.sort_values('duracao_total', ascending=False)
    
    # Retornar top N
    return agregado.head(top_n)


def agregar_por_dia(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega dados de alarmes por dia.
    
    Parâmetros:
        dataframe: DataFrame com dados de alarmes
                   Deve conter colunas: data, duracao_minutos
    
    Retorna:
        DataFrame agregado por dia
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'data': ['2025-06-01', '2025-06-01', '2025-06-02'],
        ...     'duracao_minutos': [100, 50, 200]
        ... })
        >>> df_agregado = agregar_por_dia(df)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Converter data para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(dataframe['data']):
        dataframe['data'] = pd.to_datetime(dataframe['data'])
    
    # Agrupar por data
    agregado = dataframe.groupby('data').agg({
        'duracao_minutos': ['sum', 'count']
    }).reset_index()
    
    # Renomear colunas
    agregado.columns = ['data', 'duracao_total', 'quantidade']
    
    # Ordenar por data
    agregado = agregado.sort_values('data')
    
    return agregado


def agregar_por_mes(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega dados de alarmes por mês (quando multi-mês selecionado).
    
    Parâmetros:
        dataframe: DataFrame com dados de alarmes
                   Deve conter colunas: data, duracao_minutos
    
    Retorna:
        DataFrame agregado por mês
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'data': ['2025-05-01', '2025-05-15', '2025-06-01'],
        ...     'duracao_minutos': [100, 50, 200]
        ... })
        >>> df_agregado = agregar_por_mes(df)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Converter data para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(dataframe['data']):
        dataframe['data'] = pd.to_datetime(dataframe['data'])
    
    # Extrair ano-mês
    dataframe['ano_mes'] = dataframe['data'].dt.to_period('M')
    
    # Agrupar por mês
    agregado = dataframe.groupby('ano_mes').agg({
        'duracao_minutos': ['sum', 'count']
    }).reset_index()
    
    # Renomear colunas
    agregado.columns = ['ano_mes', 'duracao_total', 'quantidade']
    
    # Formatar ano_mes como string
    agregado['ano_mes'] = agregado['ano_mes'].astype(str)
    
    # Ordenar por mês
    agregado = agregado.sort_values('ano_mes')
    
    return agregado


def calcular_ranking(
    dataframe: pd.DataFrame, 
    coluna_ordenacao: str,
    colunas_exibicao: List[str],
    limite: int = 10,
    ordem_crescente: bool = False
) -> pd.DataFrame:
    """
    Calcula ranking de um DataFrame baseado em uma coluna.
    
    Parâmetros:
        dataframe: DataFrame com os dados
        coluna_ordenacao: Coluna para ordenar o ranking
        colunas_exibicao: Lista de colunas a serem exibidas
        limite: Limite de itens no ranking (padrão: 10)
        ordem_crescente: Se True, ordena em ordem crescente (padrão: False)
    
    Retorna:
        DataFrame com ranking e colunas selecionadas
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'nome': ['A', 'B', 'C'],
        ...     'valor': [100, 200, 50]
        ... })
        >>> ranking = calcular_ranking(df, 'valor', ['nome', 'valor'], limite=2)
    """
    if dataframe.empty:
        return pd.DataFrame()
    
    # Ordenar
    df_ordenado = dataframe.sort_values(
        coluna_ordenacao, 
        ascending=ordem_crescente
    )
    
    # Adicionar coluna de posição
    df_ordenado['posicao'] = range(1, len(df_ordenado) + 1)
    
    # Selecionar colunas e limitar
    colunas_final = ['posicao'] + colunas_exibicao
    df_resultado = df_ordenado[colunas_final].head(limite)
    
    return df_resultado.reset_index(drop=True)
