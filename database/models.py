"""
Módulo de Modelos ORM

Este módulo contém todos os modelos SQLAlchemy (ORM) que representam
as tabelas do banco de dados.

NOTA: As tabelas alarm_* são dinâmicas e não possuem modelo ORM fixo.
      Elas são acessadas via queries SQL diretas.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Base para todos os modelos
Base = declarative_base()


class Usina(Base):
    """
    Modelo para a tabela power_station (usinas de geração de energia).
    
    Atributos:
        id (int): Identificador único da usina
        nome (str): Nome completo da usina
        capacidade (float): Capacidade de geração em kW
        status (int): Status da usina (1=ativa, 0=inativa)
        customer_id (int): ID do cliente proprietário
    """
    __tablename__ = "power_station"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    capacity = Column(Float)

    customer_id = Column(Integer)
    
    # Relacionamentos
    equipamentos = relationship("Equipamento", back_populates="usina")
    skids = relationship("Skid", back_populates="usina")
    
    def __repr__(self):
        return f"<Usina(id={self.id}, nome='{self.name}')>"


class Skid(Base):
    """
    Modelo para a tabela skid (agrupamentos de equipamentos).
    
    Atributos:
        id (int): Identificador único do skid
        nome (str): Nome do skid
        usina_id (int): ID da usina que contém este skid
    """
    __tablename__ = "skid"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    power_station_id = Column(Integer, ForeignKey("power_station.id"))
    
    # Relacionamentos
    usina = relationship("Usina", back_populates="skids")
    equipamentos = relationship("Equipamento", back_populates="skid")
    
    def __repr__(self):
        return f"<Skid(id={self.id}, nome='{self.name}')>"


class Equipamento(Base):
    """
    Modelo para a tabela equipment (equipamentos da usina).
    
    Atributos:
        id (int): Identificador único do equipamento
        nome (str): Nome do equipamento
        tipo (str): Tipo do equipamento (inversor, relé, etc)
        skid_id (int): ID do skid que contém este equipamento
        usina_id (int): ID da usina
        status (int): Status do equipamento (1=ativo, 0=inativo)
    """
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    equipment_class_id = Column(Integer)
    skid_id = Column(Integer, ForeignKey("skid.id"))
    power_station_id = Column(Integer, ForeignKey("power_station.id"))
    
    # Relacionamentos
    usina = relationship("Usina", back_populates="equipamentos")
    skid = relationship("Skid", back_populates="equipamentos")
    teleobjetos = relationship("Teleobjeto", back_populates="equipamento")
    
    def __repr__(self):
        return f"<Equipamento(id={self.id}, nome='{self.name}')>"


class TeleobjetoConfig(Base):
    """
    Modelo para a tabela tele_object_config (configurações de teleobjetos).
    
    Atributos:
        id (int): Identificador único da configuração
        nome (str): Nome do teleobjeto
        tele_object_type_id (int): Tipo do teleobjeto
        alarm_severity_id (int): Severidade padrão para alarmes deste teleobjeto
    """
    __tablename__ = "tele_object_config"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    tele_object_type_id = Column(Integer)
    alarm_severity_id = Column(Integer, ForeignKey("alarm_severity.id"))
    
    # Relacionamentos
    teleobjetos = relationship("Teleobjeto", back_populates="configuracao")
    
    def __repr__(self):
        return f"<TeleobjetoConfig(id={self.id}, nome='{self.name}')>"


class Teleobjeto(Base):
    """
    Modelo para a tabela tele_object (pontos de monitoramento).
    
    Atributos:
        id (int): Identificador único do teleobjeto
        equipamento_id (int): ID do equipamento que contém este teleobjeto
        tele_object_config_id (int): ID da configuração do teleobjeto
        status (int): Status do teleobjeto (1=ativo, 0=inativo)
    """
    __tablename__ = "tele_object"
    
    id = Column(Integer, primary_key=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    tele_object_config_id = Column(Integer, ForeignKey("tele_object_config.id"))
    
    # Relacionamentos
    equipamento = relationship("Equipamento", back_populates="teleobjetos")
    configuracao = relationship("TeleobjetoConfig", back_populates="teleobjetos")
    
    def __repr__(self):
        return f"<Teleobjeto(id={self.id})>"


class Severidade(Base):
    """
    Modelo para a tabela alarm_severity (níveis de severidade de alarmes).
    
    Atributos:
        id (int): Identificador único da severidade
        nome (str): Nome da severidade (Crítica, Alta, Média, Baixa, etc)
        cor (str): Cor em hexadecimal para visualização (#FF0000, etc)
        nivel (int): Nível numérico (1=mais grave, 5=menos grave)
    """
    __tablename__ = "alarm_severity"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    color = Column(String)
    level = Column(Integer)
    
    def __repr__(self):
        return f"<Severidade(id={self.id}, nome='{self.name}', nivel={self.level})>"


class Usuario(Base):
    """
    Modelo para a tabela users (usuários do sistema).
    
    Atributos:
        id (int): Identificador único do usuário
        nome (str): Nome completo do usuário
        username (str): Nome de usuário para login
        email (str): Email do usuário
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column("name", String, nullable=False)
    username = Column(String)
    email = Column(String)
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, nome='{self.name}')>"
