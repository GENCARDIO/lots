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

    key = Column(Integer(), primary_key=True)
    catalog_reference = Column(String())
    manufacturer = Column(String())
    description = Column(String())
    analytical_technique = Column(String())
    reference_units = Column(String())
    id_reactive = Column(String())
    code_SAP = Column(String())
    code_LOG = Column(String())
    active = Column(Integer())
    temp_conservation = Column(String())
    description_subreference = Column(String())
    react_or_fungible = Column(String())
    code_panel = Column(String())
    location = Column(String())
    supplier = Column(String())


class Stock_lots(Base):
    __tablename__ = 'stock_lots'

    id = Column(Integer(), primary_key=True)
    id_lot = Column(Integer())
    catalog_reference = Column(String())
    manufacturer = Column(String())
    description = Column(String())
    analytical_technique = Column(String())
    id_reactive = Column(String())
    code_SAP = Column(String())
    code_LOG = Column(String())
    temp_conservation = Column(String())
    description_subreference = Column(String())
    react_or_fungible = Column(String())
    date_expiry = Column(String())
    lot = Column(String())
    spent = Column(Integer())
    reception_date = Column(String())
    units_lot = Column(Integer())
    internal_lot = Column(Integer())
    transport_conditions = Column(String())
    packaging = Column(String())
    inspected_by = Column(String())
    date_inspected = Column(String())
    observations_inspection = Column(String())
    state = Column(String())
    comand_number = Column(String())
    revised_by = Column(String())
    date_revised = Column(String())
    delivery_note = Column(String())
    certificate = Column(String())
    type_doc_certificate = Column(String())
    type_doc_delivery = Column(String())
    group_insert = Column(Integer())
    code_panel = Column(String())
    location = Column(String())
    supplier = Column(String())
    cost_center_stock = Column(String())


class Logs(Base):
    __tablename__ = 'logs'

    id = Column(Integer(), primary_key=True)
    id_lot = Column(Integer())
    type = Column(String())
    info = Column(String())
    user = Column(String())
    id_user = Column(String())
    date = Column(String())


class Lot_consumptions(Base):
    __tablename__ = 'lot_consumptions'

    id = Column(Integer(), primary_key=True)
    id_lot = Column(Integer())
    date_open = Column(String())
    user_open = Column(String())
    date_close = Column(String())
    user_close = Column(String())
    observations_open = Column(String())
    observations_close = Column(String())


class Commands(Base):
    __tablename__ = 'commands'

    id = Column(Integer(), primary_key=True)
    id_lot = Column(Integer())
    units = Column(Integer())
    date_create = Column(String())
    user_create = Column(String())
    user_id_create = Column(String())
    date_close = Column(String())
    user_close = Column(String())
    user_id_close = Column(String())
    cost_center = Column(String())


class Cost_center(Base):
    __tablename__ = 'cost_center'

    id = Column(Integer(), primary_key=True)
    name = Column(String())
