from flask import render_template, request, flash, session
from app import app
from app.utils import requires_auth, list_desciption_lots
from app.models import session1, Stock_lots, Lot_consumptions
from sqlalchemy import func, or_
import json
from datetime import datetime


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
    select_lot = session1.query(Stock_lots, Lot_consumptions).\
        outerjoin(Lot_consumptions, Stock_lots.id == Lot_consumptions.id_lot).\
        filter(
        or_(
            func.lower(Stock_lots.catalog_reference) == reference.lower(),
            func.lower(Stock_lots.id_reactive) == reference.lower(),
            func.lower(Stock_lots.description) == reference.lower(),
            func.lower(Stock_lots.description_subreference) == reference.lower()
        ),
        Stock_lots.spent == 0,
        Stock_lots.react_or_fungible == 'Reactiu'
    ).all()

    if not select_lot:
        flash(f"No s'ha trobat cap coincidencia amb el codi entrat --> {reference}", "warning")
        return render_template('home.html', list_desciption_lots=list_desciption_lots())

    return render_template('open_close_lots.html', select_lot=select_lot, lot=select_lot[0],
                           list_desciption_lots=list_desciption_lots())


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
    observations = request.form.get("observations")
    date_open_close = request.form.get("date_open_close")
    num_lots_open = 0
    pos_close = -1
    message = ''
    str_id_lots = ''
    try:
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

        # date = instant_date()
        if action == 'open':
            if num_lots_open >= select_lots.units_lot:
                return "False_Tots els lots d'aquesta referència estan oberts."
            insert_consump = Lot_consumptions(id_lot=id_lot, date_open=date_open_close, user_open=session['acronim'],
                                              date_close='', observations_open=observations,  observations_close='')
            session1.add(insert_consump)
            if num_lots_open + 1 == 1:
                message = f"El lot s'ha obert correctament, tens {num_lots_open + 1} unitat oberta d'aquesta referència."
            else:
                message = f"El lot s'ha obert correctament, tens {num_lots_open + 1} unitats obertes d'aquesta referència."
        elif action == 'close':
            if num_lots_open > 0:
                date_open = select_consumptions[pos_close].date_open
                date_open = datetime.strptime(date_open, "%d-%m-%Y")
                date_closed = datetime.strptime(date_open_close, "%d-%m-%Y")
                if date_open > date_closed:
                    return f"False_La data de tancament -> {date_closed}, no pot ser abans que la data d'opertura -> {date_open}."

                select_consumptions[pos_close].date_close = date_open_close
                select_consumptions[pos_close].user_close = session['acronim']
                select_consumptions[pos_close].observations_close = observations
                select_lots.units_lot = select_lots.units_lot - 1
                message = "El lot s'ha tancat correctament"
                if select_lots.units_lot == 0:
                    select_group_lots = session1.query(Stock_lots).filter_by(group_insert=select_lots.group_insert).all()
                    sublot = 0
                    for lot_group in select_group_lots:
                        split_internal_lot = str(lot_group.internal_lot).split('_')
                        split_internal_lot_2 = str(select_lots.internal_lot).split('_')
                        if lot_group.id_reactive == select_lots.id_reactive and split_internal_lot[0] == split_internal_lot_2[0] and lot_group.units_lot > 0:
                            sublot += 1
                    if sublot == 0:
                        for lot_group in select_group_lots:
                            lot_group.spent = 1
                            str_id_lots += f'{lot_group.id};'
                            if lot_group.units_lot != 0:
                                select_lot_consumptions = session1.query(Lot_consumptions).filter_by(id_lot=lot_group.id, date_close='').all()
                                for lot_consumptions in select_lot_consumptions:
                                    lot_consumptions.date_close = date_open_close
                                    lot_consumptions.user_close = session['acronim']
                                lot_group.units_lot = lot_group.units_lot - len(select_lot_consumptions)
                        str_id_lots = str_id_lots[:-1]
                        message = f"El lot s'ha tancat correctament, Aquesta referència s'ha esgotat, ella i totes les subreferències han set posades com ha gastades._{str_id_lots}"
            else:
                return 'False_No es pot tancar cap lot amb aquesta referència, obre primer un lot.'
        session1.commit()
    except Exception:
        return "False_No s'ha pogut accedir a la BD, si l'error persisteix contacta amb un administrador."
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
            dict_consumption['observations_open'] = consumption.observations_open
            dict_consumption['date_close'] = consumption.date_close
            dict_consumption['user_close'] = consumption.user_close
            dict_consumption['observations_close'] = consumption.observations_close
            list_consumptions.append(dict_consumption)

        json_data = json.dumps(list_consumptions)
    except Exception:
        return "False_ No s'ha pogut accedir a la informació dels consums."

    return f'True_//_{json_data}'
