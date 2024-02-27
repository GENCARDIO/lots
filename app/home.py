from flask import render_template, request, flash, redirect, send_file, session
from app import app
from app.utils import get_data, create_excel, check_finish_sample, insert_register, read_excel, convert_xls_with_xlsx, \
                      check_excel, add_date, search_hgvsg, check_duplidates, instant_date, requires_auth
from app.models import IP_HOME, session1, Lots, Logs, Stock_lots
from sqlalchemy import or_, func, and_
from werkzeug.utils import secure_filename
import os
import jwt
import json
from config import main_dir_docs


# Pagina incial i visualització
@app.route('/')
@requires_auth
def main():
    '''
        Redirigeix al home
    '''
    return render_template('home.html')


@app.route('/logout')
def logout():
    url = IP_HOME + 'logout'

    return redirect(url)


@app.route('/apps')
@requires_auth
def apps():
    tocken_cookies = {'user_tok': session['user'], 'rols_tok': session['rols'], 'email_tok': session['email'],
                      'id_client_tok': session['idClient'], 'rol_tok': 'None', 'acronim_tok': session['acronim']}
    secret_key = '12345'
    token = jwt.encode(tocken_cookies, secret_key, algorithm='HS256')
    url = f'{IP_HOME}apps/token?token={token}'

    return redirect(url)


@app.route('/receive_token')
def receive_token():
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


@app.route('/search_add_lot', methods=['POST'])
@requires_auth
def search_add_lot():
    '''
        Busquem a la BD si el lot ja existeix.
    '''
    code_search = request.form.get("code_search")

    select_lot = session1.query(Lots).filter(Lots.catalog_reference == code_search).filter(Lots.active == 1).all()
    if not select_lot:
        select_lot = session1.query(Lots).filter(Lots.code_LOG == code_search).filter(Lots.active == 1).all()
        if not select_lot:
            select_lot = session1.query(Lots).filter(Lots.code_SAP == code_search).filter(Lots.active == 1).all()

    try:
        if not select_lot:
            return 'True_//_new'
        else:
            list_lots = []
            for log in select_lot:
                dict_lots = {'key': log.key,
                             'catalog_reference': log.catalog_reference,
                             'manufacturer': log.manufacturer,
                             'description': log.description,
                             'description_subreference': log.description_subreference,
                             'analytical_technique': log.analytical_technique,
                             'reference_units': log.reference_units,
                             'id_reactive': log.id_reactive,
                             'code_SAP': log.code_SAP,
                             'code_LOG': log.code_LOG,
                             'active': log.active}
                list_lots.append(dict_lots)
            json_data = json.dumps(list_lots)
            return f'True_//_{json_data}'
    except Exception:
        return 'False_//_False'


@app.route('/register_new_lot', methods=['POST'])
@requires_auth
def register_new_lot():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    reference_catalog = request.form.get("reference_catalog")
    list_lots_json = request.form.get("list_lots")

    list_lots = json.loads(list_lots_json)

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
                              description_subreference=lots['description_subreference'])
            session1.add(insert_lot)
        except Exception:
            session1.rollback()
            return 'False_error'
    session1.commit()
    return 'True'


@app.route('/add_stock_lot', methods=['POST'])
@requires_auth
def add_stock_lot():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    list_lots_json = request.form.get("list_lots")

    max_number_group_insert = session1.query(func.max(Stock_lots.group_insert)).scalar()
    if max_number_group_insert is not None:
        group_insert_number = int(max_number_group_insert) + 1
    else:
        group_insert_number = 1

    try:
        f = request.files["file_delivery_note"]
        filename_delivery_note = secure_filename(f.filename)
        split_dirname = filename_delivery_note.split(".")
        max_number_delivery = session1.query(func.max(Stock_lots.delivery_note)).scalar()
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
        max_number_certificate = session1.query(func.max(Stock_lots.certificate)).scalar()
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

    for lots in list_lots:
        # try:
        select_lot = session1.query(Stock_lots).filter_by(code_SAP=lots['code_SAP'], code_LOG=lots['code_LOG'], lot=lots['lot'], date_expiry=lots['date_expiry'], spent=0).first()
        if select_lot:
            select_lot.units_lot = int(select_lot.units_lot) + int(lots['units_lot'])
        else:
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
                                    units_lot=lots['units_lot'],
                                    internal_lot=lots['internal_lot'],
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
                                    group_insert=group_insert_number)
            session1.add(insert_lot)
        # except Exception:
        #     print("ha petat")
        #     session1.rollback()
        #     return 'False_error'
    session1.commit()
    return 'True'


@app.route('/search_lots', methods=['POST'])
@requires_auth
def search_lots():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    search_code = request.form['search_code']
    select_lot = session1.query(Stock_lots).filter_by(catalog_reference=search_code, spent=0).all()
    if not select_lot:
        select_lot = session1.query(Stock_lots).filter_by(code_SAP=search_code, spent=0).all()
        if not select_lot:
            select_lot = session1.query(Stock_lots).filter_by(code_LOG=search_code, spent=0).all()
            if not select_lot:
                flash(f"No s'ha trobat cap coincidencia amb el text entrat --> {search_code}", "warning")
                return render_template('home.html')

    return render_template('search_lot.html', select_lot=select_lot, lot=select_lot[0])


@app.route("/download_docs", methods=["POST"])
@requires_auth
def download_docs():
    """
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    """
    dir_name = request.form["dir_name"]
    name_doc = request.form["name_doc"]

    path = f"{main_dir_docs}/{dir_name}/{name_doc}"
    return send_file(path, as_attachment=True, download_name=f"{dir_name}_{name_doc}")
    # return send_file(path, as_attachment=True)


@app.route('/upload_docs', methods=['POST'])
@requires_auth
def upload_docs():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    dir_name = request.form.get("dir_name")
    group_insert = request.form.get("group_insert")

    select_lots = session1.query(Stock_lots).filter_by(group_insert=group_insert).all()
    if not select_lots:
        return 'False'

    try:
        f = request.files["file"]
        filename = secure_filename(f.filename)
        split_dirname = filename.split(".")

        if dir_name == 'delivery_note':
            max_number_filename = session1.query(func.max(Stock_lots.delivery_note)).scalar()
            dirname = 'albarans'
        elif dir_name == 'certificate':
            max_number_filename = session1.query(func.max(Stock_lots.certificate)).scalar()
            dirname = 'certificats'
        else:
            return 'False'

        if max_number_filename is not None and max_number_filename == '':
            new_filename = 1
            type_doc = f'.{split_dirname[1]}'
        elif max_number_filename is not None:
            new_filename = int(max_number_filename) + 1
            type_doc = f'.{split_dirname[1]}'
        else:
            return 'False'
        f.save(os.path.join(f"{main_dir_docs}/{dirname}/", f'{new_filename}.{split_dirname[1]}'))
    except Exception:
        return "False"

    id_lots = ''
    for lots in select_lots:
        id_lots += f"{lots.id};"
        if dir_name == 'delivery_note':
            lots.delivery_note = new_filename
            lots.type_doc_delivery = type_doc
        elif dir_name == 'certificate':
            lots.certificate = new_filename
            lots.type_doc_certificate = type_doc
    session1.commit()
    if id_lots[-1] == ';':
        id_lots = id_lots[:-1]
    return f'True///{id_lots}///{new_filename}///{type_doc}'


# @app.route('/change_status', methods=['POST'])
# @requires_auth
# def change_status():
#     '''
#         Caviem l'estat del lot a la BD
#     '''
#     id_lot = request.form.get("id_lot")
#     accion = request.form.get("accion")
#     send_text = 'False'

#     select_lot = session1.query(Lots).filter(Lots.id == id_lot).first()
#     if select_lot is None:
#         return 'False'

#     date = instant_date()

#     if accion == 'close':
#         select_lot.data_close = date
#         select_lot.tecnic_close = session['acronim']
#         select_lot.status = 'F'
#         send_text = f"{date} - {session['acronim']}-"
#     elif accion == 'open':
#         select_lot.data_open = date
#         select_lot.tecnic_open = session['acronim']
#         select_lot.status = 'O'
#         send_text = f"{date} - {session['acronim']}-"
#     else:
#         return 'False'

#     session1.commit()
#     return f'True_{send_text}'


# @app.route('/info_edit_lot', methods=['POST'])
# @requires_auth
# def info_edit_lot():
#     '''
#         Caviem l'estat del lot a la BD
#     '''
#     id_lot = request.form.get("id_lot")

#     select_lot = session1.query(Lots).filter(Lots.id == id_lot).first()
#     if select_lot is None:
#         return 'False/-/False'

#     dict_lot = {}
#     dict_lot['id'] = select_lot.id
#     dict_lot['type_lot'] = select_lot.type_lot
#     dict_lot['lot_name'] = select_lot.lot_name
#     dict_lot['reference'] = select_lot.reference
#     dict_lot['trademark'] = select_lot.trademark
#     dict_lot['preserved_in'] = select_lot.preserved_in
#     dict_lot['stock_minimum'] = select_lot.stock_minimum
#     dict_lot['date_arrived'] = select_lot.date_arrived
#     dict_lot['supplier_lot'] = select_lot.supplier_lot
#     dict_lot['expiry'] = select_lot.expiry
#     dict_lot['internal_lot'] = select_lot.internal_lot
#     dict_lot['tecnic'] = select_lot.tecnic
#     dict_lot['data_open'] = select_lot.data_open
#     dict_lot['tecnic_open'] = select_lot.tecnic_open
#     dict_lot['data_close'] = select_lot.data_close
#     dict_lot['tecnic_close'] = select_lot.tecnic_close
#     dict_lot['observations'] = select_lot.observations
#     dict_lot['status'] = select_lot.status
    
#     json_text = json.dumps(dict_lot)

#     return f'True/-/{json_text}'
