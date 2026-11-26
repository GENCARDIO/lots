"""Movements for the two stock control methods."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import jsonify, request, session

from app import app
from app.models import Lot_consumptions, Stock_lots, Stock_volume_discounts, session1
from app.utils import requires_auth


def _decimal_text(value):
    return format(value.normalize(), 'f')


@app.route('/stock_control_history/<int:stock_id>', methods=['GET'])
@requires_auth
def stock_control_history(stock_id):
    stock = session1.query(Stock_lots).filter_by(id=stock_id).first()
    if stock is None:
        return jsonify(message='Lot no trobat.'), 404

    if stock.type_discount in ('Descompte per reaccions', 'Descontar'):
        movements = session1.query(Stock_volume_discounts).filter_by(id_stock_lot=stock_id).order_by(
            Stock_volume_discounts.id.desc()).all()
        return jsonify(method='discount', rows=[{
            'date': row.date,
            'quantity_before': row.quantity_before,
            'quantity_discounted': row.quantity_discounted,
            'quantity_remaining': row.quantity_remaining,
            'unit': row.unit,
            'observations': row.observations or '',
            'user': row.user or '',
        } for row in movements])

    movements = session1.query(Lot_consumptions).filter_by(id_lot=stock_id).order_by(
        Lot_consumptions.id.desc()).all()
    return jsonify(method='open_close', rows=[{
        'date_open': row.date_open or '',
        'user_open': row.user_open or '',
        'observations_open': row.observations_open or '',
        'date_close': row.date_close or '',
        'user_close': row.user_close or '',
        'observations_close': row.observations_close or '',
    } for row in movements])


@app.route('/stock_control_discount', methods=['POST'])
@requires_auth
def stock_control_discount():
    stock_id = request.form.get('stock_id')
    stock = session1.query(Stock_lots).filter_by(id=stock_id).first()
    if stock is None or stock.spent != 0 or stock.react_or_fungible != 'Reactiu':
        return jsonify(message='Aquest lot no està disponible.'), 400
    if stock.type_discount not in ('Descompte per reaccions', 'Descontar'):
        return jsonify(message='Aquest producte no utilitza el descompte per reaccions.'), 400

    date = (request.form.get('date') or '').strip()
    observations = (request.form.get('observations') or '').strip()
    try:
        datetime.strptime(date, '%d-%m-%Y')
        discounted = Decimal((request.form.get('quantity_discounted') or '').strip().replace(',', '.'))
        if not discounted.is_finite() or discounted <= 0:
            raise InvalidOperation
    except (ValueError, InvalidOperation):
        return jsonify(message='Indica una data vàlida i una quantitat a descomptar superior a zero.'), 400

    latest = session1.query(Stock_volume_discounts).filter_by(id_stock_lot=stock.id).order_by(
        Stock_volume_discounts.id.desc()).first()
    if latest is None:
        unit = (request.form.get('unit') or '').strip()
        try:
            before = Decimal((request.form.get('quantity_before') or '').strip().replace(',', '.'))
            if not before.is_finite() or before <= 0:
                raise InvalidOperation
        except InvalidOperation:
            return jsonify(message='Indica el volum inicial del lot.'), 400
        if not unit:
            return jsonify(message='Indica la unitat del volum.'), 400
    else:
        before = Decimal(latest.quantity_remaining)
        unit = latest.unit

    if discounted > before:
        return jsonify(message='No pots descomptar més quantitat de la que queda.'), 400

    remaining = before - discounted
    movement = Stock_volume_discounts(
        id_stock_lot=stock.id,
        date=date,
        quantity_before=_decimal_text(before),
        quantity_discounted=_decimal_text(discounted),
        quantity_remaining=_decimal_text(remaining),
        unit=unit,
        observations=observations,
        user=session['acronim'],
    )
    try:
        session1.add(movement)
        if remaining == 0:
            stock.spent = 1
            stock.units_lot = 0
        session1.commit()
    except Exception:
        session1.rollback()
        return jsonify(message="No s'ha pogut registrar el descompte."), 500

    return jsonify(message='Descompte registrat.', remaining=_decimal_text(remaining), unit=unit)
