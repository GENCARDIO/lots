from flask import send_file, flash, render_template, request, session
from app import app
from app.utils import requires_auth, year_now, list_desciption_lots, list_cost_center, save_log, instant_date
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
        Busquem a la BD si el lot ja existeix.
        Si existeix agafem tota la informació la posem en una llista de diccionaris i la enviem per ajax.
        Si no existesix enviem una resposta per ajex avisan de que no tenim el lot registrat.

        :param str code_search: codi que hem de buscar a la BD

        :return: json amb un True o un False i la informació requerida.
        :rtype: json
    '''
    year = year_now()

    select_stock_lots = session1.query(Stock_lots).filter(Stock_lots.reception_date.like(f'%-{year}')).all()
    if not select_stock_lots:
        return "False_//_Error, No hem trobat dades de l'stock"

    dic_info_spend_money = {}
    try:
        for stock_lots in select_stock_lots:
            if stock_lots.cost_center_stock in dic_info_spend_money:
                try:
                    dic_info_spend_money[stock_lots.cost_center_stock][0] += float(stock_lots.import_unit_idibgi)
                except Exception:
                    print("No pot fer la suma, revisar que estigui ben entrat el valor a import_idibgi")
                try:
                    dic_info_spend_money[stock_lots.cost_center_stock][1] += float(stock_lots.import_unit_ics)
                except Exception:
                    print("No pot fer la suma, revisar que estigui ben entrat el valor a import_ics")
            else:
                dic_info_spend_money[stock_lots.cost_center_stock] = [
                    float(stock_lots.import_unit_idibgi),
                    float(stock_lots.import_unit_ics)
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

        json_data = json.dumps(dic_info_spend_money)
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
