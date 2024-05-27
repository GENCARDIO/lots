from flask import request, session
from app import app
from app.utils import instant_date, requires_auth, save_log, send_mail
from app.models import session1, Lots, Stock_lots
from sqlalchemy import func, Integer
from sqlalchemy.sql import cast
from werkzeug.utils import secure_filename
import os
import json
from config import main_dir_docs


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
        if not select_lot:
            select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).filter(Lots.active == 1).all()
    else:
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).filter(Lots.active == 1).all()
        if not select_lot:
            select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).filter(Lots.active == 1).all()

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
                             'code_panel': lot.code_panel,
                             'location': lot.location,
                             'supplier': lot.supplier}
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
                              code_panel=lots['code_panel'],
                              location=lots['location'],
                              supplier=lots['supplier'])
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
        max_number_delivery = session1.query(func.max(cast(Stock_lots.delivery_note, Integer))).scalar()
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
        max_number_certificate = session1.query(func.max(cast(Stock_lots.certificate, Integer))).scalar()
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

    # suma_units_lot = 0
    # number_unit_lot = 0
    # Iterar sobre cada diccionario y sumar los valores de 'units_lot'
    # for diccionario in list_lots:
    #     suma_units_lot += int(diccionario.get('units_lot', 0))

    # Iterem sobre la llista de lots, transformem el json a diccionari,
    # consultem si el lo que anem a inserir ja esta introduït
    # si es que si afegirem les unitats a l'stock.
    # Si no mirem si es fungible o reactiu, preparem les dades perque es pugin inserir, la part mes dificil es que si
    # es reactiu s'insereixen un linia per cada unitat i si es fungible una row amb el numero total d'unitas.
    list_info_excel = []
    for lots in list_lots:
        try:
            json_lots = json.dumps(lots)
            select_lot = session1.query(Stock_lots).filter_by(code_SAP=lots['code_SAP'], code_LOG=lots['code_LOG'], lot=lots['lot'], date_expiry=lots['date_expiry'], internal_lot=lots['internal_lot'], spent=0).first()
            if select_lot:
                select_lot.units_lot = int(select_lot.units_lot) + int(lots['units_lot'])
                type_log = 'insert add stock'
                dict_info_excel = {'catalog_reference': lots['catalog_reference'],
                                   'description': lots['description'],
                                   'description_subreference': lots['description_subreference'],
                                   'id_reactive': lots['id_reactive'],
                                   'lot': lots['lot'],
                                   'internal_lot_value': lots['internal_lot'],
                                   'reception_date': lots['reception_date'],
                                   'date_expiry': lots['date_expiry'],
                                   'analytical_technique': lots['analytical_technique']}
                list_info_excel.append(dict_info_excel)
            else:
                type_log = 'insert new stock'

                if lots['react_or_fungible'] == 'Fungible':
                    units_lots_reactive = 1
                    unit_lot_value = lots['units_lot']
                    temperature_value = ''
                else:
                    units_lots_reactive = int(lots['units_lot'])
                    unit_lot_value = 1
                    temperature_value = lots['temp_conservation']

                number_unit_lot = 0
                for i in range(units_lots_reactive):
                    number_unit_lot += 1

                    if lots['react_or_fungible'] == 'Fungible':
                        internal_lot_value = ''
                    else:
                        internal_lot_value = f"{lots['internal_lot']}_{number_unit_lot}/{lots['units_lot']}"

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
                                            units_lot=unit_lot_value,
                                            internal_lot=internal_lot_value,
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
                                            temp_conservation=temperature_value,
                                            react_or_fungible=lots['react_or_fungible'],
                                            code_panel=lots['code_panel'],
                                            location=lots['location'],
                                            supplier=lots['supplier'],
                                            cost_center_stock=lots['cost_center_stock'],
                                            purchase_format=lots['purchase_format'],
                                            units_format=lots['units_format'])
                    session1.add(insert_lot)

                    dict_info_excel = {'catalog_reference': lots['catalog_reference'],
                                       'description': lots['description'],
                                       'description_subreference': lots['description_subreference'],
                                       'id_reactive': lots['id_reactive'],
                                       'lot': lots['lot'],
                                       'internal_lot_value': internal_lot_value,
                                       'reception_date': lots['reception_date'],
                                       'date_expiry': lots['date_expiry'],
                                       'analytical_technique': lots['analytical_technique']}
                    list_info_excel.append(dict_info_excel)

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
    send_mail(list_info_excel)
    return 'True'
