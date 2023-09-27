# coding=utf-8
from flask import Flask

# FLASK
app = Flask(__name__)
app.test_client()
app.config.from_object("config.TestingConfig")

from app import models, utils, home
