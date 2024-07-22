from flask import request, session, render_template, flash, send_file
from app import app
from app.utils import instant_date, requires_auth, create_excel, list_desciption_lots, list_cost_center
from app.models import session1, Lots, Commands, Cost_center, Stock_lots
from sqlalchemy import func
from config import main_dir_docs
import json
from datetime import datetime


@app.route('/search_add_command', methods=['POST'])
@requires_auth
def search_add_command():
    '''
        Busquem a la BD si el lot ja existeix.
        Si existeix agafem la informació necesaria i la enviem en un diccionari
        Si no existesix enviem una resposta per ajax avisan de que no tenim el lot registrat.

        :param str code_search: codi que hem de buscar a la BD

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    code_search = request.form.get("code_search")
    code_panel = request.form.get("code_panel")
    
    select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(Lots.active == 1).first()
    if not select_lot:
        select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).filter(Lots.active == 1).first()

    if not select_lot and code_panel != '':
        select_lot = session1.query(Lots).filter(func.lower(Lots.catalog_reference) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).filter(Lots.active == 1).all()
        if not select_lot:
            select_lot = session1.query(Lots).filter(func.lower(Lots.description) == code_search.lower()).filter(func.lower(Lots.code_panel) == code_panel.lower()).filter(Lots.active == 1).all()

    try:
        if not select_lot:
            return 'True_//_new'
        else:
            dict_lots = {'key': select_lot.key,
                         'catalog_reference': select_lot.catalog_reference,
                         'description': select_lot.description,
                         'description_subreference': select_lot.description_subreference,
                         'id_reactive': select_lot.id_reactive,
                         'code_SAP': select_lot.code_SAP,
                         'code_LOG': select_lot.code_LOG}
            json_data = json.dumps(dict_lots)
            return f'True_//_{json_data}'
    except Exception:
        return 'False_//_False'


@app.route('/add_command', methods=['POST'])
@requires_auth
def add_command():
    '''
        Recullim la informació, i com que es una comanda nova inserim la informació a la BD.
        Si el cost center es nou, s'insereix a la BD així les pròximes vegades sortira al llistat inicial.
        Comprobem que la comanda es de fungibles i si es així posarem l'stock dels producte que haguem fet comanda a 0


        :param str key_lot: Identificador únic del lot
        :param str units_command: Les unitats que s'han demanat a la comanda
        :param str cost_center: Nom del cost center
        :param str new_cost_center: Varibale amb un true o un false per saber si és un cost center nou o no.

        :function: instant_date()

        :return: json amb un True o un False i si es False una paraula amb el motiu.
        :rtype: json
    '''
    key_lot = request.form.get("key_lot")
    units_command = request.form.get("units_command")
    cost_center = request.form.get("cost_center")
    new_cost_center = request.form.get("new_cost_center")

    if new_cost_center == 'true':
        select_COCE = session1.query(Cost_center).filter(func.lower(Cost_center.name) == cost_center.lower()).first()
        if not select_COCE:
            insert_cost_center = Cost_center(name=cost_center)
            session1.add(insert_cost_center)
            session1.commit()

    date = instant_date()

    try:
        insert_command = Commands(id_lot=key_lot,
                                  units=units_command,
                                  date_create=date,
                                  user_create=session['acronim'],
                                  user_id_create=session['idClient'],
                                  date_close='',
                                  user_close='',
                                  user_id_close='',
                                  cost_center=cost_center,
                                  received=0,
                                  num_received=0,
                                  code_command='')
        session1.add(insert_command)

        select_stock_lot = session1.query(Stock_lots).filter_by(id_lot=key_lot, spent=0, react_or_fungible='Fungible').all()
        for stock in select_stock_lot:
            select_stock = session1.query(Stock_lots).filter_by(group_insert=stock.group_insert).all()
            for real_stock in select_stock:
                real_stock.spent = 1
    except Exception:
        session1.rollback()
        return 'False_error'
    session1.commit()
    return 'True'


@app.route('/search_commands')
@requires_auth
def search_commands():
    '''
        Buscarem a la BD totes les comandas que tenim pendents, les orden per ordre d'arribada i les enviarem a l'html

        :return: Llista d'objectes de les comanda i els lots corresponents
        :rtype: list objects
    '''
    select_commands = session1.query(Commands, Lots).join(Lots, Commands.id_lot == Lots.key)\
                                                    .filter(Commands.date_close == '')\
                                                    .order_by(Commands.id.desc()).all()
    # if not select_commands:
    #     flash("No hi han comandes pendents de tramitar", "warning")
    #     return render_template('home.html', list_desciption_lots=list_desciption_lots(),
    #                            list_cost_center=list_cost_center())

    return render_template('commands.html', select_commands=select_commands)


@app.route('/delete_command', methods=['POST'])
@requires_auth
def delete_command():
    '''
        Recullim la informació i eliminem la comanda amb l'id que ens proporcionen

        :param str id_command: Identificador únic del la comanda

        :function: instant_date()

        :return: json amb un True o un False.
        :rtype: json
    '''
    str_ids_commands = request.form.get("list_ids_commands")
    list_ids_commands = str_ids_commands.split(',')

    date = instant_date()

    date_now = datetime.now()
    code_command = date_now.strftime("%Y%m%d")

    # Comprobem que no s'haji fet cap altre peticio aquell dia, si es així posarem el _2 o el que toco per distingir les comandes.
    select_command_code = session1.query(Commands).filter(Commands.code_command == code_command).first()
    if select_command_code is not None:
        for i in range(2, 20):
            code_command_aux = f'{code_command}_{i}'
            select_command_code_aux = session1.query(Commands).filter(Commands.code_command == code_command_aux).first()
            if select_command_code_aux is None:
                code_command = code_command_aux
                break
    try:
        for id_command in list_ids_commands:
            select_command = session1.query(Commands).filter(Commands.id == id_command).first()
            select_command.date_close = date
            select_command.user_close = session['acronim']
            select_command.user_id_close = session['idClient']
            select_command.code_command = code_command
    except Exception:
        session1.rollback()
        return 'False'
    session1.commit()
    return 'True'


@app.route('/command_success', methods=['POST'])
@requires_auth
def command_success():
    '''
        Obté una llista de comandes tancades i les retorna en format JSON.

        Aquesta funció realitza una consulta a la base de dades per obtenir les comandes tancades associades a lots. 
        Si no es troben comandes, retorna un missatge d'error. Si es troben, crea una llista de diccionaris amb la informació 
        rellevant de cada comanda i lot, i retorna aquesta informació en format JSON.

        :return: Un missatge que indica si l'operació ha estat exitosa i, en cas afirmatiu, la informació en format JSON.
        :rtype: str
    '''
    select_command = session1.query(Commands, Lots).join(Lots, Commands.id_lot == Lots.key)\
                                                   .filter(Commands.user_close != '').all()
    if not select_command:
        return "False_//_No s'ha trobat cap comanda tramitada a l'historic"

    list_commands = []
    for command, lot in select_command:
        dict_commands = {'id': command.id,
                         'id_lot': command.id_lot,
                         'catalog_reference': lot.catalog_reference,
                         'description': lot.description,
                         'code_command': command.code_command,
                         #  'id_reactive': lot.id_reactive,
                         #  'description_subreference': lot.description_subreference,
                         'code_SAP': lot.code_SAP,
                         'code_LOG': lot.code_LOG,
                         'units': command.units,
                         # 'date_create': command.date_create,
                         # 'user_create': command.user_create,
                         'date_close': command.date_close,
                         'user_close': command.user_close,
                         'cost_center': command.cost_center}

        list_commands.append(dict_commands)

        json_info_commands = json.dumps(list_commands)

    return f'True_//_{json_info_commands}'


@app.route('/download_excel', methods=['POST'])
@requires_auth
def download_excel():
    '''
        Busquem totes les comandes pendents i creem l'excel.
        Si tot ha anat be farem que l'usuari es descarregui l'excel si no mostrarem un missatge d'error
    '''
    select_commands = session1.query(Commands, Lots).join(Lots, Commands.id_lot == Lots.key)\
                                                    .filter(Commands.date_close == '').all()

    success = create_excel(select_commands)
    if not success:
        flash("Error, no s'ha pogut crear el document", "danger")
        return render_template('home.html')
    else:
        path = f"{main_dir_docs}/comandes_pendents.csv"
        return send_file(path, as_attachment=True)
