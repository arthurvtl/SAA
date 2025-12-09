"""
Módulo de Cálculos

Este módulo contém funções para cálculo de KPIs, agregações de dados
e formatação de valores para exibição.
"""

from .kpis import (
    calcular_kpis_principais,
    calcular_tempo_medio_por_alarme,
)
from .formatacao import (
    formatar_tempo_minutos,
    formatar_tempo_horas,
    formatar_numero,
    formatar_percentual,
)
from .agregacoes import (
    agregar_por_severidade,
    agregar_por_equipamento,
    agregar_por_teleobjeto,
)

__all__ = [
    "calcular_kpis_principais",
    "calcular_tempo_medio_por_alarme",
    "formatar_tempo_minutos",
    "formatar_tempo_horas",
    "formatar_numero",
    "formatar_percentual",
    "agregar_por_severidade",
    "agregar_por_equipamento",
    "agregar_por_teleobjeto",
]
