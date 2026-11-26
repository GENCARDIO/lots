# coding=utf-8
from flask import Flask
from config import LOTS_ENV

# FLASK
app = Flask(__name__)
app.test_client()
app.config.from_object(
    'config.DevelopmentConfig' if LOTS_ENV == 'development' else 'config.ProductionConfig'
)
# 1 - En desenvolupament, F5 torna a llegir les plantilles modificades.
# 2 - Els fitxers estàtics no mantenen una còpia antiga al navegador.
# 3 - La recàrrega de Python es configura a lots.py; el navegador no es refresca sol.
if LOTS_ENV == 'development':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

from app import models

models.ensure_command_price_columns()
models.ensure_analytical_techniques()
models.ensure_stock_volume_discounts()

from app import utils, home, documents_lots, reception_lots, open_close_lots, commands, edit_delete_lots, look_spend_money, api, analytical_techniques, stock_control
