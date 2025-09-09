import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from enum import Enum
from dotenv import load_dotenv

# Detectar ambiente e carregar configurações apropriadas
def load_environment_config():
    """Carrega as configurações de ambiente apropriadas"""
    
    # Detectar se estamos no Railway
    is_railway = (
        os.getenv("RAILWAY_ENVIRONMENT") is not None or 
        os.getenv("RAILWAY_PROJECT_ID") is not None or
        os.getenv("PORT") is not None
    )
    
    if is_railway:
        print("🚂 Ambiente Railway detectado - carregando .env")
        load_dotenv()  # Carrega .env padrão (Railway)
    else:
        print("🏠 Ambiente local detectado - carregando .env.local")
        # Tenta carregar .env.local primeiro, depois .env como fallback
        if os.path.exists('.env.local'):
            load_dotenv('.env.local')
            print("✅ Configurações locais carregadas de .env.local")
        else:
            load_dotenv()
            print("⚠️ .env.local não encontrado, usando .env padrão")

# Carregar configurações de ambiente
load_environment_config()

# Configuração dinâmica do banco
def get_database_url():
    """Retorna a URL do banco de dados baseada nas variáveis de ambiente"""
    
    # Detectar se estamos no Railway (verifica várias variáveis específicas do Railway)
    is_railway = (
        os.getenv("RAILWAY_ENVIRONMENT") is not None or 
        os.getenv("RAILWAY_PROJECT_ID") is not None or
        os.getenv("PORT") is not None  # Railway sempre define PORT
    )
    
    # Priorizar PostgreSQL se configurado
    postgres_url = os.getenv("DATABASE_URL")
    if postgres_url and ("postgresql" in postgres_url or "postgres" in postgres_url):
        if is_railway:
            print(f"🚂 Rodando no Railway - PostgreSQL: {postgres_url[:50]}...")
            return postgres_url
        else:
            # Local: verificar se é conexão Railway (postgres.railway.internal)
            if "railway.internal" in postgres_url:
                print("🏠 Ambiente local detectado, mas DATABASE_URL aponta para Railway")
                print("� Usando SQLite local como fallback...")
                # Fallback para SQLite local
                filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database.db'))
                return f'sqlite:///{filename}'
            else:
                print(f"🏠 Local - PostgreSQL: {postgres_url[:50]}...")
                return postgres_url
    
    # Fallback para SQLite baseado em variável específica
    sqlite_url = os.getenv("SQLITE_DATABASE_URL")
    if sqlite_url:
        if sqlite_url.startswith("sqlite:///"):
            print(f"📄 Usando SQLite (env): {sqlite_url}")
            return sqlite_url
        else:
            filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', sqlite_url.replace('sqlite:///', '')))
            return f'sqlite:///{filename}'
    
    # Fallback padrão para SQLite
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database.db'))
    print(f"📄 Usando SQLite padrão: {filename}")
    return f'sqlite:///{filename}'

# criar a conexao no banco
db = create_engine(get_database_url(), echo=False)


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
    active = Column("active", Boolean, default=True)
    authKey = Column("authKey", String)
    privKey = Column("privKey", String)
    id_user = Column("id_usuario", Integer, ForeignKey('users.id'))
    end_points_data = relationship("EndPointsData", cascade="all, delete")
    end_points_oids = relationship("EndPointOIDs", cascade="all, delete")

    def __init__(self, ip, nickname, interval, version, community, port, user, active, authKey, privKey, id_user):
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
            active (bool): Se o endpoint está ativo.
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
        self.active = active
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
    hrStorageDescr = Column("hrStorageDescr", String)
    ifOperStatus = Column("ifOperStatus", String)
    ifInOctets = Column("ifInOctets", String)
    ifOutOctets = Column("ifOutOctets", String)
    ping_rtt = Column("ping_rtt", String)  # Tempo de resposta PING em ms
    snmp_rtt = Column("snmp_rtt", String)  # Tempo de resposta SNMP em ms
    last_updated = Column("last_updated", DateTime)
    # resposta

    def __init__(self, id_end_point, status, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, hrStorageDescr, ifOperStatus, ifInOctets, ifOutOctets, ping_rtt, snmp_rtt, last_updated):
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
            hrStorageDescr (str): Descrição do armazenamento.
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
        self.hrStorageDescr = hrStorageDescr
        self.ifOperStatus = ifOperStatus
        self.ifInOctets = ifInOctets
        self.ifOutOctets = ifOutOctets
        self.ping_rtt = ping_rtt
        self.snmp_rtt = snmp_rtt
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
    hrStorageDescr = Column("hrStorageDescr", String)
    ifOperStatus = Column("ifOperStatus", String)
    ifInOctets = Column("ifInOctets", String)
    ifOutOctets = Column("ifOutOctets", String)

    def __init__(self, id_end_point, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, hrStorageDescr, ifOperStatus, ifInOctets, ifOutOctets):
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
            hrStorageDescr (str): Descrição do armazenamento.
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
        self.hrStorageDescr = hrStorageDescr
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


class SLAMetrics(Base):
    """
    Modelo ORM para métricas de SLA agregadas.
    Armazena dados de disponibilidade, MTTR, MTBF e compliance de SLA por endpoint.
    """
    __tablename__ = 'sla_metrics'
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column("endpoint_id", Integer, ForeignKey("endpoints.id"), nullable=False)
    timestamp = Column("timestamp", DateTime, default=func.now(), nullable=False)
    
    # Métricas de Disponibilidade
    availability_percentage = Column("availability_percentage", Float, nullable=False)
    uptime_seconds = Column("uptime_seconds", Integer, default=0)
    downtime_seconds = Column("downtime_seconds", Integer, default=0)
    
    # Métricas de Qualidade de Serviço
    mttr_minutes = Column("mttr_minutes", Float, nullable=True)  # Mean Time To Recovery
    mtbf_hours = Column("mtbf_hours", Float, nullable=True)  # Mean Time Between Failures
    incidents_count = Column("incidents_count", Integer, default=0)
    
    # SLA Compliance
    sla_target = Column("sla_target", Float, default=99.9)  # Target SLA em %
    sla_compliance = Column("sla_compliance", Boolean, nullable=False)
    sla_breach_minutes = Column("sla_breach_minutes", Float, default=0.0)
    
    # Métricas de Performance
    avg_response_time = Column("avg_response_time", Float, nullable=True)  # ms
    max_response_time = Column("max_response_time", Float, nullable=True)  # ms
    min_response_time = Column("min_response_time", Float, nullable=True)  # ms
    
    # Período de medição
    measurement_period_hours = Column("measurement_period_hours", Integer, default=24)
    
    # Relacionamentos
    endpoint = relationship("EndPoints", backref="sla_metrics")
    
    def __init__(self, endpoint_id, availability_percentage, uptime_seconds=0, 
                 downtime_seconds=0, sla_target=99.9, incidents_count=0):
        """
        Inicializa uma nova métrica de SLA.
        Args:
            endpoint_id (int): ID do endpoint.
            availability_percentage (float): Percentual de disponibilidade.
            uptime_seconds (int): Tempo online em segundos.
            downtime_seconds (int): Tempo offline em segundos.
            sla_target (float): Meta de SLA em porcentagem.
            incidents_count (int): Número de incidentes no período.
        """
        self.endpoint_id = endpoint_id
        self.availability_percentage = availability_percentage
        self.uptime_seconds = uptime_seconds
        self.downtime_seconds = downtime_seconds
        self.sla_target = sla_target
        self.sla_compliance = availability_percentage >= sla_target
        self.incidents_count = incidents_count


class IncidentTracking(Base):
    """
    Modelo ORM para rastreamento estruturado de incidentes.
    Registra início, fim, duração e detalhes de cada incidente.
    """
    __tablename__ = 'incidents'
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column("endpoint_id", Integer, ForeignKey("endpoints.id"), nullable=False)
    alert_id = Column("alert_id", Integer, ForeignKey("alerts.id"), nullable=True)
    
    # Dados do Incidente
    incident_type = Column("incident_type", String(50), nullable=False)  # ping_down, snmp_down, performance
    severity = Column("severity", String(50), default="medium")
    status = Column("status", String(50), default="open")  # open, investigating, resolved, closed
    
    # Tempos
    start_time = Column("start_time", DateTime, default=func.now(), nullable=False)
    end_time = Column("end_time", DateTime, nullable=True)
    duration_seconds = Column("duration_seconds", Integer, nullable=True)
    
    # Detalhes
    root_cause = Column("root_cause", Text, nullable=True)
    impact_description = Column("impact_description", Text, nullable=True)
    resolution_notes = Column("resolution_notes", Text, nullable=True)
    
    # Responsáveis
    detected_by = Column("detected_by", String(100), default="automated_monitoring")
    resolved_by = Column("resolved_by", Integer, ForeignKey("users.id"), nullable=True)
    
    # Métricas do Incidente
    response_time_minutes = Column("response_time_minutes", Float, nullable=True)  # Tempo até resposta
    resolution_time_minutes = Column("resolution_time_minutes", Float, nullable=True)  # Tempo até resolução
    
    # Relacionamentos
    endpoint = relationship("EndPoints", backref="incidents")
    alert = relationship("Alerts", backref="incident")
    resolver = relationship("Users", backref="resolved_incidents")
    
    def __init__(self, endpoint_id, incident_type, severity="medium", 
                 impact_description=None, alert_id=None):
        """
        Inicializa um novo incidente.
        Args:
            endpoint_id (int): ID do endpoint afetado.
            incident_type (str): Tipo do incidente.
            severity (str): Severidade do incidente.
            impact_description (str): Descrição do impacto.
            alert_id (int): ID do alerta relacionado.
        """
        self.endpoint_id = endpoint_id
        self.incident_type = incident_type
        self.severity = severity
        self.impact_description = impact_description
        self.alert_id = alert_id
    
    def close_incident(self, resolved_by_user_id=None, resolution_notes=None):
        """
        Fecha o incidente calculando duração e métricas.
        Args:
            resolved_by_user_id (int): ID do usuário que resolveu.
            resolution_notes (str): Notas da resolução.
        """
        from datetime import datetime
        self.end_time = datetime.now()
        self.status = "resolved"
        self.resolved_by = resolved_by_user_id
        self.resolution_notes = resolution_notes
        
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
            self.resolution_time_minutes = delta.total_seconds() / 60


class PerformanceMetrics(Base):
    """
    Modelo ORM para métricas de performance agregadas.
    Armazena percentis e estatísticas de performance por endpoint.
    """
    __tablename__ = 'performance_metrics'
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column("endpoint_id", Integer, ForeignKey("endpoints.id"), nullable=False)
    timestamp = Column("timestamp", DateTime, default=func.now(), nullable=False)
    
    # Métricas de Tempo de Resposta (em ms)
    response_time_p50 = Column("response_time_p50", Float, nullable=True)  # Mediana
    response_time_p90 = Column("response_time_p90", Float, nullable=True)
    response_time_p95 = Column("response_time_p95", Float, nullable=True)
    response_time_p99 = Column("response_time_p99", Float, nullable=True)
    response_time_p99_9 = Column("response_time_p99_9", Float, nullable=True)
    response_time_avg = Column("response_time_avg", Float, nullable=True)
    response_time_max = Column("response_time_max", Float, nullable=True)
    response_time_min = Column("response_time_min", Float, nullable=True)
    
    # Métricas de Taxa de Erro
    error_rate_percentage = Column("error_rate_percentage", Float, default=0.0)
    total_requests = Column("total_requests", Integer, default=0)
    failed_requests = Column("failed_requests", Integer, default=0)
    
    # Métricas de Throughput
    requests_per_second = Column("requests_per_second", Float, nullable=True)
    throughput_mbps = Column("throughput_mbps", Float, nullable=True)
    
    # Métricas de Qualidade
    jitter_ms = Column("jitter_ms", Float, nullable=True)  # Variação no tempo de resposta
    packet_loss_rate = Column("packet_loss_rate", Float, default=0.0)
    
    # Período da medição
    measurement_period_minutes = Column("measurement_period_minutes", Integer, default=60)
    sample_count = Column("sample_count", Integer, default=0)
    
    # Relacionamentos
    endpoint = relationship("EndPoints", backref="performance_metrics")
    
    def __init__(self, endpoint_id, response_time_avg=None, error_rate_percentage=0.0,
                 total_requests=0, measurement_period_minutes=60):
        """
        Inicializa uma nova métrica de performance.
        Args:
            endpoint_id (int): ID do endpoint.
            response_time_avg (float): Tempo médio de resposta em ms.
            error_rate_percentage (float): Taxa de erro em %.
            total_requests (int): Total de requisições no período.
            measurement_period_minutes (int): Período de medição em minutos.
        """
        self.endpoint_id = endpoint_id
        self.response_time_avg = response_time_avg
        self.error_rate_percentage = error_rate_percentage
        self.total_requests = total_requests
        self.failed_requests = int((error_rate_percentage / 100.0) * total_requests)
        self.measurement_period_minutes = measurement_period_minutes


# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head 

