from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from center.models import AgeRange, Attendance, Child, Classroom, Club, Enrollment, LessonSchedule, Parent, StudyGroup, Subscription


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные детского центра"

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(username="center_admin", defaults={
            "email": "admin@example.local", "is_staff": True, "is_superuser": True
        })
        if not admin.has_usable_password():
            admin.set_password("CenterAdmin2026!")
            admin.save()
        teacher, _ = User.objects.get_or_create(username="teacher", defaults={
            "first_name": "Анна", "last_name": "Педагог", "email": "teacher@example.local"
        })
        if not teacher.has_usable_password():
            teacher.set_password("Teacher2026!")
            teacher.save()
        ranges = [
            ("Малыши", 3, 5), ("Дошкольники", 5, 7), ("Младшая школа", 7, 10),
            ("Средняя школа", 10, 13), ("Подростки", 13, 16)
        ]
        age_ranges = [AgeRange.objects.get_or_create(title=t, min_age=a, max_age=b)[0] for t, a, b in ranges]
        rooms = [Classroom.objects.get_or_create(name=f"Кабинет {i}", defaults={"capacity": 12})[0] for i in range(1, 5)]
        club_data = [
            ("Робототехника", "Создание моделей и программирование роботов.", "Техническое"),
            ("Рисование", "Основы композиции, цвета и работа с материалами.", "Творческое"),
            ("Шахматы", "Логика, стратегия и развитие памяти.", "Интеллектуальное"),
            ("Подготовка к школе", "Развитие речи, счёта и внимания.", "Подготовительное"),
        ]
        clubs = [Club.objects.get_or_create(name=n, defaults={"description": d, "direction": direction})[0] for n, d, direction in club_data]
        groups = []
        for index in range(32):
            club = clubs[index % len(clubs)]
            age_range = age_ranges[index % len(age_ranges)]
            group, _ = StudyGroup.objects.get_or_create(
                title=f"{club.name} — группа {index + 1}",
                defaults={"club": club, "age_range": age_range, "classroom": rooms[index % len(rooms)],
                          "teacher": teacher, "capacity": 12, "is_active": True}
            )
            groups.append(group)
        for index in range(30):
            username = f"parent_demo_{index + 1}"
            user, _ = User.objects.get_or_create(username=username, defaults={
                "first_name": f"Родитель{index + 1}", "email": f"parent{index + 1}@example.local"
            })
            parent, _ = Parent.objects.get_or_create(user=user)
            birth_year = date.today().year - (4 + index % 10)
            birth = date(birth_year, 3 + index % 9, 1 + index % 20)
            child, _ = Child.objects.get_or_create(
                parent=parent, first_name=f"Ребёнок{index + 1}", last_name=f"Тестовый{index + 1}",
                defaults={"birth_date": birth}
            )
            group = groups[index % len(groups)]
            Enrollment.objects.get_or_create(child=child, group=group)
            subscription, _ = Subscription.objects.get_or_create(
                child=child, group=group, defaults={
                    "starts_on": date.today() - timedelta(days=14),
                    "ends_on": date.today() + timedelta(days=45),
                    "total_lessons": 8, "remaining_lessons": 6, "price": 3200
                }
            )
            lesson, _ = LessonSchedule.objects.get_or_create(
                group=group, starts_at=timezone.now() + timedelta(days=index % 7),
                defaults={"classroom": group.classroom, "ends_at": timezone.now() + timedelta(days=index % 7, hours=1),
                          "topic": "Знакомство с направлением"}
            )
            Attendance.objects.get_or_create(
                lesson=lesson, child=child, defaults={"subscription": subscription, "status": "present"}
            )
        self.stdout.write(self.style.SUCCESS("Демонстрационные данные созданы."))
        self.stdout.write("Администратор: center_admin / CenterAdmin2026!")
        self.stdout.write("Педагог: teacher / Teacher2026!")
