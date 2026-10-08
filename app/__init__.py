# coding=utf-8
from flask import Flask

# FLASK
app = Flask(__name__)
app.test_client()
app.config.from_object("config.TestingConfig")

from app import models

models.ensure_command_price_columns()

from app import utils, home, documents_lots, reception_lots, open_close_lots, commands, edit_delete_lots, look_spend_money
