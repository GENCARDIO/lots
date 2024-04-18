from flask import render_template, request, redirect, session, flash
from app import app
from app.utils import requires_auth, list_desciption_lots, list_cost_center
from app.models import IP_HOME, session1, Lots, Stock_lots, Lot_consumptions
import jwt
import json
# from config import main_dir
# import pandas as pd


# Pagina incial i visualització
@app.route('/')
@requires_auth
def main():
    '''
        Redirigeix al home de lots
    '''
    return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                           list_cost_center=list_cost_center())


@app.route('/logout')
def logout():
    '''
        Redirigeix a l'applicació home/logout
    '''
    url = IP_HOME + 'logout'

    return redirect(url)


@app.route('/apps')
@requires_auth
def apps():
    '''
        Guardem les cookies en un tocken i les enviem a home/apps, perque puguin obrir cualsevol applicació a la que
        tinguin acceès.
    '''
    tocken_cookies = {'user_tok': session['user'], 'rols_tok': session['rols'], 'email_tok': session['email'],
                      'id_client_tok': session['idClient'], 'rol_tok': 'None', 'acronim_tok': session['acronim']}
    secret_key = '12345'
    token = jwt.encode(tocken_cookies, secret_key, algorithm='HS256')
    url = f'{IP_HOME}apps/token?token={token}'

    return redirect(url)


@app.route('/receive_token')
def receive_token():
    '''
        Rebem el tocken i assignem a la nostre sessions els valors.
    '''
    received_token = request.args.get('token')
    secret_key = '12345'  # Debe ser la misma clave utilizada para generar el token

    try:
        decoded_token = jwt.decode(received_token, secret_key, algorithms=['HS256'])
        session['user'] = decoded_token.get('user_tok', 'Usuario no encontrado')
        session['rols'] = decoded_token.get('rols_tok', 'Usuario no encontrado')
        session['email'] = decoded_token.get('email_tok', 'Usuario no encontrado')
        session['idClient'] = decoded_token.get('id_client_tok', 'Usuario no encontrado')
        session['rol'] = decoded_token.get('rol_tok', 'Usuario no encontrado')
        session['acronim'] = decoded_token.get('acronim_tok', 'Usuario no encontrado')
        print(session['user'])
        print(session['rols'])
        print(session['email'])
        print(session['idClient'])
        print(session['rol'])
        print(session['acronim'])
        return redirect('/')
    except Exception:
        return redirect('/logout')


@app.route('/search_lot_db', methods=['POST'])
@requires_auth
def search_lot_db():
    '''
        1 - Recollim la informació de l'ajax
        2 - Comprovem si aquest lot té història.
        2.1 - Si no en té retornem False més un missatge d'explicació per l'usuari.
        2.2 - Si és que si agafem la informació que hem trobat la posem en una llista de diccionaris.
        3 - Convertim la llista de diccionaris en un json
        4 - Retornem un True més la llista de diccionaris convertida a json.

        :param str id_lot: Identificador unit del lot

        :return: True i la llista de diccionaris amb la info o False i una explicació per l'usuari
        :rtype: json
    '''
    try:
        select_lots = session1.query(Lots).filter(Lots.active == 1).all()
        if not select_lots:
            return 'False_//_No hi ha cap lot a la BD.'

        list_lots = []
        for lot in select_lots:
            dict_lots = {}
            dict_lots['id'] = lot.key
            # dict_lots['manufacturer'] = lot.manufacturer
            # dict_lots['analytical_technique'] = lot.analytical_technique
            # dict_lots['reference_units'] = lot.reference_units
            # dict_lots['id_reactive'] = lot.id_reactive
            dict_lots['code_SAP'] = lot.code_SAP
            dict_lots['code_LOG'] = lot.code_LOG
            dict_lots['catalog_reference'] = lot.catalog_reference
            dict_lots['info_article'] = f"{lot.key}/-/{lot.catalog_reference}/-/{lot.manufacturer}/-/{lot.description}/-/{lot.analytical_technique}/-/{lot.reference_units}/-/{lot.id_reactive}/-/{lot.code_SAP}/-/{lot.code_LOG}/-/{lot.active}/-/{lot.temp_conservation}/-/{lot.description_subreference}/-/{lot.react_or_fungible}/-/{lot.code_panel}/-/{lot.location}/-/{lot.supplier}"
            dict_lots['description'] = lot.description
            dict_lots['description_subreference'] = lot.description_subreference
            # dict_lots['active'] = lot.active
            # dict_lots['temp_conservation'] = lot.temp_conservation
            # dict_lots['react_or_fungible'] = lot.react_or_fungible

            list_lots.append(dict_lots)

        json_data = json.dumps(list_lots)
    except Exception:
        return "False_ No s'ha pogut accedir a la informació dels consums."

    return f'True_//_{json_data}'


@app.route('/history_lots', methods=['POST'])
@requires_auth
def history_lots():
    '''
        1 - Recollim la informació de l'ajax
        2 - Comprovem si aquest lot té història.
        2.1 - Si no en té retornem False més un missatge d'explicació per l'usuari.
        2.2 - Si és que si agafem la informació que hem trobat la posem en una llista de diccionaris.
        3 - Convertim la llista de diccionaris en un json
        4 - Retornem un True més la llista de diccionaris convertida a json.

        :param str historic_code_lot: Identificador unit del lot

        :return: True i la llista de diccionaris amb la info o False i una explicació per l'usuari
        :rtype: json
    '''
    historic_code_lot = request.form.get("historic_code_lot")

    try:
        info_history = session1.query(Stock_lots, Lot_consumptions).\
                       join(Lot_consumptions, Stock_lots.id == Lot_consumptions.id_lot).\
                       filter(Stock_lots.lot == historic_code_lot).\
                       all()
        if not info_history:
            return 'False_//_No hi ha informació sobre aquest lot.'

        list_consumptions = []
        for stock_lot, consumption in info_history:
            dict_consumption = {}
            dict_consumption['id'] = consumption.id
            dict_consumption['id_lot'] = consumption.id_lot
            if stock_lot.description_subreference == '':
                dict_consumption['description'] = stock_lot.description
            else:
                dict_consumption['description_subreference'] = stock_lot.description_subreference
            dict_consumption['lot'] = stock_lot.lot
            dict_consumption['catalog_reference'] = stock_lot.catalog_reference
            dict_consumption['internal_lot'] = stock_lot.internal_lot
            dict_consumption['date_open'] = consumption.date_open
            dict_consumption['user_open'] = consumption.user_open
            dict_consumption['date_close'] = consumption.date_close
            dict_consumption['user_close'] = consumption.user_close
            dict_consumption['observations_open'] = consumption.observations_open
            dict_consumption['observations_close'] = consumption.observations_close
            list_consumptions.append(dict_consumption)

        json_data = json.dumps(list_consumptions)
    except Exception:
        return "False_ No s'ha pogut accedir a la informació dels consums."

    return f'True_//_{json_data}'


@app.route('/search_fungible', methods=['POST'])
@requires_auth
def search_fungible():
    '''
        1 - Recollim la informació de l'ajax
        2 - Busquem amb elcodi a les 3 columnes possibles
        2.1 - Si no en té redirigim a home i mostrem un missatge per pantalla
        2.2 - Si és que si agafem la informació que hem trobat i la enviem a l'html

        :param str code_search_fungible: Identificador del fungible

        :return: Retornem 3 llistes d'objectes a l'html corresponent
        :rtype: render_template, list, list, list
    '''
    code_search_fungible = request.form['code_search_fungible']

    try:
        if code_search_fungible == '':
            select_lots = session1.query(Stock_lots).filter_by(spent=0, react_or_fungible='Fungible').all()
        else:
            select_lots = session1.query(Stock_lots).filter_by(spent=0, react_or_fungible='Fungible', description=code_search_fungible).all()
            if not select_lots:
                select_lots = session1.query(Stock_lots).filter_by(spent=0, react_or_fungible='Fungible', catalog_reference=code_search_fungible).all()
                if not select_lots:
                    select_lots = session1.query(Stock_lots).filter_by(spent=0, react_or_fungible='Fungible', code_SAP=code_search_fungible).all()
                    if not select_lots:
                        select_lots = session1.query(Stock_lots).filter_by(spent=0, react_or_fungible='Fungible', code_LOG=code_search_fungible).all()

        if not select_lots:
            flash("No hi ha cap fungible amb el codi introduït", "warning")
            return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                                   list_cost_center=list_cost_center())
    except Exception:
        flash("Error, no s'han pogut realitzar la cerca", "danger")
        return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                               list_cost_center=list_cost_center())

    return render_template('search_fungible.html', select_lots=select_lots)


'''@app.route('/charge_excel')
def charge_excel():
    try:
        # Llegim el directori i el convertim en una llista
        directori = f'{main_dir}/info.xlsx'
        print(directori)
        df = pd.read_excel(directori, header=None)
        list_excel = df.values.tolist()
    except Exception:
        print("No s'ha pogut lleguir el document")
        return False
    print(f'linia maxima excel --> {len(list_excel)}')

    for line in range(1, len(list_excel)):
        print(list_excel[line])
        try:
            insert_lots = Lots(catalog_reference=str(list_excel[line][6]) if str(list_excel[line][6]) != 'nan' else '',
                               manufacturer=str(list_excel[line][3]) if str(list_excel[line][3]) != 'nan' else '',
                               description=str(list_excel[line][5]) if str(list_excel[line][5]) != 'nan' else '',
                            analytical_technique=str(list_excel[line][0]) if str(list_excel[line][0]) != 'nan' else '',
                               reference_units=1,
                               id_reactive='',
                               code_SAP=str(list_excel[line][8]) if str(list_excel[line][8]) != 'nan' else '',
                               code_LOG=str(list_excel[line][7]) if str(list_excel[line][7]) != 'nan' else '',
                               active=1,
                               temp_conservation=str(list_excel[line][9]) if str(list_excel[line][9]) != 'nan' else '',
                               description_subreference='',
                               react_or_fungible=str(list_excel[line][2]) if str(list_excel[line][2]) != 'nan' else '',
                               code_panel='')
            session1.add(insert_lots)
        except Exception:
            print("error")
    session1.commit()
    return "fet" '''
