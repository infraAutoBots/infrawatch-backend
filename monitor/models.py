import os
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (create_engine, Column, Integer, String, Boolean,
                        Text, DateTime, ForeignKey)



# criar a conexao no banco
filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database.db'))
db = create_engine(f'sqlite:///{filename}')


# criar a base do banco de dados
Base = declarative_base()


class EndPoints(Base):
    """
    Modelo ORM para a tabela de endpoints monitorados.
    Representa um dispositivo ou serviço monitorado pelo sistema.
    """
    __tablename__ = 'endpoints'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    ip = Column("ip", String)
    nickname = Column("nickname", String)
    interval = Column("interval", Integer, default=30)
    version = Column("version", String)
    community = Column("community", String)
    port = Column("port", Integer)
    user = Column("user", String)
    authKey = Column("authKey", String)
    privKey = Column("privKey", String)
    id_user = Column("id_usuario", Integer, ForeignKey('users.id'))
    end_points_data = relationship("EndPointsData", cascade="all, delete")
    end_points_oids = relationship("EndPointOIDs", cascade="all, delete")

    def __init__(self, ip, nickname, interval, version, community, port, user, authKey, privKey, id_user):
        """
        Inicializa um novo endpoint monitorado.
        Args:
            ip (str): Endereço IP ou domínio.
            nickname (str): Apelido do endpoint.
            interval (int): Intervalo de coleta.
            version (str): Versão SNMP.
            community (str): Comunidade SNMP.
            port (int): Porta SNMP.
            user (str): Usuário SNMPv3.
            authKey (str): Chave de autenticação SNMPv3.
            privKey (str): Chave privada SNMPv3.
            id_user (int): ID do usuário proprietário.
        """
        self.ip = ip
        self.nickname = nickname
        self.interval = interval
        self.version = version
        self.community = community
        self.port = port
        self.user = user
        self.authKey = authKey
        self.privKey = privKey
        self.id_user = id_user


class EndPointsData(Base):
    __tablename__ = 'endpoints_data'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    id_end_point = Column("id_end_point", Integer, ForeignKey('endpoints.id'))
    status = Column("status", Boolean)
    sysDescr = Column("sysDescr", Text)
    sysName = Column("sysName", String)
    sysUpTime = Column("sysUpTime", String)
    hrProcessorLoad = Column("hrProcessorLoad", String)
    memTotalReal = Column("memTotalReal", String)
    memAvailReal = Column("memAvailReal", String)
    hrStorageSize = Column("hrStorageSize", String)
    hrStorageUsed = Column("hrStorageUsed", String)
    last_updated = Column("last_updated", DateTime)
    # resposta

    def __init__(self, id_end_point, status, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, last_updated):
        self.id_end_point = id_end_point
        self.status = status
        self.sysDescr = sysDescr
        self.sysName = sysName
        self.sysUpTime = sysUpTime
        self.hrProcessorLoad = hrProcessorLoad
        self.memTotalReal = memTotalReal
        self.memAvailReal = memAvailReal
        self.hrStorageSize = hrStorageSize
        self.hrStorageUsed = hrStorageUsed
        self.last_updated = last_updated


class EndPointOIDs(Base):
    __tablename__ = 'endpoints_oids'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    id_end_point = Column("id_end_point", Integer, ForeignKey('endpoints.id'))
    sysDescr = Column("sysDescr", Text)
    sysName = Column("sysName", String)
    sysUpTime = Column("sysUpTime", String)
    hrProcessorLoad = Column("hrProcessorLoad", String)
    memTotalReal = Column("memTotalReal", String)
    memAvailReal = Column("memAvailReal", String)
    hrStorageSize = Column("hrStorageSize", String)
    hrStorageUsed = Column("hrStorageUsed", String)

    def __init__(self, id_end_point, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed):
        self.id_end_point = id_end_point
        self.sysDescr = sysDescr
        self.sysName = sysName
        self.sysUpTime = sysUpTime
        self.hrProcessorLoad = hrProcessorLoad
        self.memTotalReal = memTotalReal
        self.memAvailReal = memAvailReal
        self.hrStorageSize = hrStorageSize
        self.hrStorageUsed = hrStorageUsed


class Alerts(Base):
    """
    Modelo ORM para a tabela de alertas do sistema.
    Representa alertas gerados pelo sistema de monitoramento.
    """
    __tablename__ = 'alerts'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    title = Column("title", String(255), nullable=False)
    description = Column("description", Text, nullable=True)
    severity = Column("severity", String(50), nullable=False)
    status = Column("status", String(50), nullable=False, default="active")
    category = Column("category", String(50), nullable=False)
    impact = Column("impact", String(50), nullable=False, default="medium")
    system = Column("system", String(255), nullable=False)
    assignee = Column("assignee", String(255), nullable=True)
    
    # Relacionamentos
    id_endpoint = Column("id_endpoint", Integer, ForeignKey('endpoints.id'), nullable=True)
    id_user_created = Column("id_user_created", Integer, ForeignKey('users.id'), nullable=False)
    id_user_assigned = Column("id_user_assigned", Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column("created_at", DateTime, nullable=False)
    updated_at = Column("updated_at", DateTime, nullable=False)
    acknowledged_at = Column("acknowledged_at", DateTime, nullable=True)
    resolved_at = Column("resolved_at", DateTime, nullable=True)

    def __init__(self, title, description, severity, category, system, impact="medium", 
                 id_endpoint=None, id_user_created=None, assignee=None):
        from datetime import datetime
        self.title = title
        self.description = description
        self.severity = severity
        self.category = category
        self.system = system
        self.impact = impact
        self.id_endpoint = id_endpoint
        self.id_user_created = id_user_created
        self.assignee = assignee
        self.status = "active"
        now = datetime.now()
        self.created_at = now
        self.updated_at = now


class AlertLogs(Base):
    """
    Modelo ORM para logs/histórico de ações nos alertas.
    """
    __tablename__ = 'alert_logs'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    id_alert = Column("id_alert", Integer, ForeignKey('alerts.id'), nullable=False)
    id_user = Column("id_user", Integer, ForeignKey('users.id'), nullable=False)
    action = Column("action", String(100), nullable=False)
    comment = Column("comment", Text, nullable=True)
    created_at = Column("created_at", DateTime, nullable=False)

    def __init__(self, id_alert, id_user, action, comment=None):
        from datetime import datetime
        self.id_alert = id_alert
        self.id_user = id_user
        self.action = action
        self.comment = comment
        self.created_at = datetime.now()


# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head
