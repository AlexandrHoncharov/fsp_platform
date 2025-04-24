from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Инициализация расширений с приложением
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.routes.competitions import competitions as competitions_blueprint
    app.register_blueprint(competitions_blueprint)

    from app.routes.teams import teams as teams_blueprint
    app.register_blueprint(teams_blueprint)

    from app.routes.profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint)

    from app.routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from app.routes.rating import rating as rating_blueprint
    app.register_blueprint(rating_blueprint)

    # Регистрация функции обработки ошибок

    return app