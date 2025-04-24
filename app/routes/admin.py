from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, distinct
from app import db
from app.models import User, Team, Competition, Region, Result, UserRole, TeamStatus

admin = Blueprint('admin', __name__, url_prefix='/admin')


# Декоратор для проверки прав доступа администратора или регионального представителя
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in [UserRole.FSP_ADMIN, UserRole.REGIONAL_REPRESENTATIVE]:
            flash('У вас нет прав для доступа к этой странице.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


# Декоратор для проверки прав доступа только администратора ФСП
def fsp_admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.FSP_ADMIN:
            flash('Эта страница доступна только администраторам ФСП.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@admin.route('/')
@admin_required
def index():
    """Главная страница панели администрирования"""
    # Собираем основную статистику
    stats = {}

    # Ограничиваем данные для региональных представителей их регионом
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        region_id = current_user.region_id

        stats['users_count'] = User.query.filter_by(region_id=region_id).count()
        stats['competitions_count'] = Competition.query.filter_by(organizer_id=current_user.id).count()

        # Команды из региона представителя
        teams_query = Team.query.join(User, Team.captain_id == User.id).filter(User.region_id == region_id)
        stats['teams_count'] = teams_query.count()
        stats['pending_teams'] = teams_query.filter_by(status=TeamStatus.PENDING).count()
    else:
        # Для администраторов ФСП - полная статистика
        stats['users_count'] = User.query.count()
        stats['competitions_count'] = Competition.query.count()
        stats['teams_count'] = Team.query.count()
        stats['pending_teams'] = Team.query.filter_by(status=TeamStatus.PENDING).count()
        stats['regions_count'] = Region.query.count()

    # Получаем последние соревнования
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        recent_competitions = Competition.query.filter_by(organizer_id=current_user.id).order_by(
            Competition.created_at.desc()).limit(5).all()
    else:
        recent_competitions = Competition.query.order_by(Competition.created_at.desc()).limit(5).all()

    # Получаем команды на модерации
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        # Только команды на модерации для соревнований, созданных этим представителем
        pending_teams = Team.query.join(Competition, Team.competition_id == Competition.id).filter(
            Competition.organizer_id == current_user.id, Team.status == TeamStatus.PENDING).limit(10).all()
    else:
        pending_teams = Team.query.filter_by(status=TeamStatus.PENDING).limit(10).all()

    return render_template('admin/index.html',
                           stats=stats,
                           recent_competitions=recent_competitions,
                           pending_teams=pending_teams)


@admin.route('/users')
@admin_required
def users():
    """Список пользователей"""
    # Для региональных представителей - только пользователи их региона
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        region_id = current_user.region_id
        users_list = User.query.filter_by(region_id=region_id).all()
    else:
        users_list = User.query.all()

    return render_template('admin/users.html', users=users_list)


@admin.route('/team-approvals')
@admin_required
def team_approvals():
    """Управление заявками команд"""
    # Для региональных представителей - только команды для их соревнований
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        teams = Team.query.join(Competition, Team.competition_id == Competition.id).filter(
            Competition.organizer_id == current_user.id, Team.status == TeamStatus.PENDING).all()
    else:
        teams = Team.query.filter_by(status=TeamStatus.PENDING).all()

    return render_template('admin/team_approvals.html', teams=teams)


@admin.route('/approve-team/<int:team_id>')
@admin_required
def approve_team(team_id):
    """Подтверждение команды"""
    team = Team.query.get_or_404(team_id)

    # Проверка прав доступа для региональных представителей
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        competition = Competition.query.get_or_404(team.competition_id)
        if competition.organizer_id != current_user.id:
            flash('У вас нет прав для модерации этой команды.', 'danger')
            return redirect(url_for('admin.team_approvals'))

    team.status = TeamStatus.APPROVED
    db.session.commit()

    flash(f'Команда "{team.name}" успешно подтверждена.', 'success')
    return redirect(url_for('admin.team_approvals'))


@admin.route('/reject-team/<int:team_id>')
@admin_required
def reject_team(team_id):
    """Отклонение команды"""
    team = Team.query.get_or_404(team_id)

    # Проверка прав доступа для региональных представителей
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE:
        competition = Competition.query.get_or_404(team.competition_id)
        if competition.organizer_id != current_user.id:
            flash('У вас нет прав для модерации этой команды.', 'danger')
            return redirect(url_for('admin.team_approvals'))

    team.status = TeamStatus.REJECTED
    db.session.commit()

    flash(f'Команда "{team.name}" отклонена.', 'warning')
    return redirect(url_for('admin.team_approvals'))


@admin.route('/results/<int:competition_id>')
@admin_required
def enter_results(competition_id):
    """Ввод результатов соревнования"""
    competition = Competition.query.get_or_404(competition_id)

    # Проверка прав доступа для региональных представителей
    if current_user.role == UserRole.REGIONAL_REPRESENTATIVE and competition.organizer_id != current_user.id:
        flash('У вас нет прав для управления результатами этого соревнования.', 'danger')
        return redirect(url_for('admin.index'))

    # Получаем подтвержденные команды для этого соревнования
    teams = Team.query.filter_by(competition_id=competition_id, status=TeamStatus.APPROVED).all()

    # Получаем уже введенные результаты
    results = Result.query.filter_by(competition_id=competition_id).all()

    return render_template('admin/enter_results.html',
                           competition=competition,
                           teams=teams,
                           results=results)


@admin.route('/analytics')
@fsp_admin_required
def analytics():
    """Аналитика и статистика (только для администраторов ФСП)"""
    # Статистика по регионам
    region_stats = db.session.query(
        Region.name,
        func.count(User.id).label('users_count'),
        func.count(distinct(Team.id)).label('teams_count')
    ).outerjoin(User, User.region_id == Region.id) \
        .outerjoin(Team, Team.captain_id == User.id) \
        .group_by(Region.id).all()

    # Статистика по дисциплинам
    discipline_stats = db.session.query(
        Competition.discipline,
        func.count(Competition.id).label('competitions_count'),
        func.count(distinct(Team.id)).label('teams_count')
    ).outerjoin(Team, Team.competition_id == Competition.id) \
        .group_by(Competition.discipline).all()

    return render_template('admin/analytics.html',
                           region_stats=region_stats,
                           discipline_stats=discipline_stats)