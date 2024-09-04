from app import app
from app.utils import requires_auth, year_now
from app.models import session1, Stock_lots
import json


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
    # try:
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
    # except Exception:
    #     return 'False_//_False'
