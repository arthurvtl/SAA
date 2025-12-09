"""
Módulo de Gráficos

Este módulo contém funções para criar todos os gráficos do sistema
usando PyEcharts e Streamlit.

Os gráficos seguem o padrão de cores definido para as severidades e
incluem interatividade para melhor experiência do usuário.
"""

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar, Line
from pyecharts.globals import ThemeType
from typing import List, Dict, Any, Optional
import streamlit as st
from streamlit_echarts import st_echarts

from calculos.formatacao import formatar_duracao_para_grafico, formatar_percentual
from config import CORES_SEVERIDADE


# ============================================================================
# GRÁFICO 1: PIZZA - TEMPO TOTAL POR SEVERIDADE
# ============================================================================

def criar_grafico_pizza_severidade(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de pizza mostrando tempo total por severidade.
    
    Parâmetros:
        dataframe: DataFrame com colunas [severidade_nome, severidade_cor, 
                                          duracao_total_minutos, percentual_do_total]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    
    Exemplo:
        >>> df = obter_tempo_por_severidade(86, periodos)
        >>> grafico = criar_grafico_pizza_severidade(df)
        >>> st_echarts(grafico, height="400px")
    """
    if dataframe.empty:
        return {}
    
    # Preparar dados para o gráfico
    dados = [
        {
            "name": row['severidade_nome'],
            "value": round(row['duracao_total_minutos'], 2),
            "itemStyle": {"color": CORES_SEVERIDADE.get(row['severidade_id'], row['severidade_cor'])}
        }
        for _, row in dataframe.iterrows()
    ]
    
    opcoes = {
        "title": {
            "text": "Tempo Total por Severidade",
            "left": "center",
            "top": "10",
            "textStyle": {"fontSize": 18, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} min ({d}%)"
        },
        "legend": {
            "orient": "vertical",
            "right": "10",
            "top": "center",
            "textStyle": {"fontSize": 12}
        },
        "series": [
            {
                "name": "Tempo por Severidade",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["40%", "50%"],
                "avoidLabelOverlap": True,
                "label": {
                    "show": True,
                    "formatter": "{b}\n{d}%",
                    "fontSize": 11
                },
                "emphasis": {
                    "label": {
                        "show": True,
                        "fontSize": 14,
                        "fontWeight": "bold"
                    }
                },
                "data": dados
            }
        ]
    }
    
    return opcoes


# ============================================================================
# GRÁFICO 2 E 3: BARRAS HORIZONTAIS - TOP EQUIPAMENTOS/TELEOBJETOS
# ============================================================================

def criar_grafico_barras_horizontais(
    dataframe: pd.DataFrame,
    titulo: str,
    coluna_nome: str,
    coluna_valor: str,
    nome_serie: str = "Valor",
    cor: str = "#5470c6",
    mostrar_valor: bool = True,
    formato_valor: str = "numero"  # "numero", "tempo", "percentual"
) -> Dict[str, Any]:
    """
    Cria gráfico de barras horizontais genérico.
    
    Parâmetros:
        dataframe: DataFrame com os dados
        titulo: Título do gráfico
        coluna_nome: Nome da coluna com labels (eixo Y)
        coluna_valor: Nome da coluna com valores (eixo X)
        nome_serie: Nome da série de dados
        cor: Cor das barras
        mostrar_valor: Se deve mostrar valores nas barras
        formato_valor: Formato dos valores ("numero", "tempo", "percentual")
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    
    Exemplo:
        >>> df = obter_top_equipamentos_por_quantidade(86, periodos, 10)
        >>> grafico = criar_grafico_barras_horizontais(
        ...     df, "Top 10 Equipamentos", "equipamento_nome", 
        ...     "quantidade_alarmes", "Quantidade"
        ... )
        >>> st_echarts(grafico, height="500px")
    """
    if dataframe.empty:
        return {}
    
    # Inverter ordem para mostrar maior no topo
    df_ordenado = dataframe.sort_values(coluna_valor, ascending=True)
    
    # Preparar labels e valores
    labels = df_ordenado[coluna_nome].tolist()
    valores = df_ordenado[coluna_valor].tolist()
    
    # Formatar valores para exibição e criar estrutura de dados
    dados_formatados = []
    for v in valores:
        if formato_valor == "tempo":
            label_formatada = formatar_duracao_para_grafico(v)
        elif formato_valor == "percentual":
            label_formatada = formatar_percentual(v)
        else:
            label_formatada = f"{int(v):,}".replace(",", ".")
        
        dados_formatados.append({
            "value": v,
            "label": {
                "show": mostrar_valor,
                "position": "right",
                "formatter": label_formatada,
                "fontSize": 10
            }
        })
    
    opcoes = {
        "title": {
            "text": titulo,
            "left": "center",
            "top": "10",
            "textStyle": {"fontSize": 16, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "grid": {
            "left": "20%",
            "right": "10%",
            "top": "80",
            "bottom": "60"
        },
        "xAxis": {
            "type": "value",
            "name": nome_serie,
            "nameLocation": "middle",
            "nameGap": 35,
            "nameTextStyle": {"fontSize": 12}
        },
        "yAxis": {
            "type": "category",
            "data": labels,
            "axisLabel": {"fontSize": 10}
        },
        "series": [
            {
                "name": nome_serie,
                "type": "bar",
                "data": dados_formatados,
                "itemStyle": {"color": cor},
                "barWidth": "60%"
            }
        ]
    }
    
    return opcoes


# ============================================================================
# GRÁFICO 4: BARRAS HORIZONTAIS - SEM COMUNICAÇÃO
# ============================================================================

def criar_grafico_sem_comunicacao(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras horizontais para equipamentos sem comunicação.
    
    Parâmetros:
        dataframe: DataFrame com colunas [equipamento_nome, duracao_total_minutos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    return criar_grafico_barras_horizontais(
        dataframe=dataframe,
        titulo="Tempo em 'Sem Comunicação' por Equipamento",
        coluna_nome="equipamento_nome",
        coluna_valor="duracao_total_minutos",
        nome_serie="Duração (min)",
        cor="#e74c3c",
        formato_valor="tempo"
    )


# ============================================================================
# GRÁFICO 5: BARRAS - TEMPO MÉDIO DE RECONHECIMENTO POR SEVERIDADE
# ============================================================================

def criar_grafico_barras_tempo_medio(
    dataframe: pd.DataFrame,
    usar_cores_severidade: bool = True
) -> Dict[str, Any]:
    """
    Cria gráfico de barras mostrando tempo médio de reconhecimento por severidade.
    
    Parâmetros:
        dataframe: DataFrame com colunas [severidade_nome, severidade_cor,
                                          tempo_medio_reconhecimento_minutos]
        usar_cores_severidade: Se deve usar cores específicas das severidades
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    if dataframe.empty:
        return {}
    
    # Inverter ordem para mostrar maior no topo
    df_ordenado = dataframe.sort_values('tempo_medio_reconhecimento_minutos', ascending=True)
    
    labels = df_ordenado['severidade_nome'].tolist()
    valores = df_ordenado['tempo_medio_reconhecimento_minutos'].tolist()
    
    # Preparar dados com cores e labels formatadas
    dados = []
    if usar_cores_severidade and 'severidade_cor' in df_ordenado.columns:
        cores = df_ordenado['severidade_cor'].tolist()
        for valor, cor in zip(valores, cores):
            dados.append({
                "value": valor,
                "itemStyle": {"color": cor},
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": formatar_duracao_para_grafico(valor),
                    "fontSize": 10
                }
            })
    else:
        for valor in valores:
            dados.append({
                "value": valor,
                "label": {
                    "show": True,
                    "position": "right",
                    "formatter": formatar_duracao_para_grafico(valor),
                    "fontSize": 10
                }
            })
    
    opcoes = {
        "title": {
            "text": "Tempo Médio de Reconhecimento por Severidade",
            "left": "center",
            "top": "10",
            "textStyle": {"fontSize": 16, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "grid": {
            "left": "20%",
            "right": "10%",
            "top": "80",
            "bottom": "60"
        },
        "xAxis": {
            "type": "value",
            "name": "Tempo Médio (min)",
            "nameLocation": "middle",
            "nameGap": 35
        },
        "yAxis": {
            "type": "category",
            "data": labels
        },
        "series": [
            {
                "name": "Tempo Médio",
                "type": "bar",
                "data": dados,
                "barWidth": "60%"
            }
        ]
    }
    
    return opcoes


# ============================================================================
# GRÁFICO 6: BARRAS HORIZONTAIS - TOP USUÁRIOS RECONHECIMENTO
# ============================================================================

def criar_grafico_top_usuarios(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras com top usuários que mais reconhecem alarmes.
    
    Parâmetros:
        dataframe: DataFrame com colunas [usuario_nome, quantidade_reconhecimentos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    return criar_grafico_barras_horizontais(
        dataframe=dataframe,
        titulo="Top Usuários que Mais Reconhecem Alarmes",
        coluna_nome="usuario_nome",
        coluna_valor="quantidade_reconhecimentos",
        nome_serie="Reconhecimentos",
        cor="#27ae60"
    )


# ============================================================================
# GRÁFICO 7 E 8: BARRAS - ALARMES CRÍTICOS
# ============================================================================

def criar_grafico_alarmes_criticos_equipamento(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras com alarmes críticos por equipamento.
    
    Parâmetros:
        dataframe: DataFrame com colunas [equipamento_nome, duracao_total_minutos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    return criar_grafico_barras_horizontais(
        dataframe=dataframe,
        titulo="Alarmes Críticos - Tempo Total por Equipamento",
        coluna_nome="equipamento_nome",
        coluna_valor="duracao_total_minutos",
        nome_serie="Duração (min)",
        cor="#c0392b",
        formato_valor="tempo"
    )


def criar_grafico_alarmes_criticos_teleobjeto(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras com alarmes críticos por teleobjeto.
    
    Parâmetros:
        dataframe: DataFrame com colunas [teleobjeto_nome, duracao_total_minutos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    return criar_grafico_barras_horizontais(
        dataframe=dataframe,
        titulo="Alarmes Críticos - Tempo Total por Teleobjeto",
        coluna_nome="teleobjeto_nome",
        coluna_valor="duracao_total_minutos",
        nome_serie="Duração (min)",
        cor="#c0392b",
        formato_valor="tempo"
    )


# ============================================================================
# GRÁFICO 9: BARRAS - ALARMES NÃO FINALIZADOS
# ============================================================================

def criar_grafico_alarmes_nao_finalizados(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras com top alarmes não finalizados por equipamento.
    
    Parâmetros:
        dataframe: DataFrame com colunas [equipamento_nome, quantidade_alarmes_ativos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    """
    return criar_grafico_barras_horizontais(
        dataframe=dataframe,
        titulo="Top 10 Alarmes Não Finalizados por Equipamento",
        coluna_nome="equipamento_nome",
        coluna_valor="quantidade_alarmes_ativos",
        nome_serie="Alarmes Ativos",
        cor="#f39c12"
    )


# ============================================================================
# GRÁFICO 10: LINHA - EVOLUÇÃO DIÁRIA
# ============================================================================

def criar_grafico_linha_evolucao(
    dataframe: pd.DataFrame,
    modo: str = "quantidade"  # "quantidade" ou "duracao"
) -> Dict[str, Any]:
    """
    Cria gráfico de linha mostrando evolução diária de alarmes.
    
    Parâmetros:
        dataframe: DataFrame com colunas [data, quantidade_alarmes, duracao_total_minutos]
        modo: "quantidade" para mostrar quantidade de alarmes, 
              "duracao" para mostrar duração total
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    
    Exemplo:
        >>> df = obter_evolucao_diaria(86, periodos)
        >>> grafico_qtd = criar_grafico_linha_evolucao(df, modo="quantidade")
        >>> grafico_dur = criar_grafico_linha_evolucao(df, modo="duracao")
    """
    if dataframe.empty:
        return {}
    
    # Converter data para string formatada
    dataframe['data_str'] = pd.to_datetime(dataframe['data']).dt.strftime('%d/%m')
    
    datas = dataframe['data_str'].tolist()
    
    if modo == "quantidade":
        valores = dataframe['quantidade_alarmes'].tolist()
        titulo = "Evolução Diária - Quantidade de Alarmes"
        nome_serie = "Quantidade"
        cor = "#3498db"
    else:
        valores = dataframe['duracao_total_minutos'].tolist()
        titulo = "Evolução Diária - Duração Total"
        nome_serie = "Duração (min)"
        cor = "#e67e22"
    
    opcoes = {
        "title": {
            "text": titulo,
            "left": "center",
            "top": "10",
            "textStyle": {"fontSize": 16, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "top": "80",
            "bottom": "80"
        },
        "xAxis": {
            "type": "category",
            "data": datas,
            "boundaryGap": False,
            "axisLabel": {
                "rotate": 45,
                "fontSize": 10
            }
        },
        "yAxis": {
            "type": "value",
            "name": nome_serie,
            "nameLocation": "middle",
            "nameGap": 50
        },
        "series": [
            {
                "name": nome_serie,
                "type": "line",
                "data": valores,
                "smooth": True,
                "itemStyle": {"color": cor},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0,
                        "y": 0,
                        "x2": 0,
                        "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": cor},
                            {"offset": 1, "color": "#ffffff"}
                        ]
                    }
                },
                "lineStyle": {"width": 2},
                "symbol": "circle",
                "symbolSize": 6
            }
        ],
        "dataZoom": [
            {
                "type": "slider",
                "start": 0,
                "end": 100,
                "bottom": "20"
            }
        ]
    }
    
    return opcoes


# ============================================================================
# GRÁFICO 11: BARRAS AGRUPADAS - RESUMO POR MÊS (MULTI-MÊS)
# ============================================================================

def criar_grafico_resumo_mensal(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Cria gráfico de barras agrupadas mostrando resumo por mês.
    
    Usado quando múltiplos meses são selecionados.
    
    Parâmetros:
        dataframe: DataFrame com colunas [ano_mes, quantidade_alarmes, duracao_total_minutos]
    
    Retorna:
        Dict: Configuração do gráfico para st_echarts
    
    Exemplo:
        >>> # Quando usuário seleciona maio, junho e julho de 2025
        >>> df = obter_resumo_mensal(86, periodos)
        >>> grafico = criar_grafico_resumo_mensal(df)
        >>> st_echarts(grafico, height="400px")
    """
    if dataframe.empty:
        return {}
    
    meses = dataframe['ano_mes'].tolist()
    quantidades = dataframe['quantidade_alarmes'].tolist()
    duracoes = (dataframe['duracao_total_minutos'] / 60).round(1).tolist()  # Converter para horas
    
    opcoes = {
        "title": {
            "text": "Resumo por Mês",
            "left": "center",
            "top": "10",
            "textStyle": {"fontSize": 16, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "legend": {
            "data": ["Quantidade de Alarmes", "Duração Total (horas)"],
            "top": "50",
            "textStyle": {"fontSize": 12}
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "top": "100",
            "bottom": "60"
        },
        "xAxis": {
            "type": "category",
            "data": meses,
            "axisLabel": {"fontSize": 11}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Quantidade",
                "position": "left",
                "nameTextStyle": {"fontSize": 11}
            },
            {
                "type": "value",
                "name": "Duração (h)",
                "position": "right",
                "nameTextStyle": {"fontSize": 11}
            }
        ],
        "series": [
            {
                "name": "Quantidade de Alarmes",
                "type": "bar",
                "data": quantidades,
                "itemStyle": {"color": "#3498db"}
            },
            {
                "name": "Duração Total (horas)",
                "type": "bar",
                "yAxisIndex": 1,
                "data": duracoes,
                "itemStyle": {"color": "#e67e22"}
            }
        ]
    }
    
    return opcoes


# ============================================================================
# FUNÇÃO AUXILIAR: EXIBIR GRÁFICO COM TOGGLE
# ============================================================================

def exibir_grafico_com_toggle(
    dataframe: pd.DataFrame,
    titulo_base: str,
    coluna_nome: str,
    coluna_quantidade: str,
    coluna_duracao: str,
    key_prefix: str,
    limite_inicial: int = 5,
    limite_expandido: int = 50,
    cor_quantidade: str = "#3498db",
    cor_duracao: str = "#e67e22"
):
    """
    Exibe gráfico com toggle entre Quantidade/Duração e botão "Ver Mais".
    
    Parâmetros:
        dataframe: DataFrame com os dados
        titulo_base: Título base do gráfico
        coluna_nome: Coluna com nomes dos itens
        coluna_quantidade: Coluna com quantidade de alarmes
        coluna_duracao: Coluna com duração total
        key_prefix: Prefixo único para keys do Streamlit
        limite_inicial: Limite inicial de itens (padrão: 5)
        limite_expandido: Limite após expandir (padrão: 50)
        cor_quantidade: Cor para modo quantidade
        cor_duracao: Cor para modo duração
    
    Exemplo:
        >>> df = obter_top_equipamentos_por_quantidade(86, periodos, 50)
        >>> exibir_grafico_com_toggle(
        ...     df, "Top Equipamentos", "equipamento_nome",
        ...     "quantidade_alarmes", "duracao_total_minutos",
        ...     "equipamentos"
        ... )
    """
    if dataframe.empty:
        st.info("Nenhum dado disponível para exibir.")
        return
    
    # Toggle entre Quantidade e Duração
    col1, col2 = st.columns([3, 1])
    with col2:
        modo = st.radio(
            "Exibir por:",
            options=["Quantidade", "Duração"],
            key=f"{key_prefix}_modo",
            horizontal=True
        )
    
    # Botão "Ver Mais"
    if f"{key_prefix}_expandido" not in st.session_state:
        st.session_state[f"{key_prefix}_expandido"] = False
    
    limite = limite_expandido if st.session_state[f"{key_prefix}_expandido"] else limite_inicial
    
    # Filtrar dados conforme limite
    df_exibir = dataframe.head(limite)
    
    # Criar gráfico conforme modo selecionado
    if modo == "Quantidade":
        grafico = criar_grafico_barras_horizontais(
            df_exibir,
            f"{titulo_base} - Top {limite} (Quantidade)",
            coluna_nome,
            coluna_quantidade,
            "Quantidade de Alarmes",
            cor_quantidade
        )
    else:
        grafico = criar_grafico_barras_horizontais(
            df_exibir,
            f"{titulo_base} - Top {limite} (Duração)",
            coluna_nome,
            coluna_duracao,
            "Duração Total (min)",
            cor_duracao,
            formato_valor="tempo"
        )
    
    # Exibir gráfico
    st_echarts(grafico, height="500px")
    
    # Botão "Ver Mais" / "Ver Menos"
    if len(dataframe) > limite_inicial:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            if not st.session_state[f"{key_prefix}_expandido"]:
                if st.button(f"🔍 Ver Mais (até Top {limite_expandido})", key=f"{key_prefix}_btn"):
                    st.session_state[f"{key_prefix}_expandido"] = True
                    st.rerun()
            else:
                if st.button(f"🔼 Ver Menos (Top {limite_inicial})", key=f"{key_prefix}_btn"):
                    st.session_state[f"{key_prefix}_expandido"] = False
                    st.rerun()
