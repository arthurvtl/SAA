"""
Módulo Database

Este módulo contém todos os componentes necessários para acesso ao banco de dados:
- Conexão com PostgreSQL via SQLAlchemy
- Modelos ORM para todas as tabelas
- Funções de consulta SQL otimizadas
"""

from .conexao import obter_engine, obter_sessao, testar_conexao
from .models import (
    Usina,
    Equipamento,
    Skid,
    Teleobjeto,
    TeleobjetoConfig,
    Severidade,
    Usuario,
)

__all__ = [
    "obter_engine",
    "obter_sessao",
    "testar_conexao",
    "Usina",
    "Equipamento",
    "Skid",
    "Teleobjeto",
    "TeleobjetoConfig",
    "Severidade",
    "Usuario",
]
