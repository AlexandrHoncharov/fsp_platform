"""
Скрипт для инициализации системы достижений:
- Создает базовые достижения по категориям
"""

from app import create_app, db
from app.models import Achievement


def init_achievements():
    # Создание приложения в режиме разработки
    app = create_app('development')

    with app.app_context():
        # Проверяем, что таблица достижений пуста
        if Achievement.query.count() == 0:
            print("Добавление достижений...")

            # Категория: Участие в соревнованиях
            participation_achievements = [
                {
                    'name': 'Первые шаги',
                    'description': 'Участие в первом соревновании',
                    'badge_icon': 'bi-pencil',
                    'category': 'Участие',
                    'points': 10
                },
                {
                    'name': 'Активный участник',
                    'description': 'Приняли участие в 5 соревнованиях',
                    'badge_icon': 'bi-person-check',
                    'category': 'Участие',
                    'points': 25
                },
                {
                    'name': 'Ветеран',
                    'description': 'Приняли участие в 20 соревнованиях',
                    'badge_icon': 'bi-shield',
                    'category': 'Участие',
                    'points': 50
                },
                {
                    'name': 'Легенда',
                    'description': 'Приняли участие в 50 соревнованиях',
                    'badge_icon': 'bi-shield-fill-check',
                    'category': 'Участие',
                    'points': 100
                }
            ]

            # Категория: Победы
            victory_achievements = [
                {
                    'name': 'Первая победа',
                    'description': 'Заняли 1 место в соревновании',
                    'badge_icon': 'bi-trophy',
                    'category': 'Победы',
                    'points': 50
                },
                {
                    'name': 'Победитель',
                    'description': 'Заняли 1 место в 5 соревнованиях',
                    'badge_icon': 'bi-trophy-fill',
                    'category': 'Победы',
                    'points': 100
                },
                {
                    'name': 'Неудержимый',
                    'description': 'Заняли 1 место в 3 соревнованиях подряд',
                    'badge_icon': 'bi-lightning',
                    'category': 'Победы',
                    'points': 150
                },
                {
                    'name': 'Чемпион',
                    'description': 'Заняли 1 место во всероссийском соревновании',
                    'badge_icon': 'bi-award-fill',
                    'category': 'Победы',
                    'points': 200
                }
            ]

            # Категория: Дисциплины
            discipline_achievements = [
                {
                    'name': 'Продуктовик',
                    'description': 'Участие в 3 соревнованиях по продуктовому программированию',
                    'badge_icon': 'bi-box',
                    'category': 'Дисциплины',
                    'points': 30
                },
                {
                    'name': 'Защитник',
                    'description': 'Участие в 3 соревнованиях по программированию систем информационной безопасности',
                    'badge_icon': 'bi-shield-lock',
                    'category': 'Дисциплины',
                    'points': 30
                },
                {
                    'name': 'Алгоритмист',
                    'description': 'Участие в 3 соревнованиях по алгоритмическому программированию',
                    'badge_icon': 'bi-code-square',
                    'category': 'Дисциплины',
                    'points': 30
                },
                {
                    'name': 'Робототехник',
                    'description': 'Участие в 3 соревнованиях по программированию робототехники',
                    'badge_icon': 'bi-robot',
                    'category': 'Дисциплины',
                    'points': 30
                },
                {
                    'name': 'Авиатор',
                    'description': 'Участие в 3 соревнованиях по программированию беспилотных авиационных систем',
                    'badge_icon': 'bi-airplane',
                    'category': 'Дисциплины',
                    'points': 30
                },
                {
                    'name': 'Многопрофильный специалист',
                    'description': 'Участие в соревнованиях по всем 5 дисциплинам',
                    'badge_icon': 'bi-stars',
                    'category': 'Дисциплины',
                    'points': 100
                }
            ]

            # Категория: Командная работа
            team_achievements = [
                {
                    'name': 'Капитан',
                    'description': 'Создание первой команды',
                    'badge_icon': 'bi-person-fill',
                    'category': 'Команда',
                    'points': 20
                },
                {
                    'name': 'Лидер',
                    'description': 'Создание 5 успешных команд',
                    'badge_icon': 'bi-people-fill',
                    'category': 'Команда',
                    'points': 50
                },
                {
                    'name': 'Командный игрок',
                    'description': 'Участие в 10 различных командах',
                    'badge_icon': 'bi-people',
                    'category': 'Команда',
                    'points': 40
                },
                {
                    'name': 'Верность',
                    'description': 'Участие в 5 соревнованиях с одной и той же командой',
                    'badge_icon': 'bi-heart-fill',
                    'category': 'Команда',
                    'points': 60
                }
            ]

            # Объединяем все достижения
            all_achievements = []
            all_achievements.extend(participation_achievements)
            all_achievements.extend(victory_achievements)
            all_achievements.extend(discipline_achievements)
            all_achievements.extend(team_achievements)

            # Добавляем в базу данных
            for achievement_data in all_achievements:
                achievement = Achievement(**achievement_data)
                db.session.add(achievement)

            db.session.commit()
            print(f"Добавлено {len(all_achievements)} достижений")
        else:
            print("Таблица достижений уже заполнена")

        print("Инициализация достижений завершена")


if __name__ == "__main__":
    init_achievements()