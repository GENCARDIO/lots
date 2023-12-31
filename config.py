# coding=utf-8
import os

# Docker
# URLGLOBALEXCELS = '/CONFIRMACIO_FAMILIARS/excels/'
# Api
URLGLOBALEXCELS = '/home/gencardio/Escriptori/excels'
IP_FTP = '172.19.1.17'
USER = '40358047Q'
PWD = 'As687390'

main_dir = os.path.dirname(os.path.abspath(__file__))
ip_address = 'http://172.16.82.47'
main_dir = f'{main_dir}_db'

# Docker
# ip_address = 'http://172.16.78.83'
# main_dir = f'{main_dir}/DB'

# Producció qumulo
# ip_address = 'http://172.16.83.23'
# main_dir = f'{main_dir}/DB/docs'


class Config(object):
    SECRET_KEY = 'lablam.2017'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@prod_host:port/db_name'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@dev_host:port/db_name'


class TestingConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@test_host:port/db_name'


class Config_Arxius(object):
    # SCHEDULER_TIMEZONE = "Europe/Berlin"
    UPLOADS = URLGLOBALEXCELS
    WORKING_DIRECTORY = main_dir
    MAX_CONTENT_LENGHT = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    SEND_FILE_MAX_AGE_DEFAULT = 5
