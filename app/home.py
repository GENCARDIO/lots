from flask import render_template, request, flash, redirect, send_file, session
from app import app
from app.utils import instant_date, requires_auth, save_log
from app.models import IP_HOME, session1, Lots, Stock_lots, Lot_consumptions
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
import jwt
import json
from config import main_dir_docs, main_dir
import pandas as pd


# Pagina incial i visualització
@app.route('/')
@requires_auth
def main():
    '''
        Redirigeix al home de lots
    '''
    return render_template('home.html')


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


@app.route('/search_add_lot', methods=['POST'])
@requires_auth
def search_add_lot():
    '''
        Busquem a la BD si el lot ja existeix.
        Si existeix agafem tota la informació la posem en una llista de diccionaris i la enviem per ajax.
        Si no existesix enviem una resposta per ajex avisan de que no tenim el lot registrat.

        :param str code_search: codi que hem de buscar a la BD

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    code_search = request.form.get("code_search")
    code_panel = request.form.get("code_panel")

    if code_panel == '':
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(Lots.active == 1).all()
    else:
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).filter(Lots.active == 1).all()

    try:
        if not select_lot:
            return 'True_//_new'
        else:
            list_lots = []
            for lot in select_lot:
                dict_lots = {'key': lot.key,
                             'catalog_reference': lot.catalog_reference,
                             'manufacturer': lot.manufacturer,
                             'description': lot.description,
                             'description_subreference': lot.description_subreference,
                             'analytical_technique': lot.analytical_technique,
                             'reference_units': lot.reference_units,
                             'id_reactive': lot.id_reactive,
                             'code_SAP': lot.code_SAP,
                             'code_LOG': lot.code_LOG,
                             'active': lot.active,
                             'temp_conservation': lot.temp_conservation,
                             'react_or_fungible': lot.react_or_fungible,
                             'code_panel': lot.code_panel}
                list_lots.append(dict_lots)
            json_data = json.dumps(list_lots)
            return f'True_//_{json_data}'
    except Exception:
        return 'False_//_False'


@app.route('/register_new_lot', methods=['POST'])
@requires_auth
def register_new_lot():
    '''
        Recullim la informació, i com que es un registre nou inserim la informació a la BD.
        Guardarem un log de l'inserció.

        :param str reference_catalog: Referencia del proveÑidor del producte seleccionat
        :param str list_lots: llista amb la informació dels lots que hem de modificar

        :function: save_log(dict)

        :return: json amb un True o un False i si es False una paraula amb el motiu.
        :rtype: json
    '''
    reference_catalog = request.form.get("reference_catalog")
    list_lots_json = request.form.get("list_lots")

    list_lots = json.loads(list_lots_json)
    date = instant_date()

    for lots in list_lots:
        try:
            insert_lot = Lots(catalog_reference=reference_catalog,
                              manufacturer=lots['manufacturer'],
                              description=lots['description'],
                              analytical_technique=lots['analytical_technique'],
                              reference_units=1,
                              id_reactive=lots['id_reactiu'],
                              code_SAP=lots['code_sap'],
                              code_LOG=lots['code_log'],
                              active=1,
                              temp_conservation=lots['temp_conservation'],
                              react_or_fungible=lots['react_or_fungible'],
                              description_subreference=lots['description_subreference'],
                              code_panel=lots['code_panel'])
            session1.add(insert_lot)

            json_lots = json.dumps(lots)

            select_lot = session1.query(Lots).order_by(Lots.key.desc()).first()
            info_lot = {'id_lot': select_lot.key,
                        'type': 'insert new lot',
                        'info': json_lots,
                        'user': session['acronim'],
                        'id_user': session['idClient'],
                        'date': date}
            save_log(info_lot)
        except Exception:
            session1.rollback()
            return 'False_error'
    session1.commit()
    return 'True'


@app.route('/add_stock_lot', methods=['POST'])
@requires_auth
def add_stock_lot():
    '''
        1 - Recollim la informació de l'ajax.
        2 - Assignem el següent número de grup a la inserció.
        3 - Guardem els 2 documents que ens han pujat, no és obligatori que carreguin fitxers.
        4 - Transformem la informació de l'ajax en una llista de diccionaris.
        5 - Iterem sobre la llista i primer buscarem si el lot ja estava introduït.
        5.1 - Si o esta sumarem les unitats actuals més les que entren i actualitzaré el lot
        5.2 - Si no afegirem a l'estoc el lot.
        6 - Guardarem un log de l'operació.

        :param str list_lots_json: json amb la informació del lots que hem d'inserir.
        :param str file_delivery_note: Document que ens ha facilitat l'usuari.
        :param str file_certificate: Document que ens ha facilitat l'usuari.

        :return: json amb un True o un False i si es falte una paraula amb el motiu.
        :rtype: json
    '''
    list_lots_json = request.form.get("list_lots")
    date = instant_date()

    max_number_group_insert = session1.query(func.max(Stock_lots.group_insert)).scalar()
    if max_number_group_insert is not None:
        group_insert_number = int(max_number_group_insert) + 1
    else:
        group_insert_number = 1

    try:
        f = request.files["file_delivery_note"]
        filename_delivery_note = secure_filename(f.filename)
        split_dirname = filename_delivery_note.split(".")
        max_number_delivery = session1.query(func.max(Stock_lots.delivery_note)).scalar()
        if max_number_delivery is not None:
            filename_delivery = int(max_number_delivery) + 1
            type_doc_delivery = f'.{split_dirname[1]}'
        else:
            filename_delivery = 1
            type_doc_delivery = f'.{split_dirname[1]}'

        f.save(os.path.join(f"{main_dir_docs}/albarans/", f'{filename_delivery}.{split_dirname[1]}'))
    except Exception:
        filename_delivery = ''
        type_doc_delivery = ''

    try:
        f2 = request.files["file_certificate"]
        filename_certificate_aux = secure_filename(f2.filename)
        split_dirname = filename_certificate_aux.split(".")
        max_number_certificate = session1.query(func.max(Stock_lots.certificate)).scalar()
        if max_number_certificate is not None:
            filename_certificate = int(max_number_certificate) + 1
            type_doc_certificate = f'.{split_dirname[1]}'
        else:
            filename_certificate = 1
            type_doc_certificate = f'.{split_dirname[1]}'

        f2.save(os.path.join(f"{main_dir_docs}/certificats/", f'{filename_certificate}.{split_dirname[1]}'))
    except Exception:
        filename_certificate = ''
        type_doc_certificate = ''

    list_lots = json.loads(list_lots_json)

    suma_units_lot = 0
    number_unit_lot = 0
    # Iterar sobre cada diccionario y sumar los valores de 'units_lot'
    for diccionario in list_lots:
        suma_units_lot += int(diccionario.get('units_lot', 0))

    for lots in list_lots:
        try:
            json_lots = json.dumps(lots)
            select_lot = session1.query(Stock_lots).filter_by(code_SAP=lots['code_SAP'], code_LOG=lots['code_LOG'], lot=lots['lot'], date_expiry=lots['date_expiry'], internal_lot=lots['internal_lot'], spent=0).first()
            if select_lot:
                select_lot.units_lot = int(select_lot.units_lot) + int(lots['units_lot'])
                type_log = 'insert add stock'
            else:
                type_log = 'insert new stock'

                for i in range(int(lots['units_lot'])):
                    number_unit_lot += 1
                    insert_lot = Stock_lots(id_lot=lots['key'],
                                            catalog_reference=lots['catalog_reference'],
                                            manufacturer=lots['manufacturer'],
                                            description=lots['description'],
                                            description_subreference=lots['description_subreference'],
                                            analytical_technique=lots['analytical_technique'],
                                            id_reactive=lots['id_reactive'],
                                            code_SAP=lots['code_SAP'],
                                            code_LOG=lots['code_LOG'],
                                            date_expiry=lots['date_expiry'],
                                            lot=lots['lot'],
                                            spent=0,
                                            reception_date=lots['reception_date'],
                                            units_lot=1,
                                            internal_lot=f"{lots['internal_lot']}_{number_unit_lot}/{suma_units_lot}",
                                            transport_conditions=lots['transport_conditions'],
                                            packaging=lots['packaging'],
                                            inspected_by=lots['inspected_by'],
                                            date_inspected=lots['date_inspected'],
                                            observations_inspection=lots['observations_inspection'],
                                            state=lots['state'],
                                            comand_number=lots['comand_number'],
                                            revised_by=lots['revised_by'],
                                            date_revised=lots['date_revised'],
                                            delivery_note=filename_delivery,
                                            certificate=filename_certificate,
                                            type_doc_certificate=type_doc_certificate,
                                            type_doc_delivery=type_doc_delivery,
                                            group_insert=group_insert_number,
                                            temp_conservation=lots['temp_conservation'],
                                            react_or_fungible=lots['react_or_fungible'],
                                            code_panel=lots['code_panel'])
                    session1.add(insert_lot)

            select_lot = session1.query(Stock_lots).order_by(Stock_lots.id.desc()).first()
            info_lot = {'id_lot': select_lot.id,
                        'type': type_log,
                        'info': json_lots,
                        'user': session['acronim'],
                        'id_user': session['idClient'],
                        'date': date}
            save_log(info_lot)
        except Exception:
            session1.rollback()
            return 'False_error'
    session1.commit()
    return 'True'


@app.route('/search_lots', methods=['POST'])
@requires_auth
def search_lots():
    '''
        1 - Recollim la informació de l'html
        2 - Busquem a la BD amb la informació que ens han facilitat
        2.1 - Si no es troba coincidència retornem un missatge d'error a l'html
        2.2 - Si es troba coincidència retornarem el que hem trobat a l'html.

        :param str search_code: Codi a buscar.

        :return: La informació dels lots trobada i un int que és l'id de lot.
        :rtype: render_template, object, int
    '''
    search_code = request.form['search_code']
    code_panel = request.form['code_panel_search']

    if code_panel == '':
        select_lot = session1.query(Stock_lots).filter(func.lower(Stock_lots.catalog_reference) == search_code.lower(), Stock_lots.spent == 0).all()
    else:
        select_lot = session1.query(Stock_lots).filter(func.lower(Stock_lots.catalog_reference) == search_code.lower(), func.lower(Stock_lots.code_panel) == code_panel.lower(), Stock_lots.spent == 0).all()
    if not select_lot:
        flash(f"No s'ha trobat cap coincidencia amb el text entrat --> {search_code}", "warning")
        return render_template('home.html')

    return render_template('search_lot.html', select_lot=select_lot, lot=select_lot[0])


@app.route("/download_docs", methods=["POST"])
@requires_auth
def download_docs():
    """
        1 - Recollim la informació
        2 - Preparem la ruta on estan els documents
        3 - Descarreguem el document i li formatem el nom.

        :param str dir_name: Nom de la carpeta on hi ha el document.
        :param str name_doc: Nom del document.

        :return: Retorna l'arxiu que ha estat carregat previament
        :rtype: archive
    """
    dir_name = request.form["dir_name"]
    name_doc = request.form["name_doc"]

    path = f"{main_dir_docs}/{dir_name}/{name_doc}"
    return send_file(path, as_attachment=True, download_name=f"{dir_name}_{name_doc}")


@app.route('/upload_docs', methods=['POST'])
@requires_auth
def upload_docs():
    '''
        1 - Recollim la informació de l'ajax
        2 - Busquem si aquest lot va ser introduït amb algun lot addicional
        3 - Mirem quin nom li toca al document
        4 - Guardem el document a la carpeta que toca.
        5 - Actualitzem a stock_lots els camps que facin falta.
        6 - Retornem la resposta a l'ajax de si el procés ha anat bé o no.

        :param str dir_name: Nom de la carpeta on hi ha el document.
        :param str group_insert: Referència que ens diu quins stock_lots s'han inserit junts.
        :param str file: Document que ens carrega l'usuari.

        :return: Retorna True o False, si és True també enviem diverses dades que es necessiten.
        :rtype: json
    '''
    dir_name = request.form.get("dir_name")
    group_insert = request.form.get("group_insert")

    select_lots = session1.query(Stock_lots).filter_by(group_insert=group_insert).all()
    if not select_lots:
        return 'False'

    try:
        f = request.files["file"]
        filename = secure_filename(f.filename)
        split_dirname = filename.split(".")

        if dir_name == 'delivery_note':
            max_number_filename = session1.query(func.max(Stock_lots.delivery_note)).scalar()
            dirname = 'albarans'
        elif dir_name == 'certificate':
            max_number_filename = session1.query(func.max(Stock_lots.certificate)).scalar()
            dirname = 'certificats'
        else:
            return 'False'

        if max_number_filename is not None and max_number_filename == '':
            new_filename = 1
            type_doc = f'.{split_dirname[1]}'
        elif max_number_filename is not None:
            new_filename = int(max_number_filename) + 1
            type_doc = f'.{split_dirname[1]}'
        else:
            return 'False'
        f.save(os.path.join(f"{main_dir_docs}/{dirname}/", f'{new_filename}.{split_dirname[1]}'))
    except Exception:
        return "False"

    id_lots = ''
    for lots in select_lots:
        id_lots += f"{lots.id};"
        if dir_name == 'delivery_note':
            lots.delivery_note = new_filename
            lots.type_doc_delivery = type_doc
        elif dir_name == 'certificate':
            lots.certificate = new_filename
            lots.type_doc_certificate = type_doc
    session1.commit()
    if id_lots[-1] == ';':
        id_lots = id_lots[:-1]
    return f'True///{id_lots}///{new_filename}///{type_doc}'


@app.route('/search_lots_open_close', methods=['POST'])
@requires_auth
def search_lots_open_close():
    '''
        1 - Recuperem la informació de l'html
        2 - Busquem a Stock_lots la informació requerida
        2.1 - Si no la trobem, retornem un missatge comunicant que no hi ha dades
        2.2 - Si en trobem, Retornem la informació de la Bd i id_lot

        :param str reference: Referència per buscar a stock_lots

        :return: Retorem una llista d'objectes amb la informació que hem trobat a la BD i el id_lot
        :rtype: object, int
    '''
    reference = request.form['reference']
    # select_lot = session1.query(Stock_lots).filter_by(catalog_reference=reference, react_or_fungible='Reactiu', spent=0).all()
    select_lot = session1.query(Stock_lots).filter(func.lower(Stock_lots.catalog_reference) == reference.lower(), Stock_lots.spent == 0, Stock_lots.react_or_fungible == 'Reactiu').all()
    if not select_lot:
        # select_lot = session1.query(Stock_lots).filter_by(id_reactive=reference, react_or_fungible='Reactiu', spent=0).all()
        select_lot = session1.query(Stock_lots).filter(func.lower(Stock_lots.id_reactive) == reference.lower(), Stock_lots.spent == 0, Stock_lots.react_or_fungible == 'Reactiu').all()
        if not select_lot:
            flash(f"No s'ha trobat cap coincidencia amb el codi entrat --> {reference}", "warning")
            return render_template('home.html')

    return render_template('open_close_lots.html', select_lot=select_lot, lot=select_lot[0])


@app.route('/open_close_lots', methods=['POST'])
@requires_auth
def open_close_lots():
    '''
        1 - Recollim les dades de l'ajax
        2 - Busquem la informació a la BD amb l'id que ens donen.
        2.1 - Si no el trobem retornarem un False amb l'explicació de l'error.
        3 - Busquem a Lot_consumption quan lots tenim oberts amb l'id que ens han donat, també guardarem la posició del\
            primer lot que no tingui data_tancament, aquest serà el lot que tancarem.
        4 - Obtenim la data actual
        5 - Si l'acció és obrir un lot
        5.1 - Comprovem que hi hagin lots per obrir
        5.2 - Si no hi ha lots retornem un False amb l'explicació de l'error.
        5.3 - Si hi ha lots per obrir, inserirem una obertura de lot a Lot_consumptins amb les dades necessàries.
        5.4 - Retornarem un True amb un missatge d'informació per l'usuari.
        6 - Si l'acció és tancar un lot
        6.1 - Comprovem que hi hagin lots per tancar
        6.2 - Si no hi ha lots per tancar retornem un False amb l'explicació de l'error
        6.3 - Actualitzem les dades de Lot_consumption
        6.4 - Si al actualitzar les dades les unitats arriben a 0, tots els lots que comparteixen grup s'han de tancar\
            i bloquejar, ja que quan un arriba a 0 els altres ja no es poden fer servir.
        7 - Retornem un missatge amb True o False, dependent de si tot a sortit bé o no i també afegirem una explicació\
            per l'usuari

        :param str id_lot: Identificador unit del lot
        :param str action: Tipu d'acció que es realitza

        :return: True o False i una explicació per l'usuari
        :rtype: json
    '''
    id_lot = request.form.get("id_lot")
    action = request.form.get("action")
    num_lots_open = 0
    pos_close = -1
    message = ''
    str_id_lots = ''
    # try:
    select_lots = session1.query(Stock_lots).filter_by(id=id_lot).first()
    if select_lots is None:
        return 'False_No hem trobat el lot seleccionat.'

    select_consumptions = session1.query(Lot_consumptions).filter_by(id_lot=id_lot).all()
    if select_consumptions:
        lot_open = 0
        lot_close = 0
        for index, consumptions in enumerate(select_consumptions):
            if consumptions.date_close != '':
                lot_open += 1
                lot_close += 1
            else:
                lot_open += 1
                if pos_close == -1:
                    pos_close = index

        num_lots_open = lot_open - lot_close

    date = instant_date()
    if action == 'open':
        if num_lots_open >= select_lots.units_lot:
            return "False_Tots els lots d'aquesta referència estan oberts."
        insert_consump = Lot_consumptions(id_lot=id_lot, date_open=date, user_open=session['acronim'], date_close='')
        session1.add(insert_consump)
        if num_lots_open + 1 == 1:
            message = f"El lot s'ha obert correctament, tens {num_lots_open + 1} unitat oberta d'aquesta referència."
        else:
            message = f"El lot s'ha obert correctament, tens {num_lots_open + 1} unitats obertes d'aquesta referència."
    elif action == 'close':
        if num_lots_open > 0:
            select_consumptions[pos_close].date_close = date
            select_consumptions[pos_close].user_close = session['acronim']
            select_lots.units_lot = select_lots.units_lot - 1
            message = "El lot s'ha tancat correctament"
            if select_lots.units_lot == 0:
                select_group_lots = session1.query(Stock_lots).filter_by(group_insert=select_lots.group_insert).all()
                sublot = 0
                for lot_group in select_group_lots:
                    split_internal_lot = str(lot_group.internal_lot).split('_')
                    split_internal_lot_2 = str(select_lots.internal_lot).split('_')
                    if lot_group.id_reactive == select_lots.id_reactive and \
                        split_internal_lot[0] == split_internal_lot_2[0] and \
                        lot_group.units_lot > 0:
                        sublot += 1
                        print(sublot)
                if sublot == 0:
                    for lot_group in select_group_lots:
                        lot_group.spent = 1
                        str_id_lots += f'{lot_group.id};'
                        if lot_group.units_lot != 0:
                            select_lot_consumptions = session1.query(Lot_consumptions).filter_by(id_lot=lot_group.id, date_close='').all()
                            for lot_consumptions in select_lot_consumptions:
                                lot_consumptions.date_close = date
                                lot_consumptions.user_close = session['acronim']
                            lot_group.units_lot = lot_group.units_lot - len(select_lot_consumptions)
                    str_id_lots = str_id_lots[:-1]
                    message = f"El lot s'ha tancat correctament, Aquesta referència s'ha esgotat, ella i totes les subreferències han set posades com ha gastades._{str_id_lots}"
        else:
            return 'False_No es pot tancar cap lot amb aquesta referència, obre primer un lot.'
    session1.commit()
    # except Exception:
    #     return "False_No s'ha pogut accedir a la BD, si l'error persisteix contacta amb un administrador."
    return f'True_{message}'


@app.route('/history_lot', methods=['POST'])
@requires_auth
def history_lot():
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
    id_lot = request.form.get("id_lot")

    try:
        select_consumptions = session1.query(Lot_consumptions).filter_by(id_lot=id_lot).all()
        if not select_consumptions:
            return 'False_//_No hi ha cap consumisio registrada.'

        list_consumptions = []
        for consumption in select_consumptions:
            dict_consumption = {}
            dict_consumption['id'] = consumption.id
            dict_consumption['id_lot'] = consumption.id_lot
            dict_consumption['date_open'] = consumption.date_open
            dict_consumption['user_open'] = consumption.user_open
            dict_consumption['date_close'] = consumption.date_close
            dict_consumption['user_close'] = consumption.user_close
            list_consumptions.append(dict_consumption)

        json_data = json.dumps(list_consumptions)
    except Exception:
        return "False_ No s'ha pogut accedir a la informació dels consums."

    return f'True_//_{json_data}'


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
            # dict_lots['key'] = lot.key
            # dict_lots['manufacturer'] = lot.manufacturer
            # dict_lots['analytical_technique'] = lot.analytical_technique
            # dict_lots['reference_units'] = lot.reference_units
            # dict_lots['id_reactive'] = lot.id_reactive
            dict_lots['code_SAP'] = lot.code_SAP
            dict_lots['code_LOG'] = lot.code_LOG
            dict_lots['catalog_reference'] = lot.catalog_reference
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


@app.route('/charge_excel')
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
    return "fet"
