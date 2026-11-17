# coding=utf-8
from app import app


if __name__ == '__main__':
    # 1 - En desenvolupament, reiniciem Flask quan canvia un fitxer Python muntat.
    # 2 - El navegador només mostra el canvi quan l'usuari actualitza la pàgina.
    development = app.config['DEPLOYMENT_ENV'] == 'development'
    app.run(host='0.0.0.0', port=5017,
            use_reloader=development)
