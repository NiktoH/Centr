from datetime import date
from pathlib import Path
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Child, Enrollment, MedicalCertificate, Parent, StudyGroup


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Имя", max_length=80)
    last_name = forms.CharField(label="Фамилия", max_length=80)
    phone = forms.CharField(label="Телефон", max_length=30, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            Parent.objects.create(user=user, phone=self.cleaned_data.get("phone", ""))
        return user


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ["first_name", "last_name", "birth_date", "photo", "notes"]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Размер изображения не должен превышать 5 МБ.")
            if Path(photo.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise forms.ValidationError("Допустимые форматы: JPG, PNG, WEBP.")
        return photo

    def clean_birth_date(self):
        value = self.cleaned_data["birth_date"]
        if value >= date.today():
            raise forms.ValidationError("Дата рождения должна быть в прошлом.")
        return value


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["child", "group"]

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent:
            self.fields["child"].queryset = Child.objects.filter(parent=parent)
        self.fields["group"].queryset = StudyGroup.objects.filter(is_active=True).select_related("club", "age_range")

    def clean(self):
        cleaned = super().clean()
        child = cleaned.get("child")
        group = cleaned.get("group")
        if child and group:
            if not group.age_range.min_age <= child.age <= group.age_range.max_age:
                raise forms.ValidationError("Возраст ребёнка не соответствует возрастному диапазону группы.")
            current = group.enrollments.filter(is_active=True).exclude(pk=self.instance.pk)
            if current.count() >= group.capacity:
                raise forms.ValidationError("В группе нет свободных мест.")
            if current.filter(child=child).exists():
                raise forms.ValidationError("Ребёнок уже записан в эту группу.")
        return cleaned


class MedicalCertificateForm(forms.ModelForm):
    class Meta:
        model = MedicalCertificate
        fields = ["attendance", "file", "illness_from", "illness_to", "parent_comment"]
        widgets = {
            "illness_from": forms.DateInput(attrs={"type": "date"}),
            "illness_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent:
            self.fields["attendance"].queryset = (
                self.fields["attendance"].queryset
                .filter(child__parent=parent, status="missed")
                .exclude(certificate__isnull=False)
            )

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if uploaded:
            if uploaded.size > 8 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 8 МБ.")
            if Path(uploaded.name).suffix.lower() not in {".pdf", ".jpg", ".jpeg", ".png"}:
                raise forms.ValidationError("Допустимые форматы: PDF, JPG, PNG.")
        return uploaded

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("illness_from")
        end = cleaned.get("illness_to")
        if start and end and end < start:
            self.add_error("illness_to", "Дата окончания болезни не может быть раньше даты начала.")
        return cleaned
