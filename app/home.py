from flask import render_template, request, redirect, session, flash, jsonify, send_file
from app import app
from app.utils import requires_auth, list_desciption_lots, list_cost_center, to_dict, save_log
from app.models import IP_HOME, session1, Lots, Stock_lots, Lot_consumptions
import jwt
import json
from sqlalchemy import and_, or_, outerjoin
from datetime import datetime
from config import main_dir
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from config import main_dir_docs
import os


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
            dict_lots['info_article'] = f"{lot.key}/-/{lot.catalog_reference}/-/{lot.manufacturer}/-/{lot.description}/-/{lot.analytical_technique}/-/{lot.reference_units}/-/{lot.id_reactive}/-/{lot.code_SAP}/-/{lot.code_LOG}/-/{lot.active}/-/{lot.temp_conservation}/-/{lot.description_subreference}/-/{lot.react_or_fungible}/-/{lot.code_panel}/-/{lot.location}/-/{lot.supplier}/-/{lot.purchase_format}/-/{lot.units_format}/-/{lot.import_unit_ics}/-/{lot.import_unit_idibgi}/-/{lot.local_management}/-/{lot.plataform_command_preferent}/-/{lot.maximum_amount}/-/{lot.purchase_format_supplier}/-/{lot.units_format_supplier}/-/{lot.name_logaritme}/-/{lot.units_for_discount}/-/{lot.units_measurement}/-/{lot.observations}"
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

    # date = datetime.now()
    # year = date.strftime("-%Y")
    # list_year = [year, int(year)+1, int(year)+2, int(year)+3, int(year)+4]
    # print(year)
    # print(list_year)
    # try:
    if search_data_code == '':
        return 'False_//_Es codi no pot estar buit.'
    else:
        # select_lots = (
        #     session1.query(Stock_lots, Lot_consumptions)
        #     .outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id)
        #     .filter(
        #         or_(
        #             Stock_lots.cost_center_stock == search_data_code,
        #             Stock_lots.catalog_reference == search_data_code,
        #             Stock_lots.code_SAP == search_data_code,
        #             Stock_lots.reception_date == search_data_code.replace('/', '-')
        #         ),
        #         or_(*[Stock_lots.reception_date.like(f"%{year}%") for year in list_year])
        #     )
        #     .all()
        # )

        # select_lots = (
        #     session1.query(Stock_lots, Lot_consumptions)
        #     .outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id)
        #     .filter(
        #         or_(
        #             Stock_lots.cost_center_stock == search_data_code,
        #             Stock_lots.catalog_reference == search_data_code,
        #             Stock_lots.code_SAP == search_data_code,
        #             Stock_lots.reception_date == search_data_code.replace('/', '-')
        #         )
        #     ).all()
        # )

        if search_data_code != 'Tots':
            select_lots = (
                session1.query(Stock_lots, Lot_consumptions)
                .outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id)
                .filter(Stock_lots.reception_date.like(f'%{search_data_code}'))
                .all()
            )
        else:
            select_lots = (
                session1.query(Stock_lots, Lot_consumptions)
                .outerjoin(Lot_consumptions, Lot_consumptions.id_lot == Stock_lots.id)
                .all()
            )

    print(len(select_lots))
    if not select_lots:
        # return f"False_//_No s'ha trobat stock amb el codi {search_data_code}"
        return jsonify({"success": False, "data": f"No s'ha trobat stock de l'any {search_data_code}"})
    else:
        list_info_stock_aux = [
            {
                **to_dict(stock),
                **(to_dict(consumption) if consumption else {})  # si no hi ha consumption, afegeix dict buit
            } for stock, consumption in select_lots
        ]
        # list_info_stock = json.dumps(list_info_stock_aux)
    # except Exception:
    #     return "False_//_Error, no s'ha pout realitzar la cerca"

    # return f'True_//_{list_info_stock}'
    return jsonify({"success": True, "data": list_info_stock_aux})


@app.route('/download_certificate_pending', methods=['POST'])
@requires_auth
def download_certificate_pending():
    '''
    '''
    # try:
    # select_lot = session1.query(Stock_lots).filter(Stock_lots.react_or_fungible == 'Reactiu').group_by(Stock_lots.lot, Stock_lots.reception_date).all()
    # if not select_lot:
    #     flash("No s'ha trobat informació a la BD", "danger")
    #     return render_template('home.html', list_desciption_lots=list_desciption_lots(),
    #                             list_cost_center=list_cost_center())

    list_json = request.form['list_json']
                        
    # Crear un DataFrame con los datos
    data = {
        'Referencia Cataleg': [],
        'Descripció': [],
        'Codi subreferencia': [],
        'Descripció subref.': [],
        'Lot': [],
        'Lot intern': [],
        'Data recepció': [],
        'Data caducitat': [],
        'Observacions inspecció': [],
        'Proveidor': []
    }

    # for row in select_lot:
    #     if row.certificate != '':
    #         data['Referencia Cataleg'].append(row.catalog_reference)
    #         data['Descripció'].append(row.description)
    #         data['Codi subreferencia'].append(row.id_reactive)
    #         data['Descripció subref.'].append(row.description_subreference)
    #         data['Lot'].append(row.lot)
    #         data['Lot intern'].append(row.internal_lot)
    #         data['Data recepció'].append(str(row.reception_date))
    #         data['Data caducitat'].append(str(row.date_expiry))
    #         data['Observacions inspecció'].append(row.observations_inspection)

    list_data = json.loads(list_json)

    for row in list_data:
        data['Referencia Cataleg'].append(row['referencia_cataleg'])
        data['Descripció'].append(row['descripcio'])
        data['Codi subreferencia'].append(row['codi_subreferencia'])
        data['Descripció subref.'].append(row['descripcio_subref'])
        data['Lot'].append(row['lot'])
        data['Lot intern'].append(row['lot_intern'])
        data['Data recepció'].append(row['data_recepcio'])
        data['Data caducitat'].append(row['data_caducitat'])
        data['Observacions inspecció'].append(row['observacions_inspeccio'])
        data['Proveidor'].append(row['manufacturer'])

    df = pd.DataFrame(data)

    # Guardar el DataFrame en un archivo Excel
    path = f"{main_dir_docs}/plantillas/preus_articles.xlsx"
    df.to_excel(path, index=False)

    # Ajustar el tamaño de las columnas automáticamente
    wb = load_workbook(path)  # Cargar el archivo Excel
    ws = wb.active  # Obtener la hoja activa

    # --- Aplicar estilos al encabezado ---
    header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Fondo amarillo
    header_font = Font(size=13, bold=True)  # Letra tamaño 13 y en negrita
    for cell in ws[1]:  # Primera fila (encabezado)
        cell.fill = header_fill
        cell.font = header_font

    # --- Ajustar el tamaño de las columnas automáticamente ---
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter  # Obtener la letra de la columna
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2  # Ajustar ancho

    ws.column_dimensions['B'].width = 24  # Ajustar ancho
    ws.column_dimensions['F'].width = 16  # Ajustar ancho
    ws.column_dimensions['G'].width = 17  # Ajustar ancho

    # --- Ajustar altura de todas las filas (margen superior e inferior) ---
    for row in ws.iter_rows():
        ws.row_dimensions[row[0].row].height = 19  # Ajustar altura de fila
        for cell in row:
            cell.alignment = Alignment(vertical="center", horizontal="left")  # Alineación vertical centrada

    wb.save(path)  # Guardar cambios
    return send_file(path, as_attachment=True)
    # except Exception:
    #     flash("Error inesperat, contacteu amb un administrador", "danger")
    #     return render_template('home.html', list_desciption_lots=list_desciption_lots(),
    #                            list_cost_center=list_cost_center())


@app.route("/info_description_lots")
@requires_auth
def info_description_lots():
    lots = list_desciption_lots()

    data = [
        {
            "catalog_reference": x.catalog_reference,
            "description": x.description,
            "analytical_technique": x.analytical_technique,
            "id_reactive": x.id_reactive,
            "description_subreference": x.description_subreference,
            "code_panel": x.code_panel,
            "name_logaritme": x.name_logaritme,
        }
        for x in lots
    ]
    return jsonify(data)


@app.route("/upadate_bd")
@requires_auth
def upadate_bd():
    """
        Llegeix un fitxer Excel des del directori principal i processa les files per actualitzar la BD.

        El fitxer Excel s'espera que tingui capçaleres (noms de columna) a la primera fila.
        Es recorre fila a fila i es crea un diccionari amb tots els camps per a cada fila.

        :return: Resposta JSON amb el resultat del procés.
        :rtype: flask.wrappers.Response

        :raises ValueError: Si no es troba el fitxer o si falten columnes esperades.
    """
    modify = 0
    not_found = ''
    found = 0
    # --- Config ---
    # Comentari en català: ruta del fitxer Excel dins el directori principal del projecte
    csv_filename = "new_db.xlsx"  # <-- canvia-ho pel nom real
    csv_path = os.path.join(main_dir, csv_filename)

    if not os.path.exists(csv_path):
        return jsonify({"result": False, "message": f"No s'ha trobat l'Excel a: {csv_path}"}), 404

    print(csv_path)

    # try:
    df = pd.read_excel(csv_path)
    # except Exception as exc:
    #     return "Error al lleguir el document"

    # Comentari en català: neteja bàsica (files buides i NaN)
    df = df.dropna(how="all").fillna("")

    # (Opcional però recomanat) validar que tens les 11 columnes esperades
    # expected_cols = ["ID Petició", "...", "..."]  # posa aquí les 11 columnes reals
    # missing = [c for c in expected_cols if c not in df.columns]
    # if missing:
    #     return jsonify({"result": False, "message": f"Falten columnes: {missing}"}), 400

    not_match: list[str] = []
    updated: int = 0

    # Comentari en català: iteració fila a fila; cada fila és un dict amb totes les columnes
    for row_dict in df.to_dict(orient="records"):
        dict_log = {}
        # Exemple: obtenir un camp concret
        key_raw = row_dict.get("key", "")
        key = str(key_raw).strip()

        catalog_reference_raw = row_dict.get("catalog_reference", "")
        catalog_reference = str(catalog_reference_raw).strip()

        manufacturer_raw = row_dict.get("manufacturer", "")
        manufacturer = str(manufacturer_raw).strip()

        description_raw = row_dict.get("description", "")
        description = str(description_raw).strip()

        analytical_technique_raw = row_dict.get("analytical_technique", "")
        analytical_technique = str(analytical_technique_raw).strip()

        reference_units_raw = row_dict.get("reference_units", "")
        reference_units = str(reference_units_raw).strip()

        id_reactive_raw = row_dict.get("id_reactive", "")
        id_reactive = str(id_reactive_raw).strip()

        code_SAP_raw = row_dict.get("code_SAP", "")
        code_SAP = str(code_SAP_raw).strip()

        code_LOG_raw = row_dict.get("code_LOG", "")
        code_LOG = str(code_LOG_raw).strip()

        active_raw = row_dict.get("active", "")
        active = str(active_raw).strip()

        temp_conservation_raw = row_dict.get("temp_conservation", "")
        temp_conservation = str(temp_conservation_raw).strip()

        description_subreference_raw = row_dict.get("description_subreference", "")
        description_subreference = str(description_subreference_raw).strip()

        react_or_fungible_raw = row_dict.get("react_or_fungible", "")
        react_or_fungible = str(react_or_fungible_raw).strip()

        code_panel_raw = row_dict.get("code_panel", "")
        code_panel = str(code_panel_raw).strip()

        location_raw = row_dict.get("location", "")
        location = str(location_raw).strip()

        supplier_raw = row_dict.get("supplier", "")
        supplier = str(supplier_raw).strip()

        purchase_format_raw = row_dict.get("purchase_format", "")
        purchase_format = str(purchase_format_raw).strip()

        units_format_raw = row_dict.get("units_format", "")
        units_format = str(units_format_raw).strip()

        import_unit_ics_raw = row_dict.get("import_unit_ics", "")
        import_unit_ics = str(import_unit_ics_raw).strip()

        import_unit_idibgi_raw = row_dict.get("import_unit_idibgi", "")
        import_unit_idibgi = str(import_unit_idibgi_raw).strip()

        local_management_raw = row_dict.get("local_management", "")
        local_management = str(local_management_raw).strip()

        plataform_command_preferent_raw = row_dict.get("plataform_command_preferent", "")
        plataform_command_preferent = str(plataform_command_preferent_raw).strip()

        maximum_amount_raw = row_dict.get("maximum_amount", "")
        maximum_amount = str(maximum_amount_raw).strip()

        purchase_format_supplier_raw = row_dict.get("purchase_format_supplier", "")
        purchase_format_supplier = str(purchase_format_supplier_raw).strip()

        units_format_supplier_raw = row_dict.get("units_format_supplier", "")
        units_format_supplier = str(units_format_supplier_raw).strip()

        nom_logaritme_raw = row_dict.get("Nom logaritme", "")
        name_logaritme = str(nom_logaritme_raw).strip()

        ubicació_raw = row_dict.get("Ubicació", "")
        ubicació = str(ubicació_raw).strip()

        unitats_raw = row_dict.get("Unitats", "")
        units = str(unitats_raw).strip()

        unitats_de_mesuta_raw = row_dict.get("Unitats de Mesuta", "")
        units_measurement = str(unitats_de_mesuta_raw).strip()

        observacions_raw = row_dict.get("Observacions", "")
        observations = str(observacions_raw).strip()

        select_lot = session1.query(Lots).filter(Lots.key == key).first()
        if not select_lot:
            not_found += f"<br>{key}"
        else:
            found += 1
            if select_lot.catalog_reference != catalog_reference:
                select_lot.catalog_reference = catalog_reference
                dict_log['catalog_reference_new'] = catalog_reference
                dict_log['catalog_reference_old'] = select_lot.catalog_reference

            if select_lot.manufacturer != manufacturer:
                select_lot.manufacturer = manufacturer
                dict_log['manufacturer_new'] = manufacturer
                dict_log['manufacturer_old'] = select_lot.manufacturer

            if select_lot.description != description:
                select_lot.description = description
                dict_log['description_new'] = description
                dict_log['description_old'] = select_lot.description

            if select_lot.analytical_technique != analytical_technique:
                select_lot.analytical_technique = analytical_technique
                dict_log['analytical_technique_new'] = analytical_technique
                dict_log['analytical_technique_old'] = select_lot.analytical_technique

            if select_lot.reference_units != reference_units:
                select_lot.reference_units = reference_units
                dict_log['reference_units_new'] = reference_units
                dict_log['reference_units_old'] = select_lot.reference_units

            if select_lot.id_reactive != id_reactive:
                select_lot.id_reactive = id_reactive
                dict_log['id_reactive_new'] = id_reactive
                dict_log['id_reactive_old'] = select_lot.id_reactive

            if select_lot.code_SAP != code_SAP:
                select_lot.code_SAP = code_SAP
                dict_log['code_SAP_new'] = code_SAP
                dict_log['code_SAP_old'] = select_lot.code_SAP

            if select_lot.code_LOG != code_LOG:
                select_lot.code_LOG = code_LOG
                dict_log['code_LOG_new'] = code_LOG
                dict_log['code_LOG_old'] = select_lot.code_LOG

            if select_lot.active != int(active):
                select_lot.active = int(active)
                dict_log['active_new'] = active
                dict_log['active_old'] = select_lot.active

            if select_lot.temp_conservation != temp_conservation:
                select_lot.temp_conservation = temp_conservation
                dict_log['temp_conservation_new'] = temp_conservation
                dict_log['temp_conservation_old'] = select_lot.temp_conservation

            if select_lot.description_subreference != description_subreference:
                select_lot.description_subreference = description_subreference
                dict_log['description_subreference_new'] = description_subreference
                dict_log['description_subreference_old'] = select_lot.description_subreference

            if select_lot.react_or_fungible != react_or_fungible:
                select_lot.react_or_fungible = react_or_fungible
                dict_log['react_or_fungible_new'] = react_or_fungible
                dict_log['react_or_fungible_old'] = select_lot.react_or_fungible

            if select_lot.code_panel != code_panel:
                select_lot.code_panel = code_panel
                dict_log['code_panel_new'] = code_panel
                dict_log['code_panel_old'] = select_lot.code_panel
                
            if select_lot.location != location:
                select_lot.location = location
                dict_log['location_new'] = location
                dict_log['location_old'] = select_lot.location

            if select_lot.supplier != supplier:
                select_lot.supplier = supplier
                dict_log['supplier_new'] = supplier
                dict_log['supplier_old'] = select_lot.supplier

            if select_lot.purchase_format != purchase_format:
                select_lot.purchase_format = purchase_format
                dict_log['purchase_format_new'] = purchase_format
                dict_log['purchase_format_old'] = select_lot.purchase_format

            if select_lot.units_format != int(units_format):
                select_lot.units_format = int(units_format)
                dict_log['units_format_new'] = units_format
                dict_log['units_format_old'] = select_lot.units_format

            if select_lot.import_unit_ics != import_unit_ics:
                select_lot.import_unit_ics = import_unit_ics
                dict_log['import_unit_ics_new'] = import_unit_ics
                dict_log['import_unit_ics_old'] = select_lot.import_unit_ics

            if select_lot.import_unit_idibgi != import_unit_idibgi:
                select_lot.import_unit_idibgi = import_unit_idibgi
                dict_log['import_unit_idibgi_new'] = import_unit_idibgi
                dict_log['import_unit_idibgi_old'] = select_lot.import_unit_idibgi

            if select_lot.local_management != local_management:
                select_lot.local_management = local_management
                dict_log['local_management_new'] = local_management
                dict_log['local_management_old'] = select_lot.local_management

            if select_lot.plataform_command_preferent != plataform_command_preferent:
                select_lot.plataform_command_preferent = plataform_command_preferent
                dict_log['plataform_command_preferent_new'] = plataform_command_preferent
                dict_log['plataform_command_preferent_old'] = select_lot.plataform_command_preferent

            try:
                if select_lot.maximum_amount != int(maximum_amount):
                    select_lot.maximum_amount = int(maximum_amount)
                    dict_log['maximum_amount_new'] = maximum_amount
                    dict_log['maximum_amount_old'] = select_lot.maximum_amount
            except:
                print(select_lot.maximum_amount)

            if select_lot.purchase_format_supplier != purchase_format_supplier:
                select_lot.purchase_format_supplier = purchase_format_supplier
                dict_log['purchase_format_supplier_new'] = purchase_format_supplier
                dict_log['purchase_format_supplier_old'] = select_lot.purchase_format_supplier

            try:
                if select_lot.units_format_supplier != int(units_format_supplier):
                    select_lot.units_format_supplier = int(units_format_supplier)
                    dict_log['units_format_supplier_new'] = units_format_supplier
                    dict_log['units_format_supplier_old'] = select_lot.units_format_supplier
            except:
                print(select_lot.units_format_supplier)

            # if select_lot.name_logaritme != name_logaritme:
            select_lot.name_logaritme = name_logaritme
            #     dict_log['name_logaritme_new'] = name_logaritme
            #     dict_log['name_logaritme_old'] = select_lot.name_logaritme

            # if select_lot.units_for_discount != units:
            select_lot.units_for_discount = units
            #     dict_log['units_new'] = units
            #     dict_log['units_old'] = select_lot.units

            # if select_lot.units_measurement != units_measurement:
            select_lot.units_measurement = units_measurement
            #     dict_log['units_measurement_new'] = units_measurement
            #     dict_log['units_measurement_old'] = select_lot.units_measurement

            # if select_lot.observations != observations:
            select_lot.observations = observations
            #     dict_log['observations_new'] = observations
            #     dict_log['observations_old'] = select_lot.observations

            if ubicació != '':
                select_lot.location = ubicació
                dict_log['location_new'] = location
                dict_log['location_old'] = select_lot.location

            select_stock = session1.query(Stock_lots).filter(Stock_lots.id_lot == key).all()
            for stock in select_stock:
                stock.catalog_reference = catalog_reference
                stock.manufacturer = manufacturer
                stock.description = description
                stock.analytical_technique = analytical_technique
                stock.reference_units = reference_units
                stock.id_reactive = id_reactive
                stock.code_SAP = code_SAP
                stock.code_LOG = code_LOG
                stock.active = active
                stock.temp_conservation = temp_conservation
                stock.description_subreference = description_subreference
                stock.react_or_fungible = react_or_fungible
                stock.code_panel = code_panel
                stock.location = location
                stock.supplier = supplier
                stock.purchase_format = purchase_format
                stock.units_format = units_format
                stock.local_management = local_management
                stock.plataform_command_preferent = plataform_command_preferent
                stock.maximum_amount = maximum_amount
                stock.purchase_format_supplier = purchase_format_supplier
                stock.units_format_supplier = units_format_supplier
                stock.name_logaritme = name_logaritme
                stock.units_for_discount = units
                stock.units_measurement = units_measurement
                stock.observations = observations
                
                if ubicació != '':
                    stock.location = ubicació

            if dict_log:
                modify += 1
                dict_save_info = {'id_lot': key,
                                  'type': 'update_bd_excel',
                                  'user': session['acronim'],
                                  'info': json.dumps(dict_log),
                                  'id_user': session['idClient'],
                                  'date': '03-03-2025'}

                save_log(dict_save_info)

        session1.commit()

    return f"True<br>trobats ->{found}<br>Modificats ->{modify}<br>No trobats -> {not_found}"


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
