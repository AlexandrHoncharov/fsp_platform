from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Competition, UserRole, CompetitionFormat, CompetitionDiscipline, Region, Team, TeamStatus
from app.forms import CompetitionForm

competitions = Blueprint('competitions', __name__, url_prefix='/competitions')


@competitions.route('/list')
@competitions.route('/')
def list():
    """Список всех активных соревнований"""
    # Фильтрация по параметрам запроса (формат, дисциплина, регион, дата)
    format_filter = request.args.get('format')
    discipline_filter = request.args.get('discipline')
    region_filter = request.args.get('region')
    date_filter = request.args.get('date')

    query = Competition.query.filter(Competition.registration_end >= datetime.utcnow())

    if format_filter:
        query = query.filter(Competition.format == format_filter)
    if discipline_filter:
        query = query.filter(Competition.discipline == discipline_filter)
    if region_filter:
        query = query.join(Competition.regions).filter(Region.id == region_filter)
    if date_filter:
        # Предполагаем, что date_filter будет в формате YYYY-MM-DD
        try:
            date = datetime.strptime(date_filter, '%Y-%m-%d')
            query = query.filter(Competition.start_date >= date)
        except ValueError:
            pass

    competitions_list = query.order_by(Competition.start_date).all()

    # Дополнительные данные для фильтров
    disciplines = [
        (CompetitionDiscipline.PRODUCT, "Продуктовое программирование"),
        (CompetitionDiscipline.SECURITY, "Программирование систем информационной безопасности"),
        (CompetitionDiscipline.ALGORITHM, "Алгоритмическое программирование"),
        (CompetitionDiscipline.ROBOTICS, "Программирование робототехники"),
        (CompetitionDiscipline.DRONE, "Программирование беспилотных авиационных систем")
    ]
    formats = [
        (CompetitionFormat.OPEN, "Открытые"),
        (CompetitionFormat.REGIONAL, "Региональные"),
        (CompetitionFormat.FEDERAL, "Всероссийские")
    ]
    regions = Region.query.order_by(Region.name).all()

    # Передача текущей даты для проверки статуса регистрации
    now = datetime.utcnow()

    return render_template('competitions/list.html',
                           competitions=competitions_list,
                           disciplines=disciplines,
                           formats=formats,
                           regions=regions,
                           now=now)


@competitions.route('/view/<int:id>')
def view(id):
    """Просмотр информации о соревновании"""
    competition = Competition.query.get_or_404(id)
    teams = Team.query.filter_by(competition_id=id).all()

    # Разделяем команды на утвержденные и формирующиеся
    approved_teams = [t for t in teams if t.status == TeamStatus.APPROVED]
    forming_teams = [t for t in teams if t.status == TeamStatus.FORMING and t.needs_members]

    # Проверяем, может ли текущий пользователь регистрировать команду
    can_register = False
    if current_user.is_authenticated:
        # Проверка на соответствие региональным ограничениям
        if competition.format == CompetitionFormat.OPEN:
            can_register = True
        elif competition.format == CompetitionFormat.REGIONAL:
            # Проверяем, входит ли регион пользователя в список разрешенных
            allowed_regions = [r.id for r in competition.regions]
            can_register = current_user.region_id in allowed_regions
        elif competition.format == CompetitionFormat.FEDERAL:
            # Только региональные представители могут регистрироваться
            can_register = current_user.role == UserRole.REGIONAL_REPRESENTATIVE

    return render_template('competitions/view.html',
                           competition=competition,
                           approved_teams=approved_teams,
                           forming_teams=forming_teams,
                           can_register=can_register)


@competitions.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Создание нового соревнования (только для организаторов)"""
    # Проверка прав доступа
    if current_user.role not in [UserRole.FSP_ADMIN, UserRole.REGIONAL_REPRESENTATIVE]:
        flash('У вас нет прав для создания соревнований.', 'danger')
        return redirect(url_for('competitions.list'))

    form = CompetitionForm()

    # Заполняем варианты для выпадающих списков
    form.discipline.choices = [
        (CompetitionDiscipline.PRODUCT, "Продуктовое программирование"),
        (CompetitionDiscipline.SECURITY, "Программирование систем информационной безопасности"),
        (CompetitionDiscipline.ALGORITHM, "Алгоритмическое программирование"),
        (CompetitionDiscipline.ROBOTICS, "Программирование робототехники"),
        (CompetitionDiscipline.DRONE, "Программирование беспилотных авиационных систем")
    ]

    # В зависимости от роли пользователя определяем доступные форматы
    if current_user.role == UserRole.FSP_ADMIN:
        form.format.choices = [
            (CompetitionFormat.OPEN, "Открытые"),
            (CompetitionFormat.REGIONAL, "Региональные"),
            (CompetitionFormat.FEDERAL, "Всероссийские")
        ]
    else:  # Региональный представитель
        form.format.choices = [
            (CompetitionFormat.OPEN, "Открытые"),
            (CompetitionFormat.REGIONAL, "Региональные")
        ]

    # Для региональных соревнований нужно выбрать регионы
    regions = Region.query.order_by(Region.name).all()
    form.regions.choices = [(r.id, r.name) for r in regions]

    if form.validate_on_submit():
        competition = Competition(
            name=form.name.data,
            description=form.description.data,
            discipline=form.discipline.data,
            format=form.format.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            registration_start=form.registration_start.data,
            registration_end=form.registration_end.data,
            max_participants=form.max_participants.data,
            is_team_competition=form.is_team_competition.data,
            organizer_id=current_user.id
        )

        # Для региональных соревнований добавляем регионы
        if form.format.data == CompetitionFormat.REGIONAL and form.regions.data:
            selected_regions = Region.query.filter(Region.id.in_(form.regions.data)).all()
            competition.regions = selected_regions
        elif form.format.data == CompetitionFormat.FEDERAL:
            # Для федеральных соревнований добавляем все регионы
            competition.regions = Region.query.all()

        db.session.add(competition)
        db.session.commit()

        flash('Соревнование успешно создано!', 'success')
        return redirect(url_for('competitions.view', id=competition.id))

    return render_template('competitions/create.html', form=form)