from flask import render_template, request, redirect, session, flash, jsonify
from app import app
from app.utils import requires_auth, list_desciption_lots, list_cost_center, to_dict
from app.models import IP_HOME, session1, Lots, Stock_lots, Lot_consumptions
import jwt
import json
from sqlalchemy import and_, or_, outerjoin
from datetime import datetime
from config import main_dir
import pandas as pd


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
        select_lots = session1.query(Lots).all()
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
            dict_lots['info_article'] = f"{lot.key}/-/{lot.catalog_reference}/-/{lot.manufacturer}/-/{lot.description}/-/{lot.analytical_technique}/-/{lot.reference_units}/-/{lot.id_reactive}/-/{lot.code_SAP}/-/{lot.code_LOG}/-/{lot.active}/-/{lot.temp_conservation}/-/{lot.description_subreference}/-/{lot.react_or_fungible}/-/{lot.code_panel}/-/{lot.location}/-/{lot.supplier}/-/{lot.purchase_format}/-/{lot.units_format}/-/{lot.import_unit_ics}/-/{lot.import_unit_idibgi}/-/{lot.local_management}/-/{lot.plataform_command_preferent}/-/{lot.maximum_amount}/-/{lot.purchase_format_supplier}/-/{lot.units_format_supplier}"
            dict_lots['description'] = lot.description
            dict_lots['description_subreference'] = lot.description_subreference
            dict_lots['active'] = lot.active
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
        Realitza una cerca de lots fungibles basant-se en un codi introduït pel usuari.

        Aquesta funció utilitza el codi introduït per buscar lots fungibles en la base de dades. Primer cerca per la descripció 
        del lot, després cerca per la referència del catàleg, el codi SAP i el codi LOG si no es troben resultats inicials. 
        Si no es troben lots que coincideixin amb el codi, mostra un missatge d'advertència. Si ocorre un error durant la cerca, 
        mostra un missatge d'error.

        :param request: L'objecte de sol·licitud que conté el codi de cerca introduït pel usuari.
        :type request: flask.Request

        :return: Renderitza la plantilla `search_fungible.html` amb els lots seleccionats si la cerca té èxit, 
                o la plantilla `home.html` amb missatges d'advertència o error si no es troben lots o ocorre un error.
        :rtype: flask.Response
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


@app.route('/search_all_year', methods=['POST'])
@requires_auth
def search_all_year():
    '''
        Realitza una cerca de lots basant-se en un codi de cerca i la data de recepció de l'any actual.

        Aquesta funció busca lots en la base de dades utilitzant el codi de cerca proporcionat i l'any actual com a criteris.
        Primer busca per centre de cost, després per referència del catàleg, codi SAP, i finalment per la data de recepció
        si no es troben resultats. Si no es troben lots amb el codi introduït, retorna un missatge indicant que no s'ha trobat
        stock. Si ocorre un error durant la cerca, retorna un missatge d'error.

        :param request: L'objecte de sol·licitud que conté el codi de cerca introduït pel usuari.
        :type request: flask.Request

        :return: Una cadena amb el resultat de la cerca. Si la cerca és exitosa, retorna `True_//_{list_info_stock}` amb
                la informació del stock en format JSON. Si no es troben lots o ocorre un error, retorna un missatge d'error
                amb el prefix `False_//_`.
        :rtype: str
    '''
    search_data_code = request.form['search_data_code']

    date = datetime.now()
    year = date.strftime("-%Y")
    list_year = [year, int(year)+1, int(year)+2, int(year)+3, int(year)+4]
    print(year)
    print(list_year)
    # try:
    if search_data_code == '':
        return 'False_//_Es codi no pot estar buit.'
    else:
        # select_lots = session1.query(Stock_lots).filter(and_(Stock_lots.cost_center_stock == search_data_code,
        #                                                      or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year]))).all()
        # if not select_lots:
        #     select_lots = session1.query(Stock_lots).filter(and_(Stock_lots.catalog_reference == search_data_code,
        #                                                          or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year]))).all()
        # if not select_lots:
        #     select_lots = session1.query(Stock_lots).filter(and_(Stock_lots.code_SAP == search_data_code,
        #                                                          or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year]))).all()
        # if not select_lots:
        #     search_data_code = search_data_code.replace('/', '-')
        #     select_lots = session1.query(Stock_lots).filter(Stock_lots.reception_date == search_data_code).all()

        # 1r intent
        select_lots = session1.query(Stock_lots, Lot_consumptions).\
            outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id).\
            filter(
                and_(
                    Stock_lots.cost_center_stock == search_data_code,
                    or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year])
                )
            ).all()

        # 2n intent
        if not select_lots:
            select_lots = session1.query(Stock_lots, Lot_consumptions).\
                outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id).\
                filter(
                    and_(
                        Stock_lots.catalog_reference == search_data_code,
                        or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year])
                    )
                ).all()

        # 3r intent
        if not select_lots:
            select_lots = session1.query(Stock_lots, Lot_consumptions).\
                outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id).\
                filter(
                    and_(
                        Stock_lots.code_SAP == search_data_code,
                        or_(*[Stock_lots.reception_date.like(f'%{year}%') for year in list_year])
                    )
                ).all()

        # 4t intent
        if not select_lots:
            search_data_code = search_data_code.replace('/', '-')
            select_lots = session1.query(Stock_lots, Lot_consumptions).\
                outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id).\
                filter(Stock_lots.reception_date == search_data_code).all()

    if not select_lots:
        return f"False_//_No s'ha trobat stock amb el codi {search_data_code}"
    else:
        list_info_stock_aux = [
            {
                **to_dict(stock),
                **(to_dict(consumption) if consumption else {})  # si no hi ha consumption, afegeix dict buit
            } for stock, consumption in select_lots
        ]
        list_info_stock = json.dumps(list_info_stock_aux)
    # except Exception:
    #     return "False_//_Error, no s'ha pout realitzar la cerca"

    return f'True_//_{list_info_stock}'


@app.route('/search_all_lots', methods=['POST'])
@requires_auth
def search_all_lots():
    '''
        1 - Recollim la informació de l'html
        2 - Busquem a la BD amb la informació que ens han facilitat
        2.1 - Si no es troba coincidència retornem un missatge d'error a l'html
        2.2 - Si es troba coincidència retornarem el que hem trobat a l'html.

        :param str search_code: Codi a buscar.

        :return: La informació dels lots trobada i un int que és l'id de lot.
        :rtype: render_template, object, int
    '''
    select_lot = session1.query(Stock_lots).group_by(Stock_lots.lot, Stock_lots.reception_date).all()

    if not select_lot:
        flash(f"Error, no hem trobat informació a la BD", "warning")
        return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                               list_cost_center=list_cost_center())

    return render_template('search_lot.html', select_lot=select_lot, show_second_bar='')


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


'''@app.route('/add_samples_for_excel')
@requires_auth
def add_samples_for_excel():
    # directori = f'{main_dir}/doc_nuria_articles_unics.xlsx'
    # directori = f'{main_dir}/doc_nuria_all.xlsx'
    # df = pd.read_excel(directori)
    # df = pd.read_excel(directori, header=None)
    # list_excel = df.values.tolist()
    # print("inici del documenttttt")
    # list = []
    # list_dupl = []
    # for line in range(1, len(list_excel)):
    #     if str(list_excel[line][2]).rstrip() not in list:
    #             list.append(str(list_excel[line][2]))
        # if list_excel[line][11] == 'SI':
        #     # Esto ha sido para seleccionar los que tiene subreferencias i hacer-les un update de los datos conjuntos
        #     # select_lot = session1.query(Lots).filter(Lots.catalog_reference == str(list_excel[line][2]).rstrip()).all()
        #     # if select_lot:

        #     select_lot = session1.query(Lots).filter(Lots.catalog_reference == str(list_excel[line][2]).rstrip()).first()
        #     if select_lot is not None:
        #         # print(f"El lot {list_excel[line][2]} ja esta introduit, -> {select_lot.key}")
        #         for select in select_lot:
        #             select.manufacturer = list_excel[line][23]
        #             select.description = list_excel[line][1]
        #             select.analytical_technique = list_excel[line][0]
        #             select.reference_units = 1
        #             select.id_reactive = ''
        #             select.code_SAP = list_excel[line][4]
        #             select.code_LOG = list_excel[line][3]
        #             select.active = 1
        #             select.temp_conservation = list_excel[line][13]
        #             select.description_subreference = ''
        #             select.react_or_fungible = list_excel[line][10]
        #             select.location = list_excel[line][14]
        #             select.supplier = list_excel[line][20]
        #             select.purchase_format = list_excel[line][9]
        #             select.units_format = list_excel[line][8]
        #             select.import_unit_ics = list_excel[line][21]
        #             select.import_unit_idibgi = list_excel[line][22]
        #             select.local_management = list_excel[line][7]
        #             select.plataform_command_preferent = list_excel[line][5]
        #             select.maximum_amount = list_excel[line][19]
        #             select.purchase_format_supplier = list_excel[line][16]
        #             select.units_format_supplier = list_excel[line][15]
        #         session1.commit()
        #     else:
        #         print("ha entrat a noussssssssssssssssssssssssssssssss")
        #         for i in range(list_excel[line][12]):
        #             insert_lot = Lots(catalog_reference=str(list_excel[line][2]).rstrip(),
        #                               manufacturer=list_excel[line][23],
        #                               description=list_excel[line][1],
        #                               analytical_technique=list_excel[line][0],
        #                               reference_units=1,
        #                               id_reactive='',
        #                               code_SAP=list_excel[line][4],
        #                               code_LOG=list_excel[line][3],
        #                               active=1,
        #                               temp_conservation=list_excel[line][13],
        #                               description_subreference='',
        #                               react_or_fungible=list_excel[line][10],
        #                               code_panel='',
        #                               location=list_excel[line][14],
        #                               supplier=list_excel[line][20],
        #                               purchase_format=list_excel[line][9],
        #                               units_format=list_excel[line][8],
        #                               import_unit_ics=list_excel[line][21],
        #                               import_unit_idibgi=list_excel[line][22],
        #                               local_management=list_excel[line][7],
        #                               plataform_command_preferent=list_excel[line][5],
        #                               maximum_amount=list_excel[line][19],
        #                               purchase_format_supplier=list_excel[line][16],
        #                               units_format_supplier=list_excel[line][15]
        #             )

        #             session1.add(insert_lot)
        #         session1.commit()
        # else:
        #     # aixo es per saber quins tenia duplicats a l'excel
        #     # if str(list_excel[line][2]).rstrip() not in list:
        #     #     list.append(str(list_excel[line][2]).rstrip())
        #     # else:
        #     #     if str(list_excel[line][2]).rstrip() not in list_dupl:
        #     #         list_dupl.append(str(list_excel[line][2]).rstrip())

        #     # Aqui inserirem o actualitzarem la info
        #     select_lot = session1.query(Lots).filter(Lots.catalog_reference == str(list_excel[line][2]).rstrip()).all()
        #     if select_lot:
        #         if len(select_lot) > 1:
        #             print(f"El lot {list_excel[line][2]} se nan trobat 2")
        #         else:
        #             for select in select_lot:
        #                 select.manufacturer = list_excel[line][23]
        #                 select.description = list_excel[line][1]
        #                 select.analytical_technique = list_excel[line][0]
        #                 select.reference_units = 1
        #                 select.id_reactive = ''
        #                 select.code_SAP = list_excel[line][4]
        #                 select.code_LOG = list_excel[line][3]
        #                 select.active = 1
        #                 select.temp_conservation = list_excel[line][13]
        #                 select.description_subreference = ''
        #                 select.react_or_fungible = list_excel[line][10]
        #                 select.location = list_excel[line][14]
        #                 select.supplier = list_excel[line][20]
        #                 select.purchase_format = list_excel[line][9]
        #                 select.units_format = list_excel[line][8]
        #                 select.import_unit_ics = list_excel[line][21]
        #                 select.import_unit_idibgi = list_excel[line][22]
        #                 select.local_management = list_excel[line][7]
        #                 select.plataform_command_preferent = list_excel[line][5]
        #                 select.maximum_amount = list_excel[line][19]
        #                 select.purchase_format_supplier = list_excel[line][16]
        #                 select.units_format_supplier = list_excel[line][15]
        #             session1.commit()
        #     else:
        #         print("ha entrat a noussssssssssssssssssssssssssssssss")
        #         insert_lot = Lots(catalog_reference=str(list_excel[line][2]).rstrip(),
        #                           manufacturer=list_excel[line][23],
        #                           description=list_excel[line][1],
        #                           analytical_technique=list_excel[line][0],
        #                           reference_units=1,
        #                           id_reactive='',
        #                           code_SAP=list_excel[line][4],
        #                           code_LOG=list_excel[line][3],
        #                           active=1,
        #                           temp_conservation=list_excel[line][13],
        #                           description_subreference='',
        #                           react_or_fungible=list_excel[line][10],
        #                           code_panel='',
        #                           location=list_excel[line][14],
        #                           supplier=list_excel[line][20],
        #                           purchase_format=list_excel[line][9],
        #                           units_format=list_excel[line][8],
        #                           import_unit_ics=list_excel[line][21],
        #                           import_unit_idibgi=list_excel[line][22],
        #                           local_management=list_excel[line][7],
        #                           plataform_command_preferent=list_excel[line][5],
        #                           maximum_amount=list_excel[line][19],
        #                           purchase_format_supplier=list_excel[line][16],
        #                           units_format_supplier=list_excel[line][15])
        #         session1.add(insert_lot)
        #         session1.commit()

    # select_lot = session1.query(Lots).all()
    # for lot in select_lot:
    #     if lot.catalog_reference not in list:
    #         if lot.catalog_reference not in list_dupl:
    #             list_dupl.append(lot.catalog_reference)

    select = session1.query(Stock_lots).all()s

    return "fet" '''
