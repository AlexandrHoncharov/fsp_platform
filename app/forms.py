from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms import SelectField, SelectMultipleField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User


class LoginForm(FlaskForm):
    """Форма авторизации"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    """Форма регистрации"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    region = SelectField('Регион', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Этот email уже зарегистрирован в системе.')


class ProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('Новый пароль', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль',
                                     validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Сохранить')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None and user.id != user.id:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None and user.id != user.id:
            raise ValidationError('Этот email уже зарегистрирован в системе.')


class CompetitionForm(FlaskForm):
    """Форма создания соревнования"""
    name = StringField('Название', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    discipline = SelectField('Дисциплина', validators=[DataRequired()])
    format = SelectField('Формат проведения', validators=[DataRequired()])
    start_date = DateTimeField('Дата начала', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeField('Дата окончания', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    registration_start = DateTimeField('Начало регистрации', format='%Y-%m-%dT%H:%M',
                                      validators=[DataRequired()])
    registration_end = DateTimeField('Конец регистрации', format='%Y-%m-%dT%H:%M',
                                    validators=[DataRequired()])
    max_participants = IntegerField('Максимальное количество участников', validators=[Optional()])
    is_team_competition = BooleanField('Командное соревнование', default=True)
    regions = SelectMultipleField('Регионы (для региональных соревнований)', coerce=int)
    submit = SubmitField('Создать соревнование')

    def validate_end_date(self, end_date):
        if end_date.data <= self.start_date.data:
            raise ValidationError('Дата окончания должна быть позже даты начала.')

    def validate_registration_end(self, registration_end):
        if registration_end.data <= self.registration_start.data:
            raise ValidationError('Дата окончания регистрации должна быть позже даты начала регистрации.')

        if registration_end.data > self.start_date.data:
            raise ValidationError('Регистрация должна закончиться до начала соревнования.')


class TeamForm(FlaskForm):
    """Форма создания команды"""
    name = StringField('Название команды', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Описание команды', validators=[Optional()])
    needs_members = BooleanField('Требуются участники', default=False)
    submit = SubmitField('Создать команду')


class TeamMemberForm(FlaskForm):
    """Форма добавления участника в команду"""
    role_description = StringField('Ваша роль в команде', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Отправить заявку')


class ResultForm(FlaskForm):
    """Форма для внесения результатов соревнования"""
    place = IntegerField('Место', validators=[DataRequired()])
    score = IntegerField('Баллы', validators=[DataRequired()])
    submit = SubmitField('Сохранить результат')