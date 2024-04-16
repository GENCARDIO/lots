# -*- coding: utf-8 -*-
from datetime import datetime
from app.models import Logs, session1, Lots, Cost_center
from functools import wraps
from flask import session, redirect
from app.models import IP_HOME
from config import main_dir_docs


# Authentication
def requires_auth(f):
    @wraps(f)
    def decorated_function(*args):
        if session['rol'] == 'None' or session['rol'] is None or session['rol'] == '':
            url = f'{IP_HOME}logout/You dont have permissions'
            return redirect(url)
        else:
            pass
        return f(*args)
    return decorated_function


def instant_date():
    '''
    1 - Obtenim la data actual
    2 - La formatem perquè estigui com nosaltres volem
    3 - Enviem la data formatada.

    :return: La data actual formatada.
    :rtype: string

    '''
    date = datetime.now()
    format_date = date.strftime("%d-%m-%Y")
    return format_date


def save_log(dict_info_lot):
    '''
        1 - Afegim a la BD de Logs una linia amb la info que ens donen

        :param str dict_info_lot: Diccionari amb la informació requerida

        :return: True o False.
        :rtype: json

    '''
    try:
        insert_log = Logs(id_lot=dict_info_lot['id_lot'],
                          type=dict_info_lot['type'],
                          info=dict_info_lot['info'],
                          user=dict_info_lot['user'],
                          id_user=dict_info_lot['id_user'],
                          date=dict_info_lot['date'])
        session1.add(insert_log)
        # session1.commit()
    except Exception:
        return "False"
    return 'True'


def list_desciption_lots():
    '''
        1 - Agafem tots el lots actius i els retornem.

        :return: llista amb els objectes de tipo Lots que hem trobat a la BD
        :rtype: llista d'objectes
    '''
    select_lot = session1.query(Lots).filter(Lots.active == 1).all()
    return select_lot


def list_cost_center():
    '''
        1 - Agafem tots els camps de cost center

        :return: llista amb els objectes de tipo Cost center que hem trobat a la BD
        :rtype: llista d'objectes
    '''
    select_cost_center = session1.query(Cost_center).all()
    return select_cost_center


def create_excel(select_row):
    '''
        Creem un csv amb la informació que recollim de la BD
        Iterem la llista i anem posant la informació on toca
    '''
    try:
        # Crear arxiu nou
        archivo = f"{main_dir_docs}/comandes_pendents.csv"
        csv = open(archivo, "w")
        # Inserir linies al csv
        csv.write('Codi proveidor;Descripció;Codi SAP;Codi LOG;Unitats;Data creació;Usuari;CECO\n')
        for command, lot in select_row:
            linia_csv = str(lot.catalog_reference) + ';'
            linia_csv += str(lot.description) + ';'
            linia_csv += str(lot.code_SAP) + ';'
            linia_csv += str(lot.code_LOG) + ';'
            linia_csv += str(command.units) + ';'
            linia_csv += str(command.date_create) + ';'
            linia_csv += str(command.user_create) + ';'
            linia_csv += str(command.cost_center) + ';'
            linia_csv += '\n'
            csv.write(linia_csv)
        csv.close()
        return True
    except Exception:
        return False
