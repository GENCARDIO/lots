from flask import request, session
from app import app
from app.utils import instant_date, requires_auth, save_log
from app.models import session1, Lots, Stock_lots
import json


@app.route('/edit_lot', methods=['POST'])
@requires_auth
def edit_lot():
    '''
        1 - Recollim la informació que pot haver modificat l'usuari.
        2 - Comprovem que l'id_lot sigui correcte i agafem el lot de la BD.
        2.1 - Si no podem agafar el lot de la BD, retornarem un missatge d'error a l'HTML.
        3 - Agafem la data actual i la guardem a la variable date.
        4 - Creem un diccionari per si alguna variable ha canviat, poder guardar el canvi a la BD dels lots.
        5 - Omplim el diccionari amb les dades comunes.
        6 - Comprovem que la dada que ens arriba sigui igual que la que tenim a la BD.
        6.1 - Si és igual, no es fa res.
        6.2 - Si no és igual, creem un diccionari amb el camp modificat, el contingut nou i el vell.
        6.3 - Guardem la nova informació a la BD.
        6.4 - Convertim el diccionari que hem creat al pas 6.2 en un JSON i afegim aquesta informació al diccionari general.
        6.5 - Guardem la informació a la BD dels logs.
        7 - Mirem si d'aquest lot teníem estoc i modifiquem la informació dels lots en estoc que faci falta.
        8 - Es guardarà un log amb els IDs dels lots en estoc que s'hagin modificat.
        9 - Retornem True o False amb un missatge per a l'usuari via AJAX.

        :param str id_lot: Identificador únic del lot.
        :param str reference_catalog: Referència del proveïdor.
        :param str manufacturer: Nom del fabricant.
        :param str description: Descripció del lot.
        :param str analytical_technique: Nom de la tècnica que es fa servir.
        :param str id_reactive: Identificador del reactiu.
        :param str code_sap: Codi SAP del lot.
        :param str code_log: Codi LOG del lot.
        :param str active: Si el producte està actiu o no.
        :param str temp_conservation: Temperatura a la qual es guardarà el producte.
        :param str description_subref: Descripció de la subreferència.
        :param str react_or_fungible: Si és un reactiu o un fungible.
        :param str code_panel: Si és un panell, tindrà un codi de panell.
        :param str location: On es guarda del laboratori.
        :param str supplier: Nom del proveïdor.

        :funciotn: instant_date()
        :funciotn: save_log(dict)

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    id_lot = request.form.get("id_lot")
    reference_catalog = request.form.get("reference_catalog")
    manufacturer = request.form.get("manufacturer")
    description = request.form.get("description")
    analytical_technique = request.form.get("analytical_technique")
    id_reactive = request.form.get("id_reactive")
    code_sap = request.form.get("code_sap")
    code_log = request.form.get("code_log")
    active = request.form.get("active")
    temp_conservation = request.form.get("temp_conservation")
    description_subref = request.form.get("description_subref")
    react_or_fungible = request.form.get("react_or_fungible")
    code_panel = request.form.get("code_panel")
    location = request.form.get("location")
    supplier = request.form.get("supplier")

    select_lot = session1.query(Lots).filter(Lots.key == id_lot).first()

    try:
        if not select_lot:
            return "False_//_No hem trobat l'article a la BD"
        else:
            change_confirmed = False
            date = instant_date()
            dict_save_info = {'id_lot': id_lot,
                              'type': 'edit',
                              'user': session['acronim'],
                              'id_user': session['idClient'],
                              'date': date}

            if select_lot.catalog_reference != reference_catalog:
                info_change = {"field": 'catalog_reference', "old_info": select_lot.catalog_reference, "new_info": reference_catalog}
                select_lot.catalog_reference = reference_catalog
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.manufacturer != manufacturer:
                info_change = {"field": 'manufacturer', "old_info": select_lot.manufacturer, "new_info": manufacturer}
                select_lot.manufacturer = manufacturer
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.description != description:
                info_change = {"field": 'description', "old_info": select_lot.description, "new_info": description}
                select_lot.description = description
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.analytical_technique != analytical_technique:
                info_change = {"field": 'analytical_technique', "old_info": select_lot.analytical_technique, "new_info": analytical_technique}
                select_lot.analytical_technique = analytical_technique
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.id_reactive != id_reactive:
                info_change = {"field": 'id_reactive', "old_info": select_lot.id_reactive, "new_info": id_reactive}
                select_lot.id_reactive = id_reactive
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.catalog_reference != code_sap:
                info_change = {"field": 'code_SAP', "old_info": select_lot.code_SAP, "new_info": code_sap}
                select_lot.catalog_reference = code_sap
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.code_LOG != code_log:
                info_change = {"field": 'code_LOG', "old_info": select_lot.code_LOG, "new_info": code_log}
                select_lot.code_LOG = code_log
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.active != str(active):
                info_change = {"field": 'active', "old_info": select_lot.active, "new_info": active}
                select_lot.active = active
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.temp_conservation != temp_conservation:
                info_change = {"field": 'temp_conservation', "old_info": select_lot.temp_conservation, "new_info": temp_conservation}
                select_lot.temp_conservation = temp_conservation
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.description_subreference != description_subref:
                info_change = {"field": 'description_subref', "old_info": select_lot.description_subreference, "new_info": description_subref}
                select_lot.description_subreference = description_subref
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.react_or_fungible != react_or_fungible:
                info_change = {"field": 'react_or_fungible', "old_info": select_lot.react_or_fungible, "new_info": react_or_fungible}
                select_lot.react_or_fungible = react_or_fungible
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.code_panel != code_panel:
                info_change = {"field": 'code_panel', "old_info": select_lot.code_panel, "new_info": code_panel}
                select_lot.code_panel = code_panel
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.location != location:
                info_change = {"field": 'location', "old_info": select_lot.location, "new_info": location}
                select_lot.location = location
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.supplier != supplier:
                info_change = {"field": 'supplier', "old_info": select_lot.supplier, "new_info": supplier}
                select_lot.supplier = supplier
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if not change_confirmed:
                return "False_//_No has fet cap canvi respecte l'original."

            # Si es fan canvis al lot s'han de reflexa a l'stock.
            select_stock_lot = session1.query(Stock_lots).filter(Stock_lots.id_lot == id_lot).all()
            if len(select_stock_lot) > 0:
                id_stock_lots_change = ''
                for lot_stock in select_stock_lot:
                    id_stock_lots_change += f'{lot_stock.id}; '
                    if lot_stock.catalog_reference != reference_catalog:
                        lot_stock.catalog_reference = reference_catalog

                    if lot_stock.manufacturer != manufacturer:
                        lot_stock.manufacturer = manufacturer

                    if lot_stock.description != description:
                        lot_stock.description = description

                    if lot_stock.analytical_technique != analytical_technique:
                        lot_stock.analytical_technique = analytical_technique

                    if lot_stock.id_reactive != id_reactive:
                        lot_stock.id_reactive = id_reactive

                    if lot_stock.code_SAP != code_sap:
                        lot_stock.code_SAP = code_sap

                    if lot_stock.code_LOG != code_log:
                        lot_stock.code_LOG = code_log

                    if lot_stock.temp_conservation != temp_conservation:
                        lot_stock.temp_conservation = temp_conservation

                    if lot_stock.description_subreference != description_subref:
                        lot_stock.description_subreference = description_subref

                    if lot_stock.react_or_fungible != react_or_fungible:
                        lot_stock.react_or_fungible = react_or_fungible

                    if lot_stock.code_panel != code_panel:
                        lot_stock.code_panel = code_panel

                    if lot_stock.location != location:
                        lot_stock.location = location

                    if lot_stock.supplier != supplier:
                        lot_stock.supplier = supplier

                if len(id_stock_lots_change) > 2:
                    id_stock_lots_change = id_stock_lots_change[:-2]

                info_change = {"field": 'BD stock_lots', "old_info": 'ids que s han modidifica per el canvi a lots', "new_info": id_stock_lots_change}
                dict_save_info['id_lot'] = '0'
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)

            session1.commit()

            return "True_//_Els canvis s'han realitzat correctament"
    except Exception:
        return "False_//_Error a l'inserir l'article a la BD"


@app.route('/delete_lot', methods=['POST'])
@requires_auth
def delete_lot():
    '''
        1 - Recollim la informació que pot haver modificat l'usuari.
        2 - Comprovem que l'id_lot sigui correcte i agafem el lot de la BD.
        2.1 - Si no podem agafar el lot de la BD, retornarem un missatge d'error a l'HTML.
        3 - Agafem la data actual i la guardem a la variable date.
        4 - Creem un diccionari per si alguna variable ha canviat, poder guardar el canvi a la BD dels lots.
        5 - Omplim el diccionari amb les dades comunes.
        6 - Comprovem que la dada que ens arriba sigui igual que la que tenim a la BD.
        6.1 - Si és igual, no es fa res.
        6.2 - Si no és igual, creem un diccionari amb el camp modificat, el contingut nou i el vell.
        6.3 - Guardem la nova informació a la BD.
        6.4 - Convertim el diccionari que hem creat al pas 6.2 en un JSON i afegim aquesta informació al diccionari general.
        6.5 - Guardem la informació a la BD dels logs.
        7 - Mirem si d'aquest lot teníem estoc i modifiquem la informació dels lots en estoc que faci falta.
        8 - Es guardarà un log amb els IDs dels lots en estoc que s'hagin modificat.
        9 - Retornem True o False amb un missatge per a l'usuari via AJAX.

        :param str id_lot: Identificador únic del lot.
        :param str reference_catalog: Referència del proveïdor.
        :param str manufacturer: Nom del fabricant.
        :param str description: Descripció del lot.
        :param str analytical_technique: Nom de la tècnica que es fa servir.
        :param str id_reactive: Identificador del reactiu.
        :param str code_sap: Codi SAP del lot.
        :param str code_log: Codi LOG del lot.
        :param str active: Si el producte està actiu o no.
        :param str temp_conservation: Temperatura a la qual es guardarà el producte.
        :param str description_subref: Descripció de la subreferència.
        :param str react_or_fungible: Si és un reactiu o un fungible.
        :param str code_panel: Si és un panell, tindrà un codi de panell.
        :param str location: On es guarda del laboratori.
        :param str supplier: Nom del proveïdor.

        :funciotn: instant_date()
        :funciotn: save_log(dict)

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    id_lot = request.form.get("id_lot")

    select_lot = session1.query(Lots).filter(Lots.key == id_lot).first()

    try:
        if not select_lot:
            return "False_//_No hem trobat l'article a la BD"
        else:
            date = instant_date()

            dict_info_lot = {"key": select_lot.key,
                             "catalog_reference": select_lot.catalog_reference,
                             "manufacturer": select_lot.manufacturer,
                             "description": select_lot.description,
                             "analytical_technique": select_lot.analytical_technique,
                             "reference_units": select_lot.reference_units,
                             "id_reactive": select_lot.id_reactive,
                             "code_SAP": select_lot.code_SAP,
                             "code_LOG": select_lot.code_LOG,
                             "active": select_lot.active,
                             "temp_conservation": select_lot.temp_conservation,
                             "description_subreference": select_lot.description_subreference,
                             "react_or_fungible": select_lot.react_or_fungible,
                             "code_panel": select_lot.code_panel,
                             "location": select_lot.location,
                             "supplier": select_lot.supplier }

            dict_save_info = {'id_lot': id_lot,
                              'type': 'delete',
                              'user': session['acronim'],
                              'id_user': session['idClient'],
                              'date': date,
                              'info': json.dumps(dict_info_lot)}

            save_log(dict_save_info)

            # Si es fan canvis al lot s'han de reflexa a l'stock.
            # select_stock_lot = session1.query(Stock_lots).filter(Stock_lots.id_lot == id_lot).all()
            # if len(select_stock_lot) > 0:
            #     id_stock_lots_change = ''
            #     for lot_stock in select_stock_lot:
            #         lot_stock.spent = '0'

            session1.commit()

            return "True_//_L'article s'ha eliminat correctament"
    except Exception:
        return "False_//_Error en eliminar l'article a la BD"


@app.route('/modify_reactive', methods=['POST'])
@requires_auth
def modify_reactive():
    '''
        1 - Recollim la informació que pot haver modificat l'usuari.
        2 - Comprovem que l'id_lot sigui correcte i agafem el lot de la BD.
        2.1 - Si no podem agafar el lot de la BD, retornarem un missatge d'error a l'HTML.
        3 - Agafem la data actual i la guardem a la variable date.
        4 - Creem un diccionari per si alguna variable ha canviat, poder guardar el canvi a la BD dels lots.
        5 - Omplim el diccionari amb les dades comunes.
        6 - Comprovem que la dada que ens arriba sigui igual que la que tenim a la BD.
        6.1 - Si és igual, no es fa res.
        6.2 - Si no és igual, creem un diccionari amb el camp modificat, el contingut nou i el vell.
        6.3 - Guardem la nova informació a la BD.
        6.4 - Convertim el diccionari que hem creat al pas 6.2 en un JSON i afegim aquesta informació al diccionari general.
        6.5 - Guardem la informació a la BD dels logs.
        7 - Mirem si d'aquest lot teníem estoc i modifiquem la informació dels lots en estoc que faci falta.
        8 - Es guardarà un log amb els IDs dels lots en estoc que s'hagin modificat.
        9 - Retornem True o False amb un missatge per a l'usuari via AJAX.

        :param str id_lot: Identificador únic del lot.
        :param str reference_catalog: Referència del proveïdor.
        :param str manufacturer: Nom del fabricant.
        :param str description: Descripció del lot.
        :param str analytical_technique: Nom de la tècnica que es fa servir.
        :param str id_reactive: Identificador del reactiu.
        :param str code_sap: Codi SAP del lot.
        :param str code_log: Codi LOG del lot.
        :param str active: Si el producte està actiu o no.
        :param str temp_conservation: Temperatura a la qual es guardarà el producte.
        :param str description_subref: Descripció de la subreferència.
        :param str react_or_fungible: Si és un reactiu o un fungible.
        :param str code_panel: Si és un panell, tindrà un codi de panell.
        :param str location: On es guarda del laboratori.
        :param str supplier: Nom del proveïdor.

        :funciotn: instant_date()
        :funciotn: save_log(dict)

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    date_expiry_modify = request.form.get("date_expiry_modify")
    lot_reactive_modify = request.form.get("lot_reactive_modify")
    id_lot_modify = request.form.get("id_lot_modify")

    select_lot = session1.query(Stock_lots).filter(Stock_lots.id == id_lot_modify).first()

    try:
        if not select_lot:
            return "False_//_No hem trobat l'article a la BD"
        else:
            change_confirmed = False
            date = instant_date()
            dict_save_info = {'id_lot': id_lot_modify,
                              'type': 'edit',
                              'user': session['acronim'],
                              'id_user': session['idClient'],
                              'date': date}

            if select_lot.date_expiry != date_expiry_modify:
                info_change = {"field": 'Stok_lots - date_expiry', "old_info": select_lot.date_expiry, "new_info": date_expiry_modify}
                select_lot.date_expiry = date_expiry_modify
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if select_lot.lot != lot_reactive_modify:
                info_change = {"field": 'Stock_lot - lot', "old_info": select_lot.lot, "new_info": lot_reactive_modify}
                select_lot.lot = lot_reactive_modify
                dict_save_info['info'] = json.dumps(info_change)
                save_log(dict_save_info)
                change_confirmed = True

            if not change_confirmed:
                return "False_//_No has fet cap canvi respecte l'original."

            # Si es fan canvis al lot s'han de reflexa a l'stock.
            # select_stock_lot = session1.query(Stock_lots).filter(Stock_lots.id_lot == id_lot).all()
            # if len(select_stock_lot) > 0:
            #     id_stock_lots_change = ''
            #     for lot_stock in select_stock_lot:
            #         id_stock_lots_change += f'{lot_stock.id}; '
            #         if lot_stock.catalog_reference != reference_catalog:
            #             lot_stock.catalog_reference = reference_catalog

            #         if lot_stock.manufacturer != manufacturer:
            #             lot_stock.manufacturer = manufacturer

            #         if lot_stock.description != description:
            #             lot_stock.description = description

            #         if lot_stock.analytical_technique != analytical_technique:
            #             lot_stock.analytical_technique = analytical_technique

            #         if lot_stock.id_reactive != id_reactive:
            #             lot_stock.id_reactive = id_reactive

            #         if lot_stock.code_SAP != code_sap:
            #             lot_stock.code_SAP = code_sap

            #         if lot_stock.code_LOG != code_log:
            #             lot_stock.code_LOG = code_log

            #         if lot_stock.temp_conservation != temp_conservation:
            #             lot_stock.temp_conservation = temp_conservation

            #         if lot_stock.description_subreference != description_subref:
            #             lot_stock.description_subreference = description_subref

            #         if lot_stock.react_or_fungible != react_or_fungible:
            #             lot_stock.react_or_fungible = react_or_fungible

            #         if lot_stock.code_panel != code_panel:
            #             lot_stock.code_panel = code_panel

            #         if lot_stock.location != location:
            #             lot_stock.location = location

            #         if lot_stock.supplier != supplier:
            #             lot_stock.supplier = supplier

            #     if len(id_stock_lots_change) > 2:
            #         id_stock_lots_change = id_stock_lots_change[:-2]

            #     info_change = {"field": 'BD stock_lots', "old_info": 'ids que s han modidifica per el canvi a lots', "new_info": id_stock_lots_change}
            #     dict_save_info['id_lot'] = '0'
            #     dict_save_info['info'] = json.dumps(info_change)
            #     save_log(dict_save_info)

            session1.commit()

            return "True_//_Els canvis s'han realitzat correctament"
    except Exception:
        return "False_//_Error a l'inserir l'article a la BD"
