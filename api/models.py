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
    created_at = Column("created_at", DateTime, default=func.now())
    updated_at = Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, name, email, password, state, last_login, access_level):
        self.name = name
        self.email = email
        self.password = password
        self.state = state
        self.last_login = last_login
        self.access_level = access_level
        self.created_at = func.now()
        self.updated_at = func.now()


class EndPoints(Base):
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
    webhook = Column("webhook", String)
    id_user = Column("id_usuario", Integer, ForeignKey('users.id'))
    end_points_data = relationship("EndPointsData", cascade="all, delete")
    end_points_oids = relationship("EndPointOIDs", cascade="all, delete")

    def __init__(self, ip, interval, version, community, port, user, authKey, privKey, webhook, id_user):
        self.ip = ip
        self.interval = interval
        self.version = version
        self.community = community
        self.port = port
        self.user = user
        self.authKey = authKey
        self.privKey = privKey
        self.webhook = webhook
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

# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head 
