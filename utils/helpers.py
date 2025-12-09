"""
Módulo de Funções Auxiliares

Este módulo contém funções utilitárias gerais que são usadas em
diferentes partes do sistema.
"""

import streamlit as st
from typing import List, Dict, Any, Tuple
from datetime import datetime
import calendar

from config import LIMITE_MAXIMO_MESES


def validar_periodos_selecionados(periodos: List[Dict[str, int]]) -> Tuple[bool, str]:
    """
    Valida se os períodos selecionados estão dentro das regras de negócio.
    
    Parâmetros:
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        Tuple (valido: bool, mensagem_erro: str)
    
    Regras:
        - Máximo de 3 meses por consulta
        - Pelo menos 1 período deve ser selecionado
    
    Exemplo:
        >>> periodos = [{'ano': 2025, 'mes': 6}, {'ano': 2025, 'mes': 7}]
        >>> valido, msg = validar_periodos_selecionados(periodos)
        >>> if not valido:
        ...     print(msg)
    """
    # Verificar se pelo menos 1 período foi selecionado
    if not periodos or len(periodos) == 0:
        return False, "⚠️ Por favor, selecione pelo menos 1 período (mês/ano) para análise."
    
    # Verificar limite máximo de meses
    if len(periodos) > LIMITE_MAXIMO_MESES:
        return False, f"⚠️ Máximo de {LIMITE_MAXIMO_MESES} meses por consulta. Você selecionou {len(periodos)} meses."
    
    return True, ""


def obter_nome_mes(numero_mes: int) -> str:
    """
    Obtém o nome do mês em português a partir do número.
    
    Parâmetros:
        numero_mes: Número do mês (1-12)
    
    Retorna:
        str: Nome do mês em português
    
    Exemplo:
        >>> obter_nome_mes(1)
        'Janeiro'
        >>> obter_nome_mes(12)
        'Dezembro'
    """
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    if 1 <= numero_mes <= 12:
        return meses[numero_mes - 1]
    
    return f"Mês {numero_mes}"


def obter_nome_mes_abreviado(numero_mes: int) -> str:
    """
    Obtém o nome abreviado do mês em português.
    
    Parâmetros:
        numero_mes: Número do mês (1-12)
    
    Retorna:
        str: Nome abreviado do mês
    
    Exemplo:
        >>> obter_nome_mes_abreviado(1)
        'Jan'
        >>> obter_nome_mes_abreviado(12)
        'Dez'
    """
    meses_abrev = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]
    
    if 1 <= numero_mes <= 12:
        return meses_abrev[numero_mes - 1]
    
    return f"M{numero_mes}"


def construir_texto_periodo(periodos: List[Dict[str, int]]) -> str:
    """
    Constrói texto descritivo do período selecionado.
    
    Parâmetros:
        periodos: Lista de períodos {'ano': ..., 'mes': ...}
    
    Retorna:
        str: Texto descritivo do período
    
    Exemplo:
        >>> periodos = [{'ano': 2025, 'mes': 6}]
        >>> construir_texto_periodo(periodos)
        'Junho/2025'
        
        >>> periodos = [
        ...     {'ano': 2025, 'mes': 5},
        ...     {'ano': 2025, 'mes': 6},
        ...     {'ano': 2025, 'mes': 7}
        ... ]
        >>> construir_texto_periodo(periodos)
        'Maio/2025, Junho/2025, Julho/2025'
    """
    if not periodos:
        return "Nenhum período selecionado"
    
    # Ordenar períodos por ano e mês
    periodos_ordenados = sorted(periodos, key=lambda p: (p['ano'], p['mes']))
    
    # Construir lista de textos
    textos = []
    for periodo in periodos_ordenados:
        mes_nome = obter_nome_mes(periodo['mes'])
        textos.append(f"{mes_nome}/{periodo['ano']}")
    
    # Se forem consecutivos do mesmo ano, pode usar formato compacto
    if len(periodos_ordenados) > 2:
        primeiro = periodos_ordenados[0]
        ultimo = periodos_ordenados[-1]
        
        # Verificar se são consecutivos
        consecutivos = True
        for i in range(1, len(periodos_ordenados)):
            diff_meses = (
                periodos_ordenados[i]['ano'] * 12 + periodos_ordenados[i]['mes']
            ) - (
                periodos_ordenados[i-1]['ano'] * 12 + periodos_ordenados[i-1]['mes']
            )
            if diff_meses != 1:
                consecutivos = False
                break
        
        if consecutivos and primeiro['ano'] == ultimo['ano']:
            # Formato compacto: "Maio a Julho/2025"
            return f"{obter_nome_mes(primeiro['mes'])} a {obter_nome_mes(ultimo['mes'])}/{primeiro['ano']}"
    
    # Formato padrão: lista separada por vírgulas
    return ", ".join(textos)


def inicializar_session_state():
    """
    Inicializa variáveis do session_state do Streamlit.
    
    Esta função deve ser chamada no início do app.py para garantir
    que todas as variáveis de estado necessárias existam.
    
    Variáveis inicializadas:
        - pagina_atual: Página selecionada ('home' ou 'analise')
        - usina_selecionada: ID da usina selecionada
        - ano_selecionado: Ano selecionado
        - meses_selecionados: Lista de meses selecionados
        - pagina_tabela: Página atual da tabela de alarmes
        - equipamentos_expandido: Se gráfico de equipamentos está expandido
        - teleobjetos_expandido: Se gráfico de teleobjetos está expandido
    
    Exemplo:
        >>> # No início do app.py
        >>> inicializar_session_state()
    """
    # Variáveis de navegação
    if 'pagina_atual' not in st.session_state:
        st.session_state['pagina_atual'] = 'home'
    
    # Variáveis de seleção de usina e período
    if 'usina_selecionada' not in st.session_state:
        st.session_state['usina_selecionada'] = None
    
    if 'ano_selecionado' not in st.session_state:
        st.session_state['ano_selecionado'] = datetime.now().year
    
    if 'meses_selecionados' not in st.session_state:
        st.session_state['meses_selecionados'] = []
    
    # Variáveis de paginação
    if 'pagina_tabela' not in st.session_state:
        st.session_state['pagina_tabela'] = 1
    
    # Variáveis de expansão de gráficos
    if 'equipamentos_expandido' not in st.session_state:
        st.session_state['equipamentos_expandido'] = False
    
    if 'teleobjetos_expandido' not in st.session_state:
        st.session_state['teleobjetos_expandido'] = False


def limpar_cache_graficos():
    """
    Limpa o cache de gráficos e estados de expansão.
    
    Útil quando o usuário muda de usina ou período.
    
    Exemplo:
        >>> # Quando usuário seleciona nova usina
        >>> limpar_cache_graficos()
        >>> st.rerun()
    """
    st.session_state['equipamentos_expandido'] = False
    st.session_state['teleobjetos_expandido'] = False
    st.session_state['pagina_tabela'] = 1


def gerar_opcoes_anos(ano_inicial: int = 2021, ano_final: int = None) -> List[int]:
    """
    Gera lista de anos para seleção.
    
    Parâmetros:
        ano_inicial: Ano inicial (padrão: 2021)
        ano_final: Ano final (padrão: ano atual)
    
    Retorna:
        List[int]: Lista de anos em ordem decrescente
    
    Exemplo:
        >>> anos = gerar_opcoes_anos(2021, 2025)
        >>> print(anos)
        [2025, 2024, 2023, 2022, 2021]
    """
    if ano_final is None:
        ano_final = datetime.now().year
    
    return list(range(ano_final, ano_inicial - 1, -1))


def gerar_opcoes_meses() -> List[Dict[str, Any]]:
    """
    Gera lista de meses para seleção.
    
    Retorna:
        List[Dict]: Lista com dicionários {'numero': int, 'nome': str}
    
    Exemplo:
        >>> meses = gerar_opcoes_meses()
        >>> print(meses[0])
        {'numero': 1, 'nome': 'Janeiro'}
    """
    return [
        {'numero': i, 'nome': obter_nome_mes(i)}
        for i in range(1, 13)
    ]


def formatar_lista_meses(numeros_meses: List[int]) -> str:
    """
    Formata lista de números de meses como texto.
    
    Parâmetros:
        numeros_meses: Lista de números de meses (1-12)
    
    Retorna:
        str: Texto formatado com nomes dos meses
    
    Exemplo:
        >>> formatar_lista_meses([1, 2, 3])
        'Janeiro, Fevereiro, Março'
    """
    if not numeros_meses:
        return "Nenhum mês selecionado"
    
    nomes = [obter_nome_mes(m) for m in sorted(numeros_meses)]
    return ", ".join(nomes)


def criar_chave_unica(prefixo: str, *args) -> str:
    """
    Cria uma chave única para widgets do Streamlit.
    
    Parâmetros:
        prefixo: Prefixo da chave
        *args: Argumentos adicionais para compor a chave
    
    Retorna:
        str: Chave única
    
    Exemplo:
        >>> chave = criar_chave_unica("grafico", "equipamentos", 86, 2025)
        >>> print(chave)
        'grafico_equipamentos_86_2025'
    """
    partes = [str(prefixo)] + [str(arg) for arg in args]
    return "_".join(partes)


def validar_conexao_banco() -> bool:
    """
    Valida se a conexão com o banco de dados está funcionando.
    
    Retorna:
        bool: True se conexão OK, False caso contrário
    
    Exemplo:
        >>> if not validar_conexao_banco():
        ...     st.error("Erro de conexão com banco de dados!")
        ...     st.stop()
    """
    from database.conexao import testar_conexao
    return testar_conexao()


def exibir_mensagem_erro_padrao(erro: Exception):
    """
    Exibe mensagem de erro padronizada.
    
    Parâmetros:
        erro: Exceção capturada
    
    Exemplo:
        >>> try:
        ...     # alguma operação
        ...     pass
        >>> except Exception as e:
        ...     exibir_mensagem_erro_padrao(e)
    """
    st.error(
        f"""
        ❌ **Erro ao processar solicitação**
        
        Ocorreu um erro inesperado. Por favor, tente novamente.
        
        **Detalhes técnicos:**  
        `{str(erro)}`
        
        Se o erro persistir, entre em contato com o suporte.
        """
    )
