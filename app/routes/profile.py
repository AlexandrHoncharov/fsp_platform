from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, TeamMember, Team, Competition, Result, MemberStatus
from app.forms import ProfileForm

profile = Blueprint('profile', __name__, url_prefix='/profile')


@profile.route('/')
@login_required
def view():
    """Просмотр личного профиля пользователя"""
    # Получение результатов участия в соревнованиях
    results = Result.query.filter_by(user_id=current_user.id).all()

    # Получение текущих команд пользователя
    team_memberships = TeamMember.query.filter_by(
        user_id=current_user.id,
        status=MemberStatus.CONFIRMED
    ).all()

    teams = []
    for membership in team_memberships:
        team = Team.query.get(membership.team_id)
        if team:
            competition = Competition.query.get(team.competition_id)
            teams.append({
                'team': team,
                'competition': competition,
                'role': membership.role_description
            })

    # Получение приглашений в команды
    invitations = TeamMember.query.filter_by(
        user_id=current_user.id,
        status=MemberStatus.INVITED
    ).all()

    invitation_data = []
    for invitation in invitations:
        team = Team.query.get(invitation.team_id)
        if team:
            competition = Competition.query.get(team.competition_id)
            captain = User.query.get(team.captain_id)
            invitation_data.append({
                'id': invitation.id,
                'team': team,
                'competition': competition,
                'captain': captain,
                'role': invitation.role_description
            })

    return render_template('profiles/view.html',
                           user=current_user,
                           results=results,
                           teams=teams,
                           invitations=invitation_data)


@profile.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Редактирование профиля пользователя"""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        # Обновление пароля, если он был введен
        if form.new_password.data:
            current_user.password = form.new_password.data

        db.session.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('profile.view'))

    return render_template('profiles/edit.html', form=form)


@profile.route('/accept_invitation/<int:invitation_id>')
@login_required
def accept_invitation(invitation_id):
    """Принятие приглашения в команду"""
    invitation = TeamMember.query.get_or_404(invitation_id)

    # Проверка, что приглашение действительно для текущего пользователя
    if invitation.user_id != current_user.id:
        flash('Это приглашение не предназначено для вас.', 'danger')
        return redirect(url_for('profile.view'))

    invitation.status = MemberStatus.CONFIRMED
    db.session.commit()

    flash('Вы успешно присоединились к команде!', 'success')
    return redirect(url_for('profile.view'))


@profile.route('/decline_invitation/<int:invitation_id>')
@login_required
def decline_invitation(invitation_id):
    """Отклонение приглашения в команду"""
    invitation = TeamMember.query.get_or_404(invitation_id)

    # Проверка, что приглашение действительно для текущего пользователя
    if invitation.user_id != current_user.id:
        flash('Это приглашение не предназначено для вас.', 'danger')
        return redirect(url_for('profile.view'))

    invitation.status = MemberStatus.REJECTED
    db.session.commit()

    flash('Вы отклонили приглашение в команду.', 'info')
    return redirect(url_for('profile.view'))