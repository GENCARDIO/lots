# -*- coding: utf-8 -*-
from datetime import datetime
from app.models import Logs, session1, Lots, Cost_center
from functools import wraps
from flask import session, redirect
from app.models import IP_HOME
from config import main_dir_docs
from email.message import EmailMessage
import smtplib


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


def send_mail(list_info_excel):
    '''
        1 - Cridem a create excel info reception pero que ens crei un excel
        2 - Preparem totes les dades del correu
        3 - Adjuntem l'archiu al correu
        3 - Enviem el correu amb totes les dades requerides.

        :param list list_info_excel: llista de diccionaris amb la informació requerida

        :return: None
        :rtype: None
    '''
    try:
        create_excel_info_reception(list_info_excel)

        message = "S'han rebut productes associats a la teva tècnica analítica. T'adjunto un excel amb la informació."

        subject = 'UDMMP | Recepció de productes'

        em = EmailMessage()
        email_sender = "udmmp.girona.ics@gencat.cat"
        em["From"] = email_sender

        if list_info_excel[0]['analytical_technique'] == 'NGS':
            emails = ['monicacoll.girona.ics@gencat.cat', 'llopez@gencardio.com', 'mcorona.girona.ics@gencat.cat', 'mmoliner@idibgi.org', 'msoriano@idibgi.cat', 'mpinsach.girona.ics@gencat.cat', 'aperezs.girona.ics@gencat.cat']
            em["To"] = ', '.join(emails)
        elif list_info_excel[0]['analytical_technique'] == 'Genotipat2':
            emails = ['nneto.girona.ics@gencat.cat', 'mpuigmule.girona.ics@gencat.cat', 'mmoliner@idibgi.org']
            em["To"] = ', '.join(emails)
        elif list_info_excel[0]['analytical_technique'] == 'Sanger2':
            emails = ['ferran.pico@gencardio.com', 'aardila@idibgi.org', 'aperezs.girona.ics@gencat.cat']
            em["To"] = ', '.join(emails)
        if list_info_excel[0]['analytical_technique'] == 'Extracció2':
            emails = ['abatchelli.girona.ics@gencat.cat', 'igomez.girona.ics@gencat.cat']
            em["To"] = ', '.join(emails)
        else:
            # emails = ['asimon.girona.ics@gencat.cat', 'asimon@gencardio.com']
            # em["To"] = ', '.join(emails)
            return

        em["Subject"] = subject
        em.set_content(message)

        with open(f"{main_dir_docs}/recepcio_stock.csv", 'rb') as file:
            file_data = file.read()
            file_name = 'recepcio_stock.csv'
        em.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

        with smtplib.SMTP("172.16.2.137", 25) as smtp:
            smtp.sendmail(email_sender, emails, em.as_string())
            # smtp.send_message(em)
    except Exception:
        return
    return


def create_excel_info_reception(list_info_excel):
    '''
        Creem un excel i l'omplim amb la informació de la llista que ens pasen per parametre

        :param list list_info_excel: llista de diccionaris amb la informació requerida

        :return: False o True
        :rtype: bool
    '''
    try:
        # Crear arxiu nou
        archivo = f"{main_dir_docs}/recepcio_stock.csv"
        csv = open(archivo, "w")
        # Inserir linies al csv
        csv.write('Nom producte;Referencia producte;Nom producte subreferencia;Identificador subreferencia;Lot;Lot intern;Data recepcio;Data caducitat;\n')

        for info_excel in list_info_excel:
            linia_csv = str(info_excel['catalog_reference']) + ';'
            linia_csv += str(info_excel['description']) + ';'
            linia_csv += str(info_excel['description_subreference']) + ';'
            linia_csv += str(info_excel['id_reactive']) + ';'
            linia_csv += str(info_excel['lot']) + ';'
            linia_csv += str(info_excel['internal_lot_value']) + ';'
            linia_csv += str(info_excel['reception_date']) + ';'
            linia_csv += str(info_excel['date_expiry']) + ';'
            linia_csv += '\n'
            csv.write(linia_csv)
        csv.close()
        return True
    except Exception:
        return False
