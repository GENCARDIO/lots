from flask import send_file, flash, render_template, request, session
from app import app
from app.utils import requires_auth, year_now, list_desciption_lots, list_cost_center, save_log, instant_date, format_price
from app.models import session1, Stock_lots, Lots
import json
from config import main_dir_docs
from werkzeug.utils import secure_filename
import os
import pandas as pd


@app.route('/look_spend_money', methods=['POST'])
@requires_auth
def look_spend_money():
    '''
        dasjfasdfklajsflsñkadfjañlsdfkjñlasdfjñladfjñlajflñdafjñdajsñ

        :param str code_search: codi que hem de buscar a la BD

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    year = year_now()
    select_stock_lots = session1.query(Stock_lots).filter(Stock_lots.reception_date.like(f'%-{year}')).all()
    if not select_stock_lots:
        return "False_//_Error, No hem trobat dades de l'stock"

    dic_info_spend_money = {}
    oligos_list = []
    try:
        for stock_lots in select_stock_lots:
            if stock_lots.cost_center_stock in dic_info_spend_money:
                # Als fungible hem de tenir en compte que segurament tindràn més d'una unitat per lot i s'ha de multiplicar el valor
                if stock_lots.react_or_fungible == 'Fungible':
                    try:
                        total_value_idibi = int(stock_lots.units_lot) * float(stock_lots.import_unit_idibgi.replace(",", "."))
                        dic_info_spend_money[stock_lots.cost_center_stock][0] += total_value_idibi
                    except Exception:
                        print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                        print(stock_lots.import_unit_idibgi)
                    try:
                        total_value_ics = int(stock_lots.units_lot) * float(stock_lots.import_unit_ics.replace(",", "."))
                        dic_info_spend_money[stock_lots.cost_center_stock][1] += total_value_ics
                    except Exception:
                        print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                        print(stock_lots.import_unit_ics)
                else:
                    # Els reactius semre seran 1 unitat exceptuan els oligos que s'ha de tenir en compte els parell de bases
                    if "Oligos" in stock_lots.description:
                        key_oligos = f'{stock_lots.reception_date}_{stock_lots.pb_oligos}'
                        if key_oligos not in oligos_list:
                            oligos_list.append(key_oligos)

                            try:
                                total_oligos_val = int(stock_lots.pb_oligos) * float(stock_lots.import_unit_idibgi.replace(",", "."))
                                dic_info_spend_money[stock_lots.cost_center_stock][0] += total_oligos_val
                            except Exception:
                                print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                                print(stock_lots.import_unit_idibgi)
                            try:
                                total_oligos_val2 = int(stock_lots.pb_oligos) * float(stock_lots.import_unit_ics.replace(",", "."))
                                dic_info_spend_money[stock_lots.cost_center_stock][1] += total_oligos_val2
                            except Exception:
                                print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                                print(stock_lots.import_unit_ics)
                    else:
                        # Si el lot te subreferencies, nomes s'ha de contar el primer, si sumesim els suman extra
                        # El que fem es mirar si es el 1/x i si ho es el sumem, sino no fem res
                        if stock_lots.description_subreference != '':
                            lot_one = stock_lots.internal_lot.split('_')
                            if lot_one[1][0] == '1':
                                try:
                                    dic_info_spend_money[stock_lots.cost_center_stock][0] += float(stock_lots.import_unit_idibgi.replace(",", "."))
                                except Exception:
                                    print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                                    print(stock_lots.import_unit_idibgi)
                                try:
                                    dic_info_spend_money[stock_lots.cost_center_stock][1] += float(stock_lots.import_unit_ics.replace(",", "."))
                                except Exception:
                                    print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                                    print(stock_lots.import_unit_ics)
                        else:
                            try:
                                dic_info_spend_money[stock_lots.cost_center_stock][0] += float(stock_lots.import_unit_idibgi.replace(",", "."))
                            except Exception:
                                print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                                print(stock_lots.import_unit_idibgi)
                            try:
                                dic_info_spend_money[stock_lots.cost_center_stock][1] += float(stock_lots.import_unit_ics.replace(",", "."))
                            except Exception:
                                print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                                print(stock_lots.import_unit_ics)
            else:
                total_value_idibgi = 0
                total_value_ics = 0
                if stock_lots.react_or_fungible == 'Fungible':
                    try:
                        total_value_idibgi = int(stock_lots.units_lot) * float(stock_lots.import_unit_idibgi.replace(",", "."))
                    except Exception:
                        print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                    try:
                        total_value_ics = int(stock_lots.units_lot) * float(stock_lots.import_unit_ics.replace(",", "."))
                    except Exception:
                        print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                elif "Oligos" in stock_lots.description:
                    key_oligos = f'{stock_lots.reception_date}_{stock_lots.pb_oligos}'
                    if key_oligos not in oligos_list:
                        oligos_list.append(key_oligos)
                        try:
                            total_value_idibgi = int(stock_lots.pb_oligos) * float(stock_lots.import_unit_idibgi.replace(",", "."))
                        except Exception:
                            print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")

                        try:
                            total_value_ics = int(stock_lots.pb_oligos) * float(stock_lots.import_unit_ics.replace(",", "."))
                        except Exception:
                            print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
                else:
                    total_value_idibgi = float(stock_lots.import_unit_idibgi.replace(",", "."))
                    total_value_ics = float(stock_lots.import_unit_ics.replace(",", "."))

                dic_info_spend_money[stock_lots.cost_center_stock] = [
                    float(total_value_idibgi),
                    float(total_value_ics)
                ]

        for key, value_list in dic_info_spend_money.items():
            for i in range(len(value_list)):
                value = value_list[i]
                # Si el valor tiene parte decimal .0, conviértelo a entero
                if value.is_integer():
                    dic_info_spend_money[key][i] = int(value)  # Convertir a entero
                else:
                    # Convertir el valor a un float con hasta dos decimales
                    dic_info_spend_money[key][i] = round(value, 2)  # Redondear a dos decimales

        # print(dic_info_spend_money)

        def formatear_euros(valor):
            partes = f"{valor:.2f}".split(".")  # Convertir a string con 2 decimales
            entero = partes[0]  # Parte entera
            decimal = partes[1]  # Parte decimal
            entero_con_puntos = "{:,}".format(int(entero)).replace(",", ".")  # Agregar puntos a los miles
            return f"{entero_con_puntos},{decimal} €"  # Combinar todo con la coma y el símbolo €

        # Formatear los valores del diccionario
        dict_formated = {
            clave: [formatear_euros(valor) for valor in valores]
            for clave, valores in dic_info_spend_money.items()
        }

        # print(dict_formated)

        # Això és fa perque dependet del CECO volem que no surti informació en la columna en qüestió
        for key, value_list in dict_formated.items():
            if key == '8852' or key == '8860':
                dict_formated[key][0] = '-'
            if 'IDIBGI' in key or 'idigi' in key:
                dict_formated[key][1] = '-'
            if 'GRATUIT' in key or 'gratuit' in key:
                dict_formated[key][0] = '0'
                dict_formated[key][1] = '0'

        json_data = json.dumps(dict_formated)
        return f'True_//_{json_data}'
    except Exception:
        return 'False_//_False'


@app.route('/download_template_price', methods=['POST'])
@requires_auth
def download_template_price():
    '''
        1 - Agafem tota la informació de lots que tenim.
        2 - Creem un excel i l'omplim amb l'informació del lots.
        3 - Guardem el document.
        4 - Posem en descarga l'arxiu que acabem de crear.

        :return: L'arxiu que l'usuari es descarregar
        :rtype: csv
    '''
    try:
        select_lot = session1.query(Lots).all()
        if not select_lot:
            flash("No s'ha trobat informació a la BD", "danger")
            return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                                   list_cost_center=list_cost_center())

        # Crear un DataFrame con los datos
        data = {
            'Id': [],
            'Referencia Cataleg': [],
            'SAP': [],
            'LOG': [],
            'Descripció': [],
            'Preu ICS': [],
            'Preu IDIBGI': []
        }

        for row in select_lot:
            data['Id'].append(row.key)
            data['Referencia Cataleg'].append(row.catalog_reference)
            data['SAP'].append(row.code_SAP)
            data['LOG'].append(row.code_LOG)
            data['Descripció'].append(row.description)
            data['Preu ICS'].append(str(row.import_unit_ics))
            data['Preu IDIBGI'].append(str(row.import_unit_idibgi))

        df = pd.DataFrame(data)

        # Guardar el DataFrame en un archivo Excel
        path = f"{main_dir_docs}/plantillas/preus_articles.xlsx"
        df.to_excel(path, index=False)
        return send_file(path, as_attachment=True)
    except Exception:
        flash("Error inesperat, contacteu amb un administrador", "danger")
        return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                               list_cost_center=list_cost_center())


@app.route('/upload_template_price2', methods=['POST'])
@requires_auth
def upload_template_price2():
    '''
        1 - Recollim la informació de l'ajax
        2 - Guardem el document que ens han carregat
        3 - Lleguim el document
        4 - Agafem els 4 camps que necesitem i fem les comprovacion per si s'ha de canviar o no
        5 - Si el preu ha canviat, guardarem un loc de l'acció i farem el canvi
        6 - En el cas que alguna cerca falli, es guardara un log i és mostrar per pantalla a l'usuari
        7 - Quan tot acabi és fara un commit i es retornara True o False i el missatge corresponent

        :param str file: Document que ens carrega l'usuari.

        :return: Retorna True o False i un missatge amb informació.
        :rtype: json
    '''
    info_error = ''
    one_change = False

    try:
        f = request.files["file"]
        filename = secure_filename(f.filename)
        f.save(os.path.join(f"{main_dir_docs}/preu/", filename))
    except Exception:
        return "False_//_Error, no s'ha pogut carregar/guardar el document"

    # Leer el archivo según su extensión
    try:
        if '.xlsx' in filename:
            df = pd.read_excel(f"{main_dir_docs}/preu/{filename}", engine='openpyxl')
            list_excel = df.values.tolist()
        else:
            return "False_//_Error, el format no és valid."
    except Exception:
        return "False_//_Error, no s'ha pogut lleguir el document"

    dict_info_save = {
        'id_lot': '',
        'type': 'update price',
        'info': '',
        'user': session['acronim'],
        'id_user': session['idClient'],
        'date': instant_date()
    }

    # Iterar sobre cada fila y extraer las columnas A (índice 0), F (índice 5), y G (índice 6)
    try:
        for line in range(0, len(list_excel)):
            # print(list_excel[line])
            id = list_excel[line][0]
            catalog_reference = list_excel[line][1]
            description = list_excel[line][4]
            price_ics = str(list_excel[line][5])
            price_idibgi = str(list_excel[line][6])

            if '.0' in str(price_ics):
                price_ics = str(price_ics).replace('.0', '')

            if '.0' in str(price_idibgi):
                price_idibgi = str(price_idibgi).replace('.0', '')

            dict_info_save['id_lot'] = id
            select_lots = session1.query(Lots).filter(Lots.key == int(id)).filter(Lots.description == str(description)).first()
            if select_lots is not None:
                if str(select_lots.import_unit_ics) != str(price_ics):
                    one_change = True
                    info_dict = {
                        "field": "import_unit_ics",
                        "old_info": str(select_lots.import_unit_ics),
                        "new_info": str(price_ics)
                    }

                    dict_info_save['info'] = json.dumps(info_dict)

                    save_log(dict_info_save)

                    select_lots.import_unit_ics = str(price_ics)

                if str(select_lots.import_unit_idibgi) != str(price_idibgi):
                    one_change = True
                    info_dict = {
                        "field": "import_unit_idibgi",
                        "old_info": str(select_lots.import_unit_idibgi),
                        "new_info": str(price_idibgi)
                    }

                    dict_info_save['info'] = json.dumps(info_dict)

                    save_log(dict_info_save)

                    select_lots.import_unit_idibgi = str(price_idibgi)
            else:
                info_error += f"El { catalog_reference } --- { description } no s'ha pogut actualitzar el preu<br>"
    except Exception:
        return "False_//_Error, al processar les dades del document"

    try:
        session1.commit()
    except Exception:
        session1.rollback()
        return "False_//_Error, no s'han pogut guardar les dades de l'operació"

    return f'True_//_{info_error}_//_{one_change}'


@app.route('/upload_template_price', methods=['POST'])
@requires_auth
def upload_template_price():
    '''
        1 - Recollim la informació de l'ajax
        2 - Guardem el document que ens han carregat
        3 - Lleguim el document
        4 - Agafem els 4 camps que necesitem i fem les comprovacion per si s'ha de canviar o no
        5 - Si el preu ha canviat, guardarem un loc de l'acció i farem el canvi
        6 - En el cas que alguna cerca falli, es guardara un log i és mostrar per pantalla a l'usuari
        7 - Quan tot acabi és fara un commit i es retornara True o False i el missatge corresponent

        :param str file: Document que ens carrega l'usuari.

        :return: Retorna True o False i un missatge amb informació.
        :rtype: json
    '''
    try:
        f = request.files["file"]
        filename = secure_filename(f.filename)
        f.save(os.path.join(f"{main_dir_docs}/preu/", filename))
    except Exception:
        return "False_//_Error, no s'ha pogut carregar/guardar el document"

    # Leer el archivo según su extensión
    try:
        if '.xlsx' in filename:
            df = pd.read_excel(f"{main_dir_docs}/preu/{filename}", engine='openpyxl')
            list_excel = df.values.tolist()
        else:
            return "False_//_Error, el format no és valid."
    except Exception:
        return "False_//_Error, no s'ha pogut lleguir el document"

    dict_info_save = {
        'id_lot': '',
        'type': 'update price',
        'info': '',
        'user': session['acronim'],
        'id_user': session['idClient'],
        'date': instant_date()
    }

    lot_found = []
    lot_not_found = []
    price_change = False

    # Iterar sobre cada fila y extraer las columnas A (índice 0), F (índice 5), y G (índice 6)
    # Comprobarem si hi ha lots amb la descripció i guardarem els resultat en un diccionri
    try:
        for line in range(0, len(list_excel)):
            # print(list_excel[line])
            catalog_reference = str(list_excel[line][1]).strip()
            description = list_excel[line][0]
            price_ics = str(list_excel[line][4])

            if '.0' in str(price_ics):
                price_ics = str(price_ics).replace('.0', '')

            select_lots = session1.query(Lots).filter(Lots.description == str(description)).filter(Lots.catalog_reference == catalog_reference).first()
            if select_lots is not None:
                dict_lot = {
                    'id_lot': select_lots.key,
                    'description': select_lots.description,
                    'catalog_reference': select_lots.catalog_reference,
                    'price_ics_old': format_price(select_lots.import_unit_ics),
                    'price_ics_new': format_price(price_ics)
                }
                lot_found.append(dict_lot)
            else:
                dict_lot = {
                    'description': description,
                    'catalog_reference': str(catalog_reference),
                    'price_ics_new': price_ics
                }
                lot_not_found.append(dict_lot)

        # Si tenim lots que no s'han trobat no es farà cap canvi i mostrarem per pantalla els lots que no s'han trobat
        if lot_not_found:
            print(len(lot_not_found))
            for lott in lot_not_found:
                print(lott)
            json_data = json.dumps(lot_not_found)
            return f"True_//_not_found_//_{json_data}"
        else:
            # Iterem sobre la llista de trobats, formatejarem els imports i farem els canvis que siguin necesaris, es guardara log de totes les operacions
            for found in lot_found:
                if found['price_ics_old'] != found['price_ics_new']:
                    print(f"Canvi de {found['price_ics_old']} a {found['price_ics_new']}")
                    select_lot = session1.query(Lots).filter(Lots.catalog_reference == found['catalog_reference']).filter(Lots.description == found['description']).all()
                    for lot in select_lot:
                        lot.import_unit_ics = found['price_ics_new']
                        price_change = True

                    dict_change = {
                        'id_lot': found['id_lot'],
                        'description': found['description'],
                        'catalog_reference': found['catalog_reference'],
                        'price_ics_old': found['price_ics_old'],
                        'price_ics_new': found['price_ics_new'],
                    }

                    json_data = json.dumps(dict_change)

                    dict_info_save['id_lot'] = found['id_lot']
                    dict_info_save['info'] = json_data

                    save_log(dict_info_save)

            if price_change:
                session1.commit()
                return 'True_//_OK_//_OK'
            else:
                return 'True_//_True_//_False'
    except Exception:
        session1.rollback()
        return "False_//_Error, al processar les dades del document"
