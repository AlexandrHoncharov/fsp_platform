from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Team, TeamMember, User, Competition, TeamStatus, MemberStatus
from app.forms import TeamForm, TeamMemberForm

teams = Blueprint('teams', __name__, url_prefix='/teams')


@teams.route('/create/<int:competition_id>', methods=['GET', 'POST'])
@login_required
def create(competition_id):
    """Создание новой команды для соревнования"""
    competition = Competition.query.get_or_404(competition_id)

    # Проверка, что регистрация открыта
    from datetime import datetime
    if datetime.utcnow() < competition.registration_start or datetime.utcnow() > competition.registration_end:
        flash('Регистрация на это соревнование закрыта.', 'danger')
        return redirect(url_for('competitions.view', id=competition_id))

    form = TeamForm()

    if form.validate_on_submit():
        # Создание команды
        team = Team(
            name=form.name.data,
            description=form.description.data,
            captain_id=current_user.id,
            competition_id=competition_id,
            needs_members=form.needs_members.data,
            status=TeamStatus.FORMING if form.needs_members.data else TeamStatus.PENDING
        )
        db.session.add(team)

        # Добавляем капитана как участника команды
        captain_member = TeamMember(
            team=team,
            user_id=current_user.id,
            status=MemberStatus.CONFIRMED,
            role_description="Капитан"
        )
        db.session.add(captain_member)

        db.session.commit()

        flash('Команда успешно создана!', 'success')
        return redirect(url_for('teams.view', id=team.id))

    return render_template('teams/create.html', form=form, competition=competition)


@teams.route('/view/<int:id>')
def view(id):
    """Просмотр информации о команде"""
    team = Team.query.get_or_404(id)
    members = team.members.all()

    # Проверка, является ли текущий пользователь капитаном команды
    is_captain = current_user.is_authenticated and current_user.id == team.captain_id

    # Проверка, может ли пользователь присоединиться к команде
    can_join = False
    if current_user.is_authenticated and team.needs_members:
        # Проверка, что пользователь еще не в команде
        is_member = any(m.user_id == current_user.id for m in members)
        can_join = not is_member

    return render_template('teams/view.html',
                           team=team,
                           members=members,
                           is_captain=is_captain,
                           can_join=can_join)


@teams.route('/join/<int:id>', methods=['GET', 'POST'])
@login_required
def join(id):
    """Присоединение к команде"""
    team = Team.query.get_or_404(id)

    # Проверка, что команда все еще набирает участников
    if not team.needs_members or team.status != TeamStatus.FORMING:
        flash('Эта команда не набирает новых участников.', 'danger')
        return redirect(url_for('teams.view', id=id))

    # Проверка, что пользователь еще не в команде
    existing_member = TeamMember.query.filter_by(team_id=id, user_id=current_user.id).first()
    if existing_member:
        flash('Вы уже являетесь участником этой команды.', 'warning')
        return redirect(url_for('teams.view', id=id))

    form = TeamMemberForm()

    if form.validate_on_submit():
        member = TeamMember(
            team_id=id,
            user_id=current_user.id,
            role_description=form.role_description.data,
            status=MemberStatus.INVITED  # Капитан еще должен подтвердить
        )
        db.session.add(member)
        db.session.commit()

        flash('Заявка на вступление в команду отправлена!', 'success')
        return redirect(url_for('teams.view', id=id))

    return render_template('teams/join.html', form=form, team=team)


@teams.route('/approve_member/<int:member_id>')
@login_required
def approve_member(member_id):
    """Подтверждение заявки на вступление в команду (только для капитана)"""
    member = TeamMember.query.get_or_404(member_id)
    team = Team.query.get_or_404(member.team_id)

    # Проверка, что текущий пользователь - капитан команды
    if current_user.id != team.captain_id:
        flash('У вас нет прав для управления этой командой.', 'danger')
        return redirect(url_for('teams.view', id=team.id))

    member.status = MemberStatus.CONFIRMED
    db.session.commit()

    flash('Участник успешно добавлен в команду!', 'success')
    return redirect(url_for('teams.view', id=team.id))


@teams.route('/reject_member/<int:member_id>')
@login_required
def reject_member(member_id):
    """Отклонение заявки на вступление в команду (только для капитана)"""
    member = TeamMember.query.get_or_404(member_id)
    team = Team.query.get_or_404(member.team_id)

    # Проверка, что текущий пользователь - капитан команды
    if current_user.id != team.captain_id:
        flash('У вас нет прав для управления этой командой.', 'danger')
        return redirect(url_for('teams.view', id=team.id))

    member.status = MemberStatus.REJECTED
    db.session.commit()

    flash('Заявка на вступление в команду отклонена.', 'success')
    return redirect(url_for('teams.view', id=team.id))


@teams.route('/submit/<int:id>')
@login_required
def submit(id):
    """Отправка заявки команды на модерацию (только для капитана)"""
    team = Team.query.get_or_404(id)

    # Проверка, что текущий пользователь - капитан команды
    if current_user.id != team.captain_id:
        flash('У вас нет прав для управления этой командой.', 'danger')
        return redirect(url_for('teams.view', id=id))

    # Проверка, что все участники подтвердили участие
    confirmed_members = TeamMember.query.filter_by(team_id=id, status=MemberStatus.CONFIRMED).count()

    if confirmed_members < 2:  # Минимум 2 участника (включая капитана)
        flash('В команде должно быть минимум 2 подтвержденных участника.', 'danger')
        return redirect(url_for('teams.view', id=id))

    team.status = TeamStatus.PENDING
    team.needs_members = False
    db.session.commit()

    flash('Заявка команды отправлена на модерацию!', 'success')
    return redirect(url_for('teams.view', id=id))