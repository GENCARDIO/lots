# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from app.models import Registres_sanger, session1, IP_HOME
from config import main_dir_docs
import pandas as pd
import os
from sqlalchemy import desc
from flask import session, redirect
from functools import wraps


# Authentication
def requires_auth(f):
    @wraps(f)
    def decorated_function(*args):
        if session['rol'] == 'None' or session['rol'] is None or session['rol'] == '':
            url = f'{IP_HOME}logout/You dont have permissions'
            return redirect(url)
        else:
            pass
        return f(*args)
    return decorated_function


def instant_date():
    date = datetime.now()
    format_date = date.strftime("%d/%m/%Y")
    return format_date


def add_date(date_now, weeks):
    if date_now is None or date_now == 'None' or date_now == '' or str(date_now) == 'nan':
        date = datetime.now()
    else:
        date_str = date_now.replace('-', '/')
        if date_str.endswith('00'):
            split_aux = date_str.split(' ')
            split_date = split_aux[0].split('/')
            if len(split_date[0]) == 4:
                date_str = f'{split_date[2]}/{split_date[1]}/{split_date[0]}'
            else:
                date_str = f'{split_date[0]}/{split_date[1]}/{split_date[2]}'
        date = datetime.strptime(date_str, "%d/%m/%Y")

    format_date = date.strftime("%d/%m/%Y")
    three_weeks = timedelta(weeks=weeks)
    new_date = date + three_weeks
    format_new_date = new_date.strftime("%d/%m/%Y")

    return format_date, format_new_date


def get_data(type):
    '''
        Recullim les dades de l'any en curs i les retornem

        :param str type: String que identifica quin registres hem d'extreure

        :return: Objecte amb la informació requerida per l'usuari.
        :rtype: Object
    '''
    date_now = datetime.now()
    year = date_now.year

    if type == 'Sanger':
        select_data = session1.query(Registres_sanger).filter(Registres_sanger.data_entrada.like(f"%{year}%")).all()
    else:
        select_data = []

    return select_data


def create_excel(select_row):
    '''
        Calculem eles indicadors i ho guardem en una llista de diccionaris.
        Creem un csv i posem la capçalera.
        Iterem la llista i anem posant la informació on toca
    '''
    try:
        # Crear arxiu nou
        archivo = f"{main_dir_docs}/registres.csv"
        csv = open(archivo, "w")
        # Inserir linies al csv
        csv.write('Mostra;Gen;Isoforma;Intró-Exó;Posició Genomica;Familiar-Index;data assignació;Sentit;Sequencia\n')
        for row in select_row:
            linia_csv = str(row.mostra) + ';'
            linia_csv += str(row.gen) + ';'
            linia_csv += str(row.isoforma) + ';'
            linia_csv += str(row.intro_exo) + ';'
            linia_csv += str(row.posicio_cromosomica) + ';'
            linia_csv += str(row.panell_mlpa_qpcr) + ';'
            linia_csv += str(row.data_assignacio) + ';'
            if str(row.panell_mlpa_qpcr) == 'NGS-LIC' or str(row.panell_mlpa_qpcr) == 'NGS-SUDD' or\
               str(row.panell_mlpa_qpcr) == 'NGS_SUDD' or str(row.panell_mlpa_qpcr) == 'NGS_LIC' or\
               str(row.panell_mlpa_qpcr) == 'SANGER_SUDD':
                if str(row.sequence) == 'nan' or len(row.sequence) < 5:
                    linia_csv += '2;'
                else:
                    linia_csv += '1;'
            else:
                linia_csv += '2;'
            linia_csv += str(row.sequencia)
            linia_csv += '\n'
            csv.write(linia_csv)
        csv.close()
        return True
    except Exception:
        return False


def check_finish_sample(sample, type):
    try:
        date = instant_date()
        select_row = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample).all()
        if not select_row:
            return 'False_sample'

        sample_finish = True

        for row in select_row:
            if type == 'tecnic':
                if row.confirmacio is None or row.confirmacio == '':
                    sample_finish = False
            else:
                if row.validacio is None or row.validacio == '':
                    sample_finish = False

        if sample_finish:
            if type == 'tecnic':
                for row in select_row:
                    row.fi_analisi = date
            else:
                for row in select_row:
                    row.informe_pendent = 'T'
            session1.commit()
            return 'True'
        else:
            return 'False_found'
    except Exception:
        return 'False_error'


def insert_register(list_samples):
    try:
        for sample in list_samples:
            insert = Registres_sanger(panell_mlpa_qpcr=sample['panell'],
                                      familiar_index=sample['index'],
                                      mostra=sample['sample'],
                                      codi_extern=sample['code'],
                                      patologia='',
                                      data_entrada=sample['date_entered'],
                                      data_limit=sample['date_limit'],
                                      fi_analisi='',
                                      gen=sample['gene'],
                                      isoforma=sample['isoform'],
                                      intro_exo=sample['intron-exon'],
                                      posicio_cromosomica=sample['code_g'],
                                      nucleotid=sample['nucleotid'],
                                      aminoacid=sample['aminoacid'],
                                      rs='',
                                      sequencia=sample['sequence'],
                                      confirmacio='',
                                      tecnic='',
                                      data_confirmacio='',
                                      observacions_laboratori='',
                                      num_pcr='',
                                      num_db='',
                                      validacio='',
                                      data_validacio='',
                                      observacions_gestor_dades='',
                                      status='',
                                      dies_retard='',
                                      data_assignacio='',
                                      informe_pendent='F',
                                      dissenyar_primer=sample['primer_design'],)
            session1.add(insert)
        session1.commit()
    except Exception:
        return False
    return True


def read_excel(name, type):
    list_samples = []

    try:
        # Llegim el directori i el convertim en una llista
        directori = f'{main_dir_docs}/{name}.xlsx'
        print(directori)
        df = pd.read_excel(directori, header=None)
        list_excel = df.values.tolist()
    except Exception:
        print("No s'ha pogut lleguir el document")
        return False
    print(f'linia maxima excel --> {len(list_excel)}')

    if type == 'genincode' or type == 'compendi':
        start = 1
        weeks = 3
    elif type == 'genotipat':
        start = 2
        weeks = 3
    elif type == 'cancer':
        start = 5
        weeks = 1
    for line in range(start, len(list_excel)):
        print(list_excel[line])
        try:
            if list_excel[line][0] != '' and str(list_excel[line][0]) != 'nan' \
               and list_excel[line][0] is not None and 'Nota: Si cal' not in list_excel[line][0]:
                if type == 'genincode' or type == 'genotipat':
                    dict_samples = {}
                    dict_samples['panell'] = str(list_excel[line][0])
                    dict_samples['index'] = str(list_excel[line][1])
                    dict_samples['sample'] = str(list_excel[line][2]) if str(list_excel[line][2]) != 'nan' else ''
                    dict_samples['code'] = str(list_excel[line][3]) if str(list_excel[line][3]) != 'nan' else ''
                    date_now, date_end = add_date(str(list_excel[line][4]), weeks)
                    dict_samples['date_entered'] = date_now
                    dict_samples['date_limit'] = date_end
                    dict_samples['gene'] = str(list_excel[line][5])
                    dict_samples['isoform'] = str(list_excel[line][6])
                    dict_samples['intron-exon'] = str(list_excel[line][7])
                    dict_samples['code_g'] = str(list_excel[line][8])
                    if type == 'genotipat':
                        dict_samples['type'] = 'genotipat'
                        dict_samples['sequence'] = str(list_excel[line][9])
                        dict_samples['aminoacid'] = ''
                        dict_samples['nucleotid'] = ''
                        try:
                            dict_samples['primer_design'] = str(list_excel[line][10])
                        except Exception:
                            dict_samples['primer_design'] = ""
                    else:
                        dict_samples['type'] = 'genincode'
                        dict_samples['nucleotid'] = str(list_excel[line][9])
                        dict_samples['aminoacid'] = str(list_excel[line][10])
                        dict_samples['sequence'] = str(list_excel[line][11])
                        try:
                            dict_samples['primer_design'] = str(list_excel[line][12])
                        except Exception:
                            dict_samples['primer_design'] = ""
                    list_samples.append(dict_samples)
                elif type == 'cancer':
                    list_exon = ['9', '11', '13', '14']
                    for exon in range(len(list_exon)):
                        dict_samples = {}
                        dict_samples['type'] = 'cancer'
                        dict_samples['panell'] = 'sanger_diagnóstic càncer'
                        dict_samples['index'] = ''
                        dict_samples['sample'] = str(list_excel[line][0])
                        dict_samples['code'] = str(list_excel[line][0])
                        print(str(list_excel[0][2]))
                        date_now, date_end = add_date(str(list_excel[0][2]), weeks)
                        dict_samples['date_entered'] = date_now
                        dict_samples['date_limit'] = date_end
                        dict_samples['gene'] = "POLE"
                        dict_samples['isoform'] = "NM_006231.4"
                        dict_samples['intron-exon'] = list_exon[exon]
                        dict_samples['code_g'] = ''
                        dict_samples['sequence'] = ''
                        dict_samples['aminoacid'] = ''
                        dict_samples['nucleotid'] = ''
                        dict_samples['primer_design'] = ''
                        list_samples.append(dict_samples)
                elif type == 'compendi':
                    dict_samples = {}
                    dict_samples['type'] = 'compendi'
                    dict_samples['panell'] = ''
                    dict_samples['index'] = ''
                    dict_samples['sample'] = str(list_excel[line][1]) if str(list_excel[line][2]) != 'nan' else ''
                    dict_samples['code'] = ''
                    date_now, date_end = add_date('', weeks)
                    dict_samples['date_entered'] = date_now
                    dict_samples['date_limit'] = date_end
                    dict_samples['gene'] = str(list_excel[line][2])
                    dict_samples['isoform'] = str(list_excel[line][3])
                    dict_samples['intron-exon'] = f'{list_excel[line][7]} {list_excel[line][5]}'
                    dict_samples['code_g'] = str(list_excel[line][6])
                    dict_samples['sequence'] = str(list_excel[line][9])
                    dict_samples['aminoacid'] = ''
                    dict_samples['nucleotid'] = ''
                    dict_samples['primer_design'] = ''
                    list_samples.append(dict_samples)
        except Exception:
            print("error")
        # os.remove(directori)
    return list_samples


def convert_xls_with_xlsx(name_xls):
    dir = f'{main_dir_docs}/{name_xls}.xls'
    dir_xlsx = f'{main_dir_docs}/{name_xls}.xlsx'

    try:
        # Leer el archivo .xls con pandas
        df = pd.read_excel(dir, engine='xlrd')
        # Escribir el DataFrame en un archivo .xlsx utilizando openpyxl
        df.to_excel(dir_xlsx, index=False, engine='openpyxl')

        os.remove(dir)
    except Exception:
        return False
    return True


def check_excel(type, name):
    if type == 'cancer':
        if 'AP' not in name:
            return False
        else:
            return True
    elif type == 'genotipat':
        if 'GENOTIPAT' not in name:
            return False
        else:
            return True
    elif type == 'genincode':
        if 'GENinCode' not in name and 'Service_Request' not in name and 'SANGER' not in name:
            return False
        else:
            return True
    elif type == 'compendi':
        if 'SangerVariants' not in name:
            return False
        else:
            return True
    else:
        return False


def search_hgvsg(hgvsg):
    dict_family = {}
    info_row = session1.query(Registres_sanger)\
        .filter(Registres_sanger.posicio_cromosomica == hgvsg)\
        .order_by(desc(Registres_sanger.id)).first()
    if info_row is None:
        return dict_family
    else:
        dict_family['panell'] = info_row.panell_mlpa_qpcr
        dict_family['index'] = info_row.familiar_index
        dict_family['sample'] = info_row.mostra
        dict_family['code'] = info_row.codi_extern
        dict_family['date_entered'] = ''
        dict_family['gene'] = info_row.gen
        dict_family['isoform'] = info_row.isoforma
        dict_family['intron-exon'] = info_row.intro_exo
        dict_family['code_g'] = info_row.posicio_cromosomica
        dict_family['aminoacid'] = info_row.aminoacid
        dict_family['nucleotid'] = info_row.resultat_validacio_facultativa
        dict_family['sequence'] = info_row.sequencia

    return dict_family


def check_duplidates(list_samples):
    samples_duplicates = ''
    found_duplicate = False
    for sample in list_samples:
        if sample['type'] == 'genincode':
            select_sample = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample['sample'])\
                                                            .filter(Registres_sanger.gen == sample['gene'])\
                                                            .filter(Registres_sanger.intro_exo == sample['intron-exon'])\
                                                            .filter(Registres_sanger.nucleotid == sample['nucleotid'])\
                                                            .first()
        elif sample['type'] == 'genotipat':
            select_sample = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample['sample'])\
                                                .filter(Registres_sanger.gen == sample['gene'])\
                                                .filter(Registres_sanger.intro_exo == sample['intron-exon'])\
                                                .first()
        elif sample['type'] == 'cancer':
            select_sample = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample['sample']).first()
        elif sample['type'] == 'compendi':
            select_sample = session1.query(Registres_sanger).filter(Registres_sanger.mostra == sample['sample'])\
                                                .filter(Registres_sanger.gen == sample['gene'])\
                                                .filter(Registres_sanger.intro_exo == sample['intron-exon'])\
                                                .first()
        if select_sample is not None:
            found_duplicate = True
            samples_duplicates += f'{select_sample.mostra};'

    if len(samples_duplicates) > 2:
        samples_duplicates = samples_duplicates[:-1]

    return found_duplicate, samples_duplicates
