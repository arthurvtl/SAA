"""
Módulo de Tabelas

Este módulo contém funções para exibir tabelas formatadas usando Streamlit.
Inclui tabelas de alarmes com paginação e tabelas de ranking.
"""

import pandas as pd
import streamlit as st
from typing import Optional
from datetime import datetime

from calculos.formatacao import (
    formatar_tempo_minutos,
    formatar_data_hora_brasileira,
    formatar_numero
)
from config import ALARMES_POR_PAGINA


def exibir_tabela_alarmes(
    dataframe: pd.DataFrame,
    pagina_atual: int = 1,
    alarmes_por_pagina: int = ALARMES_POR_PAGINA
):
    """
    Exibe tabela de alarmes com paginação.
    
    Parâmetros:
        dataframe: DataFrame com colunas [data_inicio, data_fim, duracao_minutos,
                                         equipamento_nome, teleobjeto_nome,
                                         severidade_nome, severidade_cor,
                                         descricao, data_reconhecimento,
                                         usuario_reconhecimento]
        pagina_atual: Número da página atual (padrão: 1)
        alarmes_por_pagina: Número de alarmes por página (padrão: 50)
    
    Exemplo:
        >>> df = obter_lista_alarmes(86, periodos, offset=0, limite=50)
        >>> exibir_tabela_alarmes(df, pagina_atual=1)
    """
    if dataframe.empty:
        st.info("📄 Nenhum alarme encontrado para o período selecionado.")
        return
    
    # Calcular total de páginas
    total_registros = len(dataframe)
    total_paginas = (total_registros + alarmes_por_pagina - 1) // alarmes_por_pagina
    
    # Calcular offset
    offset = (pagina_atual - 1) * alarmes_por_pagina
    df_pagina = dataframe.iloc[offset:offset + alarmes_por_pagina]
    
    # Preparar DataFrame para exibição
    df_exibir = df_pagina.copy()
    
    # Formatar colunas
    df_exibir['Data Início'] = df_exibir['data_inicio'].apply(
        lambda x: formatar_data_hora_brasileira(x) if pd.notna(x) else '-'
    )
    
    df_exibir['Data Fim'] = df_exibir['data_fim'].apply(
        lambda x: formatar_data_hora_brasileira(x) if pd.notna(x) else 'Em andamento'
    )
    
    df_exibir['Duração'] = df_exibir['duracao_minutos'].apply(
        lambda x: formatar_tempo_minutos(x) if pd.notna(x) else '-'
    )
    
    df_exibir['Reconhecimento'] = df_exibir.apply(
        lambda row: (
            f"{formatar_data_hora_brasileira(row['data_reconhecimento'])} "
            f"({row['usuario_reconhecimento']})"
            if pd.notna(row['data_reconhecimento']) else 'Não reconhecido'
        ),
        axis=1
    )
    
    # Selecionar colunas para exibição
    colunas_exibir = [
        'Data Início',
        'Data Fim',
        'Duração',
        'equipamento_nome',
        'teleobjeto_nome',
        'severidade_nome',
        'descricao',
        'Reconhecimento'
    ]
    
    df_final = df_exibir[colunas_exibir].copy()
    
    # Renomear colunas
    df_final.columns = [
        'Data Início',
        'Data Fim',
        'Duração',
        'Equipamento',
        'Teleobjeto',
        'Severidade',
        'Descrição',
        'Reconhecimento'
    ]
    
    # Exibir tabela
    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Controles de paginação
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if pagina_atual > 1:
            if st.button("◀️ Anterior", key="btn_anterior"):
                st.session_state['pagina_atual'] = pagina_atual - 1
                st.rerun()
    
    with col3:
        st.markdown(
            f"<div style='text-align: center; padding-top: 8px;'>"
            f"Página {pagina_atual} de {total_paginas} "
            f"({total_registros} alarmes)"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col5:
        if pagina_atual < total_paginas:
            if st.button("Próxima ▶️", key="btn_proxima"):
                st.session_state['pagina_atual'] = pagina_atual + 1
                st.rerun()


def exibir_tabela_ranking(
    dataframe: pd.DataFrame,
    titulo: str = "Ranking de Usinas",
    colunas_personalizadas: Optional[dict] = None,
    mostrar_botao_analisar: bool = False
):
    """
    Exibe tabela de ranking com formatação.
    
    Parâmetros:
        dataframe: DataFrame com os dados do ranking
        titulo: Título da tabela
        colunas_personalizadas: Dicionário para renomear colunas
                                Ex: {'usina_nome': 'Usina', 'total_alarmes': 'Total'}
        mostrar_botao_analisar: Se deve mostrar botão "Analisar" em cada linha
    
    Exemplo:
        >>> df = obter_ranking_usinas()
        >>> exibir_tabela_ranking(
        ...     df, 
        ...     "Ranking de Usinas",
        ...     colunas_personalizadas={'nome': 'Usina', 'alarmes': 'Total'},
        ...     mostrar_botao_analisar=True
        ... )
    """
    if dataframe.empty:
        st.info(f"📄 Nenhum dado disponível para {titulo}.")
        return
    
    st.subheader(titulo)
    
    # Aplicar renomeação de colunas se fornecida
    df_exibir = dataframe.copy()
    if colunas_personalizadas:
        df_exibir = df_exibir.rename(columns=colunas_personalizadas)
    
    # Se houver botão "Analisar"
    if mostrar_botao_analisar:
        for idx, row in df_exibir.iterrows():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Exibir dados da linha
                texto_linha = " | ".join(
                    [f"**{col}:** {val}" for col, val in row.items()]
                )
                st.markdown(texto_linha)
            
            with col2:
                if st.button("🔍 Analisar", key=f"analisar_{idx}"):
                    # Armazenar usina selecionada no session_state
                    st.session_state['usina_selecionada'] = row.get('id', idx)
                    st.session_state['pagina_atual'] = 'analise'
                    st.rerun()
            
            st.markdown("---")
    else:
        # Exibir tabela normal
        st.dataframe(
            df_exibir,
            use_container_width=True,
            hide_index=True
        )


def exibir_tabela_simples(
    dataframe: pd.DataFrame,
    titulo: Optional[str] = None,
    altura: int = 400
):
    """
    Exibe uma tabela simples sem paginação.
    
    Parâmetros:
        dataframe: DataFrame a ser exibido
        titulo: Título opcional da tabela
        altura: Altura da tabela em pixels (padrão: 400)
    
    Exemplo:
        >>> df = pd.DataFrame({'Nome': ['A', 'B'], 'Valor': [10, 20]})
        >>> exibir_tabela_simples(df, "Minha Tabela")
    """
    if dataframe.empty:
        st.info("📄 Nenhum dado disponível.")
        return
    
    if titulo:
        st.subheader(titulo)
    
    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        height=altura
    )


def aplicar_estilo_severidade(dataframe: pd.DataFrame, coluna_severidade: str = 'severidade_nome') -> pd.DataFrame:
    """
    Aplica estilo de cores baseado na severidade.
    
    Parâmetros:
        dataframe: DataFrame com dados
        coluna_severidade: Nome da coluna com severidade
    
    Retorna:
        DataFrame estilizado
    
    Exemplo:
        >>> df = pd.DataFrame({
        ...     'alarme': ['A1', 'A2'],
        ...     'severidade_nome': ['Crítica', 'Alta']
        ... })
        >>> df_estilizado = aplicar_estilo_severidade(df)
    """
    def estilizar_linha(row):
        severidade = row[coluna_severidade]
        
        cores_map = {
            'Crítica': 'background-color: #ffebee',
            'Alta': 'background-color: #fff3e0',
            'Média': 'background-color: #fffde7',
            'Baixa': 'background-color: #e0f7fa',
        }
        
        cor = cores_map.get(severidade, '')
        return [cor] * len(row)
    
    return dataframe.style.apply(estilizar_linha, axis=1)
