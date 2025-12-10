"""
Arquivo de Configurações do Sistema de Análise de Alarmes (SAA)

Este módulo contém todas as configurações necessárias para conexão com o banco de dados
e outras configurações gerais do sistema.
"""

import os
from typing import Final

# ============================================================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ============================================================================

# URL de conexão com PostgreSQL
DATABASE_URL: Final[str] = "BANCO DE DADOS"


# ============================================================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================================================

# Limite máximo de meses que podem ser selecionados por vez
LIMITE_MAXIMO_MESES: Final[int] = 3

# Quantidade de alarmes por página na tabela
ALARMES_POR_PAGINA: Final[int] = 50

# Limite de registros para rankings
LIMITE_TOP_5: Final[int] = 5
LIMITE_TOP_10: Final[int] = 10
LIMITE_TOP_20: Final[int] = 20
LIMITE_TOP_50: Final[int] = 50

# ============================================================================
# CONFIGURAÇÕES DE SEVERIDADE
# ============================================================================

# ID da severidade crítica (conforme banco de dados)
SEVERIDADE_CRITICA_ID: Final[int] = 1

# Mapeamento de cores das severidades (padrão)
CORES_SEVERIDADE: Final[dict] = {
    1: "#f14e4e",  # Crítica - vermelho
    2: "#fdc262",  # Alta - laranja
    3: "#ffe00a",  # Média - amarelo
    4: "#80FFFF",  # Baixa - azul claro
    5: "#F0F0F0",  # Não Aplicável - cinza
    6: "#000000",  # Urgente - preto
}

# ============================================================================
# CONFIGURAÇÕES DE APARÊNCIA
# ============================================================================

# Tema do sistema
TEMA: Final[str] = "light"

# Título da aplicação
TITULO_APLICACAO: Final[str] = "🔆 Sistema de Análise de Alarmes - Inversores Solares"

# Ícone da aplicação (emoji)
ICONE_APLICACAO: Final[str] = "🔆"

# Layout da página
LAYOUT_PAGINA: Final[str] = "wide"
