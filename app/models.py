# from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from config import main_dir, ip_address

# Connexio amb la BD
engine = create_engine(f'sqlite:////{main_dir}/lots.db', connect_args={'check_same_thread': False})
IP_HOME = f'{ip_address}:5000/'


Base = declarative_base()
Session1 = sessionmaker(engine)
session1 = Session1()

# Definicio del Models/taules de la BD, Cada classe es una taula de la BD i els seus atributs son les columnes


class Lots(Base):
    __tablename__ = 'lots'

    id = Column(Integer(), primary_key=True)
    type_lot = Column(String())
    lot_name = Column(String())
    reference = Column(String())
    trademark = Column(String())
    preserved_in = Column(String())
    stock_minimum = Column(String())
    date_arrived = Column(String())
    supplier_lot = Column(String())
    expiry = Column(String())
    internal_lot = Column(String())
    tecnic = Column(String())
    data_open = Column(String())
    tecnic_open = Column(String())
    data_close = Column(String())
    tecnic_close = Column(String())
    observations = Column(String())


class Logs(Base):
    __tablename__ = 'logs'

    id = Column(Integer(), primary_key=True)
    field = Column(String())
    old_info = Column(String())
    new_info = Column(String())
    reason_change = Column(String())
    user = Column(String())
    id_user = Column(String())
    date = Column(String())
