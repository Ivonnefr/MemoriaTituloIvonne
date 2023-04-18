from flask import Flask
def create_app():
    app =Flask(__name__)
    app.config['SECRET_KEY']= 'ivonne'

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prfeix='/')
    app.register_blueprint(auth, url_prefix = '/auth/')
    return app 