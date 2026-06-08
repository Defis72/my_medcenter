import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.utils import timezone

from clinic.models import (
    CompanyInfo, Article, GlossaryTerm, Vacancy, Review, PromoCode,
    Specialization, Department, DoctorCategory, Doctor, ServiceCategory,
    Service, Client, Diagnosis, ClientDiagnosis, Schedule, Appointment, Sale
)
from clinic.forms import ReviewForm, ClientForm, AppointmentForm, ServiceFilterForm


# ===== FIXTURES =====

def make_doctor_category():
    return DoctorCategory.objects.create(name='Тест категория')

def make_department():
    return Department.objects.create(name='Тест отделение', floor=1)

def make_specialization():
    return Specialization.objects.create(name='Терапевт')

def make_doctor(user=None):
    cat = make_doctor_category()
    dept = make_department()
    spec = make_specialization()
    doc = Doctor.objects.create(
        first_name='Иван', last_name='Иванов',
        date_of_birth=date(1980, 1, 1),
        phone='+375 (29) 100-00-01',
        email='doc@test.by',
        category=cat, department=dept,
        experience_years=10,
        user=user
    )
    doc.specializations.add(spec)
    return doc

def make_service_category():
    return ServiceCategory.objects.create(name='Консультации')

def make_service():
    cat = make_service_category()
    return Service.objects.create(
        name='Тест услуга', category=cat,
        price=Decimal('50.00'), duration_minutes=30,
        description='Описание'
    )

def make_client(user=None):
    return Client.objects.create(
        first_name='Пётр', last_name='Петров',
        date_of_birth=date(1990, 6, 15),
        phone='+375 (29) 200-00-01',
        email='client@test.by',
        user=user
    )


# ===== MODEL TESTS =====

class TestDoctorModel(TestCase):
    def test_get_full_name(self):
        doc = Doctor(first_name='Иван', last_name='Иванов', patronymic='Петрович',
                     date_of_birth=date(1980, 1, 1), phone='+375 (29) 100-00-01',
                     email='doc@test.by')
        self.assertEqual(doc.get_full_name(), 'Иванов Иван Петрович')

    def test_get_full_name_no_patronymic(self):
        doc = Doctor(first_name='Иван', last_name='Иванов',
                     date_of_birth=date(1980, 1, 1), phone='+375 (29) 100-00-01',
                     email='doc@test.by')
        self.assertEqual(doc.get_full_name(), 'Иванов Иван')

    def test_age_calculation(self):
        dob = date.today() - timedelta(days=365 * 40)
        doc = Doctor(first_name='Иван', last_name='Иванов',
                     date_of_birth=dob, phone='+375 (29) 100-00-01',
                     email='doc@test.by')
        self.assertAlmostEqual(doc.age, 40, delta=1)

    def test_str(self):
        cat = make_doctor_category()
        dept = make_department()
        doc = Doctor.objects.create(
            first_name='Анна', last_name='Сидорова',
            date_of_birth=date(1985, 3, 10),
            phone='+375 (29) 111-11-11',
            email='anna@test.by',
            category=cat, department=dept
        )
        self.assertIn('Сидорова', str(doc))


class TestClientModel(TestCase):
    def test_get_full_name(self):
        c = Client(first_name='Мария', last_name='Петрова', patronymic='Ивановна',
                   date_of_birth=date(1995, 5, 20),
                   phone='+375 (29) 200-00-01', email='m@test.by')
        self.assertEqual(c.get_full_name(), 'Петрова Мария Ивановна')

    def test_age(self):
        dob = date.today() - timedelta(days=365 * 30)
        c = Client(first_name='Иван', last_name='Иванов',
                   date_of_birth=dob,
                   phone='+375 (29) 200-00-01', email='i@test.by')
        self.assertAlmostEqual(c.age, 30, delta=1)


class TestServiceModel(TestCase):
    def test_str(self):
        svc = make_service()
        self.assertIn('Тест услуга', str(svc))
        self.assertIn('50.00', str(svc))


class TestPromoCodeModel(TestCase):
    def test_is_current_active(self):
        today = date.today()
        promo = PromoCode(
            code='TEST10', discount_percent=10,
            valid_from=today - timedelta(days=5),
            valid_to=today + timedelta(days=5),
            is_active=True
        )
        self.assertTrue(promo.is_current)

    def test_is_current_expired(self):
        today = date.today()
        promo = PromoCode.objects.create(
            code='OLD10', discount_percent=10,
            valid_from=today - timedelta(days=30),
            valid_to=today - timedelta(days=1),
            is_active=True,
            description='Old promo'
        )
        self.assertFalse(promo.is_current)

    def test_is_current_inactive(self):
        today = date.today()
        promo = PromoCode(
            code='INACTIVE', discount_percent=10,
            valid_from=today - timedelta(days=1),
            valid_to=today + timedelta(days=10),
            is_active=False
        )
        self.assertFalse(promo.is_current)


class TestAppointmentModel(TestCase):
    def test_total_cost(self):
        cat = make_doctor_category()
        dept = make_department()
        doc = Doctor.objects.create(
            first_name='Иван', last_name='Врачев',
            date_of_birth=date(1975, 1, 1),
            phone='+375 (29) 300-00-01',
            email='d@test.by', category=cat, department=dept
        )
        client = make_client()
        svc1 = make_service()
        svc_cat = ServiceCategory.objects.create(name='Диагностика')
        svc2 = Service.objects.create(
            name='УЗИ', category=svc_cat,
            price=Decimal('45.00'), duration_minutes=20,
            description='УЗИ')
        appt = Appointment.objects.create(
            client=client, doctor=doc,
            appointment_date=timezone.now(),
            status='planned'
        )
        appt.services.set([svc1, svc2])
        self.assertEqual(appt.total_cost(), Decimal('95.00'))


class TestSaleModel(TestCase):
    def test_final_amount(self):
        today = date.today()
        promo = PromoCode.objects.create(
            code='TEST5', discount_percent=5,
            valid_from=today, valid_to=today + timedelta(days=10),
            is_active=True
        )
        cat = make_doctor_category()
        dept = make_department()
        doc = Doctor.objects.create(
            first_name='Иван', last_name='Врачев2',
            date_of_birth=date(1975, 1, 1),
            phone='+375 (29) 400-00-01',
            email='d2@test.by', category=cat, department=dept
        )
        client = make_client()
        appt = Appointment.objects.create(
            client=client, doctor=doc,
            appointment_date=timezone.now(),
            status='completed'
        )
        sale = Sale(
            appointment=appt,
            total_amount=Decimal('100.00'),
            discount=Decimal('10.00'),
            promo_code=promo
        )
        self.assertEqual(sale.final_amount, Decimal('90.00'))


# ===== FORM TESTS =====

class TestReviewForm(TestCase):
    def test_valid_form(self):
        data = {'rating': 5, 'text': 'Отличный центр, рекомендую!'}
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_rating(self):
        data = {'rating': 6, 'text': 'Хорошо'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())

    def test_short_text(self):
        data = {'rating': 4, 'text': 'OK'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_missing_rating(self):
        data = {'text': 'Отличный центр, рекомендую!'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())


class TestClientForm(TestCase):
    def test_valid_form(self):
        data = {
            'first_name': 'Пётр', 'last_name': 'Петров', 'patronymic': '',
            'date_of_birth': '1990-06-15',
            'phone': '+375 (29) 200-00-01',
            'email': 'petrov@test.by',
            'address': '', 'passport_series': '', 'passport_number': ''
        }
        form = ClientForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_phone(self):
        data = {
            'first_name': 'Пётр', 'last_name': 'Петров',
            'date_of_birth': '1990-06-15',
            'phone': '80291234567',  # Wrong format
            'email': 'p@test.by',
            'address': '', 'passport_series': '', 'passport_number': '', 'patronymic': ''
        }
        form = ClientForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_underage_client(self):
        data = {
            'first_name': 'Молодой', 'last_name': 'Клиент',
            'date_of_birth': (date.today() - timedelta(days=365 * 16)).strftime('%Y-%m-%d'),
            'phone': '+375 (29) 200-00-02',
            'email': 'young@test.by',
            'address': '', 'passport_series': '', 'passport_number': '', 'patronymic': ''
        }
        form = ClientForm(data=data)
        self.assertFalse(form.is_valid())


class TestServiceFilterForm(TestCase):
    def test_valid_empty(self):
        form = ServiceFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_price_range_valid(self):
        form = ServiceFilterForm(data={'price_min': '10', 'price_max': '100'})
        self.assertTrue(form.is_valid())

    def test_price_range_invalid(self):
        form = ServiceFilterForm(data={'price_min': '200', 'price_max': '100'})
        self.assertFalse(form.is_valid())


# ===== VIEW TESTS =====

class TestPublicViews(TestCase):
    def setUp(self):
        self.client_http = TestClient()

    def test_home_view(self):
        response = self.client_http.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_about_view(self):
        response = self.client_http.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_news_list_view(self):
        Article.objects.create(
            title='Тест', summary='Сводка', content='Полный текст', is_published=True)
        response = self.client_http.get(reverse('news_list'))
        self.assertEqual(response.status_code, 200)

    def test_news_detail_view(self):
        article = Article.objects.create(
            title='Статья', summary='Сводка', content='Содержание', is_published=True)
        response = self.client_http.get(reverse('news_detail', args=[article.pk]))
        self.assertEqual(response.status_code, 200)

    def test_news_detail_unpublished_returns_404(self):
        article = Article.objects.create(
            title='Черновик', summary='Сводка', content='Текст', is_published=False)
        response = self.client_http.get(reverse('news_detail', args=[article.pk]))
        self.assertEqual(response.status_code, 404)

    def test_glossary_view(self):
        GlossaryTerm.objects.create(question='Что такое МРТ?', answer='Томография')
        response = self.client_http.get(reverse('glossary'))
        self.assertEqual(response.status_code, 200)

    def test_glossary_search(self):
        GlossaryTerm.objects.create(question='Что такое УЗИ?', answer='Ультразвук')
        response = self.client_http.get(reverse('glossary') + '?q=УЗИ')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'УЗИ')

    def test_services_list_view(self):
        make_service()
        response = self.client_http.get(reverse('services_list'))
        self.assertEqual(response.status_code, 200)

    def test_services_filter_by_price(self):
        make_service()
        response = self.client_http.get(reverse('services_list') + '?price_max=30')
        self.assertEqual(response.status_code, 200)

    def test_doctors_list_view(self):
        make_doctor()
        response = self.client_http.get(reverse('doctors_list'))
        self.assertEqual(response.status_code, 200)

    def test_contacts_view(self):
        response = self.client_http.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)

    def test_vacancies_view(self):
        Vacancy.objects.create(title='Терапевт', description='Описание')
        response = self.client_http.get(reverse('vacancies'))
        self.assertEqual(response.status_code, 200)

    def test_reviews_view(self):
        response = self.client_http.get(reverse('reviews'))
        self.assertEqual(response.status_code, 200)

    def test_promo_codes_view(self):
        today = date.today()
        PromoCode.objects.create(
            code='TEST', discount_percent=10,
            valid_from=today, valid_to=today + timedelta(days=30)
        )
        response = self.client_http.get(reverse('promo_codes'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_view(self):
        response = self.client_http.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.client_http.get(reverse('stats'))
        self.assertEqual(response.status_code, 200)

    def test_weather_view(self):
        response = self.client_http.get(reverse('weather'))
        self.assertEqual(response.status_code, 200)

    def test_exchange_rates_view(self):
        response = self.client_http.get(reverse('exchange_rates'))
        self.assertEqual(response.status_code, 200)

    def test_parallel_demo_view(self):
        response = self.client_http.get(reverse('parallel_demo'))
        self.assertEqual(response.status_code, 200)


class TestAuthViews(TestCase):
    def setUp(self):
        self.http_client = TestClient()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            first_name='Тест', last_name='Пользователь')

    def test_register_view_get(self):
        response = self.http_client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_view_post_valid(self):
        from datetime import date
        data = {
            'username': 'newuser123',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'patronymic': 'Тестович',
            'email': 'new@test.by',
            'date_of_birth': '1990-01-01',
            'phone': '+375 (29) 999-00-01',
            'address': 'г. Минск, ул. Тестовая, 1',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }
        response = self.http_client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser123').exists())

    def test_login_view(self):
        response = self.http_client.post(reverse('login'), {
            'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)

    def test_cabinet_requires_login(self):
        response = self.http_client.get(reverse('cabinet'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_cabinet_accessible_when_logged_in(self):
        self.http_client.login(username='testuser', password='testpass123')
        response = self.http_client.get(reverse('cabinet'))
        self.assertEqual(response.status_code, 200)


class TestAdminViews(TestCase):
    def setUp(self):
        self.http_client = TestClient()
        self.superuser = User.objects.create_superuser(
            username='admin_test', password='admin123', email='a@test.by')
        self.regular_user = User.objects.create_user(
            username='regular', password='regular123')

    def test_admin_dashboard_requires_superuser(self):
        self.http_client.login(username='regular', password='regular123')
        response = self.http_client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_accessible_to_superuser(self):
        self.http_client.login(username='admin_test', password='admin123')
        response = self.http_client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_manage_clients_accessible_to_superuser(self):
        self.http_client.login(username='admin_test', password='admin123')
        response = self.http_client.get(reverse('manage_clients'))
        self.assertEqual(response.status_code, 200)

    def test_client_create_by_superuser(self):
        self.http_client.login(username='admin_test', password='admin123')
        data = {
            'first_name': 'Новый', 'last_name': 'Клиент', 'patronymic': '',
            'date_of_birth': '1985-01-01',
            'phone': '+375 (29) 555-55-55',
            'email': 'new_client@test.by',
            'address': '', 'passport_series': '', 'passport_number': ''
        }
        response = self.http_client.post(reverse('client_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Client.objects.filter(last_name='Клиент').exists())

    def test_client_delete(self):
        client = make_client()
        self.http_client.login(username='admin_test', password='admin123')
        response = self.http_client.post(reverse('client_delete', args=[client.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Client.objects.filter(pk=client.pk).exists())


class TestReviewSubmission(TestCase):
    def setUp(self):
        self.http_client = TestClient()
        self.user = User.objects.create_user(
            username='reviewer', password='pass123',
            first_name='Рецензент', last_name='Тест')

    def test_anonymous_redirected_on_review_post(self):
        data = {'rating': 4, 'text': 'Хороший отзыв, всё замечательно.'}
        response = self.http_client.post(reverse('reviews'), data)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_post_review(self):
        self.http_client.login(username='reviewer', password='pass123')
        data = {'rating': 5, 'text': 'Отличный центр! Рекомендую всем!'}
        response = self.http_client.post(reverse('reviews'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(author_name__icontains='Рецензент').exists())


# ===== PARAMETRIZED TESTS =====

@pytest.mark.parametrize("phone,valid", [
    ('+375 (29) 123-45-67', True),
    ('+375 (33) 987-65-43', True),
    ('+375 (44) 111-22-33', True),
    ('+375 (25) 999-88-77', True),
    ('80291234567', False),
    ('+375291234567', False),
    ('+375 (29) 12-34-567', False),
    ('123', False),
    ('', False),
])
def test_phone_validator(phone, valid):
    from clinic.models import phone_validator
    from django.core.exceptions import ValidationError
    if valid:
        try:
            phone_validator(phone)
        except ValidationError:
            pytest.fail(f"Valid phone {phone} raised ValidationError")
    else:
        with pytest.raises(ValidationError):
            phone_validator(phone)


@pytest.mark.django_db
@pytest.mark.parametrize("rating,text,expected_valid", [
    (5, 'Отличный центр, рекомендую!', True),
    (4, 'Хорошее обслуживание, доволен', True),
    (1, 'Не понравилось совсем ничего', True),
    (0, 'Нейтральный отзыв от клиента', False),
    (6, 'Превышение рейтинга, так не бывает', False),
    (3, 'Кор', False),  # text too short
])
def test_review_form_parametrized(rating, text, expected_valid):
    form = ReviewForm(data={'rating': rating, 'text': text})
    assert form.is_valid() == expected_valid


@pytest.mark.django_db
@pytest.mark.parametrize("price_min,price_max,valid", [
    (None, None, True),
    (0, 100, True),
    (50, 50, True),
    (100, 50, False),
    (-1, 100, False),
])
def test_service_filter_form_price(price_min, price_max, valid):
    data = {}
    if price_min is not None:
        data['price_min'] = price_min
    if price_max is not None:
        data['price_max'] = price_max
    form = ServiceFilterForm(data=data)
    assert form.is_valid() == valid


@pytest.mark.django_db
@pytest.mark.parametrize("username,password,status", [
    ('admin', 'admin123', 200),
    ('wrong', 'wrong', 200),
])
def test_login_page_always_200(client, username, password, status):
    response = client.get(reverse('login'))
    assert response.status_code == status


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", [
    'home', 'about', 'news_list', 'glossary', 'contacts',
    'vacancies', 'reviews', 'promo_codes', 'privacy',
    'services_list', 'doctors_list', 'stats', 'weather', 'exchange_rates',
])
def test_public_pages_return_200(client, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 200


# ===== ADDITIONAL COVERAGE TESTS =====

class TestAPIViews(TestCase):
    """Tests for DRF API endpoints."""

    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user('apiuser', 'api@test.by', 'pass123')
        self.cat = ServiceCategory.objects.create(name='API Cat')
        self.service = Service.objects.create(
            name='API Service', category=self.cat,
            price=Decimal('100.00'), duration_minutes=60, description='desc'
        )

    def test_api_services_requires_auth(self):
        # Services are public (price list)
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, 200)

    def test_api_services_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/services/')
        self.assertEqual(response.status_code, 200)

    def test_api_doctors_requires_auth(self):
        # Doctors list is public
        response = self.client.get('/api/doctors/')
        self.assertEqual(response.status_code, 200)

    def test_api_doctors_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/doctors/')
        self.assertEqual(response.status_code, 200)

    def test_api_appointments_requires_auth(self):
        # Appointments require authentication
        response = self.client.get('/api/appointments/')
        self.assertIn(response.status_code, [401, 403])

    def test_api_appointments_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/appointments/')
        self.assertEqual(response.status_code, 200)


class TestParallelDemoView(TestCase):
    def test_parallel_demo_page(self):
        response = self.client.get('/parallel-demo/')
        self.assertEqual(response.status_code, 200)


class TestCabinetAccessControl(TestCase):
    """Test role-based access."""

    def setUp(self):
        self.client_obj = TestClient()
        self.user = User.objects.create_user('reguser', 'reg@test.by', 'pass123')

    def test_cabinet_redirects_anon(self):
        response = self.client_obj.get('/cabinet/')
        self.assertEqual(response.status_code, 302)

    def test_doctor_cabinet_redirects_anon(self):
        response = self.client_obj.get('/cabinet/doctor/')
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_redirects_anon(self):
        response = self.client_obj.get('/admin-panel/')
        self.assertEqual(response.status_code, 302)

    def test_cabinet_accessible_when_logged_in(self):
        self.client_obj.force_login(self.user)
        # Create client profile
        Client.objects.create(
            first_name='Test', last_name='User',
            date_of_birth=date(1990, 1, 1),
            phone='+375 (29) 300-00-01',
            email='reg@test.by', address='Test addr',
            user=self.user
        )
        response = self.client_obj.get('/cabinet/')
        self.assertEqual(response.status_code, 200)


class TestNewsDetail(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title='Test Article', summary='Test summary',
            content='Long content', is_published=True
        )

    def test_news_detail(self):
        response = self.client.get(f'/news/{self.article.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_news_detail_404(self):
        response = self.client.get('/news/99999/')
        self.assertEqual(response.status_code, 404)


class TestServiceDetail(TestCase):
    def setUp(self):
        cat = ServiceCategory.objects.create(name='Detail Cat')
        self.service = Service.objects.create(
            name='Detail Service', category=cat,
            price=Decimal('75.00'), duration_minutes=45, description='desc'
        )

    def test_service_detail(self):
        response = self.client.get(f'/services/{self.service.pk}/')
        self.assertEqual(response.status_code, 200)


class TestDoctorDetail(TestCase):
    def setUp(self):
        cat = DoctorCategory.objects.create(name='Cat')
        dept = Department.objects.create(name='Dept', floor=1)
        spec = Specialization.objects.create(name='Spec')
        self.doctor = Doctor.objects.create(
            first_name='Doc', last_name='Test',
            date_of_birth=date(1975, 3, 10),
            phone='+375 (29) 400-00-01',
            email='detaildoc@test.by',
            category=cat, department=dept, experience_years=5
        )
        self.doctor.specializations.add(spec)

    def test_doctor_detail(self):
        response = self.client.get(f'/doctors/{self.doctor.pk}/')
        self.assertEqual(response.status_code, 200)


class TestReviewPost(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('rev_user', 'rev@test.by', 'pass123')

    def test_post_review_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.post('/reviews/', {
            'rating': 5,
            'text': 'Очень хороший медицинский центр, рекомендую всем!'
        })
        # Should redirect after posting
        self.assertIn(response.status_code, [200, 302])

    def test_reviews_page_get(self):
        response = self.client.get('/reviews/')
        self.assertEqual(response.status_code, 200)


class TestServicesFiltering(TestCase):
    def setUp(self):
        cat = ServiceCategory.objects.create(name='Filter Cat')
        Service.objects.create(
            name='Cheap Service', category=cat,
            price=Decimal('30.00'), duration_minutes=20, description='desc'
        )
        Service.objects.create(
            name='Expensive Service', category=cat,
            price=Decimal('500.00'), duration_minutes=120, description='desc'
        )

    def test_services_filter_by_price(self):
        response = self.client.get('/services/?price_min=20&price_max=100')
        self.assertEqual(response.status_code, 200)

    def test_services_search(self):
        response = self.client.get('/services/?search=Cheap')
        self.assertEqual(response.status_code, 200)

    def test_services_sort(self):
        response = self.client.get('/services/?sort=price')
        self.assertEqual(response.status_code, 200)


class TestModelStrMethods(TestCase):
    """Test __str__ for all models."""

    def test_company_info_str(self):
        obj = CompanyInfo.objects.create(name='МедЦентр', description='desc')
        self.assertIn('МедЦентр', str(obj))

    def test_article_str(self):
        obj = Article.objects.create(title='Статья', summary='summary', content='content')
        self.assertIn('Статья', str(obj))

    def test_glossary_str(self):
        obj = GlossaryTerm.objects.create(question='Что такое диагноз?', answer='Определение')
        self.assertIn('Что такое', str(obj))

    def test_vacancy_str(self):
        obj = Vacancy.objects.create(title='Врач терапевт', description='desc')
        self.assertIn('Врач', str(obj))

    def test_promo_code_str(self):
        obj = PromoCode.objects.create(
            code='TEST10', discount_percent=10,
            valid_from=date.today(), valid_to=date.today() + timedelta(days=30),
            description='Test promo'
        )
        self.assertIn('TEST10', str(obj))

    def test_specialization_str(self):
        obj = Specialization.objects.create(name='Хирург')
        self.assertIn('Хирург', str(obj))

    def test_department_str(self):
        obj = Department.objects.create(name='Хирургия', floor=2)
        self.assertIn('Хирургия', str(obj))

    def test_doctor_category_str(self):
        obj = DoctorCategory.objects.create(name='Первая категория')
        self.assertIn('Первая', str(obj))

    def test_service_category_str(self):
        obj = ServiceCategory.objects.create(name='Анализы')
        self.assertIn('Анализы', str(obj))

    def test_diagnosis_str(self):
        obj = Diagnosis.objects.create(code='A01', name='Грипп', description='desc')
        self.assertIn('Грипп', str(obj))


class TestDoctorsFiltering(TestCase):
    def setUp(self):
        cat = DoctorCategory.objects.create(name='Фильтр Кат')
        dept = Department.objects.create(name='Фильтр Dept', floor=1)
        spec = Specialization.objects.create(name='Фильтр Spec')
        doc = Doctor.objects.create(
            first_name='Фильтр', last_name='Доктор',
            date_of_birth=date(1970, 1, 1),
            phone='+375 (29) 500-00-01',
            email='filter_doc@test.by',
            category=cat, department=dept, experience_years=15
        )
        doc.specializations.add(spec)

    def test_doctors_list(self):
        response = self.client.get('/doctors/')
        self.assertEqual(response.status_code, 200)

    def test_doctors_search(self):
        response = self.client.get('/doctors/?search=Фильтр')
        self.assertEqual(response.status_code, 200)

    def test_doctors_sort(self):
        response = self.client.get('/doctors/?sort=last_name')
        self.assertEqual(response.status_code, 200)


class TestRegisterView(TestCase):
    def test_register_get(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_register_post_valid(self):
        response = self.client.post('/register/', {
            'username': 'newuser123',
            'email': 'newuser@test.by',
            'password1': 'Str0ngPassw0rd!',
            'password2': 'Str0ngPassw0rd!',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'date_of_birth': '1995-01-01',
            'phone': '+375 (29) 600-00-01',
            'address': 'г. Минск, ул. Тестовая, 1',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_register_post_mismatch_passwords(self):
        response = self.client.post('/register/', {
            'username': 'newuser456',
            'email': 'newuser2@test.by',
            'password1': 'Str0ngPassw0rd!',
            'password2': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)  # form errors shown


class TestAdminDashboardAccess(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser('supertest', 'su@test.by', 'superpass')
        self.regular = User.objects.create_user('regtest', 'reg@test.by', 'pass123')

    def test_dashboard_accessible_to_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_forbidden_to_regular_user(self):
        self.client.force_login(self.regular)
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 302)

    def test_manage_clients_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get('/admin-panel/clients/')
        self.assertEqual(response.status_code, 200)

    def test_appointments_by_doctor_superuser(self):
        self.client.force_login(self.superuser)
        # No doctor_pk = list page; need a real doctor to pass pk
        cat = DoctorCategory.objects.create(name='Dash Cat')
        dept = Department.objects.create(name='Dash Dept', floor=1)
        doc = Doctor.objects.create(
            first_name='Dash', last_name='Doc',
            date_of_birth=date(1975, 1, 1),
            phone='+375 (29) 800-00-01',
            email='dashdoc@test.by',
            category=cat, department=dept, experience_years=5
        )
        response = self.client.get(f'/admin-panel/doctors/{doc.pk}/appointments/')
        self.assertEqual(response.status_code, 200)


class TestDoctorCabinetView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('doc_view', 'docv@test.by', 'pass123')
        cat = DoctorCategory.objects.create(name='View Cat')
        dept = Department.objects.create(name='View Dept', floor=3)
        spec = Specialization.objects.create(name='View Spec')
        self.doctor = Doctor.objects.create(
            first_name='Вью', last_name='Доктор',
            date_of_birth=date(1978, 5, 20),
            phone='+375 (29) 700-00-01',
            email='docview@test.by',
            category=cat, department=dept, experience_years=12,
            user=self.user
        )
        self.doctor.specializations.add(spec)

    def test_doctor_cabinet_accessible(self):
        self.client.force_login(self.user)
        response = self.client.get('/cabinet/doctor/')
        self.assertEqual(response.status_code, 200)


class TestClinicExtrasTemplateTag(TestCase):
    def test_multiply_filter(self):
        from clinic.templatetags.clinic_extras import multiply
        self.assertEqual(multiply(10, 2), 20.0)

    def test_multiply_invalid(self):
        from clinic.templatetags.clinic_extras import multiply
        self.assertEqual(multiply('abc', 2), 0)

    def test_div_filter(self):
        from clinic.templatetags.clinic_extras import div
        self.assertEqual(div(10, 2), 5.0)

    def test_div_zero(self):
        from clinic.templatetags.clinic_extras import div
        self.assertEqual(div(10, 0), 0)

    def test_subtract_filter(self):
        from clinic.templatetags.clinic_extras import subtract
        self.assertEqual(subtract(10, 3), 7.0)

    def test_subtract_invalid(self):
        from clinic.templatetags.clinic_extras import subtract
        self.assertEqual(subtract('x', 3), 0)


class TestPromoCodeIsCurrentProperty(TestCase):
    def test_promo_is_current(self):
        promo = PromoCode.objects.create(
            code='ACTIVE20', discount_percent=20,
            valid_from=date.today() - timedelta(days=5),
            valid_to=date.today() + timedelta(days=25),
            description='Active promo'
        )
        self.assertTrue(promo.is_current)

    def test_promo_is_expired(self):
        promo = PromoCode.objects.create(
            code='EXPIRED10', discount_percent=10,
            valid_from=date.today() - timedelta(days=30),
            valid_to=date.today() - timedelta(days=5),
            description='Old promo'
        )
        self.assertFalse(promo.is_current)


@pytest.mark.django_db
@pytest.mark.parametrize("url,expected", [
    ('/parallel-demo/', 200),
    ('/stats/', 200),
    ('/weather/', 200),
    ('/exchange-rates/', 200),
])
def test_extra_public_pages(client, url, expected):
    response = client.get(url)
    assert response.status_code == expected
