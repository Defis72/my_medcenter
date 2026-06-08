import re
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger('clinic')

phone_validator = RegexValidator(
    regex=r'^\+375 \((?:29|33|44|25)\) \d{3}-\d{2}-\d{2}$',
    message='Номер телефона должен быть в формате +375 (29) XXX-XX-XX'
)


def validate_adult(value):
    today = timezone.now().date()
    age = (today - value).days // 365
    if age < 18:
        raise ValidationError('Возраст должен быть 18 лет и старше.')


# ==================== SITE PAGES MODELS ====================

class CompanyInfo(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    logo = models.ImageField('Логотип', upload_to='company/', blank=True, null=True)
    video_url = models.URLField('Видео', blank=True)
    founded_year = models.PositiveIntegerField('Год основания', blank=True, null=True)
    address = models.TextField('Адрес', blank=True)
    phone = models.CharField('Телефон', max_length=25, blank=True)
    email = models.EmailField('Email', blank=True)
    inn = models.CharField('ИНН', max_length=20, blank=True)
    ogrn = models.CharField('ОГРН', max_length=20, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Информация о компании'
        verbose_name_plural = 'Информация о компании'

    def __str__(self):
        return self.name


class CompanyHistory(models.Model):
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name='history')
    year = models.PositiveIntegerField('Год')
    event = models.TextField('Событие')

    class Meta:
        verbose_name = 'История компании'
        verbose_name_plural = 'История компании'
        ordering = ['year']

    def __str__(self):
        return f'{self.year}: {self.event[:50]}'


class Article(models.Model):
    title = models.CharField('Заголовок', max_length=300)
    summary = models.CharField('Краткое содержание', max_length=500)
    content = models.TextField('Содержание')
    image = models.ImageField('Изображение', upload_to='articles/', blank=True, null=True)
    image_data = models.TextField('Изображение (base64)', blank=True, default='')
    published_at = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    is_published = models.BooleanField('Опубликована', default=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class GlossaryTerm(models.Model):
    question = models.CharField('Вопрос/Термин', max_length=400)
    answer = models.TextField('Ответ/Определение')
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Термин/FAQ'
        verbose_name_plural = 'Словарь терминов/FAQ'
        ordering = ['question']

    def __str__(self):
        return self.question[:80]


class Contact(models.Model):
    full_name = models.CharField('ФИО', max_length=200)
    position = models.CharField('Должность', max_length=200)
    photo = models.ImageField('Фото', upload_to='contacts/', blank=True, null=True)
    photo_data = models.TextField('Фото (base64)', blank=True, default='')
    phone = models.CharField('Телефон', max_length=25, validators=[phone_validator])
    email = models.EmailField('Email')
    description = models.TextField('Описание', blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['order', 'full_name']

    def __str__(self):
        return f'{self.full_name} — {self.position}'


class Vacancy(models.Model):
    title = models.CharField('Название вакансии', max_length=200)
    description = models.TextField('Описание')
    salary_from = models.DecimalField('Зарплата от', max_digits=10, decimal_places=2, blank=True, null=True)
    salary_to = models.DecimalField('Зарплата до', max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    author_name = models.CharField('Имя автора', max_length=100)
    rating = models.IntegerField('Оценка', choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField('Текст отзыва')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    is_approved = models.BooleanField('Одобрен', default=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author_name} — {self.rating}★'


class PromoCode(models.Model):
    code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание')
    discount_percent = models.DecimalField('Скидка %', max_digits=5, decimal_places=2,
                                           validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateField('Действует с')
    valid_to = models.DateField('Действует до')
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды и купоны'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.discount_percent}%)'

    @property
    def is_current(self):
        from datetime import date as date_cls
        today = date_cls.today()
        return self.is_active and self.valid_from <= today <= self.valid_to


# ==================== MAIN CLINIC MODELS ====================

class Specialization(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField('Название отделения', max_length=200)
    description = models.TextField('Описание', blank=True)
    floor = models.PositiveIntegerField('Этаж', default=1)

    class Meta:
        verbose_name = 'Отделение'
        verbose_name_plural = 'Отделения'
        ordering = ['name']

    def __str__(self):
        return self.name


class DoctorCategory(models.Model):
    name = models.CharField('Категория', max_length=100)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория врача'
        verbose_name_plural = 'Категории врачей'

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь',
                                null=True, blank=True)
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True)
    date_of_birth = models.DateField('Дата рождения', validators=[validate_adult])
    phone = models.CharField('Телефон', max_length=25, validators=[phone_validator])
    email = models.EmailField('Email')
    photo = models.ImageField('Фото', upload_to='doctors/', blank=True, null=True)
    photo_data = models.TextField('Фото (base64)', blank=True, default='')
    category = models.ForeignKey(DoctorCategory, on_delete=models.SET_NULL, null=True,
                                  verbose_name='Категория')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True,
                                    verbose_name='Отделение')
    specializations = models.ManyToManyField(Specialization, verbose_name='Специализации')
    experience_years = models.PositiveIntegerField('Стаж (лет)', default=0)
    bio = models.TextField('Биография', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)

    def get_specializations_str(self):
        return ', '.join(s.name for s in self.specializations.all())

    @property
    def age(self):
        today = timezone.now().date()
        return (today - self.date_of_birth).days // 365


class ServiceCategory(models.Model):
    name = models.CharField('Название категории', max_length=200)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'
        ordering = ['name']

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE,
                                  related_name='services', verbose_name='Категория')
    name = models.CharField('Название услуги', max_length=300)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    duration_minutes = models.PositiveIntegerField('Длительность (мин)', default=30)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} — {self.price} руб.'


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь',
                                null=True, blank=True)
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True)
    date_of_birth = models.DateField('Дата рождения', validators=[validate_adult])
    phone = models.CharField('Телефон', max_length=25, validators=[phone_validator])
    email = models.EmailField('Email')
    address = models.TextField('Адрес', blank=True)
    passport_series = models.CharField('Серия паспорта', max_length=10, blank=True)
    passport_number = models.CharField('Номер паспорта', max_length=20, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)

    @property
    def age(self):
        today = timezone.now().date()
        return (today - self.date_of_birth).days // 365


class Diagnosis(models.Model):
    code = models.CharField('Код МКБ', max_length=20)
    name = models.CharField('Название', max_length=300)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Диагноз'
        verbose_name_plural = 'Диагнозы'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class ClientDiagnosis(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='diagnoses',
                                verbose_name='Клиент')
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, verbose_name='Диагноз')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True,
                                verbose_name='Лечащий врач')
    date_set = models.DateField('Дата постановки', default=timezone.now)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Диагноз клиента'
        verbose_name_plural = 'Диагнозы клиентов'
        ordering = ['-date_set']

    def __str__(self):
        return f'{self.client} — {self.diagnosis}'


class Schedule(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
        (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedule',
                                verbose_name='Врач')
    weekday = models.IntegerField('День недели', choices=WEEKDAY_CHOICES)
    time_from = models.TimeField('Начало приёма')
    time_to = models.TimeField('Конец приёма')

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['weekday', 'time_from']
        unique_together = ['doctor', 'weekday']

    def __str__(self):
        return f'{self.doctor} — {self.get_weekday_display()} {self.time_from}-{self.time_to}'


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Запланирован'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments',
                                verbose_name='Клиент')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments',
                                verbose_name='Врач')
    services = models.ManyToManyField(Service, verbose_name='Услуги')
    appointment_date = models.DateTimeField('Дата и время приёма')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='planned')
    notes = models.TextField('Примечания врача', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Приём'
        verbose_name_plural = 'Приёмы'
        ordering = ['appointment_date']

    def __str__(self):
        return f'{self.client} → {self.doctor} {self.appointment_date.strftime("%d/%m/%Y %H:%M")}'

    def total_cost(self):
        return sum(s.price for s in self.services.all())


class Sale(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE,
                                        related_name='sale', verbose_name='Приём')
    total_amount = models.DecimalField('Итоговая сумма', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Скидка', max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Промокод')
    paid_at = models.DateTimeField('Дата оплаты', auto_now_add=True)
    payment_method = models.CharField('Способ оплаты', max_length=50, default='cash',
                                       choices=[('cash', 'Наличные'), ('card', 'Карта'), ('online', 'Онлайн')])

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['-paid_at']

    def __str__(self):
        return f'Оплата #{self.pk} — {self.total_amount} руб.'

    @property
    def final_amount(self):
        return self.total_amount - self.discount
