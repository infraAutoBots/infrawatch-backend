import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base



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

    def __init__(self, name, email, password, state, last_login, access_level):
        self.name = name
        self.email = email
        self.password = password
        self.state = state
        self.last_login = last_login
        self.access_level = access_level


class Devices(Base):
    __tablename__ = 'devices'

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

    def __init__(self, ip, interval, version, community, port, user, authKey, privKey, id_user):
        self.ip = ip
        self.interval = interval
        self.version = version
        self.community = community
        self.port = port
        self.user = user
        self.authKey = authKey
        self.privKey = privKey
        self.id_user = id_user


class DeviceData(Base):
    __tablename__ = 'device_data'

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    id_device = Column("id_device", Integer, ForeignKey('devices.id'))
    status = Column("status", Boolean)
    sys_descr = Column("sys_descr", Text)
    cpu = Column("cpu", String)
    disk = Column("disk", String)
    uptime = Column("uptime", String)
    storage = Column("storage", String)
    last_updated = Column("last_updated", DateTime)

    def __init__(self, id_device, status, sys_descr, cpu, disk, uptime, storage, last_updated):
        self.id_device = id_device
        self.status = status
        self.sys_descr = sys_descr
        self.cpu = cpu
        self.disk = disk
        self.uptime = uptime
        self.storage = storage
        self.last_updated = last_updated

# executar a criacao dos metadados do banco de dados
# alembic init alembic

# gerar bd
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head 