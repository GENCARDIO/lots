from flask import render_template, request, flash, redirect, send_file, session
from app import app
from app.utils import get_data, create_excel, check_finish_sample, insert_register, read_excel, convert_xls_with_xlsx,\
                      check_excel, add_date, search_hgvsg, check_duplidates, instant_date, requires_auth
from app.models import IP_HOME, session1, Lots, Logs
from sqlalchemy import or_, func, and_
from werkzeug.utils import secure_filename
import os
import jwt
import json
# import requests


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


@app.route('/insert_lot', methods=['POST'])
@requires_auth
def insert_lot():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    type_lot = request.form.get("type_lot")
    lot_name = request.form.get("lot_name")
    reference = request.form.get("reference")
    trademark = request.form.get("trademark")
    preserved_in = request.form.get("preserved_in")
    stock_minimum = request.form.get("stock_minimum")
    date_arrived = request.form.get("date_arrived")
    supplier_lot = request.form.get("supplier_lot")
    expiry = request.form.get("expiry")
    internal_lot = request.form.get("internal_lot")
    tecnic = request.form.get("tecnic")
    observations = request.form.get("observations")

    try:
        insert = Lots(type_lot=type_lot,
                      lot_name=lot_name,
                      reference=reference,
                      trademark=trademark,
                      preserved_in=preserved_in,
                      stock_minimum=stock_minimum,
                      date_arrived=date_arrived,
                      supplier_lot=supplier_lot,
                      expiry=expiry,
                      internal_lot=internal_lot,
                      tecnic=tecnic,
                      observations=observations,)
        session1.add(insert)
        session1.commit()
        return 'True'
    except Exception:
        # session1.rollback()
        return 'False'


@app.route('/search_lots', methods=['POST'])
@requires_auth
def search_lots():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    select_type = request.form.get("select_type")

    if select_type == 'Sanger':
        select_row = session1.query(Registres_sanger)\
            .filter(or_(Registres_sanger.confirmacio is None, Registres_sanger.confirmacio == ''))\
            .filter(Registres_sanger.tecnic == '').all()

        select_row_batch = session1.query(Registres_sanger.batch)\
            .filter(Registres_sanger.tecnic == session['acronim'])\
            .filter(Registres_sanger.confirmacio == '')\
            .distinct(Registres_sanger.batch).all()
        if not select_row:
            flash("No hi ha cap mostra pendent", "warning")
            return render_template('home.html')

        return render_template('select_register.html', select_row=select_row, select_type=select_type,
                               select_row_batch=select_row_batch)
    else:
        flash("Error, no s'ha pogut redirigir a la pàgina per seleccionar mostres.", "danger")
        return render_template('home.html')

####################################################
####################################################
####################################################

@app.route('/look_register', methods=['POST'])
@requires_auth
def look_register():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    type = request.form['type']

    if type == 'Sanger':
        list_data = get_data(type)
    elif type == 'Extraccio':
        list_data = get_data(type)
    else:
        flash("Error no s'ha pogut fer la cerca", "danger")
        return render_template('home.html')

    return render_template('show_data.html', list_data=list_data)


@app.route('/modify_register', methods=['POST'])
@requires_auth
def modify_register():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id_row = request.form.get("id_row")
    panel = request.form.get("panel")
    f_index = request.form.get("f_index")
    mostra = request.form.get("mostra")
    external_code = request.form.get("external_code")
    date_entered = request.form.get("date_entered")
    limit_date = request.form.get("limit_date")
    end_analysis = request.form.get("end_analysis")
    gene = request.form.get("gene")
    isoform = request.form.get("isoform")
    intro_exon = request.form.get("intro_exon")
    c_code = request.form.get("c_code")
    nucleotides = request.form.get("nucleotides")
    aminoacid = request.form.get("aminoacid")
    sequence = request.form.get("sequence")
    confirmation = request.form.get("confirmation")
    technician = request.form.get("technician")
    confirmation_date = request.form.get("confirmation_date")
    observations_lab = request.form.get("observations_lab")
    num_pcr = request.form.get("num_pcr")
    num_db = request.form.get("num_db")
    validation = request.form.get("validation")
    validation_date = request.form.get("validation_date")
    observations_data_manager = request.form.get("observations_data_manager")
    status = request.form.get("status")
    days_later = request.form.get("days_later")
    reason_change = request.form.get("reason_change")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id_row).first()

    if select_row is None:
        return 'False'

    date = instant_date()

    if select_row.panell_mlpa_qpcr != panel:
        add_log = Logs(field='panell_mlpa_qpcr', old_info=select_row.panell_mlpa_qpcr, new_info=panel,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.panell_mlpa_qpcr = panel

    if select_row.familiar_index != f_index:
        add_log = Logs(field='familiar_index', old_info=select_row.familiar_index, new_info=f_index,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.familiar_index = f_index

    if select_row.mostra != mostra:
        add_log = Logs(field='mostra', old_info=select_row.mostra, new_info=mostra,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.mostra = mostra

    if select_row.codi_extern != external_code:
        add_log = Logs(field='codi_extern', old_info=select_row.codi_extern, new_info=external_code,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.codi_extern = external_code

    if select_row.data_entrada != date_entered:
        add_log = Logs(field='data_entrada', old_info=select_row.data_entrada, new_info=date_entered,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.data_entrada = date_entered

    if select_row.data_limit != limit_date:
        add_log = Logs(field='data_limit', old_info=select_row.data_limit, new_info=limit_date,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.data_limit = limit_date

    if select_row.fi_analisi != end_analysis:
        add_log = Logs(field='fi_analisi', old_info=select_row.fi_analisi, new_info=end_analysis,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.fi_analisi = end_analysis

    if select_row.gen != gene:
        add_log = Logs(field='gen', old_info=select_row.gen, new_info=gene,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.gen = gene

    if select_row.isoforma != isoform:
        add_log = Logs(field='isoforma', old_info=select_row.isoforma, new_info=isoform,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.isoforma = isoform

    if select_row.intro_exo != intro_exon:
        add_log = Logs(field='intro_exo', old_info=select_row.intro_exo, new_info=intro_exon,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.intro_exo = intro_exon

    if select_row.posicio_cromosomica != c_code:
        add_log = Logs(field='posicio_cromosomica', old_info=select_row.posicio_cromosomica, new_info=c_code,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.posicio_cromosomica = c_code

    if select_row.nucleotid != nucleotides:
        add_log = Logs(field='nucleotid', old_info=select_row.nucleotid, new_info=nucleotides,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.nucleotid = nucleotides

    if select_row.aminoacid != aminoacid:
        add_log = Logs(field='aminoacid', old_info=select_row.aminoacid, new_info=aminoacid,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.aminoacid = aminoacid

    if select_row.sequencia != sequence:
        add_log = Logs(field='sequencia', old_info=select_row.sequencia, new_info=sequence,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.sequencia = sequence

    if select_row.confirmacio != confirmation:
        add_log = Logs(field='confirmacio', old_info=select_row.confirmacio, new_info=confirmation,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.confirmacio = confirmation

    if select_row.tecnic != technician:
        add_log = Logs(field='tecnic', old_info=select_row.tecnic, new_info=technician,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.tecnic = technician

    if select_row.data_confirmacio != confirmation_date:
        add_log = Logs(field='data_confirmacio', old_info=select_row.data_confirmacio, new_info=confirmation_date,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.data_confirmacio = confirmation_date

    if select_row.observacions_laboratori != observations_lab:
        add_log = Logs(field='observacions_laboratori', old_info=select_row.observacions_laboratori,
                       new_info=observations_lab, reason_change=reason_change, user=session['user'],
                       id_user=session['idClient'])
        session1.add(add_log)
        select_row.observacions_laboratori = observations_lab

    if select_row.num_pcr != num_pcr:
        add_log = Logs(field='num_pcr', old_info=select_row.num_pcr, new_info=num_pcr,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.num_pcr = num_pcr

    if select_row.num_db != num_db:
        add_log = Logs(field='num_db', old_info=select_row.num_db, new_info=num_db,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.num_db = num_db

    if select_row.validacio != validation:
        add_log = Logs(field='validacio', old_info=select_row.validacio, new_info=validation,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.validacio = validation

    if select_row.data_validacio != validation_date:
        add_log = Logs(field='data_validacio', old_info=select_row.data_validacio, new_info=validation_date,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.data_validacio = validation_date

    if select_row.observacions_gestor_dades != observations_data_manager:
        add_log = Logs(field='observacions_gestor_dades', old_info=select_row.observacions_gestor_dades,
                       new_info=observations_data_manager, reason_change=reason_change, user=session['user'],
                       id_user=session['idClient'])
        session1.add(add_log)
        select_row.observacions_gestor_dades = observations_data_manager

    if select_row.status != status:
        add_log = Logs(field='status', old_info=select_row.status, new_info=status,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.status = status

    if select_row.dies_retard != days_later:
        add_log = Logs(field='dies_retard', old_info=select_row.dies_retard, new_info=days_later,
                       reason_change=reason_change, user=session['user'], id_user=session['idClient'],
                       date=date)
        session1.add(add_log)
        select_row.dies_retard = days_later

    session1.commit()

    return 'True'


@app.route('/add_register', methods=['POST'])
@requires_auth
def add_register():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    panel = request.form.get("panel")
    f_index = request.form.get("f_index")
    mostra = request.form.get("mostra")
    external_code = request.form.get("external_code")
    date_entered = request.form.get("date_entered")
    limit_date = request.form.get("limit_date")
    end_analysis = request.form.get("end_analysis")
    gene = request.form.get("gene")
    isoform = request.form.get("isoform")
    intro_exon = request.form.get("intro_exon")
    c_code = request.form.get("c_code")
    nucleotides = request.form.get("nucleotides")
    aminoacid = request.form.get("aminoacid")
    sequence = request.form.get("sequence")
    confirmation = request.form.get("confirmation")
    technician = request.form.get("technician")
    confirmation_date = request.form.get("confirmation_date")
    observations_lab = request.form.get("observations_lab")
    num_pcr = request.form.get("num_pcr")
    num_db = request.form.get("num_db")
    validation = request.form.get("validation")
    validation_date = request.form.get("validation_date")
    observations_data_manager = request.form.get("observations_data_manager")
    status = request.form.get("status")
    days_later = request.form.get("days_later")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.mostra == mostra).first()
    if select_row is not None:
        return 'False_d'

    try:
        insert_register = Registres_sanger(panell_mlpa_qpcr=panel, familiar_index=f_index, mostra=mostra,
                                           codi_extern=external_code, data_entrada=date_entered, data_limit=limit_date,
                                           fi_analisi=end_analysis, gen=gene, isoforma=isoform, intro_exo=intro_exon,
                                           posicio_cromosomica=c_code, nucleotid=nucleotides, aminoacid=aminoacid,
                                           sequencia=sequence, confirmacio=confirmation, tecnic=technician,
                                           data_confirmacio=confirmation_date, observacions_laboratori=observations_lab,
                                           num_pcr=num_pcr, num_db=num_db, validacio=validation,
                                           data_validacio=validation_date, status=status, dies_retard=days_later,
                                           observacions_gestor_dades=observations_data_manager)
        session1.add(insert_register)
        session1.commit()
        return f'True_{insert_register.id}'
    except Exception:
        session1.rollback()
        return 'False'


# Seleccio Mostres
@app.route('/select_register', methods=['POST'])
@requires_auth
def select_register():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    select_type = request.form.get("select_type")

    if select_type == 'Sanger':
        select_row = session1.query(Registres_sanger)\
            .filter(or_(Registres_sanger.confirmacio is None, Registres_sanger.confirmacio == ''))\
            .filter(Registres_sanger.tecnic == '').all()

        select_row_batch = session1.query(Registres_sanger.batch)\
            .filter(Registres_sanger.tecnic == session['acronim'])\
            .filter(Registres_sanger.confirmacio == '')\
            .distinct(Registres_sanger.batch).all()
        if not select_row:
            flash("No hi ha cap mostra pendent", "warning")
            return render_template('home.html')

        return render_template('select_register.html', select_row=select_row, select_type=select_type,
                               select_row_batch=select_row_batch)
    else:
        flash("Error, no s'ha pogut redirigir a la pàgina per seleccionar mostres.", "danger")
        return render_template('home.html')


@app.route('/download_excel', methods=['POST'])
@requires_auth
def download_excel():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    batch = request.form['n_batch']
    username = session['acronim']

    select_row = session1.query(Registres_sanger)\
        .filter(Registres_sanger.tecnic == username)\
        .filter(Registres_sanger.batch == batch)\
        .filter(Registres_sanger.confirmacio == '').all()
    if not select_row:
        flash("Error, No s'ha trobat cap mostra assignada al nom del técnic", "danger")
        return render_template('home.html')

    success = create_excel(select_row)

    if not success:
        flash("Error, no s'ha pogut crear el document", "danger")
        return render_template('home.html')
    else:
        path = f"{main_dir_docs}/registres.csv"
        return send_file(path, as_attachment=True)


@app.route('/assign_register', methods=['POST'])
@requires_auth
def assign_register():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id_tr = request.form.get("id_tr")
    username = request.form.get("username")
    name_batch = request.form.get("name_batch")

    split_id = id_tr.split(',')
    for id in split_id:
        select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id).first()

        if select_row is None:
            return 'False'

        date = instant_date()

        select_row.tecnic = username
        select_row.data_assignacio = date
        select_row.batch = name_batch

    session1.commit()

    return 'True'


@app.route('/consult_registers_assign', methods=['POST'])
@requires_auth
def consult_registers_assign():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    list_register = []
    username = request.form.get("username")
    batch = request.form.get("batch")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.tecnic == username)\
        .filter(Registres_sanger.batch == batch)\
        .filter(Registres_sanger.confirmacio == '').all()
    if len(select_row) == 0:
        return list_register
    else:
        for row in select_row:
            dict_register = {}
            dict_register['sample'] = row.mostra
            dict_register['gene'] = row.gen
            dict_register['isoform'] = row.isoforma
            dict_register['intron-exon'] = row.intro_exo
            dict_register['code_g'] = row.posicio_cromosomica
            dict_register['id'] = row.id
            list_register.append(dict_register)
    return list_register


@app.route('/release_register', methods=['POST'])
@requires_auth
def release_register():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id = request.form.get("id")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id).first()
    if select_row is None:
        return 'False'
    else:
        select_row.tecnic = ''
        select_row.data_assignacio = ''
        session1.commit()

        row_data = {"id": select_row.id, "tecnic": select_row.tecnic, "panell_mlpa_qpcr": select_row.panell_mlpa_qpcr,
                    "mostra": select_row.mostra, "data_limit": select_row.data_limit, "gen": select_row.gen,
                    "isoforma": select_row.isoforma, "intro_exo": select_row.intro_exo,
                    "posicio_cromosomica": select_row.posicio_cromosomica, "nucleotid": select_row.nucleotid,
                    "observacions_laboratori": select_row.observacions_laboratori, "sequencia": select_row.sequencia}
        json_string = json.dumps(row_data)
    return f"True{json_string}"


# Entrada de resultats
@app.route('/add_results', methods=['POST'])
@requires_auth
def add_results():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    select_type = request.form.get("result_type")

    if select_type == 'Sanger':
        select_row = session1.query(Registres_sanger)\
            .filter(or_(Registres_sanger.confirmacio is None, Registres_sanger.confirmacio == ''))\
            .filter(Registres_sanger.tecnic != '').all()
        if not select_row:
            flash("No hi ha cap mostra pendent", "warning")
            return render_template('home.html')
    else:
        flash("Error, no s'ha pogut redirigir a la pàgina per seleccionar mostres.", "danger")
        return render_template('home.html')

    return render_template('add_results.html', select_row=select_row, select_type=select_type)


@app.route('/add_results_db', methods=['POST'])
@requires_auth
def add_results_db():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id_row = request.form.get("id_row")
    confirmation = request.form.get("confirmation")
    date_confirmation = request.form.get("date_confirmation")
    num_pcr = request.form.get("num_pcr")
    num_db = request.form.get("num_db")
    observations_lab = request.form.get("observations_lab")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id_row).first()
    if select_row is None:
        return 'False_id'

    select_row.confirmacio = confirmation
    select_row.data_confirmacio = date_confirmation
    select_row.num_pcr = num_pcr
    select_row.num_db = num_db
    select_row.observacions_laboratori = observations_lab

    session1.commit()

    success = check_finish_sample(select_row.mostra, 'tecnic')

    return success


@app.route('/release_sample', methods=['POST'])
@requires_auth
def release_sample():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id_row = request.form.get("id_row")
    num_pcr = request.form.get("num_pcr")
    observations_lab = request.form.get("observations_lab")
    delete_tecnic = request.form.get("delete_tecnic")
    n_bigdye = request.form.get("n_bigdye")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id_row).first()
    if select_row is None:
        return 'False_id'

    try:
        select_row.num_pcr = num_pcr
        select_row.observacions_laboratori = observations_lab
        select_row.num_db = n_bigdye
        if delete_tecnic == 'Si':
            select_row.tecnic = ''
            select_row.data_assignacio = ''
        session1.commit()

        return 'True'
    except Exception:
        return 'False_error'


# Inserir registres
@app.route('/insert_home')
@requires_auth
def insert_home():
    return render_template('insert.html')


@app.route('/insert_by_docs', methods=['POST'])
@requires_auth
def insert_by_docs():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    type_selected = request.form.get("type_selected")
    llistaAcceptats = ['xlsx', 'xls']

    # if type_selected == 'familiars':
    #     hgvsg = request.form.get("hgvsg")

    # obtenemos el archivo del input "archivo"
    f = request.files['archivo']
    filename = secure_filename(f.filename)

    # Check per saber si han entrat l'excel que tocaba
    check_success = check_excel(type_selected, filename)
    if not check_success:
        flash("Error, el nom de l'archiu que has introduït no correspon amb els que tenim registrats.", "danger")
        return render_template('insert.html')

    split_dirname = filename.split('.')
    if len(split_dirname) > 1:
        # Mirem que el document sigui dels que tenim permesos.
        if split_dirname[len(split_dirname) - 1] not in llistaAcceptats:
            flash("Error, el format del document no és correcta.")
            return render_template('insert.html')
        else:
            # Guardem l'archiu que ens ha donat l'usuari
            f.save(os.path.join(f'{main_dir_docs}/', str(filename)))

            # Si l'archiu es .xls s'ha de convertir a xlsx
            if split_dirname[1] == 'xls':
                success = convert_xls_with_xlsx(split_dirname[0])
                filename = {split_dirname[0]}
                if not success:
                    flash("Error, l'archiu era .xls i no s'ha pogut convertir.", "danger")
                    return render_template('insert.html')

            # Lleguim el document i ho guardem tot en una llista de diccionaris
            list_samples = read_excel(split_dirname[0], type_selected)
            if len(list_samples) == 0:
                flash("Error, no hem trobat dades al document facilitat.", "danger")
                return render_template('insert.html')

            # Comprvem que les mostres no estiguin ja inserides a la bd
            found_duplicate, samples_duplicates = check_duplidates(list_samples)
            if (found_duplicate):
                flash(f"Les mostres no s'han inserit, ja que els codis de les mostres {samples_duplicates} ja estan \
                      inserides a la bd, si no és un error si us plau modifiqueu les mostres amb _rep i torneu a \
                      carregar el document, gràcies.", "warning")
                return render_template('home.html')

            # Insertem les dades a la BD
            inser_success = insert_register(list_samples)
            if not inser_success:
                flash("Error, no s'han inserit les mostres a la bd.", "danger")
                return render_template('insert.html')
            else:
                flash("Les mostres s'han introduït correctament", "success")
    else:
        if filename == '':
            flash("Error, s'ha de carregar mínim un document.", "danger")
            return render_template('insert.html')
        else:
            flash("Error, no s'ha pogut reconèixer l'extensió del document.", "danger")
            return render_template('insert.html')

    return render_template('home.html', block_back=True)


@app.route('/insert_manual', methods=['POST'])
@requires_auth
def insert_manual():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    panel = request.form.get("panel")
    f_index = request.form.get("f_index")
    mostra = request.form.get("mostra")
    external_code = request.form.get("external_code")
    date_entered = request.form.get("date_entered")
    gene = request.form.get("gene")
    isoform = request.form.get("isoform")
    intro_exon = request.form.get("intro_exon")
    c_code = request.form.get("c_code")
    nucleotides = request.form.get("nucleotides")
    aminoacid = request.form.get("aminoacid")
    sequence = request.form.get("sequence")

    sample_list = []
    sample_dict = {'sample': mostra}
    sample_list.append(sample_dict)

    # Comprvem que les mostres no estiguin ja inserides a la bd
    found_duplicate, samples_duplicates = check_duplidates(sample_list)
    if (found_duplicate):
        text = f'False//La mostra {samples_duplicates} ja està a la bd, modifiqueu les mostres amb _rep i torneu-la a inserir'
        return text

    if 'AP' in mostra or 'ap' in mostra:
        weeks = 1
    else:
        weeks = 3

    date_now, date_end = add_date(date_entered, weeks)

    # select_row = session1.query(Registres_sanger).filter(Registres_sanger.mostra == mostra).first()
    # if select_row is not None:
    #     return 'False_d'

    try:
        if 'ap' in str(mostra) or 'AP' in str(mostra):
            weeks = 1
        else:
            weeks = 3
        list_samples = []
        dict_samples = {}
        dict_samples['panell'] = panel
        dict_samples['index'] = f_index
        dict_samples['sample'] = str(mostra) if str(mostra) != 'nan' else ''
        dict_samples['code'] = str(external_code) if str(external_code) != 'nan' else ''
        date_now, date_end = add_date('', weeks)
        dict_samples['date_entered'] = date_now
        dict_samples['date_limit'] = date_end
        dict_samples['gene'] = gene
        dict_samples['isoform'] = isoform
        dict_samples['intron-exon'] = intro_exon
        dict_samples['code_g'] = c_code
        dict_samples['sequence'] = sequence
        dict_samples['aminoacid'] = aminoacid
        dict_samples['nucleotid'] = nucleotides
        list_samples.append(dict_samples)

        success = insert_register(list_samples)

        # insert_register = Registres_sanger(panell_mlpa_qpcr=panel, familiar_index=f_index, mostra=mostra,
        #                                    codi_extern=external_code, data_entrada=date_now, data_limit=date_end,
        #                                    gen=gene, isoforma=isoform, intro_exo=intro_exon,
        #                                    posicio_cromosomica=c_code, nucleotid=nucleotides, aminoacid=aminoacid,
        #                                    sequencia=sequence)
        # session1.add(insert_register)
        # session1.commit()
        return str(success)
    except Exception:
        # session1.rollback()
        return 'False'


@app.route('/search_family', methods=['POST'])
@requires_auth
def search_family():
    '''
        Recullim la informació, mirem que la no estigui duplicada i si no ho esta afegim la informació a la BD.
    '''
    hgvsg = request.form.get("hgvsg")

    dict_rb = search_hgvsg(hgvsg)

    return dict_rb


@app.route('/received_primer', methods=['POST'])
@requires_auth
def received_primer():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id = request.form.get("id_tr")
    username = request.form.get("username")

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id).first()
    if select_row is None:
        return 'False'
    select_row.dissenyar_primer = ''

    date = instant_date()

    add_log = Logs(field='active primer', old_info='blocked', new_info='active',
                   reason_change='arrived primer', user=username,
                   id_user=session['idClient'], date=date)
    session1.add(add_log)

    session1.commit()

    return 'True'


# Validació facultativa
@app.route('/collect_pending_validations', methods=['POST'])
@requires_auth
def collect_pending_validations():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    select_type = request.form.get("validation_type")

    if select_type == 'Sanger':
        select_row = session1.query(Registres_sanger)\
            .filter(Registres_sanger.confirmacio != '')\
            .filter(Registres_sanger.tecnic != '')\
            .filter(Registres_sanger.validacio == '').all()

        if not select_row:
            flash("No hi ha cap mostra pendent de validar", "warning")
            return render_template('home.html')

        select_row_end = []
        for row in select_row:
            select_row_aux = session1.query(Registres_sanger).filter(Registres_sanger.mostra == row.mostra).all()
            sample_finish = True
            for row2 in select_row_aux:
                if row2.confirmacio is None or row2.confirmacio == '':
                    sample_finish = False

            if sample_finish:
                select_row_end.append(row)

        if len(select_row_end) == 0:
            flash("No hi ha cap mostra pendent de validar", "warning")
            return render_template('home.html')

        subquery = (
            session1.query(Registres_sanger.mostra, func.max(Registres_sanger.id).label("max_id"))
            .group_by(Registres_sanger.mostra)
            .subquery()
        )

        # Consulta principal para unir la tabla con la subconsulta
        query = (
            session1.query(Registres_sanger)
            .join(subquery, and_(Registres_sanger.mostra == subquery.c.mostra, Registres_sanger.id == subquery.c.max_id))
            .filter(Registres_sanger.informe_pendent == "T")
        )

        # Obtener los resultados
        resultados = query.all()

        return render_template('validation_facultative.html', select_row=select_row_end, select_type=select_type,
                               sample_report=resultados)
    else:
        flash("Error, no s'ha pogut redirigir a la pàgina per seleccionar mostres.", "danger")
        return render_template('home.html')


@app.route('/validation', methods=['POST'])
@requires_auth
def validation():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    id_row = request.form.get("id_row")
    observations_gd = request.form.get("observations_gd")
    option_type = request.form.get("option_type")
    username = request.form.get("username")
    validation_facultative = request.form.get("validation_facultative")

    date = instant_date()

    select_row = session1.query(Registres_sanger).filter(Registres_sanger.id == id_row).first()
    if option_type == '1':  # Validar
        if select_row is not None:
            select_row.validacio = username
            select_row.data_validacio = date
            select_row.observacions_gestor_dades = observations_gd
            if '√' in select_row.confirmacio or select_row.confirmacio == 'Variant no trobada':
                select_row.resultat_validacio_facultativa = select_row.nucleotid
            else:
                select_row.resultat_validacio_facultativa = select_row.confirmacio
            session1.commit()

            success = check_finish_sample(select_row.mostra, 'validacio')

            return success
        else:
            return 'False_found2'
    elif option_type == '2':  # Validar i repetir
        if select_row is not None:
            select_row.validacio = username
            select_row.data_validacio = date
            select_row.observacions_gestor_dades = observations_gd
            if '√' in select_row.confirmacio or select_row.confirmacio == 'Variant no trobada':
                select_row.resultat_validacio_facultativa = select_row.nucleotid
            else:
                select_row.resultat_validacio_facultativa = select_row.confirmacio
            session1.commit()

            if 'ap' in select_row.mostra or 'AP' in select_row.mostra:
                weeks = 1
            else:
                weeks = 3

            if '_rep' not in select_row.mostra:
                sample = f'{select_row.mostra}_rep'
            else:
                parts = select_row.mostra.split('_')
                base = parts[0]
                suffix = parts[-1]

                if suffix.startswith('rep'):
                    try:
                        rep_number = int(suffix[3:]) + 1
                        sample = f'{base}_rep{rep_number}'
                    except Exception:
                        return 'False_sample2'
                else:
                    return 'False_sample2'

            list_samples = []
            dict_samples = {}
            dict_samples['panell'] = select_row.panell_mlpa_qpcr
            dict_samples['index'] = select_row.familiar_index
            dict_samples['sample'] = sample
            dict_samples['code'] = select_row.codi_extern
            date_now, date_end = add_date('', weeks)
            dict_samples['date_entered'] = date_now
            dict_samples['date_limit'] = date_end
            dict_samples['gene'] = select_row.gen
            dict_samples['isoform'] = select_row.isoforma
            dict_samples['intron-exon'] = select_row.intro_exo
            dict_samples['code_g'] = select_row.posicio_cromosomica
            dict_samples['sequence'] = select_row.sequencia
            dict_samples['aminoacid'] = select_row.aminoacid
            dict_samples['nucleotid'] = select_row.nucleotid
            list_samples.append(dict_samples)

            success = insert_register(list_samples)
            if success:
                return 'True'
            else:
                return 'False_insert'
        else:
            return 'False_found2'
    elif option_type == '3':  # Validar amb canvis
        if select_row is not None:
            select_row.validacio = username
            select_row.data_validacio = date
            select_row.observacions_gestor_dades = observations_gd
            select_row.resultat_validacio_facultativa = validation_facultative
            session1.commit()

            success = check_finish_sample(select_row.mostra, 'validacio')
            return success
        else:
            return 'False_found2'
    else:
        return "False_error"


@app.route('/report_made', methods=['POST'])
@requires_auth
def report_made():
    '''
        Creem la llista que passarem al html.
        Redirigim a estadistiques.html
    '''
    sample = request.form.get("sample")
    try:
        select_petitions = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample).all()
        for petition in select_petitions:
            petition.informe_pendent = 'F'
        session1.commit()
    except Exception:
        return 'False'
    return 'True'
