from flask import render_template, request, flash, send_file
from app import app
from app.utils import requires_auth, list_desciption_lots, list_cost_center
from app.models import session1, Lots, Stock_lots
from sqlalchemy import func, Integer
from sqlalchemy.sql import cast
from werkzeug.utils import secure_filename
import os
from config import main_dir_docs
from docxtpl import DocxTemplate, R
import subprocess


@app.route('/search_lots', methods=['POST'])
@requires_auth
def search_lots():
    '''
        1 - Recollim la informació de l'html
        2 - Busquem a la BD amb la informació que ens han facilitat
        2.1 - Si no es troba coincidència retornem un missatge d'error a l'html
        2.2 - Si es troba coincidència retornarem el que hem trobat a l'html.

        :param str search_code: Codi a buscar.

        :return: La informació dels lots trobada i un int que és l'id de lot.
        :rtype: render_template, object, int
    '''
    search_code = request.form['search_code']
    code_panel = request.form['code_panel_search']

    if code_panel == '':
        select_lot = session1.query(Stock_lots).filter(
            Stock_lots.id.in_(
                session1.query(func.min(Stock_lots.id)).filter(
                    func.lower(Stock_lots.catalog_reference) == search_code.lower(),
                    Stock_lots.spent == 0
                ).group_by(Stock_lots.lot)
            )
        ).all()
        if not select_lot:
            select_lot = session1.query(Stock_lots).filter(
                Stock_lots.id.in_(
                    session1.query(func.min(Stock_lots.id)).filter(
                        func.lower(Stock_lots.description) == search_code.lower(),
                        Stock_lots.spent == 0
                    ).group_by(Stock_lots.lot)
                )
            ).all()
    else:
        select_lot = session1.query(Stock_lots).filter(
            Stock_lots.id.in_(
                session1.query(func.min(Stock_lots.id)).filter(
                    func.lower(Stock_lots.catalog_reference) == search_code.lower(),
                    func.lower(Stock_lots.code_panel) == code_panel.lower(),
                    Stock_lots.spent == 0
                ).group_by(Stock_lots.lot)
            )
        ).all()
        if not select_lot:
            select_lot = session1.query(Stock_lots).filter(
                Stock_lots.id.in_(
                    session1.query(func.min(Stock_lots.id)).filter(
                        func.lower(Stock_lots.description) == search_code.lower(),
                        func.lower(Stock_lots.code_panel) == code_panel.lower(),
                        Stock_lots.spent == 0
                    ).group_by(Stock_lots.lot)
                )
            ).all()
    if not select_lot:
        flash(f"No s'ha trobat cap coincidencia amb el text entrat --> {search_code}", "warning")
        return render_template('home.html', list_desciption_lots=list_desciption_lots(),
                               list_cost_center=list_cost_center())

    return render_template('search_lot.html', select_lot=select_lot, lot=select_lot[0],
                           list_desciption_lots=list_desciption_lots())


@app.route("/download_docs", methods=["POST"])
@requires_auth
def download_docs():
    """
        1 - Recollim la informació
        2 - Preparem la ruta on estan els documents
        3 - Descarreguem el document i li formatem el nom.

        :param str dir_name: Nom de la carpeta on hi ha el document.
        :param str name_doc: Nom del document.

        :return: Retorna l'arxiu que ha estat carregat previament
        :rtype: archive
    """
    dir_name = request.form["dir_name"]
    name_doc = request.form["name_doc"]

    path = f"{main_dir_docs}/{dir_name}/{name_doc}"
    return send_file(path, as_attachment=True, download_name=f"{dir_name}_{name_doc}")


@app.route('/upload_docs', methods=['POST'])
@requires_auth
def upload_docs():
    '''
        1 - Recollim la informació de l'ajax
        2 - Busquem si aquest lot va ser introduït amb algun lot addicional
        3 - Mirem quin nom li toca al document
        4 - Guardem el document a la carpeta que toca.
        5 - Actualitzem a stock_lots els camps que facin falta.
        6 - Retornem la resposta a l'ajax de si el procés ha anat bé o no.

        :param str dir_name: Nom de la carpeta on hi ha el document.
        :param str group_insert: Referència que ens diu quins stock_lots s'han inserit junts.
        :param str file: Document que ens carrega l'usuari.

        :return: Retorna True o False, si és True també enviem diverses dades que es necessiten.
        :rtype: json
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
            max_number_filename = session1.query(func.max(cast(Stock_lots.delivery_note, Integer))).scalar()
            dirname = 'albarans'
        elif dir_name == 'certificate':
            max_number_filename = session1.query(func.max(cast(Stock_lots.certificate, Integer))).scalar()
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


@app.route('/create_qc', methods=['POST'])
@requires_auth
def create_qc():
    '''
        1 - Recollim la informació de l'ajax
        2 - Fem una cerca amb les dades que ens han facilitat i recollim el número de sublots i el nombre total d'unitats introduïdes.
        3 - Agafem una línia de la bd per lot, iterem sobre el que en torni la consulta i tractem les dades.
        4 - Creem una taula de diccionaris amb tota la informació requerida
        5 - Carreguem la plantilla del qc
        6 - Creem un context amb la informació que omplirà la plantilla
        7 - Omplim la plantilla i la guardem amb el nom adequat.
        8 - Transformem el document a pdf
        9 - Retornem un True més el nom de la plantilla si tot ha anat bé.
        9.1 - Retornem un False més un missatge d'error si alguna cosa ha fallat

        :param str group_insert: Identificador que relaciona els lost d'un article.
        :param str catalog_reference: Codi del proveïdor

        :return: True i el nom del fitxer creat o False i una explicació per l'usuari.
        :rtype: json
    '''
    group_insert = request.form.get("group_insert")
    catalog_reference = request.form.get("catalog_reference")
    # split_internal_lot = internal_lot.split('_')
    try:
        # info_history = session1.query(Stock_lots, Lot_consumptions).\
        #                         outerjoin(Lot_consumptions, Stock_lots.id == Lot_consumptions.id_lot).\
        #                         filter(Stock_lots.lot == lot).\
        #                         filter(Stock_lots.catalog_reference == catalog_reference).\
        #                         filter(or_(Stock_lots.internal_lot.like(f"%{split_internal_lot[0]}%"))).\
        #                         all()
        select_lot = session1.query(Lots).filter_by(catalog_reference=catalog_reference, active=1).all()
        if len(select_lot) == 1:
            unit_sublots = 0
        else:
            unit_sublots = len(select_lot)

        select_unit_lots = session1.query(Stock_lots).filter(
            func.lower(Stock_lots.catalog_reference) == catalog_reference.lower(),
            Stock_lots.group_insert == group_insert).all()
        total_units = len(select_unit_lots)

        info_history = session1.query(Stock_lots).filter(
            Stock_lots.id.in_(
                session1.query(func.min(Stock_lots.id)).filter(
                    func.lower(Stock_lots.catalog_reference) == catalog_reference.lower(),
                    Stock_lots.group_insert == group_insert
                ).group_by(Stock_lots.lot)
            )
        ).all()
        if not info_history:
            return 'False_//_No hi ha informació sobre aquest lot.'
        # total_units = 0
        info_lots = []
        # difernets_lots = []
        # info_kit = []
        # for stock_lot, consumption in info_history:
        for stock_lot in info_history:
            dict_lots = {}
            # dict_lots['id'] = consumption.id
            # dict_lots['id_lot'] = consumption.id_lot
            # try:
            #     dict_lots['date_open'] = consumption.date_open
            #     dict_lots['user_open'] = consumption.user_open
            #     dict_lots['date_close'] = consumption.date_close
            #     dict_lots['user_close'] = consumption.user_close
            #     dict_lots['observations_open'] = consumption.observations_open
            #     dict_lots['observations_close'] = consumption.observations_close
            # except Exception:
            #     dict_lots['date_open'] = ''
            #     dict_lots['user_open'] = ''
            #     dict_lots['date_close'] = ''
            #     dict_lots['user_close'] = ''
            #     dict_lots['observations_open'] = ''
            #     dict_lots['observations_close'] = ''

            # dict_lots['id'] = stock_lot.id
            # dict_lots['id_lot'] = stock_lot.id_lot
            dict_lots['catalog_reference'] = stock_lot.catalog_reference
            dict_lots['manufacturer'] = stock_lot.manufacturer
            dict_lots['description'] = stock_lot.description
            dict_lots['analytical_technique'] = stock_lot.analytical_technique
            dict_lots['id_reactive'] = stock_lot.id_reactive
            dict_lots['code_SAP'] = stock_lot.code_SAP
            dict_lots['code_LOG'] = stock_lot.code_LOG
            dict_lots['temp_conservation'] = stock_lot.temp_conservation
            dict_lots['description_subreference'] = stock_lot.description_subreference
            dict_lots['react_or_fungible'] = stock_lot.react_or_fungible
            dict_lots['date_expiry'] = stock_lot.date_expiry
            dict_lots['lot'] = stock_lot.lot
            dict_lots['spent'] = stock_lot.spent
            dict_lots['reception_date'] = stock_lot.reception_date
            dict_lots['units_lot'] = stock_lot.units_lot
            dict_lots['internal_lot'] = stock_lot.internal_lot
            # dict_lots['transport_conditions'] = stock_lot.transport_conditions
            if stock_lot.transport_conditions == 'Correcta':
                dict_lots['transport_conditions'] = 'C'
            else:
                dict_lots['transport_conditions'] = 'NC'
            if stock_lot.packaging == 'Adequat':
                dict_lots['packaging'] = 'C'
            else:
                dict_lots['packaging'] = 'NC'
            dict_lots['inspected_by'] = stock_lot.inspected_by
            dict_lots['date_inspected'] = stock_lot.date_inspected
            dict_lots['observations_inspection'] = stock_lot.observations_inspection
            dict_lots['state'] = stock_lot.state
            dict_lots['comand_number'] = stock_lot.comand_number
            dict_lots['revised_by'] = stock_lot.revised_by
            dict_lots['date_revised'] = stock_lot.date_revised
            if stock_lot.delivery_note == '':
                dict_lots['delivery_note'] = 'No'
            else:
                dict_lots['delivery_note'] = 'SI'
            if stock_lot.certificate == '':
                dict_lots['certificate'] = 'No'
            else:
                dict_lots['certificate'] = 'SI'
            dict_lots['type_doc_certificate'] = stock_lot.type_doc_certificate
            dict_lots['type_doc_delivery'] = stock_lot.type_doc_delivery
            dict_lots['group_insert'] = stock_lot.group_insert
            dict_lots['code_panel'] = stock_lot.code_panel
            dict_lots['location'] = stock_lot.location
            dict_lots['supplier'] = stock_lot.supplier
            dict_lots['cost_center_stock'] = stock_lot.cost_center_stock

            # total_units += int(stock_lot.units_lot)
            info_lots.append(dict_lots)

            # if stock_lot.id_reactive not in difernets_lots:
            #     difernets_lots.append(stock_lot.id_reactive)
            #     info_kit.append(dict_lots)

        doc = DocxTemplate(f'{main_dir_docs}/plantillas/LDG_REG_INS_generic_draft.docx')
        break_page = R("\f")
        break_line = R("\n")
        context = {
            "break_page": break_page,
            "break_line": break_line,
            "info_lots": info_lots,
            "total_units": total_units,
            "num_subunits": unit_sublots,
            # "info_kit": info_kit,
        }
        doc.render(context)

        name = 'LDG_REG_INS_generic_draft'
        filepath = os.path.join(f'{main_dir_docs}/qc', f'{name}.docx')
        doc.save(filepath)

        # Ruta del archivo de Word de entrada
        input_docx = f'{main_dir_docs}/qc/{name}.docx'

        # Ruta del archivo PDF de salida
        output_pdf = f'{main_dir_docs}/qc/'

        try:
            # Comando para convertir el archivo DOCX a PDF
            command = ['libreoffice', '--convert-to', 'pdf', '--outdir', output_pdf, input_docx]

            # Ejecutar el comando
            subprocess.run(command, check=True)

            # Mostrar mensaje si la conversión fue exitosa
            print("La conversión a PDF se ha completado con éxito.")

        except subprocess.CalledProcessError as e:
            # Mostrar mensaje si la conversión falló
            print(f"Error: La conversión a PDF ha fallado. Código de salida: {e.returncode}")
    except Exception:
        return "False_ No s'ha pogut accedir a la informació dels consums."
    return f'True_//_{name}.pdf'
