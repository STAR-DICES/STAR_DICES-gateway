from gateway.auth import login_manager
from gateway.views import blueprints

from flask import Flask, jsonify, render_template

def internal_error(e):
    return render_template('message.html', message='\_(-.-)_/ SOMETHING WENT WRONG \_(-.-)_/'), 500

def missing_page(e):
    return render_template('message.html', message='\_(-.-)_/ RESOURCE NOT FOUND \_(-.-)_/'), 404

def unauthorized_access(e):
    return render_template('message.html', message='\_(-.-)_/ UNAUTHORIZED ACCESS \_(-.-)_/', notlogged=True), 401

def create_app(test = False):
    app = Flask(__name__, static_url_path='/static')
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    if test:
        app.config['TESTING'] = True
        app.config['CELERY_ALWAYS_EAGER'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    app.users = {}
    app.register_error_handler(500, internal_error)
    app.register_error_handler(404, missing_page)
    app.register_error_handler(401, unauthorized_access)
    login_manager.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0')
