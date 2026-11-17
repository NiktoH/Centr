from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Parent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parent_profile",
        verbose_name="Пользователь",
    )
    phone = models.CharField("Телефон", max_length=20)
    address = models.CharField("Адрес", max_length=255, blank=True)

    class Meta:
        verbose_name = "Родитель"
        verbose_name_plural = "Родители"

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username


class Child(models.Model):
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="Родитель",
    )
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    birth_date = models.DateField("Дата рождения")
    photo = models.ImageField("Фотография", upload_to="children/", blank=True, null=True)
    notes = models.TextField("Особенности / примечания", blank=True)

    class Meta:
        verbose_name = "Ребёнок"
        verbose_name_plural = "Дети"
        ordering = ["last_name", "first_name"]

    @property
    def age(self):
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Club(models.Model):
    name = models.CharField("Название кружка", max_length=150)
    description = models.TextField("Описание")
    direction = models.CharField("Направление", max_length=100)
    image = models.ImageField("Обложка", upload_to="clubs/", blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Кружок / мастер-класс"
        verbose_name_plural = "Кружки и мастер-классы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AgeRange(models.Model):
    title = models.CharField("Название категории", max_length=100)
    min_age = models.PositiveSmallIntegerField("Минимальный возраст")
    max_age = models.PositiveSmallIntegerField("Максимальный возраст")

    class Meta:
        verbose_name = "Возрастная категория"
        verbose_name_plural = "Возрастные категории"
        ordering = ["min_age", "max_age"]

    def clean(self):
        if self.max_age < self.min_age:
            raise ValidationError("Максимальный возраст не может быть меньше минимального.")

    def __str__(self):
        return f"{self.title} ({self.min_age}–{self.max_age} лет)"


class Classroom(models.Model):
    name = models.CharField("Название / номер кабинета", max_length=100)
    capacity = models.PositiveSmallIntegerField("Вместимость")
    description = models.TextField("Оснащение", blank=True)

    class Meta:
        verbose_name = "Учебный кабинет"
        verbose_name_plural = "Учебные кабинеты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class StudyGroup(models.Model):
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name="Кружок",
    )
    age_range = models.ForeignKey(
        AgeRange,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="Возрастная категория",
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="Кабинет",
    )
    teacher = models.CharField("Педагог", max_length=150)
    title = models.CharField("Название группы", max_length=150)
    capacity = models.PositiveSmallIntegerField("Лимит мест", default=12)
    is_active = models.BooleanField("Набор открыт", default=True)
    children = models.ManyToManyField(
        Child,
        through="Enrollment",
        related_name="study_groups",
        verbose_name="Записанные дети",
    )

    class Meta:
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"
        ordering = ["title"]

    @property
    def occupied_places(self):
        return self.enrollments.filter(is_active=True).count()

    @property
    def free_places(self):
        return max(0, self.capacity - self.occupied_places)

    def __str__(self):
        return f"{self.title} ({self.club.name})"


class Enrollment(models.Model):
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Ребёнок",
    )
    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Группа",
    )
    enrolled_at = models.DateTimeField("Дата записи", auto_now_add=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Запись в группу"
        verbose_name_plural = "Записи в группы"
        constraints = [
            models.UniqueConstraint(
                fields=["child", "group"],
                name="unique_child_group_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.child} -> {self.group.title}"


class LessonSchedule(models.Model):
    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Группа",
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="lessons",
        verbose_name="Кабинет",
    )
    starts_at = models.DateTimeField("Начало занятия")
    ends_at = models.DateTimeField("Окончание занятия")
    topic = models.CharField("Тема занятия", max_length=200, blank=True)

    class Meta:
        verbose_name = "Занятие в расписании"
        verbose_name_plural = "Расписание занятий"
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.group.title} ({self.starts_at:%d.%m.%Y %H:%M})"


class Subscription(models.Model):
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Ребёнок",
    )
    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Группа",
    )
    title = models.CharField("Название абонемента", max_length=150)
    total_lessons = models.PositiveSmallIntegerField("Всего занятий")
    remaining_lessons = models.PositiveSmallIntegerField("Осталось занятий")
    starts_on = models.DateField("Дата начала")
    ends_on = models.DateField("Действует до")
    price = models.DecimalField("Стоимость, руб.", max_digits=10, decimal_places=2)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Абонемент"
        verbose_name_plural = "Абонементы"
        ordering = ["-ends_on"]

    def __str__(self):
        return f"{self.title} — {self.child}"


class Attendance(models.Model):
    STATUS_PRESENT = "present"
    STATUS_MISSED = "missed"
    STATUS_EXCUSED = "excused"

    STATUS_CHOICES = [
        (STATUS_PRESENT, "Присутствовал"),
        (STATUS_MISSED, "Пропустил без причины"),
        (STATUS_EXCUSED, "Пропуск по уважительной причине"),
    ]

    lesson = models.ForeignKey(
        LessonSchedule,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Занятие",
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Ребёнок",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendances",
        verbose_name="Абонемент",
    )
    status = models.CharField(
        "Статус посещения",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT,
    )
    marked_at = models.DateTimeField("Время отметки", auto_now=True)

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Учёт посещаемости"
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "child"],
                name="unique_lesson_child_attendance",
            )
        ]

    def __str__(self):
        return f"{self.child} — {self.lesson} ({self.get_status_display()})"


class MedicalCertificate(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "На проверке"),
        (STATUS_APPROVED, "Подтверждена"),
        (STATUS_REJECTED, "Отклонена"),
    ]

    attendance = models.OneToOneField(
        Attendance,
        on_delete=models.CASCADE,
        related_name="certificate",
        verbose_name="Пропущенное занятие",
    )
    file = models.FileField("Файл справки", upload_to="certificates/")
    illness_from = models.DateField("Болел с")
    illness_to = models.DateField("Болел по")
    status = models.CharField(
        "Статус проверки",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    parent_comment = models.TextField("Комментарий родителя", blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_certificates",
        verbose_name="Проверил администратор",
    )
    reviewed_at = models.DateTimeField("Дата проверки", null=True, blank=True)

    class Meta:
        verbose_name = "Медицинская справка"
        verbose_name_plural = "Медицинские справки"
        ordering = ["-id"]

        def __str__(self):
            return f"Справка: {self.attendance.child} ({self.illness_from} — {self.illness_to})"