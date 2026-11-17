from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .models import AgeRange, Child, Classroom, Club, Parent, StudyGroup
from .services import enroll_child


class EnrollmentAgeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="parent", password="StrongPass123!")
        self.parent = Parent.objects.create(user=self.user)
        self.child = Child.objects.create(
            parent=self.parent, first_name="Иван", last_name="Тестов",
            birth_date=date.today() - timedelta(days=6 * 365)
        )
        self.age_range = AgeRange.objects.create(title="От 7 до 10", min_age=7, max_age=10)
        self.club = Club.objects.create(name="Шахматы", description="Тест", direction="Интеллектуальное")
        self.room = Classroom.objects.create(name="Тестовый кабинет", capacity=10)
        self.teacher = User.objects.create_user(username="teacher", password="StrongPass123!")
        self.group = StudyGroup.objects.create(
            club=self.club, age_range=self.age_range, classroom=self.room,
            teacher=self.teacher, title="Шахматы 7+", capacity=10
        )

    def test_child_under_minimum_age_cannot_enroll(self):
        with self.assertRaises(ValidationError):
            enroll_child(self.child, self.group)
