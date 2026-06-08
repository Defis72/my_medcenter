import calendar
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import logging
import requests
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum, Q, Max, Min
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction
from statistics import mean, median

from .models import (
    CompanyInfo, Article, GlossaryTerm, Contact, Vacancy,
    Review, PromoCode, Doctor, Service, ServiceCategory,
    Client, Appointment, Sale, Schedule, Diagnosis,
    ClientDiagnosis, Department, Specialization
)
from .forms import (
    RegisterForm, ReviewForm, AppointmentForm, ClientForm,
    ServiceFilterForm, DoctorFilterForm, AppointmentFilterForm
)
from medcenter.settings import OPENWEATHER_API_KEY, EXCHANGE_API_KEY

logger = logging.getLogger('clinic')


def is_doctor(user):
    return hasattr(user, 'doctor')


def is_superuser(user):
    return user.is_superuser


# ==================== SITE INFO PAGES ====================

def home(request):
    logger.info('Home page accessed')
    latest_article = Article.objects.filter(is_published=True).first()
    context = {
        'latest_article': latest_article,
        'page_title': 'Главная',
    }
    return render(request, 'clinic/home.html', context)


def about(request):
    company = CompanyInfo.objects.prefetch_related('history').first()
    return render(request, 'clinic/about.html', {'company': company, 'page_title': 'О компании'})


def news_list(request):
    articles = Article.objects.filter(is_published=True)
    return render(request, 'clinic/news_list.html', {'articles': articles, 'page_title': 'Новости'})


def news_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, is_published=True)
    return render(request, 'clinic/news_detail.html', {'article': article})


def glossary(request):
    terms = GlossaryTerm.objects.all().order_by('question')
    query = request.GET.get('q', '')
    if query:
        terms = terms.filter(Q(question__icontains=query) | Q(answer__icontains=query))
    return render(request, 'clinic/glossary.html',
                  {'terms': terms, 'query': query, 'page_title': 'Словарь терминов'})


def contacts(request):
    contacts_list = Contact.objects.all()
    return render(request, 'clinic/contacts.html',
                  {'contacts': contacts_list, 'page_title': 'Контакты'})


def vacancies(request):
    vac_list = Vacancy.objects.filter(is_active=True)
    return render(request, 'clinic/vacancies.html',
                  {'vacancies': vac_list, 'page_title': 'Вакансии'})


def reviews(request):
    reviews_list = Review.objects.filter(is_approved=True)
    form = ReviewForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Для добавления отзыва необходимо авторизоваться.')
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.author_name = request.user.get_full_name() or request.user.username
            review.save()
            messages.success(request, 'Ваш отзыв добавлен!')
            logger.info(f'New review by {request.user.username}')
            return redirect('reviews')
    return render(request, 'clinic/reviews.html',
                  {'reviews': reviews_list, 'form': form, 'page_title': 'Отзывы'})


def privacy(request):
    return render(request, 'clinic/privacy.html', {'page_title': 'Политика конфиденциальности'})


def promo_codes(request):
    today = date.today()
    active_promos = PromoCode.objects.filter(
        is_active=True, valid_from__lte=today, valid_to__gte=today)
    archive_promos = PromoCode.objects.filter(
        Q(is_active=False) | Q(valid_to__lt=today))
    return render(request, 'clinic/promo_codes.html', {
        'active_promos': active_promos,
        'archive_promos': archive_promos,
        'page_title': 'Промокоды и купоны'
    })


# ==================== AUTH ====================

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create Client profile with DOB, phone, address from registration form
            Client.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                patronymic=form.cleaned_data.get('patronymic', ''),
                date_of_birth=form.cleaned_data['date_of_birth'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
            )
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            logger.info(f'New user registered: {user.username}')
            return redirect('cabinet')
    else:
        form = RegisterForm()
    return render(request, 'clinic/register.html', {'form': form, 'page_title': 'Регистрация'})


# ==================== SERVICES ====================

def services_list(request):
    form = ServiceFilterForm(request.GET)
    services = Service.objects.filter(is_active=True).select_related('category')
    categories = ServiceCategory.objects.all()

    if form.is_valid():
        cat = form.cleaned_data.get('category')
        pmin = form.cleaned_data.get('price_min')
        pmax = form.cleaned_data.get('price_max')
        search = form.cleaned_data.get('search')
        if cat:
            services = services.filter(category=cat)
        if pmin is not None:
            services = services.filter(price__gte=pmin)
        if pmax is not None:
            services = services.filter(price__lte=pmax)
        if search:
            services = services.filter(
                Q(name__icontains=search) | Q(description__icontains=search))

    sort = request.GET.get('sort', 'name')
    if sort in ['name', '-name', 'price', '-price']:
        services = services.order_by(sort)

    return render(request, 'clinic/services_list.html', {
        'services': services,
        'categories': categories,
        'form': form,
        'page_title': 'Услуги',
    })


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return render(request, 'clinic/service_detail.html',
                  {'service': service, 'page_title': service.name})


# ==================== DOCTORS ====================

def doctors_list(request):
    form = DoctorFilterForm(request.GET)
    doctors = Doctor.objects.filter(is_active=True).select_related(
        'category', 'department').prefetch_related('specializations')

    search = request.GET.get('search', '')
    spec = request.GET.get('specialization', '')
    dept = request.GET.get('department', '')

    if search:
        doctors = doctors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(specializations__name__icontains=search)
        ).distinct()
    if spec:
        doctors = doctors.filter(specializations__name__icontains=spec)
    if dept:
        doctors = doctors.filter(department__name__icontains=dept)

    sort = request.GET.get('sort', 'last_name')
    if sort in ['last_name', '-last_name', 'experience_years', '-experience_years']:
        doctors = doctors.order_by(sort)

    return render(request, 'clinic/doctors_list.html', {
        'doctors': doctors,
        'form': form,
        'page_title': 'Врачи',
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    schedule = Schedule.objects.filter(doctor=doctor).order_by('weekday')
    return render(request, 'clinic/doctor_detail.html',
                  {'doctor': doctor, 'schedule': schedule})


# ==================== CLIENT CABINET ====================

@login_required
def cabinet(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        client = None

    if is_doctor(request.user):
        return redirect('doctor_cabinet')

    appointments = []
    if client:
        appointments = Appointment.objects.filter(client=client).select_related(
            'doctor').prefetch_related('services').order_by('appointment_date')

    return render(request, 'clinic/cabinet.html', {
        'client': client,
        'appointments': appointments,
        'page_title': 'Личный кабинет',
    })


@login_required
def doctor_cabinet(request):
    if not is_doctor(request.user):
        return redirect('cabinet')
    doctor = request.user.doctor
    today = date.today()
    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related('client').prefetch_related('services').order_by('appointment_date')

    filter_form = AppointmentFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        d_from = filter_form.cleaned_data.get('date_from')
        d_to = filter_form.cleaned_data.get('date_to')
        if status:
            appointments = appointments.filter(status=status)
        if d_from:
            appointments = appointments.filter(appointment_date__date__gte=d_from)
        if d_to:
            appointments = appointments.filter(appointment_date__date__lte=d_to)

    return render(request, 'clinic/doctor_cabinet.html', {
        'doctor': doctor,
        'appointments': appointments,
        'filter_form': filter_form,
        'page_title': 'Кабинет врача',
    })


@login_required
def create_appointment(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.warning(request, 'Сначала заполните данные профиля.')
        return redirect('edit_profile')

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.client = client
            appt.save()
            form.save_m2m()
            messages.success(request, 'Приём успешно записан!')
            logger.info(f'Appointment created by {request.user.username}')
            return redirect('cabinet')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/appointment_form.html',
                  {'form': form, 'page_title': 'Запись на приём'})


@login_required
def edit_profile(request):
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        client = None

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            c.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('cabinet')
    else:
        form = ClientForm(instance=client)
    return render(request, 'clinic/edit_profile.html',
                  {'form': form, 'page_title': 'Редактировать профиль'})


# ==================== ADMIN / SUPERUSER VIEWS ====================
def generate_revenue_chart(monthly_data):
    """Generate bar chart of monthly revenue using matplotlib, return base64 PNG."""
    months = [d['month'] for d in monthly_data]
    revenues = [d['revenue'] for d in monthly_data]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(months, revenues, color='#0d6efd', edgecolor='#084298', linewidth=0.8)

    for bar, val in zip(bars, revenues):
        if val > 0:
            top = max(revenues) * 0.01 if max(revenues) > 0 else 1
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + top,
                    f'{val:.0f} BYN', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_title('Выручка за последние 6 месяцев', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Месяц', fontsize=10)
    ax.set_ylabel('Сумма (BYN)', fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}'))
    max_rev = max(revenues) if revenues else 0
    ax.set_ylim(0, max_rev * 1.25 if max_rev > 0 else 100)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')



@user_passes_test(is_superuser)
def admin_dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    total_clients = Client.objects.count()
    total_doctors = Doctor.objects.filter(is_active=True).count()
    total_appointments = Appointment.objects.count()
    monthly_revenue = Sale.objects.filter(
        paid_at__date__gte=month_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Statistics
    sales = list(Sale.objects.values_list('total_amount', flat=True).order_by('total_amount'))
    sales_float = [float(s) for s in sales]
    avg_sale = mean(sales_float) if sales_float else 0
    median_sale = median(sales_float) if sales_float else 0

    client_ages = [c.age for c in Client.objects.all()]
    avg_age = mean(client_ages) if client_ages else 0
    median_age = median(client_ages) if client_ages else 0

    # Popular services
    popular_services = Service.objects.annotate(
        appt_count=Count('appointment')
    ).order_by('-appt_count')[:5]

    # Revenue by category
    revenue_by_cat = ServiceCategory.objects.annotate(
        total=Sum('services__appointment__sale__total_amount')
    ).order_by('-total')

    # Monthly sales for chart
    monthly_data = []
    for i in range(6):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        rev = Sale.objects.filter(paid_at__month=m, paid_at__year=y).aggregate(
            t=Sum('total_amount'))['t'] or 0
        monthly_data.insert(0, {
            'month': f'{m:02d}/{y}',
            'revenue': float(rev)
        })

    clients_alpha = Client.objects.order_by('last_name', 'first_name')

    # Generate matplotlib chart (Python, not JS)
    chart_image = generate_revenue_chart(monthly_data)

    return render(request, 'clinic/admin_dashboard.html', {
        'total_clients': total_clients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'monthly_revenue': monthly_revenue,
        'avg_sale': round(avg_sale, 2),
        'median_sale': round(median_sale, 2),
        'avg_age': round(avg_age, 1),
        'median_age': round(median_age, 1),
        'popular_services': popular_services,
        'revenue_by_cat': revenue_by_cat,
        'monthly_data': monthly_data,
        'chart_image': chart_image,
        'clients_alpha': clients_alpha,
        'page_title': 'Панель администратора',
    })


@user_passes_test(is_superuser)
def manage_clients(request):
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'last_name')
    clients = Client.objects.select_related('user')
    if search:
        clients = clients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    valid_sorts = ['last_name', '-last_name', 'date_of_birth', '-date_of_birth', 'created_at', '-created_at']
    if sort in valid_sorts:
        clients = clients.order_by(sort)
    return render(request, 'clinic/manage_clients.html', {
        'clients': clients,
        'search': search,
        'page_title': 'Управление клиентами',
    })


@user_passes_test(is_superuser)
def client_detail_admin(request, pk):
    client = get_object_or_404(Client, pk=pk)
    appointments = Appointment.objects.filter(client=client).select_related(
        'doctor').prefetch_related('services', 'sale')
    diagnoses = ClientDiagnosis.objects.filter(client=client).select_related('diagnosis', 'doctor')
    total_spent = Sale.objects.filter(
        appointment__client=client).aggregate(t=Sum('total_amount'))['t'] or 0
    return render(request, 'clinic/client_detail_admin.html', {
        'client': client,
        'appointments': appointments,
        'diagnoses': diagnoses,
        'total_spent': total_spent,
        'page_title': f'Клиент: {client}',
    })


@user_passes_test(is_superuser)
def appointments_by_doctor(request, doctor_pk, date_str=None):
    doctor = get_object_or_404(Doctor, pk=doctor_pk)
    appts = Appointment.objects.filter(doctor=doctor).select_related('client').prefetch_related('services')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appts = appts.filter(appointment_date__date=target_date)
        except ValueError:
            pass
    return render(request, 'clinic/appointments_by_doctor.html', {
        'doctor': doctor,
        'appointments': appts,
        'page_title': f'Приёмы: {doctor}',
    })


# ==================== CRUD OPERATIONS ====================

@user_passes_test(is_superuser)
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент добавлен.')
            return redirect('manage_clients')
    else:
        form = ClientForm()
    return render(request, 'clinic/client_form.html',
                  {'form': form, 'page_title': 'Добавить клиента'})


@user_passes_test(is_superuser)
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные клиента обновлены.')
            return redirect('client_detail_admin', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clinic/client_form.html',
                  {'form': form, 'page_title': 'Редактировать клиента'})


@user_passes_test(is_superuser)
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Клиент удалён.')
        return redirect('manage_clients')
    return render(request, 'clinic/client_confirm_delete.html',
                  {'client': client, 'page_title': 'Удалить клиента'})


# ==================== STATS & DATETIME ====================

def stats_page(request):
    user_tz = request.GET.get('tz', 'UTC')
    now_utc = timezone.now()
    now_local = localtime(now_utc)

    # Calendar
    cal = calendar.TextCalendar(calendar.MONDAY)
    cal_text = cal.formatmonth(now_local.year, now_local.month)

    # Appointments stats
    appt_stats = Appointment.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        planned=Count('id', filter=Q(status='planned')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )

    # Top doctors by appointments
    top_doctors = Doctor.objects.annotate(
        appt_count=Count('appointments')
    ).order_by('-appt_count')[:5]

    from django.conf import settings
    server_tz = settings.TIME_ZONE

    return render(request, 'clinic/stats.html', {
        'now_utc': now_utc.strftime('%d/%m/%Y %H:%M:%S'),
        'now_local': now_local.strftime('%d/%m/%Y %H:%M:%S'),
        'server_tz': server_tz,
        'calendar': cal_text,
        'appt_stats': appt_stats,
        'top_doctors': top_doctors,
        'page_title': 'Статистика',
    })


# ==================== EXTERNAL API VIEWS ====================

def weather_widget(request):
    city = request.GET.get('city', 'Minsk')
    weather_data = None
    error = None
    if OPENWEATHER_API_KEY:
        try:
            url = f'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': city,
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ru'
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                weather_data = resp.json()
            else:
                error = f'Город не найден: {city}'
        except Exception as e:
            logger.error(f'Weather API error: {e}')
            error = 'Ошибка получения погоды'
    else:
        # Demo data if no API key
        weather_data = {
            'name': city,
            'main': {'temp': 18, 'humidity': 65, 'feels_like': 17},
            'weather': [{'description': 'облачно с прояснениями', 'icon': '04d'}],
            'wind': {'speed': 3.5}
        }
    return render(request, 'clinic/weather.html', {
        'weather': weather_data,
        'city': city,
        'error': error,
        'page_title': 'Погода',
    })


def exchange_rates(request):
    rates_data = None
    error = None
    try:
        if EXCHANGE_API_KEY:
            url = f'https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/BYN'
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                rates_data = {k: v for k, v in data.get('conversion_rates', {}).items()
                              if k in ['USD', 'EUR', 'RUB', 'BYN']}
        else:
            # Demo data
            rates_data = {'USD': 0.31, 'EUR': 0.29, 'RUB': 28.5, 'BYN': 1.0}
    except Exception as e:
        logger.error(f'Exchange API error: {e}')
        error = 'Ошибка получения курсов валют'
    return render(request, 'clinic/exchange_rates.html', {
        'rates': rates_data,
        'error': error,
        'page_title': 'Курсы валют',
    })


# ==================== PARALLEL DEMO (BONUS) ====================

def parallel_demo(request):
    import threading
    import asyncio
    import multiprocessing
    import time

    results = {}

    # Threading demo — parallel price calculation
    prices = [100, 250, 75, 180, 320, 95, 440, 210, 130, 290]
    totals = []
    lock = threading.Lock()

    def calc_discount(price):
        time.sleep(0.01)
        discounted = price * 0.9
        with lock:
            totals.append(discounted)

    start = time.perf_counter()
    threads = [threading.Thread(target=calc_discount, args=(p,)) for p in prices]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    threading_time = round(time.perf_counter() - start, 4)
    results['threading'] = {
        'time': threading_time,
        'totals': sorted(totals),
        'sum': round(sum(totals), 2)
    }

    # Asyncio demo — simulated async API calls
    async def fetch_patient_data(patient_id):
        await asyncio.sleep(0.01)
        return {'id': patient_id, 'status': 'OK', 'data': f'Patient {patient_id} data loaded'}

    async def run_async():
        tasks = [fetch_patient_data(i) for i in range(1, 11)]
        return await asyncio.gather(*tasks)

    start = time.perf_counter()
    loop = asyncio.new_event_loop()
    asyncio_results = loop.run_until_complete(run_async())
    loop.close()
    asyncio_time = round(time.perf_counter() - start, 4)
    results['asyncio'] = {
        'time': asyncio_time,
        'count': len(asyncio_results),
        'sample': asyncio_results[:3]
    }

    return render(request, 'clinic/parallel_demo.html', {
        'results': results,
        'page_title': 'Демонстрация параллельности',
    })
