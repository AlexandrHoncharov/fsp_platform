from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import func, desc


# Константы для статусов и ролей
class UserRole:
    FSP_ADMIN = 'fsp_admin'  # Администратор ФСП
    REGIONAL_REPRESENTATIVE = 'regional_representative'  # Региональный представитель
    ATHLETE = 'athlete'  # Спортсмен


class CompetitionFormat:
    OPEN = 'open'  # Открытые соревнования
    REGIONAL = 'regional'  # Региональные соревнования
    FEDERAL = 'federal'  # Всероссийские соревнования


class CompetitionDiscipline:
    PRODUCT = 'product'  # Продуктовое программирование
    SECURITY = 'security'  # Программирование систем информационной безопасности
    ALGORITHM = 'algorithm'  # Алгоритмическое программирование
    ROBOTICS = 'robotics'  # Программирование робототехники
    DRONE = 'drone'  # Программирование беспилотных авиационных систем


class CompetitionStatus:
    DRAFT = 'draft'  # Черновик
    PUBLISHED = 'published'  # Опубликовано
    REGISTRATION = 'registration'  # Регистрация открыта
    ONGOING = 'ongoing'  # Идет соревнование
    COMPLETED = 'completed'  # Завершено
    ARCHIVED = 'archived'  # В архиве


class TeamStatus:
    PENDING = 'pending'  # На модерации
    APPROVED = 'approved'  # Подтверждена
    REJECTED = 'rejected'  # Отклонена
    FORMING = 'forming'  # В процессе формирования (требуются спортсмены)


class MemberStatus:
    INVITED = 'invited'  # Приглашен
    CONFIRMED = 'confirmed'  # Подтвердил участие
    REJECTED = 'rejected'  # Отклонил приглашение


# Таблица связи соревнований и регионов (для региональных соревнований)
competition_regions = db.Table('competition_regions',
                               db.Column('competition_id', db.Integer, db.ForeignKey('competitions.id')),
                               db.Column('region_id', db.Integer, db.ForeignKey('regions.id'))
                               )

# Таблица связи пользователей и достижений
user_achievements = db.Table('user_achievements',
                             db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                             db.Column('achievement_id', db.Integer, db.ForeignKey('achievements.id')),
                             db.Column('earned_at', db.DateTime, default=datetime.utcnow)
                             )


# Модель пользователя
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(30), default=UserRole.ATHLETE)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Рейтинговые поля
    rating_points = db.Column(db.Integer, default=0)
    competitions_count = db.Column(db.Integer, default=0)
    wins_count = db.Column(db.Integer, default=0)
    last_competition_date = db.Column(db.DateTime)

    # Пользовательская настройка
    theme = db.Column(db.String(20), default='light')  # Тема интерфейса
    notification_settings = db.Column(db.JSON)  # JSON с настройками уведомлений

    # Связи с другими таблицами
    region = db.relationship('Region', backref='users')
    teams_as_captain = db.relationship('Team', backref='captain', lazy='dynamic',
                                       foreign_keys='Team.captain_id')
    team_memberships = db.relationship('TeamMember', backref='user', lazy='dynamic')
    organized_competitions = db.relationship('Competition', backref='organizer', lazy='dynamic',
                                             foreign_keys='Competition.organizer_id')
    results = db.relationship('Result', backref='user', lazy='dynamic',
                              foreign_keys='Result.user_id')

    @property
    def password(self):
        raise AttributeError('Пароль не является читаемым атрибутом')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role_display(self):
        """Возвращает отображаемое название роли"""
        if self.role == UserRole.FSP_ADMIN:
            return "Администратор ФСП"
        elif self.role == UserRole.REGIONAL_REPRESENTATIVE:
            return "Региональный представитель"
        else:
            return "Спортсмен"

    def add_achievement(self, achievement):
        """Добавляет достижение пользователю"""
        if achievement not in self.achievements:
            self.achievements.append(achievement)
            self.rating_points += achievement.points
            return True
        return False

    def update_rating(self, points):
        """Обновляет рейтинг пользователя"""
        self.rating_points += points

    def __repr__(self):
        return f'<User {self.username}>'


# Модель региона
class Region(db.Model):
    __tablename__ = 'regions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True, nullable=True)  # Код региона (например, 77 для Москвы)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Region {self.name}>'


# Модель соревнования
class Competition(db.Model):
    __tablename__ = 'competitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    discipline = db.Column(db.String(30), nullable=False)
    format = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default=CompetitionStatus.DRAFT)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    registration_start = db.Column(db.DateTime, nullable=False)
    registration_end = db.Column(db.DateTime, nullable=False)
    max_participants = db.Column(db.Integer)
    is_team_competition = db.Column(db.Boolean, default=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location = db.Column(db.String(200))  # Если есть физическое место проведения
    requirements = db.Column(db.Text)  # Технические требования
    prizes = db.Column(db.Text)  # Информация о призах
    logo_url = db.Column(db.String(200))  # URL логотипа соревнования
    website = db.Column(db.String(200))  # Внешний сайт соревнования
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи с другими таблицами
    regions = db.relationship('Region',
                              secondary=competition_regions,
                              backref=db.backref('competitions', lazy='dynamic'))
    teams = db.relationship('Team', backref='competition', lazy='dynamic')
    results = db.relationship('Result', backref='competition', lazy='dynamic')

    def get_discipline_display(self):
        """Возвращает отображаемое название дисциплины"""
        disciplines = {
            CompetitionDiscipline.PRODUCT: "Продуктовое программирование",
            CompetitionDiscipline.SECURITY: "Программирование систем информационной безопасности",
            CompetitionDiscipline.ALGORITHM: "Алгоритмическое программирование",
            CompetitionDiscipline.ROBOTICS: "Программирование робототехники",
            CompetitionDiscipline.DRONE: "Программирование беспилотных авиационных систем"
        }
        return disciplines.get(self.discipline, self.discipline)

    def get_format_display(self):
        """Возвращает отображаемое название формата"""
        formats = {
            CompetitionFormat.OPEN: "Открытое",
            CompetitionFormat.REGIONAL: "Региональное",
            CompetitionFormat.FEDERAL: "Всероссийское"
        }
        return formats.get(self.format, self.format)

    def get_status_display(self):
        """Возвращает отображаемое название статуса"""
        statuses = {
            CompetitionStatus.DRAFT: "Черновик",
            CompetitionStatus.PUBLISHED: "Опубликовано",
            CompetitionStatus.REGISTRATION: "Регистрация открыта",
            CompetitionStatus.ONGOING: "Идет соревнование",
            CompetitionStatus.COMPLETED: "Завершено",
            CompetitionStatus.ARCHIVED: "В архиве"
        }
        return statuses.get(self.status, self.status)

    def update_status(self):
        """Обновляет статус соревнования в зависимости от дат"""
        now = datetime.utcnow()

        if self.status == CompetitionStatus.DRAFT:
            return  # Не меняем статус черновика автоматически

        if now < self.registration_start:
            self.status = CompetitionStatus.PUBLISHED
        elif now >= self.registration_start and now <= self.registration_end:
            self.status = CompetitionStatus.REGISTRATION
        elif now > self.registration_end and now <= self.end_date:
            self.status = CompetitionStatus.ONGOING
        elif now > self.end_date:
            self.status = CompetitionStatus.COMPLETED

    def __repr__(self):
        return f'<Competition {self.name}>'


# Модель команды
class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    status = db.Column(db.String(20), default=TeamStatus.FORMING)
    needs_members = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(200))  # URL логотипа команды
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи с другими таблицами
    members = db.relationship('TeamMember', backref='team', lazy='dynamic')
    result = db.relationship('Result', backref='team', uselist=False)

    def get_status_display(self):
        """Возвращает отображаемое название статуса"""
        statuses = {
            TeamStatus.PENDING: "На модерации",
            TeamStatus.APPROVED: "Подтверждена",
            TeamStatus.REJECTED: "Отклонена",
            TeamStatus.FORMING: "Формируется"
        }
        return statuses.get(self.status, self.status)

    def get_confirmed_members_count(self):
        """Возвращает количество подтвержденных участников команды"""
        return self.members.filter_by(status=MemberStatus.CONFIRMED).count()

    def is_member(self, user_id):
        """Проверяет, является ли пользователь участником команды"""
        return self.members.filter_by(user_id=user_id).count() > 0

    def __repr__(self):
        return f'<Team {self.name}>'


# Модель участника команды
class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default=MemberStatus.INVITED)
    role_description = db.Column(db.String(100))
    joined_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_status_display(self):
        """Возвращает отображаемое название статуса"""
        statuses = {
            MemberStatus.INVITED: "Приглашен",
            MemberStatus.CONFIRMED: "Подтвержден",
            MemberStatus.REJECTED: "Отклонен"
        }
        return statuses.get(self.status, self.status)

    def __repr__(self):
        return f'<TeamMember {self.id} - Team {self.team_id}, User {self.user_id}>'


# Модель результатов соревнований
class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    score = db.Column(db.Float)
    place = db.Column(db.Integer)
    details = db.Column(db.Text)  # Дополнительные детали результата
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_rating_points(self):
        """Рассчитывает рейтинговые очки на основе места"""
        if self.place == 1:
            return 100
        elif self.place == 2:
            return 75
        elif self.place == 3:
            return 50
        elif self.place <= 10:
            return 25
        else:
            return 10

    def __repr__(self):
        return f'<Result {self.id} - Competition {self.competition_id}>'


# Модель достижения
class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    badge_icon = db.Column(db.String(100))  # Путь к иконке или CSS-класс
    category = db.Column(db.String(50))  # Категория достижения
    points = db.Column(db.Integer, default=10)  # Баллы за достижение
    criteria = db.Column(db.Text)  # Критерии получения достижения
    is_hidden = db.Column(db.Boolean, default=False)  # Скрытое достижение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с пользователями
    users = db.relationship('User',
                            secondary=user_achievements,
                            backref=db.backref('achievements', lazy='dynamic'))

    def __repr__(self):
        return f'<Achievement {self.name}>'


# Модель рейтинга региона
class RegionRating(db.Model):
    __tablename__ = 'region_ratings'

    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.id'))
    total_points = db.Column(db.Integer, default=0)
    competitions_count = db.Column(db.Integer, default=0)
    wins_count = db.Column(db.Integer, default=0)
    top3_count = db.Column(db.Integer, default=0)  # Количество попаданий в топ-3
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с регионом
    region = db.relationship('Region', backref='rating')

    def __repr__(self):
        return f'<RegionRating {self.region.name}>'


# Модель уведомления
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20))  # Тип уведомления (info, success, warning, error)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(200))  # Ссылка на связанный объект
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id} - User {self.user_id}>'


# Модель логов системы
class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('system_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<SystemLog {self.id} - Action {self.action}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))