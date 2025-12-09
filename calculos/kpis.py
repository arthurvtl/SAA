"""
Módulo de Cálculo de KPIs

Este módulo contém funções para calcular os principais indicadores
de performance (KPIs) do sistema de análise de alarmes.
"""

from typing import Dict, Any, List
import pandas as pd


def calcular_tempo_medio_por_alarme(tempo_total_minutos: float, total_alarmes: int) -> float:
    """
    Calcula o tempo médio por alarme.
    
    Parâmetros:
        tempo_total_minutos: Tempo total em minutos que a usina ficou alarmada
        total_alarmes: Total de alarmes registrados
    
    Retorna:
        float: Tempo médio em minutos por alarme
    
    Exemplo:
        >>> tempo_medio = calcular_tempo_medio_por_alarme(1000.0, 50)
        >>> print(f"Tempo médio: {tempo_medio:.2f} minutos")
        Tempo médio: 20.00 minutos
    """
    if total_alarmes == 0:
        return 0.0
    
    return tempo_total_minutos / total_alarmes


def calcular_kpis_principais(
    total_alarmes: int,
    tempo_total_minutos: float,
    tempo_medio_reconhecimento_minutos: float
) -> Dict[str, Any]:
    """
    Calcula todos os KPIs principais do sistema.
    
    Parâmetros:
        total_alarmes: Total de alarmes no período
        tempo_total_minutos: Tempo total em alarme (minutos)
        tempo_medio_reconhecimento_minutos: Tempo médio de reconhecimento (minutos)
    
    Retorna:
        Dict contendo:
            - total_alarmes: Total de alarmes
            - tempo_total_minutos: Tempo total em minutos
            - tempo_medio_por_alarme: Tempo médio por alarme
            - tempo_medio_reconhecimento: Tempo médio de reconhecimento
    
    Exemplo:
        >>> kpis = calcular_kpis_principais(100, 5000.0, 30.5)
        >>> print(kpis)
        {
            'total_alarmes': 100,
            'tempo_total_minutos': 5000.0,
            'tempo_medio_por_alarme': 50.0,
            'tempo_medio_reconhecimento': 30.5
        }
    """
    tempo_medio_por_alarme = calcular_tempo_medio_por_alarme(
        tempo_total_minutos, 
        total_alarmes
    )
    
    return {
        'total_alarmes': total_alarmes,
        'tempo_total_minutos': tempo_total_minutos,
        'tempo_medio_por_alarme': tempo_medio_por_alarme,
        'tempo_medio_reconhecimento': tempo_medio_reconhecimento_minutos,
    }


def calcular_percentual(parte: float, total: float) -> float:
    """
    Calcula o percentual de uma parte em relação ao total.
    
    Parâmetros:
        parte: Valor da parte
        total: Valor total
    
    Retorna:
        float: Percentual (0-100)
    
    Exemplo:
        >>> percentual = calcular_percentual(25, 100)
        >>> print(f"{percentual:.2f}%")
        25.00%
    """
    if total == 0:
        return 0.0
    
    return (parte / total) * 100.0


def calcular_taxa_reconhecimento(alarmes_reconhecidos: int, total_alarmes: int) -> float:
    """
    Calcula a taxa de reconhecimento de alarmes.
    
    Parâmetros:
        alarmes_reconhecidos: Número de alarmes reconhecidos
        total_alarmes: Total de alarmes
    
    Retorna:
        float: Taxa de reconhecimento em percentual (0-100)
    
    Exemplo:
        >>> taxa = calcular_taxa_reconhecimento(80, 100)
        >>> print(f"Taxa de reconhecimento: {taxa:.2f}%")
        Taxa de reconhecimento: 80.00%
    """
    return calcular_percentual(alarmes_reconhecidos, total_alarmes)


def calcular_disponibilidade(
    tempo_total_minutos: float, 
    periodo_minutos: float
) -> float:
    """
    Calcula a disponibilidade do sistema (tempo sem alarme).
    
    Parâmetros:
        tempo_total_minutos: Tempo total em alarme (minutos)
        periodo_minutos: Tempo total do período analisado (minutos)
    
    Retorna:
        float: Disponibilidade em percentual (0-100)
    
    Exemplo:
        >>> # Período de 30 dias = 43200 minutos
        >>> disponibilidade = calcular_disponibilidade(1000, 43200)
        >>> print(f"Disponibilidade: {disponibilidade:.2f}%")
        Disponibilidade: 97.69%
    """
    if periodo_minutos == 0:
        return 0.0
    
    tempo_sem_alarme = periodo_minutos - tempo_total_minutos
    return calcular_percentual(tempo_sem_alarme, periodo_minutos)


def calcular_mtbf(total_alarmes: int, periodo_horas: float) -> float:
    """
    Calcula o MTBF (Mean Time Between Failures) - Tempo Médio Entre Falhas.
    
    Parâmetros:
        total_alarmes: Total de alarmes (falhas)
        periodo_horas: Tempo total do período em horas
    
    Retorna:
        float: MTBF em horas
    
    Exemplo:
        >>> mtbf = calcular_mtbf(100, 720)  # 30 dias = 720 horas
        >>> print(f"MTBF: {mtbf:.2f} horas")
        MTBF: 7.20 horas
    """
    if total_alarmes == 0:
        return 0.0
    
    return periodo_horas / total_alarmes


def calcular_mttr(tempo_total_horas: float, total_alarmes: int) -> float:
    """
    Calcula o MTTR (Mean Time To Repair) - Tempo Médio de Reparo.
    
    Este é essencialmente o tempo médio por alarme.
    
    Parâmetros:
        tempo_total_horas: Tempo total em alarme (horas)
        total_alarmes: Total de alarmes
    
    Retorna:
        float: MTTR em horas
    
    Exemplo:
        >>> mttr = calcular_mttr(100, 50)
        >>> print(f"MTTR: {mttr:.2f} horas")
        MTTR: 2.00 horas
    """
    if total_alarmes == 0:
        return 0.0
    
    return tempo_total_horas / total_alarmes


def calcular_top_n_percentual(
    dataframe: pd.DataFrame, 
    coluna_valor: str, 
    coluna_nome: str,
    n: int = 5
) -> pd.DataFrame:
    """
    Calcula o percentual dos top N itens em relação ao total.
    
    Parâmetros:
        dataframe: DataFrame com os dados
        coluna_valor: Nome da coluna com valores numéricos
        coluna_nome: Nome da coluna com nomes dos itens
        n: Número de top itens (padrão: 5)
    
    Retorna:
        DataFrame com coluna adicional 'percentual_do_total'
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'equipamento': ['A', 'B', 'C'],
        ...     'alarmes': [100, 50, 25]
        ... })
        >>> df_com_percentual = calcular_top_n_percentual(df, 'alarmes', 'equipamento', 3)
    """
    if dataframe.empty:
        return dataframe
    
    # Calcula o total
    total = dataframe[coluna_valor].sum()
    
    # Adiciona coluna de percentual
    dataframe['percentual_do_total'] = (dataframe[coluna_valor] / total * 100).round(2)
    
    return dataframe.head(n)
