from datetime import date
from pathlib import Path
import os
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Child, Enrollment, MedicalCertificate, Parent, StudyGroup, Attendance


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=100, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=100, required=True)
    email = forms.EmailField(label="Электронная почта", required=True)
    phone = forms.CharField(label="Телефон", max_length=20, required=True)
    address = forms.CharField(label="Адрес", max_length=255, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "address")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Parent.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
                address=self.cleaned_data["address"],
            )
        return user


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ("last_name", "first_name", "birth_date", "photo", "notes")
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("child", "group")

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent is not None:
            self.fields["child"].queryset = Child.objects.filter(parent=parent)
        self.fields["group"].queryset = StudyGroup.objects.filter(is_active=True).select_related("club", "age_range")

    def clean(self):
        cleaned_data = super().clean()
        child = cleaned_data.get("child")
        group = cleaned_data.get("group")
        if child and group:
            if not (group.age_range.min_age <= child.age <= group.age_range.max_age):
                raise ValidationError(
                    f"Запись невозможна: возраст ребёнка ({child.age} лет) не входит в диапазон "
                    f"{group.age_range.min_age}–{group.age_range.max_age} лет."
                )
            if group.free_places <= 0:
                raise ValidationError("В выбранной группе нет свободных мест.")
        return cleaned_data


class MedicalCertificateForm(forms.ModelForm):
    class Meta:
        model = MedicalCertificate
        fields = ("attendance", "file", "illness_from", "illness_to", "parent_comment")
        widgets = {
            "illness_from": forms.DateInput(attrs={"type": "date"}),
            "illness_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent is not None:
            self.fields["attendance"].queryset = Attendance.objects.filter(
                child__parent=parent,
                status=Attendance.STATUS_MISSED,
                certificate__isnull=True,
            ).select_related("lesson__group", "child")

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded:
            ext = os.path.splitext(uploaded.name)[1].lower()
            if ext not in (".pdf", ".jpg", ".jpeg", ".png"):
                raise ValidationError("Допустимы только файлы форматов PDF, JPG или PNG.")
            if uploaded.size > 8 * 1024 * 1024:
                raise ValidationError("Размер файла не должен превышать 8 МБ.")
        return uploaded

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("illness_from")
        end = cleaned_data.get("illness_to")
        if start and end and end < start:
            raise ValidationError("Дата окончания болезни не может быть раньше даты начала.")
        return cleaned_data
