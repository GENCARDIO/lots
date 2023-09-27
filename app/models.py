# from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from config import main_dir, ip_address

# Connexio amb la BD
engine = create_engine(f'sqlite:////{main_dir}/registres.db', connect_args={'check_same_thread': False})
IP_HOME = f'{ip_address}:5000/'


Base = declarative_base()
Session1 = sessionmaker(engine)
session1 = Session1()

# Definicio del Models/taules de la BD, Cada classe es una taula de la BD i els seus atributs son les columnes


class Registres_sanger(Base):
    __tablename__ = 'registres_sanger'

    id = Column(Integer(), primary_key=True)
    panell_mlpa_qpcr = Column(String())
    familiar_index = Column(String())
    mostra = Column(String())
    codi_extern = Column(String())
    patologia = Column(String())
    data_entrada = Column(String())
    data_limit = Column(String())
    fi_analisi = Column(String())
    gen = Column(String())
    isoforma = Column(String())
    intro_exo = Column(String())
    posicio_cromosomica = Column(String())
    nucleotid = Column(String())
    aminoacid = Column(String())
    rs = Column(String())
    sequencia = Column(String())
    confirmacio = Column(String())
    tecnic = Column(String())
    data_confirmacio = Column(String())
    observacions_laboratori = Column(String())
    num_pcr = Column(String())
    num_db = Column(String())
    validacio = Column(String())
    data_validacio = Column(String())
    observacions_gestor_dades = Column(String())
    status = Column(String())
    dies_retard = Column(String())
    data_assignacio = Column(String())
    informe_pendent = Column(String())
    resultat_validacio_facultativa = Column(String())
    dissenyar_primer = Column(String())
    batch = Column(String())


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
