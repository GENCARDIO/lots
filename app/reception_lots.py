from flask import request, session
from app import app
from app.utils import instant_date, requires_auth, save_log, send_mail
from app.models import session1, Lots, Stock_lots, Commands
from sqlalchemy import func, Integer, and_
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
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).all()
        if not select_lot:
            select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).all()
    else:
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).all()
        if not select_lot:
            select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).all()

    try:
        if not select_lot:
            return 'True_//_new'
        else:
            # Mirem si tot el producte esta bloquejat, si ho està ho reportem a l'html
            block_lot_mark = True
            for block_lot in select_lot:
                if int(block_lot.active) != 0:
                    block_lot_mark = False
            if block_lot_mark:
                return 'True_//_inactive'

            command_pending = ''
            id_command = ''
            ceco_command = ''
            user_add_command = ''
            list_commands = []
            # Aqui mirem la key del lot actium ja que podem tenir subreferencies bloquejades
            for lot in select_lot:
                if lot.active != 0:
                    key_lot = lot.key
                    break
            select_command = session1.query(Commands).filter(Commands.id_lot == key_lot).filter(Commands.received == 0).filter(Commands.code_command != '').all()
            if select_command:
                for command in select_command:
                    units_command = int(command.units) - int(command.num_received)
                    command_pending += f"La comanda {command.code_command} esta esperant {units_command} unitat/s.<br>"
                    id_command = f'{command.id};'
                    ceco_command = command.cost_center
                    user_add_command = command.user_create
                    list_commands.append([command.id, command.user_create, command.code_command, command.cost_center])
                if id_command[-1] == ';':
                    id_command = id_command[:-1]
            else:
                return "False_//_No hi ha comanda feta d'aquest producte, si us plau contacta amb els administradors_//_warning"

            list_lots = []
            for lot in select_lot:
                if lot.active != 0:
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
                                 'supplier': lot.supplier,
                                 'purchase_format': lot.purchase_format,
                                 'units_format': lot.units_format,
                                 'import_unit_ics': lot.import_unit_ics,
                                 'import_unit_idibgi': lot.import_unit_idibgi,
                                 'local_management': lot.local_management,
                                 'plataform_command_preferent': lot.plataform_command_preferent,
                                 'maximum_amount': lot.maximum_amount,
                                 'purchase_format_supplier': lot.purchase_format_supplier,
                                 'units_format_supplier': lot.units_format_supplier,
                                 'command_pending': command_pending,
                                 'id_command': id_command,
                                 'ceco_command': ceco_command,
                                 'user_add_command': user_add_command}
                    list_lots.append(dict_lots)
            json_data = json.dumps(list_lots)
            list_commands_json = json.dumps(list_commands) 
            return f'True_//_{json_data}_//_{list_commands_json}'
    except Exception:
        return 'False_//_Error, La cerca del lot ha fallat_//_danger'


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
                              supplier=lots['supplier'],
                              purchase_format=lots['purchase_format'],
                              units_format=lots['units_format'],
                              import_unit_ics=float(lots['import_unit_ics'].replace(',', '.')),
                              import_unit_idibgi=float(lots['import_unit_idibgi'].replace(',', '.')),
                              local_management=lots['local_management'],
                              plataform_command_preferent=lots['plataform_command_preferent'],
                              maximum_amount=lots['maximum_amount'],
                              purchase_format_supplier=lots['purchase_format_supplier'],
                              units_format_supplier=lots['units_format_supplier'])
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
    unit_total_command = request.form.get("unit_total_command")
    list_lots_json = request.form.get("list_lots")
    id_substract_command = request.form.get("id_substract_command")
    pb_oligos = request.form.get("pb_oligos")
    incidence_number = request.form.get("incidence_number")
    price_coriells = request.form.get("price_coriells")

    number_total_lot_discount = request.form.get("number_total_lot_discount")
    subreference_active = request.form.get("subreference_active")

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

    # for llo in list_lots:
    #     print(llo)

    # print(unit_total_command)
    # return "holaaaaa"

    # suma_units_lot = 0
    # number_unit_lot = 0
    # Iterar sobre cada diccionario y sumar los valores de 'units_lot'
    # for diccionario in list_lots:
    #     suma_units_lot += int(diccionario.get('units_lot', 0))

    # Aqui el que fem es mirar si hi ha lots diferents i en cas afirmatiu agafem el total de la comanda i ho guardem en una diccionario,
    # farem servir la key de l'article perque sigui la key del diccioari i així poder-los vincular, en aquest diccionari tambe hi haura
    # el units que sera per saber quin es el numero unitari que hem de posar a cada article.
    dict_totals_reference = {}
    for l_lots in list_lots:
        if l_lots['key'] not in dict_totals_reference:
            dict_totals_reference[l_lots['key']] = l_lots['units_lot']
            dict_totals_reference[f"{l_lots['key']}_unit"] = 0
        else:
            dict_totals_reference[l_lots['key']] += l_lots['units_lot']

    # Iterem sobre la llista de lots, transformem el json a diccionari,
    # consultem si el lo que anem a inserir ja esta introduït
    # si es que si afegirem les unitats a l'stock.
    # Si no mirem si es fungible o reactiu, preparem les dades perque es pugin inserir, la part mes dificil es que si
    # es reactiu s'insereixen un linia per cada unitat i si es fungible una row amb el numero total d'unitas.
    list_info_excel = []
    subrefernce_count = 0
    for lots in list_lots:
        print(lots)
        # try:
        json_lots = json.dumps(lots)
        select_lot = session1.query(Stock_lots).filter_by(code_SAP=lots['code_SAP'], code_LOG=lots['code_LOG'], lot=lots['lot'], date_expiry=lots['date_expiry'], internal_lot=lots['internal_lot'], spent=0).first()
        if select_lot:
            if select_lot.react_or_fungible != 'Reactiu':
                select_lot.units_lot = int(select_lot.units_lot) + int(lots['units_lot'])
            else:
                return 'False_reactive'
            type_log = 'insert add stock'
            dict_info_excel = {'catalog_reference': lots['catalog_reference'],
                                'description': lots['description'],
                                'description_subreference': lots['description_subreference'],
                                'id_reactive': lots['id_reactive'],
                                'lot': lots['lot'],
                                'internal_lot_value': lots['internal_lot'],
                                'reception_date': lots['reception_date'],
                                'date_expiry': lots['date_expiry'],
                                'analytical_technique': lots['analytical_technique'],
                                'user_add_command': lots['user_add_command']}
            list_info_excel.append(dict_info_excel)
        else:
            type_log = 'insert new stock'

            if lots['react_or_fungible'] == 'Fungible':
                units_lots_reactive = 1
                unit_lot_value = lots['units_lot']
                temperature_value = ''

                # Com que és un fungible posarem la resta de fungibles a 0
                select_lots_ref = session1.query(Stock_lots).filter(
                    and_(
                        Stock_lots.catalog_reference == lots['catalog_reference'],
                        Stock_lots.spent == 0,
                        Stock_lots.react_or_fungible == 'Fungible'
                    )
                ).all()

                for select_lots_r in select_lots_ref:
                    select_lots_r.units_lot = 0
                    select_lots_r.spent = 1
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
                    # internal_lot_value = f"{lots['internal_lot']}_{number_unit_lot}/{lots['units_lot']}"
                    dict_totals_reference[f"{lots['key']}_unit"] += 1
                    unit_reactive = dict_totals_reference[f"{lots['key']}_unit"]
                    internal_lot_value = f"{lots['internal_lot']}_{unit_reactive}/{dict_totals_reference[lots['key']]}"

                # Si no han carregat certificat, comprobarem si ja tenim introduït un altre lot amb el mateixos camps i així podrem aprofitar el seu certificat ja que serà el mateix
                if filename_certificate == '':
                    select_lot_certificate = session1.query(Stock_lots).filter_by(catalog_reference=lots['catalog_reference'], lot=lots['lot'], id_reactive=lots['id_reactive']).first()
                    if select_lot_certificate is not None:
                        filename_certificate = select_lot_certificate.certificate
                        type_doc_certificate = select_lot_certificate.type_doc_certificate

                # Si són coriels el preu el posen directament i no es pot fer servir el que hi ha a l'article mare
                if isinstance(lots.get('description'), str) and 'coriel' in lots['description'].lower():
                    lots['import_unit_ics'] = price_coriells
                    lots['import_unit_idibgi'] = price_coriells

                # Mirem si el lot te subreferencies, si en te mirem cuantes d'elles aniran amb preu i quantes no, com que son subreferencies nomes una de cada lot pot anar amb preu, sino es contabilitzarien extra
                if subreference_active == 'True':
                    if int(number_total_lot_discount) > int(subrefernce_count):
                        ics_price_aux = lots['import_unit_ics']
                        idibgi_price_aux = lots['import_unit_idibgi']
                    else:
                        ics_price_aux = f"subref_{lots['import_unit_ics']}"
                        idibgi_price_aux = f"subref_{lots['import_unit_idibgi']}"
                    subrefernce_count += 1
                else:
                    ics_price_aux = lots['import_unit_ics']
                    idibgi_price_aux = lots['import_unit_idibgi']

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
                                        units_format=lots['units_format'],
                                        import_unit_ics=ics_price_aux,
                                        import_unit_idibgi=idibgi_price_aux,
                                        wrong_lots=lots['wrong_lots'],
                                        local_management=lots['local_management'],
                                        plataform_command_preferent=lots['plataform_command_preferent'],
                                        maximum_amount=lots['maximum_amount'],
                                        purchase_format_supplier=lots['purchase_format_supplier'],
                                        units_format_supplier=lots['units_format_supplier'],
                                        pb_oligos=pb_oligos)
                session1.add(insert_lot)

                dict_info_excel = {'catalog_reference': lots['catalog_reference'],
                                    'description': lots['description'],
                                    'description_subreference': lots['description_subreference'],
                                    'id_reactive': lots['id_reactive'],
                                    'lot': lots['lot'],
                                    'internal_lot_value': internal_lot_value,
                                    'reception_date': lots['reception_date'],
                                    'date_expiry': lots['date_expiry'],
                                    'analytical_technique': lots['analytical_technique'],
                                    'user_add_command': lots['user_add_command']}
                list_info_excel.append(dict_info_excel)

        select_lot = session1.query(Stock_lots).order_by(Stock_lots.id.desc()).first()
        info_lot = {'id_lot': select_lot.id,
                    'type': type_log,
                    'info': json_lots,
                    'user': session['acronim'],
                    'id_user': session['idClient'],
                    'date': date}
        save_log(info_lot)
        # except Exception:
        #     session1.rollback()
        #     return 'False_error'

    # Si id_substract_command es none voldra dir que nomes hi ha un lot a descontar i haurem de buscar el id de la comanda normalment,
    # si hi ha mes d'un lot l'usuari ja haura seleccionat de quin es i ja tindrem aquest pas fet.
    if id_substract_command == 'none':
        split_id_command = list_lots[0]['id_command'].split(';')
        id_substract_command = split_id_command[0]

    select_command = session1.query(Commands).filter(Commands.id == id_substract_command).first()
    if select_command:
        # total_received = int(select_command.num_received) + int(list_lots[0]['units_lot'])
        # Si el lot te subreferncies no es pot contabilitzar normalment ja que cada subrerferencia pot portar un numero difrents d'unitats,
        # així doncs em habilitat un camp on si es una subrefencia ens posaran les unitats que hem de descontar realment
        if subreference_active == "True":
            total_received = int(select_command.num_received) + int(number_total_lot_discount)
        else:
            total_received = int(select_command.num_received) + int(unit_total_command)
        select_command.num_received = total_received
        if incidence_number != '':
            if select_command.incidence_number == '' or select_command.incidence_number is None:
                select_command.incidence_number = incidence_number
            else:
                select_command.incidence_number += f"; {incidence_number}"

        if int(total_received) == int(select_command.units):
            message_command = f"S'ha rebut tot el contingut de la comanda {select_command.code_command}"
            select_command.received = 1
            select_command.date_complete = date
        elif int(total_received) > int(select_command.units):
            message_command = f"S'ha rebut més estock del que haviem demanat a la comanda {select_command.code_command}"
            select_command.received = 1
            select_command.date_complete = date
        elif int(total_received) < int(select_command.units):
            message_command = f"Stock guardat, encara falten productes per arribar de la comanda {select_command.code_command}"
    else:
        message_command = ''

    session1.commit()
    send_mail(list_info_excel)
    return f'True_{message_command}'
