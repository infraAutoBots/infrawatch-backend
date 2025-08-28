import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func



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
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, name, email, password, state, last_login, access_level, url):
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

    def __init__(self, ip, interval, version, community, port, user, authKey, privKey, id_user):
        """
        Inicializa um novo endpoint monitorado.
        Args:
            ip (str): Endereço IP ou domínio.
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
    last_updated = Column("last_updated", DateTime)
    # resposta

    def __init__(self, id_end_point, status, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed, last_updated):
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

    def __init__(self, id_end_point, sysDescr, sysName, sysUpTime, hrProcessorLoad, memTotalReal, memAvailReal, hrStorageSize, hrStorageUsed):
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

# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head 
