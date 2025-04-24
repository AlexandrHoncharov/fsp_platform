from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Region, UserRole
from app.forms import LoginForm, RegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/')
def index():
    return render_template('index.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('auth.index')
            return redirect(next_page)
        flash('Неверный email или пароль.')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.')
    return redirect(url_for('auth.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    form = RegistrationForm()
    # Заполнение выпадающего списка регионов
    form.region.choices = [(r.id, r.name) for r in Region.query.order_by(Region.name).all()]

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole.ATHLETE,  # По умолчанию регистрируем как спортсмена
            region_id=form.region.data
        )
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем! Вы успешно зарегистрировались.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)