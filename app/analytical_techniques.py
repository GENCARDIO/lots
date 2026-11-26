"""Configuration catalogue for analytical techniques."""

from flask import jsonify, request, session
from sqlalchemy import func

from app import app
from app.models import Analytical_techniques, Lots, Stock_lots, session1
from app.utils import instant_date, requires_auth, save_log


def _serialize(technique):
    return {'id': technique.id, 'name': technique.name, 'active': bool(technique.active)}


def is_active_technique(name):
    if not name:
        return False
    return session1.query(Analytical_techniques.id).filter(
        func.lower(Analytical_techniques.name) == name.strip().lower(),
        Analytical_techniques.active == 1,
    ).first() is not None


def _log_change(technique, action, old_value, new_value):
    save_log({
        'id_lot': 0,
        'type': action,
        'info': f'analytical_technique {technique.id}: {old_value} -> {new_value}',
        'user': session['acronim'],
        'id_user': session['idClient'],
        'date': instant_date(),
    })


@app.route('/analytical_techniques', methods=['GET'])
@requires_auth
def list_analytical_techniques():
    query = session1.query(Analytical_techniques)
    if request.args.get('active') == '1':
        query = query.filter(Analytical_techniques.active == 1)
    rows = query.order_by(func.lower(Analytical_techniques.name)).all()
    return jsonify([_serialize(row) for row in rows])


@app.route('/analytical_techniques', methods=['POST'])
@requires_auth
def create_analytical_technique():
    name = (request.form.get('name') or '').strip()
    if not name:
        return jsonify(message='El nom és obligatori.'), 400
    duplicate = session1.query(Analytical_techniques).filter(
        func.lower(Analytical_techniques.name) == name.lower()
    ).first()
    if duplicate:
        return jsonify(message='Aquesta tècnica ja existeix. Si està eliminada, la pots reactivar.'), 409
    row = Analytical_techniques(name=name, active=1)
    try:
        session1.add(row)
        session1.flush()
        _log_change(row, 'analytical_technique_create', '', name)
        session1.commit()
    except Exception:
        session1.rollback()
        return jsonify(message="No s'ha pogut crear la tècnica."), 500
    return jsonify(_serialize(row)), 201


@app.route('/analytical_techniques/<int:technique_id>', methods=['POST'])
@requires_auth
def update_analytical_technique(technique_id):
    row = session1.query(Analytical_techniques).filter_by(id=technique_id).first()
    if row is None:
        return jsonify(message='Tècnica no trobada.'), 404
    name = (request.form.get('name') or '').strip()
    if not name:
        return jsonify(message='El nom és obligatori.'), 400
    duplicate = session1.query(Analytical_techniques).filter(
        func.lower(Analytical_techniques.name) == name.lower(),
        Analytical_techniques.id != technique_id,
    ).first()
    if duplicate:
        return jsonify(message='Ja existeix una tècnica amb aquest nom.'), 409
    old_name = row.name
    try:
        row.name = name
        if old_name != name:
            session1.query(Lots).filter(Lots.analytical_technique == old_name).update(
                {Lots.analytical_technique: name}, synchronize_session=False)
            session1.query(Stock_lots).filter(Stock_lots.analytical_technique == old_name).update(
                {Stock_lots.analytical_technique: name}, synchronize_session=False)
            _log_change(row, 'analytical_technique_update', old_name, name)
        session1.commit()
    except Exception:
        session1.rollback()
        return jsonify(message="No s'ha pogut modificar la tècnica."), 500
    return jsonify(_serialize(row))


@app.route('/analytical_techniques/<int:technique_id>/active', methods=['POST'])
@requires_auth
def set_analytical_technique_active(technique_id):
    row = session1.query(Analytical_techniques).filter_by(id=technique_id).first()
    if row is None:
        return jsonify(message='Tècnica no trobada.'), 404
    active = request.form.get('active')
    if active not in ('0', '1'):
        return jsonify(message='Estat incorrecte.'), 400
    try:
        if row.active != int(active):
            _log_change(row, 'analytical_technique_active', row.active, active)
            row.active = int(active)
        session1.commit()
    except Exception:
        session1.rollback()
        return jsonify(message="No s'ha pogut canviar l'estat."), 500
    return jsonify(_serialize(row))
