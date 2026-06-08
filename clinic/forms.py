from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from .models import (
    Review, Appointment, Client, Doctor, Service,
    ServiceCategory, Diagnosis, ClientDiagnosis
)

phone_validator = RegexValidator(
    regex=r'^\+375 \((?:29|33|44|25)\) \d{3}-\d{2}-\d{2}$',
    message='Номер телефона должен быть в формате +375 (29) XXX-XX-XX'
)


def validate_adult_form(value):
    """Validate age >= 18 for forms (with clear error message)."""
    today = date.today()
    age = (today - value).days // 365
    if age < 18:
        raise ValidationError(
            f'Вам должно быть не менее 18 лет. '
            f'По вашей дате рождения вам {age} лет.'
        )
    if value > today:
        raise ValidationError('Дата рождения не может быть в будущем.')
    if value.year < 1900:
        raise ValidationError('Введите корректную дату рождения.')


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=100, required=True, label='Имя')
    last_name = forms.CharField(max_length=100, required=True, label='Фамилия')
    patronymic = forms.CharField(max_length=100, required=False, label='Отчество')
    date_of_birth = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(attrs={'type': 'date', 'max': str(date.today())}),
        help_text='Необходимо быть старше 18 лет'
    )
    phone = forms.CharField(
        max_length=25, required=True,
        label='Телефон',
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+375 (29) XXX-XX-XX'})
    )
    address = forms.CharField(
        required=True, label='Адрес проживания',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'г. Минск, ул. ...'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            validate_adult_form(dob)
        return dob

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(choices=Review.RATING_CHOICES),
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Напишите ваш отзыв...'}),
        }
        labels = {
            'rating': 'Оценка',
            'text': 'Текст отзыва',
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if len(text.strip()) < 10:
            raise forms.ValidationError('Отзыв должен содержать не менее 10 символов.')
        return text


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'services', 'appointment_date', 'notes']
        widgets = {
            'appointment_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'services': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'doctor': 'Врач',
            'services': 'Услуги',
            'appointment_date': 'Дата и время',
            'notes': 'Примечания',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['appointment_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['services'].queryset = Service.objects.filter(is_active=True)
        self.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)

    def clean_appointment_date(self):
        from django.utils import timezone
        appt_date = self.cleaned_data.get('appointment_date')
        if appt_date and appt_date < timezone.now():
            raise ValidationError('Нельзя записаться на прошедшую дату.')
        return appt_date


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'patronymic', 'date_of_birth',
                  'phone', 'email', 'address', 'passport_series', 'passport_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'patronymic': 'Отчество',
            'date_of_birth': 'Дата рождения',
            'phone': 'Телефон (+375 (29) XXX-XX-XX)',
            'email': 'Email',
            'address': 'Адрес',
            'passport_series': 'Серия паспорта',
            'passport_number': 'Номер паспорта',
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            validate_adult_form(dob)
        return dob


class ServiceFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ServiceCategory.objects.all(),
        required=False,
        empty_label='Все категории',
        label='Категория'
    )
    price_min = forms.DecimalField(required=False, min_value=0, label='Цена от')
    price_max = forms.DecimalField(required=False, min_value=0, label='Цена до')
    search = forms.CharField(required=False, label='Поиск', max_length=200)
    sort = forms.ChoiceField(
        choices=[('name', 'По названию'), ('price', 'По цене ↑'), ('-price', 'По цене ↓')],
        required=False, label='Сортировка'
    )

    def clean(self):
        cleaned = super().clean()
        price_min = cleaned.get('price_min')
        price_max = cleaned.get('price_max')
        if price_min and price_max and price_min > price_max:
            raise forms.ValidationError('Минимальная цена не может быть больше максимальной.')
        return cleaned


class DoctorFilterForm(forms.Form):
    specialization = forms.CharField(required=False, label='Специализация')
    department = forms.CharField(required=False, label='Отделение')
    search = forms.CharField(required=False, label='Поиск', max_length=200)
    sort = forms.ChoiceField(
        choices=[('last_name', 'По фамилии'), ('experience_years', 'По стажу ↑'), ('-experience_years', 'По стажу ↓')],
        required=False, label='Сортировка'
    )


class AppointmentFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Все')] + list(Appointment.STATUS_CHOICES)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label='Статус')
    date_from = forms.DateField(
        required=False, label='С даты',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False, label='По дату',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
