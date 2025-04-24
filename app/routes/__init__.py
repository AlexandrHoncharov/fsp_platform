# Этот файл инициализирует пакет маршрутов (routes)
# Здесь можно импортировать все blueprints для более удобного импорта

from app.routes.auth import auth
from app.routes.competitions import competitions
from app.routes.teams import teams
from app.routes.profile import profile