import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from enum import Enum



# criar a conexao no banco
filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database.db'))
db = create_engine(f'sqlite:///{filename}')


# criar a base do banco de dados
Base = declarative_base()


#criar classes/tabela do seu banco de dados
class Users(Base):
    """
    Modelo ORM para a tabela de usuários do sistema.
    Representa um usuário com informações de autenticação, estado e permissões.
    """
    __tablename__ = 'users'

    # ACCESS_LEVEL = (
    #     ("ADMIN", 'ADMIN'),
    #     ("MONITOR", 'MONITOR'),
    #     ("VIEWER", 'VIEWER'),
    # )

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String)
    email = Column("email", String)
    password = Column("password", String)
    state = Column("state", Boolean)
    last_login = Column("last_login", DateTime)
    access_level = Column("access_level", String) # ChoiceType(choices=ACCESS_LEVEL)
    url = Column("url", String)
    alert = Column("alert", Boolean, default=True)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, name, email, password, state, last_login, access_level, url, alert=True):
        """
        Inicializa um novo usuário.
        Args:
            name (str): Nome do usuário.
            email (str): Email do usuário.
            password (str): Senha criptografada.
            state (bool): Estado ativo/inativo.
            last_login (datetime): Último login.
            access_level (str): Nível de acesso (ADMIN, MONITOR, VIEWER).
            url (str): URL do usuário.
        """
        self.name = name
        self.email = email
        self.password = password
        self.state = state
        self.last_login = last_login
        self.access_level = access_level
        self.url = url
        self.alert = alert
        self.created_at = func.now()
        self.updated_at = func.now()


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
    """
    Modelo ORM para os dados coletados dos endpoints.
    Armazena informações de status e métricas coletadas.
    """
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
    ifOperStatus = Column("ifOperStatus", String)
    ifInOctets = Column("ifInOctets", String)
    ifOutOctets = Column("ifOutOctets", String)
    last_updated = Column("last_updated", DateTime)
    # resposta

    def __init__(self, id_end_point, status, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, ifOperStatus, ifInOctets, ifOutOctets, last_updated):
        """
        Inicializa um novo registro de dados coletados de endpoint.
        Args:
            id_end_point (int): ID do endpoint.
            status (bool): Status do endpoint.
            sysDescr (str): Descrição do sistema.
            sysName (str): Nome do sistema.
            sysUpTime (str): Tempo de atividade.
            hrProcessorLoad (str): Carga do processador.
            memTotalReal (str): Memória total.
            memAvailReal (str): Memória disponível.
            hrStorageSize (str): Tamanho do armazenamento.
            hrStorageUsed (str): Armazenamento usado.
            ifOperStatus (str): Status operacional das interfaces.
            ifInOctets (str): Tráfego recebido das interfaces.
            ifOutOctets (str): Tráfego transmitido das interfaces.
            last_updated (datetime): Data da última atualização.
        """
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
        self.ifOperStatus = ifOperStatus
        self.ifInOctets = ifInOctets
        self.ifOutOctets = ifOutOctets
        self.last_updated = last_updated


class EndPointOIDs(Base):
    """
    Modelo ORM para os OIDs monitorados de cada endpoint.
    Armazena os identificadores SNMP de interesse para cada endpoint.
    """
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
    ifOperStatus = Column("ifOperStatus", String)
    ifInOctets = Column("ifInOctets", String)
    ifOutOctets = Column("ifOutOctets", String)

    def __init__(self, id_end_point, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, ifOperStatus, ifInOctets, ifOutOctets):
        """
        Inicializa um novo conjunto de OIDs para um endpoint.
        Args:
            id_end_point (int): ID do endpoint.
            sysDescr (str): Descrição do sistema.
            sysName (str): Nome do sistema.
            sysUpTime (str): Tempo de atividade.
            hrProcessorLoad (str): Carga do processador.
            memTotalReal (str): Memória total.
            memAvailReal (str): Memória disponível.
            hrStorageSize (str): Tamanho do armazenamento.
            hrStorageUsed (str): Armazenamento usado.
            ifOperStatus (str): Status operacional das interfaces.
            ifInOctets (str): Tráfego recebido das interfaces.
            ifOutOctets (str): Tráfego transmitido das interfaces.
        """
        self.id_end_point = id_end_point
        self.sysDescr = sysDescr
        self.sysName = sysName
        self.sysUpTime = sysUpTime
        self.hrProcessorLoad = hrProcessorLoad
        self.memTotalReal = memTotalReal
        self.memAvailReal = memAvailReal
        self.hrStorageSize = hrStorageSize
        self.hrStorageUsed = hrStorageUsed
        self.ifOperStatus = ifOperStatus
        self.ifInOctets = ifInOctets
        self.ifOutOctets = ifOutOctets


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class AlertCategory(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NETWORK = "network"

class AlertImpact(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Alerts(Base):
    """
    Modelo ORM para a tabela de alertas do sistema.
    Representa alertas gerados pelo sistema de monitoramento.
    """
    __tablename__ = 'alerts'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    title = Column("title", String(255), nullable=False)
    description = Column("description", Text, nullable=True)
    severity = Column("severity", String(50), nullable=False)  # critical, high, medium, low
    status = Column("status", String(50), nullable=False, default="active")  # active, acknowledged, resolved
    category = Column("category", String(50), nullable=False)  # infrastructure, security, performance, network
    impact = Column("impact", String(50), nullable=False, default="medium")  # high, medium, low
    system = Column("system", String(255), nullable=False)  # Sistema/endpoint que gerou o alerta
    assignee = Column("assignee", String(255), nullable=True)  # Responsável pelo alerta
    
    # Relacionamentos
    id_endpoint = Column("id_endpoint", Integer, ForeignKey('endpoints.id'), nullable=True)
    id_user_created = Column("id_user_created", Integer, ForeignKey('users.id'), nullable=False)
    id_user_assigned = Column("id_user_assigned", Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column("created_at", DateTime, default=func.now(), nullable=False)
    updated_at = Column("updated_at", DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), nullable=False)
    acknowledged_at = Column("acknowledged_at", DateTime, nullable=True)
    resolved_at = Column("resolved_at", DateTime, nullable=True)
     
    # Relacionamentos ORM
    endpoint = relationship("EndPoints", backref="alerts")
    user_created = relationship("Users", foreign_keys=[id_user_created], backref="created_alerts")
    user_assigned = relationship("Users", foreign_keys=[id_user_assigned], backref="assigned_alerts")
    alert_logs = relationship("AlertLogs", cascade="all, delete-orphan", backref="alert")

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
        self.status = "active"  # Define status padrão
        # Inicializar timestamps explicitamente com datetime atual
        now = datetime.now()
        self.created_at = now
        self.updated_at = now

    @property
    def duration(self):
        """Calcula a duração do alerta desde a criação"""
        from datetime import datetime
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
        else:
            delta = datetime.utcnow() - self.created_at
        
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"


class AlertLogs(Base):
    """
    Modelo ORM para logs/histórico de ações nos alertas.
    """
    __tablename__ = 'alert_logs'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    id_alert = Column("id_alert", Integer, ForeignKey('alerts.id'), nullable=False)
    id_user = Column("id_user", Integer, ForeignKey('users.id'), nullable=False)
    action = Column("action", String(100), nullable=False)  # created, acknowledged, resolved, assigned, commented
    comment = Column("comment", Text, nullable=True)
    created_at = Column("created_at", DateTime, default=func.now(), nullable=False)

    # Relacionamentos ORM
    user = relationship("Users", backref="alert_actions")

    def __init__(self, id_alert, id_user, action, comment=None):
        self.id_alert = id_alert
        self.id_user = id_user
        self.action = action
        self.comment = comment


class AlertRules(Base):
    """
    Modelo ORM para regras de geração automática de alertas.
    """
    __tablename__ = 'alert_rules'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(255), nullable=False)
    description = Column("description", Text, nullable=True)
    condition = Column("condition", Text, nullable=False)  # JSON com condições
    severity = Column("severity", String(50), nullable=False)
    category = Column("category", String(50), nullable=False)
    is_active = Column("is_active", Boolean, default=True)
    id_user_created = Column("id_user_created", Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    user_created = relationship("Users", backref="alert_rules")

    def __init__(self, name, description, condition, severity, category, id_user_created):
        self.name = name
        self.description = description
        self.condition = condition
        self.severity = severity
        self.category = category
        self.id_user_created = id_user_created


class WebHookConfig(Base):
    """
    Modelo ORM para configuração de webhooks.
    Representa um webhook configurado para receber notificações.
    """
    __tablename__ = 'webhook_config'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    url = Column("url", String, nullable=False)
    active = Column("active", Boolean, default=True)
    timeout = Column("timeout", Integer, default=30)
    access_token = Column("access_token", String, nullable=True)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, url, active=True, timeout=30, access_token=None):
        """
        Inicializa uma nova configuração de webhook.
        Args:
            url (str): URL do webhook.
            active (bool): Se o webhook está ativo.
        """
        self.url = url
        self.active = active
        self.timeout = timeout
        self.access_token = access_token


class EmailConfig(Base):
    """
    Modelo ORM para configuração de email.
    Representa as configurações SMTP para envio de emails.
    """
    __tablename__ = 'email_config'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    email = Column("email", String, nullable=False)
    password = Column("password", String, nullable=False)
    port = Column("port", Integer, nullable=False)
    server = Column("server", String, nullable=False)
    active = Column("active", Boolean, default=True)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, email, password, port, server, active=True):
        """
        Inicializa uma nova configuração de email.
        Args:
            email (str): Email remetente.
            password (str): Senha do email.
            port (int): Porta SMTP.
            server (str): Servidor SMTP.
            active (bool): Se a configuração está ativa.
        """
        self.email = email
        self.password = password
        self.port = port
        self.server = server
        self.active = active


class FailureThresholdConfig(Base):
    """
    Modelo ORM para configuração de limites de falhas consecutivas.
    Representa os limites para SNMP e ping antes de disparar alertas.
    """
    __tablename__ = 'failure_threshold_config'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    consecutive_snmp_failures = Column("consecutive_snmp_failures", Integer, default=3)
    consecutive_ping_failures = Column("consecutive_ping_failures", Integer, default=5)
    active = Column("active", Boolean, default=True)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, consecutive_snmp_failures=3, consecutive_ping_failures=5, active=True):
        """
        Inicializa uma nova configuração de limites de falhas.
        Args:
            consecutive_snmp_failures (int): Limite de falhas SNMP consecutivas.
            consecutive_ping_failures (int): Limite de falhas de ping consecutivas.
            active (bool): Se a configuração está ativa.
        """
        self.consecutive_snmp_failures = consecutive_snmp_failures
        self.consecutive_ping_failures = consecutive_ping_failures
        self.active = active


class PerformanceThresholds(Base):
    """
    Modelo ORM para configuração de limites de performance.
    Representa os limites para CPU, Memória, Disco e Rede antes de disparar alertas.
    """
    __tablename__ = 'performance_thresholds'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    metric_type = Column("metric_type", String(50), nullable=False)  # cpu, memory, storage, network
    warning_threshold = Column("warning_threshold", Integer, nullable=False)  # 80
    critical_threshold = Column("critical_threshold", Integer, nullable=False)  # 90
    enabled = Column("enabled", Boolean, default=True)
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, metric_type, warning_threshold, critical_threshold, enabled=True):
        """
        Inicializa uma nova configuração de limites de performance.
        Args:
            metric_type (str): Tipo de métrica (cpu, memory, storage, network).
            warning_threshold (int): Limite de aviso em porcentagem.
            critical_threshold (int): Limite crítico em porcentagem.
            enabled (bool): Se a configuração está ativa.
        """
        self.metric_type = metric_type
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.enabled = enabled


# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head 

