"""
Módulo de Conexão com Banco de Dados

Este módulo gerencia a conexão com o PostgreSQL usando SQLAlchemy.
Fornece funções para obter engine, sessões e testar a conexão.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import logging

from config import DATABASE_URL

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais para engine e session factory
_engine = None
_SessionFactory = None


def obter_engine():
    """
    Obtém ou cria o engine do SQLAlchemy para conexão com PostgreSQL.
    
    Esta função implementa um padrão singleton para garantir que apenas
    uma instância do engine seja criada durante a execução da aplicação.
    
    Retorna:
        Engine: Instância do engine SQLAlchemy
    
    Exemplo:
        >>> engine = obter_engine()
        >>> with engine.connect() as conexao:
        ...     resultado = conexao.execute(text("SELECT 1"))
    """
    global _engine
    
    if _engine is None:
        try:
            logger.info("Criando engine do SQLAlchemy...")
            _engine = create_engine(
                DATABASE_URL,
                pool_size=10,  # Número de conexões no pool
                max_overflow=20,  # Conexões extras além do pool_size
                pool_pre_ping=True,  # Testa conexão antes de usar
                echo=False,  # Não logar SQL (mudar para True em debug)
            )
            logger.info("Engine criado com sucesso!")
        except SQLAlchemyError as erro:
            logger.error(f"Erro ao criar engine: {erro}")
            raise
    
    return _engine


def obter_sessao() -> Session:
    """
    Obtém uma nova sessão do SQLAlchemy para executar queries.
    
    Esta função cria uma nova sessão a partir do SessionFactory.
    É importante sempre fechar a sessão após o uso (use with statement).
    
    Retorna:
        Session: Nova sessão do SQLAlchemy
    
    Exemplo:
        >>> with obter_sessao() as sessao:
        ...     usinas = sessao.query(Usina).all()
        ...     for usina in usinas:
        ...         print(usina.nome)
    """
    global _SessionFactory
    
    if _SessionFactory is None:
        engine = obter_engine()
        _SessionFactory = sessionmaker(bind=engine)
    
    return _SessionFactory()


def testar_conexao() -> bool:
    """
    Testa a conexão com o banco de dados PostgreSQL.
    
    Executa uma query simples (SELECT 1) para verificar se a conexão
    está funcionando corretamente.
    
    Retorna:
        bool: True se conexão bem-sucedida, False caso contrário
    
    Exemplo:
        >>> if testar_conexao():
        ...     print("Conexão OK!")
        ... else:
        ...     print("Falha na conexão!")
    """
    try:
        engine = obter_engine()
        with engine.connect() as conexao:
            resultado = conexao.execute(text("SELECT 1"))
            resultado.fetchone()
        logger.info("✅ Conexão com banco de dados OK!")
        return True
    except SQLAlchemyError as erro:
        logger.error(f"❌ Erro ao conectar ao banco de dados: {erro}")
        return False


def fechar_conexao():
    """
    Fecha todas as conexões do pool e descarta o engine.
    
    Esta função deve ser chamada ao finalizar a aplicação para
    liberar recursos de forma adequada.
    
    Exemplo:
        >>> fechar_conexao()
    """
    global _engine, _SessionFactory
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionFactory = None
        logger.info("Conexões fechadas com sucesso.")
