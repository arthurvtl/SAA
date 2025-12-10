"""
Módulo de Queries SQL

Este módulo contém todas as funções para executar queries SQL otimizadas
no banco de dados. As queries seguem as especificações do documento
QUERIES_COMPLETAS.pdf.

TODAS as funções usam NOMES (não IDs) fazendo JOINs apropriados.
"""

from sqlalchemy import text
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import logging

from .conexao import obter_engine
from config import LIMITE_TOP_5, LIMITE_TOP_10, LIMITE_TOP_20, LIMITE_TOP_50

logger = logging.getLogger(__name__)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def construir_nome_tabela_alarme(usina_id: int, ano: int, mes: int) -> str:
    """
    Constrói o nome da tabela de alarmes dinâmica.
    
    Parâmetros:
        usina_id: ID da usina
        ano: Ano (ex: 2025)
        mes: Mês (1-12)
    
    Retorna:
        str: Nome da tabela no formato 'alarm_{usina_id}_{ano}_{mes:02d}'
    
    Exemplo:
        >>> construir_nome_tabela_alarme(86, 2025, 6)
        'alarm_86_2025_06'
    """
    return f"alarm_{usina_id}_{ano}_{mes:02d}"


def construir_union_all_tabelas(usina_id: int, periodos: List[Dict[str, int]]) -> str:
    """
    Constrói uma query UNION ALL para combinar múltiplas tabelas de alarmes.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de dicionários com 'ano' e 'mes'
                  Ex: [{'ano': 2025, 'mes': 5}, {'ano': 2025, 'mes': 6}]
    
    Retorna:
        str: Query SQL com UNION ALL
    
    Exemplo:
        >>> periodos = [{'ano': 2025, 'mes': 5}, {'ano': 2025, 'mes': 6}]
        >>> query = construir_union_all_tabelas(86, periodos)
    """
    subqueries = []
    for periodo in periodos:
        ano = periodo['ano']
        mes = periodo['mes']
        nome_tabela = construir_nome_tabela_alarme(usina_id, ano, mes)
        
        # VALIDAÇÃO: Só adiciona se a tabela existir
        if verificar_tabela_existe(usina_id, ano, mes):
            subqueries.append(f"SELECT * FROM public.{nome_tabela}")
        else:
            logger.warning(f"Tabela {nome_tabela} não existe - pulando período {ano}/{mes:02d}")
    
    if not subqueries:
        # Retorna uma query que não retorna nada mas é sintaticamente válida
        return "SELECT * FROM (SELECT NULL AS id LIMIT 0) AS empty_result"
    return " UNION ALL ".join(subqueries)


def verificar_tabela_existe(usina_id: int, ano: int, mes: int) -> bool:
    """
    Verifica se uma tabela de alarmes existe no banco de dados.
    
    Parâmetros:
        usina_id: ID da usina
        ano: Ano (ex: 2025)
        mes: Mês (1-12)
    
    Retorna:
        bool: True se a tabela existe, False caso contrário
    
    Exemplo:
        >>> if verificar_tabela_existe(86, 2025, 6):
        ...     print("Tabela existe!")
    """
    nome_tabela = construir_nome_tabela_alarme(usina_id, ano, mes)
    
    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = :nome_tabela
        ) AS existe
    """)
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(query, {"nome_tabela": nome_tabela})
            return resultado.fetchone()[0]
    except Exception as erro:
        logger.error(f"Erro ao verificar existência de tabela {nome_tabela}: {erro}")
        return False


# ============================================================================
# QUERIES DE DESCOBERTA
# ============================================================================

def listar_usinas_disponiveis() -> List[Dict[str, Any]]:
    """
    Lista todas as usinas disponíveis no sistema.
    
    Retorna:
        List[Dict]: Lista de dicionários com 'id' e 'nome' das usinas
    
    Exemplo:
        >>> usinas = listar_usinas_disponiveis()
        >>> for usina in usinas:
        ...     print(f"{usina['id']}: {usina['nome']}")
    """
    query = text("""
        SELECT 
            id,
            name AS nome
        FROM public.power_station
        ORDER BY name ASC
    """)
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(query)
            return [dict(row._mapping) for row in resultado]
    except Exception as erro:
        logger.error(f"Erro ao listar usinas: {erro}")
        return []


def descobrir_periodos_disponiveis(usina_id: int) -> List[Dict[str, Any]]:
    """
    Descobre quais períodos (ano/mês) estão disponíveis para uma usina.
    
    Parâmetros:
        usina_id: ID da usina
    
    Retorna:
        List[Dict]: Lista de dicionários com 'ano', 'mes', 'nome_tabela'
    
    Exemplo:
        >>> periodos = descobrir_periodos_disponiveis(86)
        >>> for periodo in periodos:
        ...     print(f"{periodo['ano']}-{periodo['mes']:02d}")
    """
    query = text(f"""
        SELECT
            table_name AS nome_tabela,
            SUBSTRING(table_name FROM 'alarm_\\d+_(\\d+)_\\d+')::INTEGER AS ano,
            SUBSTRING(table_name FROM 'alarm_\\d+_\\d+_(\\d+)')::INTEGER AS mes
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name ~ '^alarm_[0-9]+_[0-9]+_[0-9]+$'
        AND table_name LIKE 'alarm_{usina_id}_%'
        ORDER BY ano DESC, mes DESC
    """)
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(query)
            return [dict(row._mapping) for row in resultado]
    except Exception as erro:
        logger.error(f"Erro ao descobrir períodos para usina {usina_id}: {erro}")
        return []


def filtrar_periodos_validos(usina_id: int, periodos: List[Dict[str, int]]) -> List[Dict[str, int]]:
    """
    Filtra apenas os períodos que possuem tabelas existentes no banco.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        List[Dict]: Lista filtrada apenas com períodos válidos
    
    Exemplo:
        >>> periodos = [{'ano': 2025, 'mes': 1}, {'ano': 2025, 'mes': 2}]
        >>> validos = filtrar_periodos_validos(100, periodos)
    """
    periodos_validos = []
    for periodo in periodos:
        if verificar_tabela_existe(usina_id, periodo['ano'], periodo['mes']):
            periodos_validos.append(periodo)
        else:
            logger.info(f"Período {periodo['ano']}/{periodo['mes']:02d} não possui dados para usina {usina_id}")
    
    return periodos_validos


# ============================================================================
# QUERIES DE KPIs
# ============================================================================

def calcular_total_alarmes(usina_id: int, periodos: List[Dict[str, int]]) -> int:
    """
    Calcula o total de alarmes para uma usina em determinados períodos.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        int: Total de alarmes
    
    Exemplo:
        >>> total = calcular_total_alarmes(86, [{'ano': 2025, 'mes': 6}])
        >>> print(f"Total de alarmes: {total}")
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT COUNT(*) AS total
        FROM (
            {union_tabelas}
        ) a
        WHERE a.power_station_id = :usina_id
    """
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(text(query_sql), {"usina_id": usina_id})
            return resultado.fetchone()[0]
    except Exception as erro:
        logger.error(f"Erro ao calcular total de alarmes: {erro}")
        return 0


def calcular_tempo_total_alarmado(usina_id: int, periodos: List[Dict[str, int]]) -> float:
    """
    Calcula o tempo total em minutos que a usina ficou em estado de alarme.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        float: Tempo total em minutos
    
    Exemplo:
        >>> tempo = calcular_tempo_total_alarmado(86, [{'ano': 2025, 'mes': 6}])
        >>> print(f"Tempo total: {tempo:.2f} minutos")
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT 
            COALESCE(SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ), 0) AS tempo_total_minutos
        FROM (
            {union_tabelas}
        ) a
        WHERE a.power_station_id = :usina_id
    """
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(text(query_sql), {"usina_id": usina_id})
            return float(resultado.fetchone()[0] or 0)
    except Exception as erro:
        logger.error(f"Erro ao calcular tempo total alarmado: {erro}")
        return 0.0


def calcular_tempo_medio_reconhecimento(usina_id: int, periodos: List[Dict[str, int]]) -> float:
    """
    Calcula o tempo médio de reconhecimento de alarmes em minutos.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        float: Tempo médio em minutos
    
    Exemplo:
        >>> tempo = calcular_tempo_medio_reconhecimento(86, [{'ano': 2025, 'mes': 6}])
        >>> print(f"Tempo médio: {tempo:.2f} minutos")
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT 
            COALESCE(AVG(
                EXTRACT(EPOCH FROM (
                    a.acknowledgement_date - a.date_time
                )) / 60
            ), 0) AS tempo_medio_minutos
        FROM (
            {union_tabelas}
        ) a
        WHERE a.power_station_id = :usina_id
        AND a.acknowledgement_date IS NOT NULL
    """
    
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(text(query_sql), {"usina_id": usina_id})
            return float(resultado.fetchone()[0] or 0)
    except Exception as erro:
        logger.error(f"Erro ao calcular tempo médio de reconhecimento: {erro}")
        return 0.0


# ============================================================================
# QUERIES DE RANKINGS - EQUIPAMENTOS
# ============================================================================

def obter_top_equipamentos_por_quantidade(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém o ranking de equipamentos por quantidade de alarmes.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos no ranking (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes, duracao_total_minutos, duracao_media_minutos]
    
    Exemplo:
        >>> df = obter_top_equipamentos_por_quantidade(86, [{'ano': 2025, 'mes': 6}], limite=5)
        >>> print(df.head())
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - ' || s.name
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_media_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        GROUP BY e.id, e.name, s.name
        ORDER BY quantidade_alarmes DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter top equipamentos por quantidade: {erro}")
        return pd.DataFrame()


def obter_top_equipamentos_por_duracao(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém o ranking de equipamentos por duração total em alarme.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos no ranking (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes, duracao_total_minutos, duracao_media_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - (' || s.name || ')'
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_media_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        GROUP BY e.id, e.name, s.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter top equipamentos por duração: {erro}")
        return pd.DataFrame()


def obter_equipamentos_sem_comunicacao(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém equipamentos com problemas de comunicação.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes, duracao_total_minutos, duracao_media_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - (' || s.name || ')'
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_media_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        AND (
            a.description ILIKE '%sem comunica%'
            OR a.description ILIKE '%sem comunicacao%'
            OR a.description ILIKE '%sem comunicação%'
        )
        GROUP BY e.id, e.name, s.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter equipamentos sem comunicação: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES DE RANKINGS - TELEOBJETOS
# ============================================================================

def obter_top_teleobjetos_por_quantidade(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém o ranking de teleobjetos por quantidade de alarmes.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de teleobjetos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [teleobjeto_nome, quantidade_alarmes, 
                           duracao_total_minutos, duracao_media_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            toc.name AS teleobjeto_nome,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_media_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        WHERE a.power_station_id = :usina_id
        GROUP BY toc.id, toc.name
        ORDER BY quantidade_alarmes DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter top teleobjetos por quantidade: {erro}")
        return pd.DataFrame()


def obter_top_teleobjetos_por_duracao(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém o ranking de teleobjetos por duração total em alarme.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de teleobjetos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [teleobjeto_nome, quantidade_alarmes, 
                           duracao_total_minutos, duracao_media_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            toc.name AS teleobjeto_nome,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_media_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        WHERE a.power_station_id = :usina_id
        GROUP BY toc.id, toc.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter top teleobjetos por duração: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES DE SEVERIDADE
# ============================================================================

def obter_tempo_por_severidade(
    usina_id: int, 
    periodos: List[Dict[str, int]]
) -> pd.DataFrame:
    """
    Obtém o tempo total e percentual por severidade de alarme.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        DataFrame: Colunas [severidade_nome, severidade_cor, quantidade_alarmes,
                           duracao_total_minutos, percentual_do_total]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            asev.id AS severidade_id,
            asev.name AS severidade_nome,
            asev.color AS severidade_cor,
            asev.level AS severidade_level,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos,
            ROUND(
                (SUM(EXTRACT(EPOCH FROM (COALESCE(a.clear_date, NOW()) - a.date_time)) / 60) * 100.0) /
                NULLIF((SELECT SUM(EXTRACT(EPOCH FROM (COALESCE(clear_date, NOW()) - date_time)) / 60)
                 FROM ({union_tabelas}) sub
                 WHERE sub.power_station_id = :usina_id), 0)
                , 2) AS percentual_do_total
        FROM (
            {union_tabelas}
        ) a
        JOIN public.alarm_severity asev ON a.alarm_severity_id = asev.id
        WHERE a.power_station_id = :usina_id
        GROUP BY asev.id, asev.name, asev.color, asev.level
        ORDER BY asev.level ASC
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter tempo por severidade: {erro}")
        return pd.DataFrame()


def obter_alarmes_criticos_por_equipamento(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém alarmes críticos por equipamento.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes_criticos, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - (' || s.name || ')'
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes_criticos,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        AND a.alarm_severity_id = 1
        GROUP BY e.id, e.name, s.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter alarmes críticos por equipamento: {erro}")
        return pd.DataFrame()


def obter_alarmes_criticos_por_teleobjeto(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém alarmes críticos por teleobjeto.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de teleobjetos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [teleobjeto_nome, quantidade_alarmes_criticos,
                           duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            toc.name AS teleobjeto_nome,
            COUNT(a.id) AS quantidade_alarmes_criticos,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        WHERE a.power_station_id = :usina_id
        AND a.alarm_severity_id = 1
        GROUP BY toc.id, toc.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter alarmes críticos por teleobjeto: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES DE EVOLUÇÃO TEMPORAL
# ============================================================================

def obter_evolucao_diaria(
    usina_id: int, 
    periodos: List[Dict[str, int]]
) -> pd.DataFrame:
    """
    Obtém a evolução diária de alarmes (quantidade e duração).
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        DataFrame: Colunas [data, quantidade_alarmes, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            DATE(a.date_time) AS data,
            COUNT(a.id) AS quantidade_alarmes,
            SUM(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        WHERE a.power_station_id = :usina_id
        GROUP BY DATE(a.date_time)
        ORDER BY data ASC
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter evolução diária: {erro}")
        return pd.DataFrame()


def obter_alarmes_nao_finalizados(
    usina_id: int, 
    periodos: List[Dict[str, int]],
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém alarmes que ainda não foram finalizados por equipamento.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes_ativos, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - (' || s.name || ')'
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes_ativos,
            SUM(
                EXTRACT(EPOCH FROM (
                    NOW() - a.date_time
                )) / 60
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        AND a.clear_date IS NULL
        GROUP BY e.id, e.name, s.name
        ORDER BY quantidade_alarmes_ativos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter alarmes não finalizados: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES DE RECONHECIMENTO
# ============================================================================

def obter_tempo_reconhecimento_por_severidade(
    usina_id: int, 
    periodos: List[Dict[str, int]]
) -> pd.DataFrame:
    """
    Obtém o tempo médio de reconhecimento por severidade.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        DataFrame: Colunas [severidade_nome, severidade_cor, 
                           tempo_medio_reconhecimento_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            asev.name AS severidade_nome,
            asev.color AS severidade_cor,
            COUNT(a.id) AS total_alarmes_reconhecidos,
            ROUND(
                AVG(
                    EXTRACT(EPOCH FROM (a.acknowledgement_date - a.date_time)) / 60
                ), 2
            ) AS tempo_medio_reconhecimento_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.alarm_severity asev ON a.alarm_severity_id = asev.id
        WHERE a.power_station_id = :usina_id
        AND a.acknowledgement_date IS NOT NULL
        GROUP BY asev.id, asev.name, asev.color
        ORDER BY asev.level ASC
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter tempo de reconhecimento por severidade: {erro}")
        return pd.DataFrame()


def obter_top_usuarios_reconhecimento(
    usina_id: int, 
    periodos: List[Dict[str, int]],
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém os usuários que mais reconhecem alarmes.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de usuários (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [usuario_nome, quantidade_reconhecimentos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            u.name AS usuario_nome,
            COUNT(a.id) AS quantidade_reconhecimentos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.users u ON a.acknowledged_user_id = u.id
        WHERE a.power_station_id = :usina_id
        AND a.acknowledgement_date IS NOT NULL
        GROUP BY u.id, u.name
        ORDER BY quantidade_reconhecimentos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter top usuários de reconhecimento: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES PARA TABELA DE ALARMES
# ============================================================================

def obter_lista_alarmes(
    usina_id: int, 
    periodos: List[Dict[str, int]],
    offset: int = 0,
    limite: int = 50
) -> pd.DataFrame:
    """
    Obtém lista completa de alarmes para exibição em tabela.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        offset: Deslocamento para paginação (padrão: 0)
        limite: Número de alarmes por página (padrão: 50)
    
    Retorna:
        DataFrame: Colunas [data_inicio, data_fim, duracao_minutos, equipamento_nome,
                           teleobjeto_nome, severidade_nome, descricao, 
                           data_reconhecimento, usuario_reconhecimento]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            a.date_time AS data_inicio,
            COALESCE(a.clear_date, NULL) AS data_fim,
            ROUND(
                EXTRACT(EPOCH FROM (
                    COALESCE(a.clear_date, NOW()) - a.date_time
                )) / 60, 2
            ) AS duracao_minutos,
            e.name AS equipamento_nome,
            toc.name AS teleobjeto_nome,
            asev.name AS severidade_nome,
            asev.color AS severidade_cor,
            COALESCE(a.description, '') AS descricao,
            a.acknowledgement_date AS data_reconhecimento,
            u.name AS usuario_reconhecimento
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        JOIN public.alarm_severity asev ON a.alarm_severity_id = asev.id
        LEFT JOIN public.users u ON a.acknowledged_user_id = u.id
        WHERE a.power_station_id = :usina_id
        ORDER BY a.date_time DESC
        LIMIT :limite OFFSET :offset
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite, "offset": offset}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter lista de alarmes: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES ESPECÍFICAS PARA NCU (Network Control Unit)
# ============================================================================

def obter_alarmes_ncu(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_10
) -> pd.DataFrame:
    """
    Obtém alarmes de equipamentos NCU (que contêm "NCU" no nome).
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de equipamentos NCU (padrão: 10)
    
    Retorna:
        DataFrame: Colunas [equipamento_nome, skid_nome, equipamento_nome_formatado,
                           quantidade_alarmes, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            e.name AS equipamento_nome,
            COALESCE(s.name, 'N/A') AS skid_nome,
            CASE 
                WHEN s.name IS NOT NULL THEN e.name || ' - (' || s.name || ')'
                ELSE e.name
            END AS equipamento_nome_formatado,
            COUNT(a.id) AS quantidade_alarmes,
            ROUND(
                SUM(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        LEFT JOIN public.skid s ON e.skid_id = s.id
        WHERE a.power_station_id = :usina_id
        AND e.name ILIKE '%NCU%'
        GROUP BY e.id, e.name, s.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter alarmes de NCU: {erro}")
        return pd.DataFrame()


def obter_teleobjetos_ncu(
    usina_id: int, 
    periodos: List[Dict[str, int]],
    ncu_nome: str,
    limite: int = LIMITE_TOP_20
) -> pd.DataFrame:
    """
    Obtém todos os teleobjetos que alarmaram para uma NCU específica.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        ncu_nome: Nome do equipamento NCU
        limite: Número máximo de teleobjetos (padrão: 20)
    
    Retorna:
        DataFrame: Colunas [teleobjeto_nome, quantidade_alarmes, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            toc.name AS teleobjeto_nome,
            COUNT(a.id) AS quantidade_alarmes,
            ROUND(
                SUM(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.equipment e ON a.equipment_id = e.id
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        WHERE a.power_station_id = :usina_id
        AND e.name = :ncu_nome
        GROUP BY toc.id, toc.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "ncu_nome": ncu_nome, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter teleobjetos da NCU {ncu_nome}: {erro}")
        return pd.DataFrame()


# ============================================================================
# QUERIES ESPECÍFICAS PARA TRACKERS (TR-XXX)
# ============================================================================

def obter_alarmes_trackers(
    usina_id: int, 
    periodos: List[Dict[str, int]], 
    limite: int = LIMITE_TOP_20
) -> pd.DataFrame:
    """
    Obtém tempo total alarmado por Tracker (TR-XXX) com aglutinação de intervalos.
    
    Agrupa todos os teleobjetos que começam com o mesmo prefixo TR-XXX,
    somando o tempo total alarmado de cada tracker SEM DUPLICIDADE.
    
    IMPORTANTE: Usa SUBQUERIES ANINHADAS para fundir intervalos sobrepostos.
    Se um tracker tem múltiplos alarmes simultâneos, o tempo é contado apenas UMA vez.
    
    Exemplo de aglutinação:
        - Alarme A: 12:00-15:00 (3h)
        - Alarme B: 13:00-15:00 (2h) 
        - Tempo real: 3h (não 5h!)
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        limite: Número máximo de trackers (padrão: 20)
    
    Retorna:
        DataFrame: Colunas [tracker_code, quantidade_alarmes, duracao_total_minutos]
    
    Exemplo:
        df = obter_alarmes_trackers(86, [{'ano': 2025, 'mes': 6}], limite=10)
        print(df.head())
        tracker_code  quantidade_alarmes  duracao_total_minutos
        TR-011        150                 1234.56
        TR-010        120                 987.65
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    # ========================================================================
    # QUERY COM SUBQUERIES ANINHADAS (6 NÍVEIS)
    # ========================================================================
    # Estratégia: Cada nível anterior é uma subquery do próximo
    # Lógica de dentro para fora:
    #   1. alarmes_tracker (mais interno) - Extrai dados brutos
    #   2. alarmes_ordenados - Adiciona LAG() para detectar sobreposição
    #   3. grupos_sobrepostos - Marca início de novos grupos
    #   4. grupos_numerados - Numera grupos com SUM() OVER
    #   5. intervalos_fundidos - Agrupa e funde intervalos
    #   6. SELECT final (mais externo) - Soma durações finais
    # ========================================================================
    
    query_sql = f"""
        SELECT 
            -- ================================================================
            -- NÍVEL 6 (MAIS EXTERNO): AGREGAÇÃO FINAL POR TRACKER
            -- ================================================================
            -- Aqui somamos o tempo total de todos os intervalos fundidos
            -- Cada tracker pode ter múltiplos intervalos fundidos (gaps entre alarmes)
            tracker_code,
            SUM(qtd_alarmes_no_intervalo) AS quantidade_alarmes,
            ROUND(
                SUM(
                    EXTRACT(EPOCH FROM (fim_intervalo - inicio_intervalo)) / 60
                ), 2
            ) AS duracao_total_minutos
        FROM (
            -- ================================================================
            -- NÍVEL 5: FUSÃO DE INTERVALOS DENTRO DE CADA GRUPO
            -- ================================================================
            -- Para cada grupo_id (intervalos sobrepostos):
            --   - MIN(inicio): Pega o início do primeiro alarme do grupo
            --   - MAX(fim): Pega o fim do último alarme do grupo
            -- Resultado: Um único intervalo fundido por grupo
            SELECT
                tracker_code,
                grupo_id,
                MIN(inicio) AS inicio_intervalo,
                MAX(fim) AS fim_intervalo,
                COUNT(alarm_id) AS qtd_alarmes_no_intervalo
            FROM (
                -- ============================================================
                -- NÍVEL 4: NUMERAÇÃO DE GRUPOS
                -- ============================================================
                -- Usa SUM(novo_grupo) OVER para numerar grupos sequencialmente
                -- Alarmes com mesmo grupo_id estão sobrepostos
                -- Exemplo:
                --   novo_grupo: 1, 0, 0, 1, 0
                --   grupo_id:   1, 1, 1, 2, 2
                SELECT
                    tracker_code,
                    inicio,
                    fim,
                    alarm_id,
                    SUM(novo_grupo) OVER (
                        PARTITION BY tracker_code 
                        ORDER BY inicio
                    ) AS grupo_id
                FROM (
                    -- ========================================================
                    -- NÍVEL 3: DETECÇÃO DE GRUPOS SOBREPOSTOS
                    -- ========================================================
                    -- Marca com 1 quando um novo grupo começa (sem sobreposição)
                    -- Marca com 0 quando alarme pertence ao grupo anterior (sobreposição)
                    -- Lógica:
                    --   - Se inicio > fim_anterior → GAP → novo_grupo = 1
                    --   - Se inicio <= fim_anterior → SOBREPOSIÇÃO → novo_grupo = 0
                    SELECT
                        tracker_code,
                        inicio,
                        fim,
                        alarm_id,
                        fim_anterior,
                        CASE 
                            -- Primeiro alarme do tracker (não tem anterior)
                            WHEN fim_anterior IS NULL THEN 1
                            -- Alarme começa DEPOIS do anterior terminar (existe um GAP)
                            WHEN inicio > fim_anterior THEN 1
                            -- Alarme sobrepõe o anterior (sem GAP)
                            ELSE 0
                        END AS novo_grupo
                    FROM (
                        -- ================================================
                        -- NÍVEL 2: ORDENAÇÃO E DETECÇÃO DE SOBREPOSIÇÃO
                        -- ================================================
                        -- Ordena alarmes por tracker_code e inicio
                        -- Usa LAG() para trazer o 'fim' do alarme anterior
                        -- Isso permite comparar se alarmes se sobrepõem
                        SELECT
                            tracker_code,
                            inicio,
                            fim,
                            alarm_id,
                            LAG(fim) OVER (
                                PARTITION BY tracker_code 
                                ORDER BY inicio
                            ) AS fim_anterior
                        FROM (
                            -- ============================================
                            -- NÍVEL 1 (MAIS INTERNO): EXTRAÇÃO DOS DADOS
                            -- ============================================
                            -- Busca todos os alarmes de trackers (TR-XXX)
                            -- Extrai apenas TR-XXX do nome completo do teleobjeto
                            -- Normaliza timestamps (usa NOW() se clear_date é NULL)
                            SELECT
                                -- Extrai 'TR-001' de 'TR-001 - Posição do Tracker'
                                SPLIT_PART(toc.name, ' - ', 1) AS tracker_code,
                                a.date_time AS inicio,
                                -- Se alarme ainda não foi cleared, usa NOW()
                                COALESCE(a.clear_date, NOW()) AS fim,
                                a.id AS alarm_id
                            FROM (
                                {union_tabelas}
                            ) a
                            JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
                            JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
                            WHERE a.power_station_id = :usina_id
                            AND toc.name LIKE 'TR-%'
                        ) alarmes_tracker
                    ) alarmes_ordenados
                ) grupos_sobrepostos
            ) grupos_numerados
            GROUP BY tracker_code, grupo_id
        ) intervalos_fundidos
        GROUP BY tracker_code
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter alarmes de Trackers: {erro}")
        return pd.DataFrame()


def obter_teleobjetos_tracker(
    usina_id: int, 
    periodos: List[Dict[str, int]],
    tracker_code: str,
    limite: int = LIMITE_TOP_20
) -> pd.DataFrame:
    """
    Obtém todos os teleobjetos que alarmaram para um Tracker específico.
    
    Parâmetros:
        usina_id: ID da usina
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
        tracker_code: Código do tracker (ex: 'TR-011')
        limite: Número máximo de teleobjetos (padrão: 20)
    
    Retorna:
        DataFrame: Colunas [teleobjeto_nome, quantidade_alarmes, duracao_total_minutos]
    """
    union_tabelas = construir_union_all_tabelas(usina_id, periodos)
    
    query_sql = f"""
        SELECT
            toc.name AS teleobjeto_nome,
            COUNT(a.id) AS quantidade_alarmes,
            ROUND(
                SUM(
                    EXTRACT(EPOCH FROM (
                        COALESCE(a.clear_date, NOW()) - a.date_time
                    )) / 60
                ), 2
            ) AS duracao_total_minutos
        FROM (
            {union_tabelas}
        ) a
        JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
        JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
        WHERE a.power_station_id = :usina_id
        AND toc.name LIKE :tracker_pattern
        GROUP BY toc.id, toc.name
        ORDER BY duracao_total_minutos DESC
        LIMIT :limite
    """
    
    try:
        engine = obter_engine()
        tracker_pattern = f"{tracker_code} - %"
        return pd.read_sql_query(
            text(query_sql), 
            engine, 
            params={"usina_id": usina_id, "tracker_pattern": tracker_pattern, "limite": limite}
        )
    except Exception as erro:
        logger.error(f"Erro ao obter teleobjetos do Tracker {tracker_code}: {erro}")
        return pd.DataFrame()
