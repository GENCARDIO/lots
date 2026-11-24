# coding=utf-8
"""Rutes HTTP que altres aplicacions poden consultar."""

from datetime import datetime
import os

from flask import jsonify, request, session
from sqlalchemy import func

from app import app
from app.models import Buy_primers, Commands, Lots, session1
from app.utils import instant_date, send_mail_generic


def receive_primers_by_ids(list_id_primer, received_by):
    date_now = instant_date()
    text_email = '<p style="margin-bottom:10px;">Hem rebut els seguents primers :</p>'
    text_header_email = 'Recepcio de primers'
    not_found = ''
    id_primers_change = ''
    send_mail = []

    for primer_id in list_id_primer:
        select_primer = session1.query(Buy_primers).filter(Buy_primers.id == primer_id).first()
        if select_primer is None:
            not_found += str(primer_id) + ';'
            continue

        if select_primer.buy == 1 and select_primer.received == 0 and select_primer.delete == 0:
            select_primer.received = 1
            select_primer.received_date = date_now
            select_primer.received_by = received_by

            text_email += f"&nbsp;&nbsp;&nbsp;• {select_primer.sequence_name} - {select_primer.sequence}<br>"
            id_primers_change += str(primer_id) + ';'
            if select_primer.email_send not in send_mail:
                send_mail.append(select_primer.email_send)

    return {
        'id_primers_change': id_primers_change.rstrip(';'),
        'not_found': not_found.rstrip(';'),
        'send_mail': send_mail,
        'text_email': text_email,
        'text_header_email': text_header_email
    }


@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify(status='ok'), 202


@app.route('/external/receive-primers', methods=['POST'])
def external_receive_primers():
    id_primer = request.form.get('id_primer') or request.form.get('lots_primer_ids') or ''
    received_by = request.form.get('received_by') or request.form.get('user') or session.get('acronim') or 'Primers'
    list_id_primer = [primer_id for primer_id in id_primer.split(';') if primer_id]

    if not list_id_primer:
        return jsonify({
            "status": "error",
            "message": "No s'ha rebut cap ID de primer per recepcionar.",
            "id": "",
            "not_found": ""
        }), 400

    try:
        received_result = receive_primers_by_ids(list_id_primer, received_by)
        session1.commit()

        if len(received_result['send_mail']) > 0:
            result_emails = ','.join(received_result['send_mail'])
            send_mail_generic(result_emails, received_result['text_email'], received_result['text_header_email'])

        return jsonify({
            "status": "success",
            "message": "Primers recepcionats correctament.",
            "id": received_result['id_primers_change'],
            "not_found": received_result['not_found']
        }), 200

    except Exception as e:
        session1.rollback()
        return jsonify({
            "status": "error",
            "message": str(e) or "No s'han pogut recepcionar els primers.",
            "id": "",
            "not_found": ""
        }), 500


@app.route('/get_lots', methods=['GET'])
def get_lots():
    """
    Retorna una llista de lots.

    :return: JSON amb la llista de lots.
    :rtype: flask.Response
    """
    lots = session1.query(Lots).group_by(Lots.manufacturer).order_by(func.lower(Lots.manufacturer)).all()

    result = []
    for lot in lots:
        result.append({
            "manufacturer": lot.manufacturer,
            "nif": lot.nif,
            "sales_contact": lot.sales_contact
        })

    return jsonify(result)


@app.route('/api/quality-indicators/purchases', methods=['GET'])
def get_quality_purchases_indicators():
    """Retorna els set recomptes mensuals de compres per a un any."""
    year = request.args.get('year', '').strip()
    if len(year) != 4 or not year.isascii() or not year.isdigit():
        return jsonify({'status': 'error', 'message': 'year must have four digits'}), 400

    months = ('Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny',
              'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre')
    supplier_keys = {
        '8852-UDMMP': 'udmmp',
        '8852-APP/Compres': 'app_compres',
        '8852-Logaritme': 'logaritme',
        'IDIBGI': 'idibgi',
    }
    keys = ('total', *supplier_keys.values(), 'late_app_compres', 'late_logaritme')
    counts = {key: {} for key in keys}

    try:
        for month_number, month_name in enumerate(months, 1):
            month_counts = {key: 0 for key in keys}
            rows = (
                session1.query(Commands.supplier, Commands.date_close, Commands.date_complete)
                .filter(Commands.date_close.like(f'%-{month_number:02d}-{year}'))
                .all()
            )
            for supplier, date_close, date_complete in rows:
                month_counts['total'] += 1
                supplier_key = supplier_keys.get(supplier)
                if supplier_key:
                    month_counts[supplier_key] += 1
                if supplier in ('8852-APP/Compres', '8852-Logaritme') and date_close and date_complete:
                    days_late = (
                        datetime.strptime(date_complete, '%d-%m-%Y')
                        - datetime.strptime(date_close, '%d-%m-%Y')
                    ).days
                    if supplier == '8852-APP/Compres' and days_late > 7:
                        month_counts['late_app_compres'] += 1
                    elif supplier == '8852-Logaritme' and days_late > 15:
                        month_counts['late_logaritme'] += 1
            for key, value in month_counts.items():
                counts[key][month_name] = value
    except Exception:
        app.logger.exception("No s'han pogut calcular els indicadors de compres")
        return jsonify({'status': 'error', 'message': 'Error loading purchases indicators'}), 500

    return jsonify({'status': 'ok', 'year': year, 'counts': counts})
