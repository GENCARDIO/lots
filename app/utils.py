# -*- coding: utf-8 -*-
from datetime import datetime
from app.models import Logs, session1
from functools import wraps
from flask import session, redirect
from app.models import IP_HOME


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
