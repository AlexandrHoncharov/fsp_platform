from flask import Blueprint, render_template, request
from sqlalchemy import desc
from app.models import User, Region, RegionRating, Achievement, CompetitionDiscipline

rating = Blueprint('rating', __name__, url_prefix='/rating')


@rating.route('/athletes')
def athletes():
    """Рейтинг спортсменов"""
    # Получение параметров фильтрации
    region_id = request.args.get('region', type=int)
    discipline = request.args.get('discipline')

    # Базовый запрос
    query = User.query.filter_by(role='athlete').order_by(desc(User.rating_points))

    # Применение фильтров
    if region_id:
        query = query.filter_by(region_id=region_id)

    # Получение списка спортсменов
    athletes_list = query.limit(100).all()

    # Получение списка регионов для фильтра
    regions = Region.query.order_by(Region.name).all()

    # Дисциплины для фильтра
    disciplines = [
        (CompetitionDiscipline.PRODUCT, "Продуктовое программирование"),
        (CompetitionDiscipline.SECURITY, "Программирование систем информационной безопасности"),
        (CompetitionDiscipline.ALGORITHM, "Алгоритмическое программирование"),
        (CompetitionDiscipline.ROBOTICS, "Программирование робототехники"),
        (CompetitionDiscipline.DRONE, "Программирование беспилотных авиационных систем")
    ]

    return render_template('rating/athletes.html',
                           athletes=athletes_list,
                           regions=regions,
                           disciplines=disciplines,
                           selected_region=region_id,
                           selected_discipline=discipline)


@rating.route('/regions')
def regions():
    """Рейтинг регионов"""
    # Получаем все регионы с рейтингом
    regions_rating = RegionRating.query.join(Region, RegionRating.region_id == Region.id).order_by(
        desc(RegionRating.total_points)).all()

    return render_template('rating/regions.html', regions_rating=regions_rating)


@rating.route('/achievements')
def achievements():
    """Список всех возможных достижений"""
    # Группируем достижения по категориям
    achievements_by_category = {}

    all_achievements = Achievement.query.order_by(Achievement.category, Achievement.points).all()

    for achievement in all_achievements:
        if achievement.category not in achievements_by_category:
            achievements_by_category[achievement.category] = []
        achievements_by_category[achievement.category].append(achievement)

    return render_template('rating/achievements.html',
                           achievements_by_category=achievements_by_category)