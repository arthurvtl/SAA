"""
Sistema de Análise de Alarmes (SAA)
Versão 2.1.1

Aplicação principal Streamlit com 2 páginas:
1. HOME: Visão geral de todas as usinas
2. ANÁLISE DETALHADA: Análise específica de uma usina

Autor: Sistema desenvolvido conforme especificação SAA
Data: 03 de dezembro de 2025
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Importações dos módulos do sistema
from config import (
    TITULO_APLICACAO,
    ICONE_APLICACAO,
    LAYOUT_PAGINA,
    LIMITE_TOP_5,
    LIMITE_TOP_10,
    LIMITE_TOP_20,
    LIMITE_MAXIMO_MESES
)

from database.conexao import testar_conexao
from database.queries import (
    listar_usinas_disponiveis,
    descobrir_periodos_disponiveis,
    filtrar_periodos_validos,
    calcular_total_alarmes,
    calcular_tempo_total_alarmado,
    calcular_tempo_medio_reconhecimento,
    obter_top_equipamentos_por_quantidade,
    obter_top_equipamentos_por_duracao,
    obter_equipamentos_sem_comunicacao,
    obter_top_teleobjetos_por_quantidade,
    obter_top_teleobjetos_por_duracao,
    obter_tempo_por_severidade,
    obter_alarmes_criticos_por_equipamento,
    obter_alarmes_criticos_por_teleobjeto,
    obter_alarmes_nao_finalizados,
    obter_evolucao_diaria,
    obter_tempo_reconhecimento_por_severidade,
    obter_top_usuarios_reconhecimento,
    obter_lista_alarmes,
    obter_alarmes_ncu,
    obter_teleobjetos_ncu,
    obter_alarmes_trackers,
    obter_teleobjetos_tracker,
)

from calculos.kpis import calcular_kpis_principais, calcular_tempo_medio_por_alarme
from calculos.formatacao import formatar_tempo_minutos, formatar_numero

from visualizacoes.cards import exibir_cards_kpis_principais, exibir_card_resumo_usina, exibir_card_alerta
from visualizacoes.graficos import (
    criar_grafico_pizza_severidade,
    criar_grafico_barras_horizontais,
    criar_grafico_sem_comunicacao,
    criar_grafico_barras_tempo_medio,
    criar_grafico_top_usuarios,
    criar_grafico_alarmes_criticos_equipamento,
    criar_grafico_alarmes_criticos_teleobjeto,
    criar_grafico_alarmes_nao_finalizados,
    criar_grafico_linha_evolucao,
    criar_grafico_resumo_mensal,
    exibir_grafico_com_toggle,
)
from visualizacoes.tabelas import exibir_tabela_alarmes, exibir_tabela_simples

from utils.helpers import (
    validar_periodos_selecionados,
    construir_texto_periodo,
    inicializar_session_state,
    gerar_opcoes_anos,
    obter_nome_mes,
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="SAA - Sistema de Análise de Alarmes",
    page_icon=ICONE_APLICACAO,
    layout=LAYOUT_PAGINA,
    initial_sidebar_state="expanded"
)

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

# Inicializar session state
inicializar_session_state()

# Testar conexão com banco de dados
if not testar_conexao():
    st.error("""
        ❌ **Erro de Conexão com Banco de Dados**
        
        Não foi possível conectar ao banco de dados PostgreSQL.
        
        Por favor, verifique:
        - Se o PostgreSQL está rodando
        - Se as credenciais em `config.py` estão corretas
        - Se o host e porta estão acessíveis
    """)
    st.stop()

# ============================================================================
# PÁGINA HOME
# ============================================================================

def pagina_home():
    """
    Página HOME - Visão geral de todas as usinas.
    
    Funcionalidades:
    - Filtros: Ano (dropdown) e Meses (checkboxes, máx 3)
    - KPIs Gerais: Total de Usinas, Total de Alarmes, Tempo Total, Tempo Médio
    - Gráfico Pizza: Distribuição de Alarmes por Usina
    - Gráfico Barras: Top 10 Usinas com Mais Alarmes
    - Tabela Ranking: Todas as 55 usinas com botão "Analisar"
    """
    # Título da seção
    st.subheader("📊 Visão Geral de Todas as Usinas")
    
    st.markdown("---")
    
    # Sidebar com filtros
    with st.sidebar:
        st.header("🔍 Filtros")
        
        # Filtro de Ano
        anos_disponiveis = gerar_opcoes_anos(2021)
        ano_selecionado = st.selectbox(
            "📅 Selecione o Ano:",
            options=anos_disponiveis,
            index=0,
            key="home_ano"
        )
        
        st.markdown("---")
        
        # Filtro de Meses (checkboxes)
        st.markdown("**📆 Selecione os Meses (máx 3):**")
        meses_selecionados = []
        
        for mes in range(1, 13):
            if st.checkbox(
                obter_nome_mes(mes),
                key=f"home_mes_{mes}"
            ):
                meses_selecionados.append(mes)
        
        st.markdown("---")
        
        # Validar seleção de meses
        if len(meses_selecionados) > LIMITE_MAXIMO_MESES:
            st.error(f"⚠️ Máximo de {LIMITE_MAXIMO_MESES} meses permitidos!")
            return
        
        if len(meses_selecionados) == 0:
            st.warning("⚠️ Selecione pelo menos 1 mês para visualizar os dados.")
            return
    
    # Construir períodos selecionados
    periodos = [{'ano': ano_selecionado, 'mes': mes} for mes in meses_selecionados]
    texto_periodo = construir_texto_periodo(periodos)
    
    # INFO: Não filtramos períodos na página HOME pois queremos mostrar dados agregados
    # mesmo que algumas usinas não tenham dados em alguns meses
    
    # Exibir período selecionado
    st.info(f"📅 **Período Selecionado:** {texto_periodo}")
    
    # Listar todas as usinas
    usinas = listar_usinas_disponiveis()
    
    if not usinas:
        st.error("❌ Nenhuma usina encontrada no sistema.")
        return
    
    # Calcular KPIs gerais (agregando todas as usinas)
    st.markdown("---")
    st.subheader("📈 Indicadores Gerais")
    
    with st.spinner("Calculando KPIs gerais..."):
        # Agregar dados de todas as usinas
        total_alarmes_geral = 0
        tempo_total_geral = 0.0
        
        for usina in usinas:
            try:
                total_alarmes = calcular_total_alarmes(usina['id'], periodos)
                tempo_total = calcular_tempo_total_alarmado(usina['id'], periodos)
                
                total_alarmes_geral += total_alarmes
                tempo_total_geral += tempo_total
            except Exception as e:
                logger.error(f"Erro ao processar usina {usina['id']}: {e}")
                continue
        
        # Calcular tempo médio
        tempo_medio_geral = calcular_tempo_medio_por_alarme(
            tempo_total_geral,
            total_alarmes_geral
        )
        
        # Exibir KPIs em cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🏭 Total de Usinas",
                value=len(usinas)
            )
        
        with col2:
            st.metric(
                label="🚨 Total de Alarmes",
                value=formatar_numero(total_alarmes_geral)
            )
        
        with col3:
            st.metric(
                label="⏱️ Tempo Total Alarmado",
                value=formatar_tempo_minutos(tempo_total_geral)
            )
        
        with col4:
            st.metric(
                label="📊 Tempo Médio por Alarme",
                value=f"{tempo_medio_geral:.2f} min"
            )
    
    st.markdown("---")
    
    # Tabela de Ranking de Usinas
    st.subheader("🏆 Ranking de Usinas")
    
    with st.spinner("Carregando ranking de usinas..."):
        # Construir ranking
        ranking_data = []
        
        for usina in usinas:
            try:
                total_alarmes = calcular_total_alarmes(usina['id'], periodos)
                tempo_total = calcular_tempo_total_alarmado(usina['id'], periodos)
                tempo_medio = calcular_tempo_medio_por_alarme(tempo_total, total_alarmes)
                
                ranking_data.append({
                    'usina_id': usina['id'],
                    'usina_nome': usina['nome'],
                    'total_alarmes': total_alarmes,
                    'tempo_total_minutos': tempo_total,
                    'tempo_medio_minutos': tempo_medio
                })
            except Exception as e:
                logger.error(f"Erro ao processar usina {usina['id']}: {e}")
                continue
        
        # Criar DataFrame
        df_ranking = pd.DataFrame(ranking_data)
        
        if not df_ranking.empty:
            # Ordenar por total de alarmes
            df_ranking = df_ranking.sort_values('total_alarmes', ascending=False)
            df_ranking['posicao'] = range(1, len(df_ranking) + 1)
            
            # Formatar para exibição
            df_exibir = df_ranking[[
                'posicao',
                'usina_nome',
                'total_alarmes',
                'tempo_total_minutos',
                'tempo_medio_minutos'
            ]].copy()
            
            # Formatar colunas
            df_exibir['tempo_total_formatado'] = df_exibir['tempo_total_minutos'].apply(
                lambda x: formatar_tempo_minutos(x)
            )
            df_exibir['tempo_medio_formatado'] = df_exibir['tempo_medio_minutos'].apply(
                lambda x: f"{x:.2f} min"
            )
            
            # Selecionar colunas finais
            df_final = df_exibir[[
                'posicao',
                'usina_nome',
                'total_alarmes',
                'tempo_total_formatado',
                'tempo_medio_formatado'
            ]].copy()
            
            df_final.columns = [
                'Posição',
                'Usina',
                'Total de Alarmes',
                'Tempo Total',
                'Tempo Médio'
            ]
            
            # Exibir tabela com botão "Analisar"
            for idx, row in df_final.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{row['Posição']}º**")
                
                with col2:
                    st.write(row['Usina'])
                
                with col3:
                    st.write(formatar_numero(row['Total de Alarmes']))
                
                with col4:
                    st.write(row['Tempo Total'])
                
                with col5:
                    st.write(row['Tempo Médio'])
                
                with col6:
                    usina_id = df_ranking.iloc[idx]['usina_id']
                    if st.button("🔍", key=f"analisar_{usina_id}"):
                        st.session_state['usina_selecionada'] = usina_id
                        st.session_state['pagina_atual'] = 'analise'
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("📄 Nenhum dado disponível para o período selecionado.")


# ============================================================================
# PÁGINA ANÁLISE DETALHADA
# ============================================================================

def pagina_analise():
    """
    Página ANÁLISE DETALHADA - Análise específica de uma usina.
    
    Funcionalidades:
    - Sidebar: Seleção de Usina, Ano, Meses
    - 4 KPIs principais
    - 11 Gráficos interativos
    - Tabela de alarmes com paginação
    """
    # Título da seção
    st.subheader("📊 Análise Detalhada de Alarmes")
    
    # Sidebar com seleção de usina e período
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Listar usinas disponíveis
        usinas = listar_usinas_disponiveis()
        
        if not usinas:
            st.error("❌ Nenhuma usina encontrada no sistema.")
            return
        
        # Dropdown de seleção de usina
        usina_opcoes = {usina['nome']: usina['id'] for usina in usinas}
        usina_nome_selecionada = st.selectbox(
            "🏭 Selecione a Usina:",
            options=list(usina_opcoes.keys()),
            key="analise_usina"
        )
        
        usina_id = usina_opcoes[usina_nome_selecionada]
        
        st.markdown("---")
        
        # Descobrir períodos disponíveis para esta usina
        periodos_disponiveis = descobrir_periodos_disponiveis(usina_id)
        
        if not periodos_disponiveis:
            st.error(f"❌ Nenhum período disponível para a usina {usina_nome_selecionada}.")
            return
        
        # Extrair anos únicos
        anos_disponiveis = sorted(
            list(set([p['ano'] for p in periodos_disponiveis])),
            reverse=True
        )
        
        # Seleção de Ano
        ano_selecionado = st.selectbox(
            "📅 Selecione o Ano:",
            options=anos_disponiveis,
            key="analise_ano"
        )
        
        # Filtrar meses disponíveis para o ano selecionado
        meses_disponiveis_ano = [
            p['mes'] for p in periodos_disponiveis 
            if p['ano'] == ano_selecionado
        ]
        meses_disponiveis_ano = sorted(meses_disponiveis_ano)
        
        st.markdown("---")
        
        # Seleção de Meses (checkboxes) - APENAS meses com dados
        st.markdown(f"**📆 Selecione os Meses (máx {LIMITE_MAXIMO_MESES}):**")
        
        if meses_disponiveis_ano:
            st.info(f"✅ {len(meses_disponiveis_ano)} meses com dados disponíveis")
            meses_selecionados = []
            
            for mes in meses_disponiveis_ano:
                if st.checkbox(
                    obter_nome_mes(mes),
                    key=f"analise_mes_{mes}"
                ):
                    meses_selecionados.append(mes)
        else:
            st.warning(f"⚠️ Nenhum mês com dados para o ano {ano_selecionado}")
            meses_selecionados = []
        
        
        # Nota: Botão "Voltar" removido pois agora usamos navegação por abas
    
    # Validar seleção de meses
    if len(meses_selecionados) > LIMITE_MAXIMO_MESES:
        st.error(f"⚠️ Máximo de {LIMITE_MAXIMO_MESES} meses permitidos!")
        return
    
    if len(meses_selecionados) == 0:
        st.warning("⚠️ Selecione pelo menos 1 mês para visualizar os dados.")
        return
    
    # Construir períodos selecionados
    periodos = [{'ano': ano_selecionado, 'mes': mes} for mes in meses_selecionados]
    
    # VALIDAÇÃO: Filtrar apenas períodos com dados disponíveis
    periodos_validos = filtrar_periodos_validos(usina_id, periodos)
    
    if not periodos_validos:
        st.warning(f"⚠️ Nenhum dado disponível para os meses selecionados.")
        st.info("💡 Selecione outros meses que possuam dados.")
        return
    
    texto_periodo = construir_texto_periodo(periodos_validos)
    
    # Exibir resumo da usina
    st.markdown("---")
    
    with st.spinner("Carregando dados da usina..."):
        try:
            # Calcular KPIs principais
            total_alarmes = calcular_total_alarmes(usina_id, periodos_validos)
            tempo_total_minutos = calcular_tempo_total_alarmado(usina_id, periodos_validos)
            tempo_reconhecimento_minutos = calcular_tempo_medio_reconhecimento(usina_id, periodos_validos)
            tempo_medio_minutos = calcular_tempo_medio_por_alarme(tempo_total_minutos, total_alarmes)
            
            # Exibir card de resumo
            exibir_card_resumo_usina(
                usina_nome_selecionada,
                total_alarmes,
                tempo_total_minutos,
                texto_periodo
            )
            
            st.markdown("---")
            
            # Exibir 4 KPIs principais
            st.subheader("📊 Indicadores Principais")
            exibir_cards_kpis_principais(
                total_alarmes,
                tempo_total_minutos,
                tempo_medio_minutos,
                tempo_reconhecimento_minutos
            )
            
            st.markdown("---")
            
            # GRÁFICO 1: Pizza - Tempo Total por Severidade
            st.subheader("🎨 Distribuição por Severidade")
            df_severidade = obter_tempo_por_severidade(usina_id, periodos_validos)
            if not df_severidade.empty:
                from streamlit_echarts import st_echarts
                grafico_pizza = criar_grafico_pizza_severidade(df_severidade)
                st_echarts(grafico_pizza, height="400px")
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            # GRÁFICOS 2 e 3: Equipamentos e Teleobjetos com Toggle
            st.subheader("⚙️ Top Equipamentos")
            df_equip_qtd = obter_top_equipamentos_por_quantidade(usina_id, periodos, LIMITE_TOP_10)
            df_equip_dur = obter_top_equipamentos_por_duracao(usina_id, periodos, LIMITE_TOP_10)
            
            # Combinar dataframes
            if not df_equip_qtd.empty and not df_equip_dur.empty:
                df_equipamentos = df_equip_qtd.merge(
                    df_equip_dur[['equipamento_nome_formatado', 'duracao_total_minutos']],
                    on='equipamento_nome_formatado',
                    how='outer',
                    suffixes=('', '_dur')
                ).fillna(0)
                
                exibir_grafico_com_toggle(
                    df_equipamentos,
                    "Top Equipamentos",
                    "equipamento_nome_formatado",
                    "quantidade_alarmes",
                    "duracao_total_minutos",
                    "equipamentos",
                    limite_inicial=5,
                    limite_expandido=50
                )
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            st.subheader("📡 Top Teleobjetos")
            df_tele_qtd = obter_top_teleobjetos_por_quantidade(usina_id, periodos, LIMITE_TOP_10)
            df_tele_dur = obter_top_teleobjetos_por_duracao(usina_id, periodos, LIMITE_TOP_10)
            
            if not df_tele_qtd.empty and not df_tele_dur.empty:
                df_teleobjetos = df_tele_qtd.merge(
                    df_tele_dur[['teleobjeto_nome', 'duracao_total_minutos']],
                    on='teleobjeto_nome',
                    how='outer',
                    suffixes=('', '_dur')
                ).fillna(0)
                
                exibir_grafico_com_toggle(
                    df_teleobjetos,
                    "Top Teleobjetos",
                    "teleobjeto_nome",
                    "quantidade_alarmes",
                    "duracao_total_minutos",
                    "teleobjetos",
                    limite_inicial=5,
                    limite_expandido=50
                )
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            # GRÁFICO 4: Sem Comunicação
            st.subheader("📶 Equipamentos Sem Comunicação")
            try:
                df_sem_com = obter_equipamentos_sem_comunicacao(usina_id, periodos, LIMITE_TOP_10)
                if not df_sem_com.empty:
                    from streamlit_echarts import st_echarts
                    grafico_sem_com = criar_grafico_barras_horizontais(
                        df_sem_com,
                        "Equipamentos Sem Comunicação - Top 10",
                        "equipamento_nome_formatado",
                        "duracao_total_minutos",
                        "Tempo Total (min)",
                        "#e74c3c",
                        formato_valor="tempo"
                    )
                    st_echarts(grafico_sem_com, height="400px")
                else:
                    st.info("📄 Nenhum alarme de 'sem comunicação' encontrado.")
            except Exception as e:
                logger.error(f"Erro ao exibir gráfico de equipamentos sem comunicação: {e}")
                st.error(f"❌ Erro ao carregar gráfico: {str(e)}")
            
            st.markdown("---")
            
            # SEÇÃO ESPECIAL: ANÁLISE DE NCUs
            st.subheader("🖥️ Análise de NCUs (Network Control Units)")
            
            try:
                # Buscar todos os alarmes de NCU
                df_ncu = obter_alarmes_ncu(usina_id, periodos_validos, LIMITE_TOP_10)
                
                if not df_ncu.empty:
                    # Gráfico de barras com NCUs
                    from streamlit_echarts import st_echarts
                    
                    grafico_ncu = criar_grafico_barras_horizontais(
                        dataframe=df_ncu,
                        titulo="Top NCUs por Tempo Total Alarmado",
                        coluna_nome="equipamento_nome_formatado",
                        coluna_valor="duracao_total_minutos",
                        nome_serie="Tempo Total (min)",
                        cor="#FF6B6B",
                        mostrar_valor=True,
                        formato_valor="tempo"
                    )
                    st_echarts(grafico_ncu, height="400px")
                    
                    # Seleção interativa de NCU para ver teleobjetos
                    st.markdown("### 🔍 Detalhes dos Teleobjetos por NCU")
                    
                    # Criar mapeamento de nome formatado para nome original
                    ncu_dict = dict(zip(df_ncu['equipamento_nome_formatado'], df_ncu['equipamento_nome']))
                    ncu_opcoes = list(ncu_dict.keys())
                    
                    ncu_selecionada_formatada = st.selectbox(
                        "Selecione uma NCU para ver seus teleobjetos:",
                        options=ncu_opcoes,
                        key="ncu_selector"
                    )
                    
                    if ncu_selecionada_formatada:
                        # Obter nome original do equipamento
                        ncu_nome_original = ncu_dict[ncu_selecionada_formatada]
                        
                        # Buscar teleobjetos da NCU selecionada
                        df_teleobjetos_ncu = obter_teleobjetos_ncu(
                            usina_id, 
                            periodos_validos, 
                            ncu_nome_original, 
                            LIMITE_TOP_20
                        )
                        
                        if not df_teleobjetos_ncu.empty:
                            st.markdown(f"**📊 Teleobjetos da NCU: {ncu_selecionada_formatada}**")
                            
                            # Gráfico de teleobjetos
                            grafico_tele_ncu = criar_grafico_barras_horizontais(
                                dataframe=df_teleobjetos_ncu,
                                titulo=f"Teleobjetos - {ncu_selecionada_formatada}",
                                coluna_nome="teleobjeto_nome",
                                coluna_valor="duracao_total_minutos",
                                nome_serie="Tempo Alarmado (min)",
                                cor="#4ECDC4",
                                mostrar_valor=True,
                                formato_valor="tempo"
                            )
                            st_echarts(grafico_tele_ncu, height="500px")
                            
                            # Tabela detalhada
                            with st.expander("📋 Ver Tabela Detalhada"):
                                st.dataframe(
                                    df_teleobjetos_ncu,
                                    use_container_width=True,
                                    hide_index=True
                                )
                        else:
                            st.info(f"📄 Nenhum teleobjeto encontrado para a NCU {ncu_selecionada_formatada}.")
                else:
                    st.info("📄 Nenhum equipamento NCU encontrado no período selecionado.")
            except Exception as e:
                logger.error(f"Erro ao exibir análise de NCU: {e}")
                st.error(f"❌ Erro ao carregar análise de NCU: {str(e)}")
            
            st.markdown("---")
            
            # GRÁFICO INTERMEDIÁRIO: Análise de Trackers (TR-XXX)
            st.subheader("📍 Análise de Trackers (TR-XXX)")
            
            try:
                # Buscar todos os alarmes agrupados por Tracker
                df_trackers = obter_alarmes_trackers(usina_id, periodos_validos, limite=20)
                
                if not df_trackers.empty:
                    # Gráfico de barras com Trackers
                    from streamlit_echarts import st_echarts
                    
                    grafico_trackers = criar_grafico_barras_horizontais(
                        dataframe=df_trackers,
                        titulo="Tempo Total Alarmado por Tracker (TR-XXX)",
                        coluna_nome="tracker_code",
                        coluna_valor="duracao_total_minutos",
                        nome_serie="Tempo Total (min)",
                        cor="#9B59B6",
                        mostrar_valor=True,
                        formato_valor="tempo"
                    )
                    st_echarts(grafico_trackers, height="450px")
                    
                    # Seleção interativa de Tracker para ver teleobjetos
                    st.markdown("### 🔍 Detalhes dos Teleobjetos por Tracker")
                    
                    tracker_opcoes = df_trackers['tracker_code'].tolist()
                    
                    tracker_selecionado = st.selectbox(
                        "Selecione um Tracker para ver seus teleobjetos:",
                        options=tracker_opcoes,
                        key="tracker_selector"
                    )
                    
                    if tracker_selecionado:
                        # Buscar teleobjetos do Tracker selecionado
                        df_teleobjetos_tracker = obter_teleobjetos_tracker(
                            usina_id, 
                            periodos_validos, 
                            tracker_selecionado, 
                            limite=25
                        )
                        
                        if not df_teleobjetos_tracker.empty:
                            st.markdown(f"**📊 Teleobjetos do Tracker: {tracker_selecionado}**")
                            
                            # Gráfico de teleobjetos
                            grafico_tele_tracker = criar_grafico_barras_horizontais(
                                dataframe=df_teleobjetos_tracker,
                                titulo=f"Teleobjetos - {tracker_selecionado}",
                                coluna_nome="teleobjeto_nome",
                                coluna_valor="duracao_total_minutos",
                                nome_serie="Tempo Alarmado (min)",
                                cor="#F39C12",
                                mostrar_valor=True,
                                formato_valor="tempo"
                            )
                            st_echarts(grafico_tele_tracker, height="500px")
                            
                            # Tabela detalhada
                            with st.expander("📋 Ver Tabela Detalhada"):
                                st.dataframe(
                                    df_teleobjetos_tracker,
                                    use_container_width=True,
                                    hide_index=True
                                )
                        else:
                            st.info(f"📄 Nenhum teleobjeto encontrado para o Tracker {tracker_selecionado}.")
                else:
                    st.info("📄 Nenhum Tracker (TR-XXX) encontrado no período selecionado.")
            except Exception as e:
                logger.error(f"Erro ao exibir análise de Trackers: {e}")
                st.error(f"❌ Erro ao carregar análise de Trackers: {str(e)}")
            
            st.markdown("---")
            
            # GRÁFICO 5: Tempo Médio de Reconhecimento por Severidade
            st.subheader("✅ Tempo de Reconhecimento por Severidade")
            df_reconh = obter_tempo_reconhecimento_por_severidade(usina_id, periodos_validos)
            if not df_reconh.empty:
                from streamlit_echarts import st_echarts
                grafico_reconh = criar_grafico_barras_tempo_medio(df_reconh)
                st_echarts(grafico_reconh, height="400px")
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            # GRÁFICO 6: Top Usuários Reconhecimento
            st.subheader("👥 Top Usuários que Mais Reconhecem")
            df_usuarios = obter_top_usuarios_reconhecimento(usina_id, periodos, LIMITE_TOP_10)
            if not df_usuarios.empty:
                from streamlit_echarts import st_echarts
                grafico_usuarios = criar_grafico_top_usuarios(df_usuarios)
                st_echarts(grafico_usuarios, height="400px")
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            # GRÁFICOS 7 e 8: Alarmes Críticos
            st.subheader("🚨 Alarmes Críticos")
            
            col_crit1, col_crit2 = st.columns(2)
            
            with col_crit1:
                st.markdown("**Por Equipamento:**")
                df_crit_equip = obter_alarmes_criticos_por_equipamento(usina_id, periodos, LIMITE_TOP_10)
                if not df_crit_equip.empty:
                    from streamlit_echarts import st_echarts
                    grafico_crit_equip = criar_grafico_barras_horizontais(
                        df_crit_equip,
                        "Alarmes Críticos - Equipamentos",
                        "equipamento_nome_formatado",
                        "duracao_total_minutos",
                        "Tempo Total (min)",
                        "#c0392b",
                        formato_valor="tempo"
                    )
                    st_echarts(grafico_crit_equip, height="400px")
                else:
                    st.info("📄 Nenhum alarme crítico.")
            
            with col_crit2:
                st.markdown("**Por Teleobjeto:**")
                df_crit_tele = obter_alarmes_criticos_por_teleobjeto(usina_id, periodos, LIMITE_TOP_10)
                if not df_crit_tele.empty:
                    from streamlit_echarts import st_echarts
                    grafico_crit_tele = criar_grafico_alarmes_criticos_teleobjeto(df_crit_tele)
                    st_echarts(grafico_crit_tele, height="400px")
                else:
                    st.info("📄 Nenhum alarme crítico.")
            
            st.markdown("---")
            
            # GRÁFICO 9: Alarmes Não Finalizados
            st.subheader("⏳ Alarmes Não Finalizados (Ativos)")
            df_nao_final = obter_alarmes_nao_finalizados(usina_id, periodos, LIMITE_TOP_10)
            if not df_nao_final.empty:
                from streamlit_echarts import st_echarts
                grafico_nao_final = criar_grafico_barras_horizontais(
                    df_nao_final,
                    "Alarmes Não Finalizados - Top 10",
                    "equipamento_nome_formatado",
                    "quantidade_alarmes_ativos",
                    "Quantidade de Alarmes Ativos",
                    "#f39c12"
                )
                st_echarts(grafico_nao_final, height="400px")
            else:
                st.info("📄 Todos os alarmes foram finalizados.")
            
            st.markdown("---")
            
            # GRÁFICO 10: Evolução Diária
            st.subheader("📈 Evolução Diária de Alarmes")
            
            # Toggle entre Quantidade e Duração
            modo_evolucao = st.radio(
                "Exibir:",
                options=["Quantidade", "Duração Total"],
                horizontal=True,
                key="modo_evolucao"
            )
            
            df_evolucao = obter_evolucao_diaria(usina_id, periodos_validos)
            if not df_evolucao.empty:
                from streamlit_echarts import st_echarts
                modo = "quantidade" if modo_evolucao == "Quantidade" else "duracao"
                grafico_evolucao = criar_grafico_linha_evolucao(df_evolucao, modo=modo)
                st_echarts(grafico_evolucao, height="400px")
            else:
                st.info("📄 Nenhum dado disponível.")
            
            st.markdown("---")
            
            # Tabela de Alarmes
            st.subheader("📋 Lista de Alarmes Detalhada")
            
            # Obter página atual
            pagina_atual = st.session_state.get('pagina_tabela', 1)
            
            # Calcular offset
            from config import ALARMES_POR_PAGINA
            offset = (pagina_atual - 1) * ALARMES_POR_PAGINA
            
            df_alarmes = obter_lista_alarmes(usina_id, periodos, offset=offset, limite=ALARMES_POR_PAGINA)
            
            if not df_alarmes.empty:
                exibir_tabela_alarmes(df_alarmes, pagina_atual=pagina_atual)
            else:
                st.info("📄 Nenhum alarme encontrado para o período selecionado.")
            
        except Exception as e:
            logger.error(f"Erro ao processar análise detalhada: {e}")
            st.error(f"""
                ❌ **Erro ao processar dados**
                
                Ocorreu um erro ao carregar os dados da usina.
                
                **Detalhes:** {str(e)}
            """)


# ============================================================================
# ROTEAMENTO DE PÁGINAS
# ============================================================================

def main():
    """
    Função principal que gerencia o roteamento entre páginas.
    """
    # Título principal da aplicação
    st.title(f"{ICONE_APLICACAO} Sistema de Análise de Alarmes")
    
    # Inicializar session_state para controle de aba
    if 'aba_ativa' not in st.session_state:
        st.session_state['aba_ativa'] = 0  # 0 = HOME, 1 = Análise
    
    # Navegação por ABAS (tabs)
    tab_home, tab_analise = st.tabs(["🏠 HOME - Visão Geral", "📊 Análise Detalhada por Usina"])
    
    # Detectar qual aba está ativa através de um truque com containers
    # Como não há callback direto para tabs, usamos session_state de forma criativa
    
    # Renderizar conteúdo apropriado em cada aba
    with tab_home:
        # Indicador de que esta aba foi acessada
        if st.button("🔄 Atualizar Página HOME", key="refresh_home", help="Clique para recarregar dados"):
            st.rerun()
        
        pagina_home()
    
    with tab_analise:
        # Indicador de que esta aba foi acessada
        if st.button("🔄 Atualizar Página Análise", key="refresh_analise", help="Clique para recarregar dados"):
            st.rerun()
        
        pagina_analise()
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #888; font-size: 12px;'>
            © 2025 ATI - Sistema de Análise de Alarmes (SAA) v2.1.1
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    main()

