from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'    # redirect to this view when login required
csrf = CSRFProtect()

def create_app():
    load_dotenv()
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
