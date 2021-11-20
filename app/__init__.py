from flask import Flask, render_template, request,session,redirect, url_for,flash,abort,make_response,current_app
from flask_bcrypt import  Bcrypt
from  flask_session  import Session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
from flask_moment import Moment
from config import config
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_pagedown import PageDown
# from celery import Celery
from config import config, Config



mail = Mail()
moment = Moment()
db = SQLAlchemy()
flask_bcrypt = Bcrypt()
mail = Mail()
session=Session()
bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
pagedown = PageDown()
# celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

# create_app() function is the application factory, which takes as an argument the name of a configuration to use for the application.
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    flask_bcrypt.init_app(app)
    db.init_app(app)
    session.init_app(app)
    
    login_manager.init_app(app)
    bootstrap.init_app(app)
    pagedown.init_app(app)
    # celery.conf.update(app.config)
    

    # Blueprint 'main' for authentication
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Blueprint 'auth' for authentication
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

   

