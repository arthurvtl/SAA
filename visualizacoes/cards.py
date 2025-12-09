"""
Módulo de Cards

Este módulo contém funções para exibir cards de KPIs usando Streamlit.
Cards são úteis para destacar métricas importantes de forma visual.
"""

import streamlit as st
from typing import Optional, Dict, Any

from calculos.formatacao import (
    formatar_tempo_minutos,
    formatar_tempo_compacto,
    formatar_numero,
    formatar_percentual
)


def exibir_card_kpi(
    titulo: str,
    valor: Any,
    icone: str = "📊",
    cor: str = "#3498db",
    subtitulo: Optional[str] = None,
    delta: Optional[str] = None,
    delta_cor: str = "normal"  # "normal", "inverse", "off"
):
    """
    Exibe um card com KPI individual.
    
    Parâmetros:
        titulo: Título do KPI
        valor: Valor do KPI (pode ser string ou número)
        icone: Emoji ou ícone a exibir
        cor: Cor de destaque do card (hex)
        subtitulo: Texto adicional abaixo do valor (opcional)
        delta: Variação do KPI (ex: "+5%", "-3 alarmes")
        delta_cor: Cor do delta ("normal", "inverse", "off")
    
    Exemplo:
        >>> exibir_card_kpi(
        ...     titulo="Total de Alarmes",
        ...     valor="1.234",
        ...     icone="🚨",
        ...     subtitulo="No período selecionado",
        ...     delta="+15%"
        ... )
    """
    # Criar container com estilo
    with st.container():
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {cor}15 0%, {cor}05 100%);
                border-left: 4px solid {cor};
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="font-size: 14px; color: #666; margin-bottom: 5px;">
                    {icone} {titulo}
                </div>
                <div style="font-size: 32px; font-weight: bold; color: {cor}; margin: 10px 0;">
                    {valor}
                </div>
                {f'<div style="font-size: 12px; color: #888;">{subtitulo}</div>' if subtitulo else ''}
                {f'<div style="font-size: 12px; color: green; margin-top: 5px;">{delta}</div>' if delta else ''}
            </div>
            """,
            unsafe_allow_html=True
        )


def exibir_cards_kpis_principais(
    total_alarmes: int,
    tempo_total_minutos: float,
    tempo_medio_minutos: float,
    tempo_reconhecimento_minutos: float
):
    """
    Exibe os 4 cards principais de KPIs lado a lado.
    
    Parâmetros:
        total_alarmes: Total de alarmes no período
        tempo_total_minutos: Tempo total em minutos que ficou alarmado
        tempo_medio_minutos: Tempo médio por alarme em minutos
        tempo_reconhecimento_minutos: Tempo médio de reconhecimento em minutos
    
    Exemplo:
        >>> exibir_cards_kpis_principais(
        ...     total_alarmes=1234,
        ...     tempo_total_minutos=5000.0,
        ...     tempo_medio_minutos=4.05,
        ...     tempo_reconhecimento_minutos=15.5
        ... )
    """
    # Criar 4 colunas
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Total de Alarmes
    with col1:
        exibir_card_kpi(
            titulo="Total de Alarmes",
            valor=formatar_numero(total_alarmes),
            icone="🚨",
            cor="#e74c3c"
        )
    
    # KPI 2: Tempo Total Alarmado
    with col2:
        exibir_card_kpi(
            titulo="Tempo Total Alarmado",
            valor=formatar_tempo_compacto(tempo_total_minutos),
            icone="⏱️",
            cor="#f39c12",
            subtitulo=formatar_tempo_minutos(tempo_total_minutos)
        )
    
    # KPI 3: Tempo Médio por Alarme
    with col3:
        exibir_card_kpi(
            titulo="Tempo Médio por Alarme",
            valor=formatar_tempo_compacto(tempo_medio_minutos),
            icone="📊",
            cor="#3498db",
            subtitulo=f"{tempo_medio_minutos:.2f} minutos"
        )
    
    # KPI 4: Tempo Médio de Reconhecimento
    with col4:
        exibir_card_kpi(
            titulo="Tempo Médio de Reconhecimento",
            valor=formatar_tempo_compacto(tempo_reconhecimento_minutos),
            icone="✅",
            cor="#27ae60",
            subtitulo=f"{tempo_reconhecimento_minutos:.2f} minutos"
        )


def exibir_card_resumo_usina(
    nome_usina: str,
    total_alarmes: int,
    tempo_total_minutos: float,
    periodo: str
):
    """
    Exibe card com resumo de uma usina específica.
    
    Parâmetros:
        nome_usina: Nome da usina
        total_alarmes: Total de alarmes
        tempo_total_minutos: Tempo total alarmado
        periodo: Período analisado (ex: "Junho/2025")
    
    Exemplo:
        >>> exibir_card_resumo_usina(
        ...     nome_usina="Usina Solar A",
        ...     total_alarmes=500,
        ...     tempo_total_minutos=2000.0,
        ...     periodo="Junho/2025"
        ... )
    """
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        ">
            <h2 style="margin: 0 0 10px 0; font-size: 24px;">
                🌞 {nome_usina}
            </h2>
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 20px;">
                Período: {periodo}
            </div>
            <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold;">
                        {formatar_numero(total_alarmes)}
                    </div>
                    <div style="font-size: 12px; opacity: 0.8;">
                        Alarmes
                    </div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 28px; font-weight: bold;">
                        {formatar_tempo_compacto(tempo_total_minutos)}
                    </div>
                    <div style="font-size: 12px; opacity: 0.8;">
                        Tempo Total
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def exibir_card_alerta(
    titulo: str,
    mensagem: str,
    tipo: str = "info"  # "info", "warning", "error", "success"
):
    """
    Exibe card de alerta colorido.
    
    Parâmetros:
        titulo: Título do alerta
        mensagem: Mensagem do alerta
        tipo: Tipo do alerta ("info", "warning", "error", "success")
    
    Exemplo:
        >>> exibir_card_alerta(
        ...     titulo="Atenção",
        ...     mensagem="Máximo de 3 meses por consulta",
        ...     tipo="warning"
        ... )
    """
    # Definir cores por tipo
    cores = {
        "info": {"bg": "#3498db", "icone": "ℹ️"},
        "warning": {"bg": "#f39c12", "icone": "⚠️"},
        "error": {"bg": "#e74c3c", "icone": "❌"},
        "success": {"bg": "#27ae60", "icone": "✅"},
    }
    
    config = cores.get(tipo, cores["info"])
    
    st.markdown(
        f"""
        <div style="
            background-color: {config['bg']}15;
            border-left: 4px solid {config['bg']};
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        ">
            <div style="font-size: 16px; font-weight: bold; color: {config['bg']}; margin-bottom: 5px;">
                {config['icone']} {titulo}
            </div>
            <div style="font-size: 14px; color: #333;">
                {mensagem}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def exibir_card_estatistica(
    titulo: str,
    valores: Dict[str, Any],
    cor: str = "#3498db"
):
    """
    Exibe card com múltiplas estatísticas.
    
    Parâmetros:
        titulo: Título do card
        valores: Dicionário com label: valor
        cor: Cor de destaque
    
    Exemplo:
        >>> exibir_card_estatistica(
        ...     titulo="Estatísticas Gerais",
        ...     valores={
        ...         "Total de Usinas": "55",
        ...         "Período": "Junho/2025",
        ...         "Alarmes Críticos": "234"
        ...     }
        ... )
    """
    linhas_html = ""
    for label, valor in valores.items():
        linhas_html += f"""
            <div style="
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            ">
                <span style="color: #666;">{label}:</span>
                <span style="font-weight: bold; color: {cor};">{valor}</span>
            </div>
        """
    
    st.markdown(
        f"""
        <div style="
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <h3 style="margin: 0 0 15px 0; color: {cor};">{titulo}</h3>
            {linhas_html}
        </div>
        """,
        unsafe_allow_html=True
    )
