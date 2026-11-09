# coding=utf-8
import os

main_dir = os.path.dirname(os.path.abspath(__file__))
LOTS_ENV = os.environ.get('LOTS_ENV', 'production').strip().lower()

if LOTS_ENV == 'production':
    main_dir = f'{main_dir}/DB'
elif LOTS_ENV == 'development':
    main_dir = f'{main_dir}_db'
else:
    raise ValueError('LOTS_ENV ha de ser production o development')

ip_address = os.environ.get('LOTS_IP_ADDRESS', '').strip().rstrip('/')
if not ip_address:
    raise ValueError('Cal definir LOTS_IP_ADDRESS al docker compose amb la URL base dels serveis, sense port')
main_dir = os.environ.get('LOTS_DATA_DIR', main_dir)
main_dir_docs = os.environ.get('LOTS_DOCS_DIR', f'{main_dir}/docs')

# Desenvolupament anterior (referència)
# main_dir = os.path.dirname(os.path.abspath(__file__))
# main_dir = f'{main_dir}_db'
# main_dir_docs = f"{main_dir}/docs"

# Docker
# main_dir = f'{main_dir}/DB'
# main_dir_docs = f"{main_dir}/docs"

# Producció qumulo
# main_dir = f'{main_dir}/DB'
# main_dir_docs = f"{main_dir}/docs"


class Config(object):
    DEPLOYMENT_ENV = LOTS_ENV
    SECRET_KEY = 'lablam.2017'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('LOTS_DEBUG', 'false').lower() in {'1', 'true', 'yes'}
    TESTING = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@prod_host:port/db_name'


class DevelopmentConfig(Config):
    DEBUG = os.environ.get('LOTS_DEBUG', 'true').lower() in {'1', 'true', 'yes'}
    SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@dev_host:port/db_name'


class TestingConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:db_pass@test_host:port/db_name'


class Config_Arxius(object):
    # SCHEDULER_TIMEZONE = "Europe/Berlin"
    WORKING_DIRECTORY = main_dir
    MAX_CONTENT_LENGHT = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    SEND_FILE_MAX_AGE_DEFAULT = 5
