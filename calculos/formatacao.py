"""
Módulo de Formatação

Este módulo contém funções para formatar valores numéricos, tempos
e percentuais para exibição amigável ao usuário.
"""

from typing import Union
import math


def formatar_tempo_minutos(minutos: float) -> str:
    """
    Formata tempo em minutos para formato legível: "X dias, Y horas, Z minutos".
    
    Parâmetros:
        minutos: Tempo em minutos
    
    Retorna:
        str: Tempo formatado no padrão "X dias, Y horas, Z minutos"
    
    Exemplo:
        >>> tempo = formatar_tempo_minutos(1500)
        >>> print(tempo)
        "1 dia, 1 hora, 0 minutos"
        
        >>> tempo = formatar_tempo_minutos(65)
        >>> print(tempo)
        "1 hora, 5 minutos"
    """
    if minutos == 0:
        return "0 minutos"
    
    # Converter para valores inteiros
    minutos_totais = int(minutos)
    
    # Calcular dias, horas e minutos
    dias = minutos_totais // 1440  # 1 dia = 1440 minutos
    horas = (minutos_totais % 1440) // 60
    mins = minutos_totais % 60
    
    # Construir string formatada
    partes = []
    
    if dias > 0:
        partes.append(f"{dias} dia" if dias == 1 else f"{dias} dias")
    
    if horas > 0:
        partes.append(f"{horas} hora" if horas == 1 else f"{horas} horas")
    
    if mins > 0 or len(partes) == 0:
        partes.append(f"{mins} minuto" if mins == 1 else f"{mins} minutos")
    
    return ", ".join(partes)


def formatar_tempo_horas(horas: float) -> str:
    """
    Formata tempo em horas para formato legível: "X horas, Y minutos".
    
    Parâmetros:
        horas: Tempo em horas
    
    Retorna:
        str: Tempo formatado
    
    Exemplo:
        >>> tempo = formatar_tempo_horas(2.5)
        >>> print(tempo)
        "2 horas, 30 minutos"
    """
    minutos = horas * 60
    return formatar_tempo_minutos(minutos)


def formatar_tempo_compacto(minutos: float) -> str:
    """
    Formata tempo em minutos para formato compacto: "Xd Yh Zm".
    
    Parâmetros:
        minutos: Tempo em minutos
    
    Retorna:
        str: Tempo formatado no padrão compacto "Xd Yh Zm"
    
    Exemplo:
        >>> tempo = formatar_tempo_compacto(1500)
        >>> print(tempo)
        "1d 1h 0m"
        
        >>> tempo = formatar_tempo_compacto(65)
        >>> print(tempo)
        "1h 5m"
    """
    if minutos == 0:
        return "0m"
    
    # Converter para valores inteiros
    minutos_totais = int(minutos)
    
    # Calcular dias, horas e minutos
    dias = minutos_totais // 1440
    horas = (minutos_totais % 1440) // 60
    mins = minutos_totais % 60
    
    # Construir string formatada
    partes = []
    
    if dias > 0:
        partes.append(f"{dias}d")
    
    if horas > 0:
        partes.append(f"{horas}h")
    
    if mins > 0 or len(partes) == 0:
        partes.append(f"{mins}m")
    
    return " ".join(partes)


def formatar_numero(numero: Union[int, float], casas_decimais: int = 0) -> str:
    """
    Formata número com separador de milhares.
    
    Parâmetros:
        numero: Número a ser formatado
        casas_decimais: Número de casas decimais (padrão: 0)
    
    Retorna:
        str: Número formatado com separador de milhares
    
    Exemplo:
        >>> num = formatar_numero(1234567)
        >>> print(num)
        "1.234.567"
        
        >>> num = formatar_numero(1234.567, 2)
        >>> print(num)
        "1.234,57"
    """
    if casas_decimais == 0:
        return f"{int(numero):,}".replace(",", ".")
    else:
        # Formatar com casas decimais
        numero_str = f"{numero:,.{casas_decimais}f}"
        # Substituir separadores para padrão brasileiro
        numero_str = numero_str.replace(",", "_").replace(".", ",").replace("_", ".")
        return numero_str


def formatar_percentual(valor: float, casas_decimais: int = 2) -> str:
    """
    Formata um valor como percentual.
    
    Parâmetros:
        valor: Valor numérico (0-100)
        casas_decimais: Número de casas decimais (padrão: 2)
    
    Retorna:
        str: Valor formatado como percentual
    
    Exemplo:
        >>> perc = formatar_percentual(25.5)
        >>> print(perc)
        "25,50%"
        
        >>> perc = formatar_percentual(100)
        >>> print(perc)
        "100,00%"
    """
    return f"{valor:.{casas_decimais}f}".replace(".", ",") + "%"


def formatar_duracao_para_grafico(minutos: float) -> str:
    """
    Formata duração para exibição em gráficos (formato curto).
    
    Parâmetros:
        minutos: Tempo em minutos
    
    Retorna:
        str: Tempo formatado para gráficos
    
    Exemplo:
        >>> duracao = formatar_duracao_para_grafico(125)
        >>> print(duracao)
        "2h 5m"
        
        >>> duracao = formatar_duracao_para_grafico(45)
        >>> print(duracao)
        "45m"
    """
    if minutos == 0:
        return "0m"
    
    minutos_totais = int(minutos)
    
    # Se for mais de 24 horas, mostrar em dias
    if minutos_totais >= 1440:
        dias = minutos_totais // 1440
        horas = (minutos_totais % 1440) // 60
        if horas > 0:
            return f"{dias}d {horas}h"
        return f"{dias}d"
    
    # Se for mais de 1 hora, mostrar em horas e minutos
    if minutos_totais >= 60:
        horas = minutos_totais // 60
        mins = minutos_totais % 60
        if mins > 0:
            return f"{horas}h {mins}m"
        return f"{horas}h"
    
    # Menos de 1 hora, mostrar em minutos
    return f"{minutos_totais}m"


def formatar_data_brasileira(data_str: str) -> str:
    """
    Formata data para padrão brasileiro DD/MM/YYYY.
    
    Parâmetros:
        data_str: Data no formato ISO (YYYY-MM-DD) ou datetime
    
    Retorna:
        str: Data no formato DD/MM/YYYY
    
    Exemplo:
        >>> data = formatar_data_brasileira("2025-06-15")
        >>> print(data)
        "15/06/2025"
    """
    from datetime import datetime
    
    # Se já é um objeto datetime
    if isinstance(data_str, datetime):
        return data_str.strftime("%d/%m/%Y")
    
    # Se é string, tentar parsear
    try:
        data = datetime.fromisoformat(str(data_str))
        return data.strftime("%d/%m/%Y")
    except:
        return str(data_str)


def formatar_data_hora_brasileira(data_str: str) -> str:
    """
    Formata data e hora para padrão brasileiro DD/MM/YYYY HH:MM.
    
    Parâmetros:
        data_str: Data/hora no formato ISO ou datetime
    
    Retorna:
        str: Data/hora no formato DD/MM/YYYY HH:MM
    
    Exemplo:
        >>> data_hora = formatar_data_hora_brasileira("2025-06-15 14:30:00")
        >>> print(data_hora)
        "15/06/2025 14:30"
    """
    from datetime import datetime
    
    # Se já é um objeto datetime
    if isinstance(data_str, datetime):
        return data_str.strftime("%d/%m/%Y %H:%M")
    
    # Se é string, tentar parsear
    try:
        data = datetime.fromisoformat(str(data_str))
        return data.strftime("%d/%m/%Y %H:%M")
    except:
        return str(data_str)


def abreviar_texto(texto: str, tamanho_maximo: int = 50) -> str:
    """
    Abrevia texto longo para exibição em gráficos.
    
    Parâmetros:
        texto: Texto a ser abreviado
        tamanho_maximo: Tamanho máximo (padrão: 50)
    
    Retorna:
        str: Texto abreviado com "..." se necessário
    
    Exemplo:
        >>> texto = abreviar_texto("Este é um texto muito longo que precisa ser abreviado", 20)
        >>> print(texto)
        "Este é um texto mu..."
    """
    if len(texto) <= tamanho_maximo:
        return texto
    
    return texto[:tamanho_maximo-3] + "..."
