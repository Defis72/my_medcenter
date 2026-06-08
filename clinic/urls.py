from django.urls import path, re_path
from . import views

urlpatterns = [
    # Home and site pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news_list'),
    re_path(r'^news/(?P<pk>\d+)/$', views.news_detail, name='news_detail'),
    path('glossary/', views.glossary, name='glossary'),
    path('contacts/', views.contacts, name='contacts'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    re_path(r'^reviews/(?P<pk>\d+)/delete/$', views.delete_review, name='delete_review'),
    path('privacy/', views.privacy, name='privacy'),
    path('promo-codes/', views.promo_codes, name='promo_codes'),

    # Auth
    path('register/', views.register, name='register'),

    # Services
    path('services/', views.services_list, name='services_list'),
    re_path(r'^services/(?P<pk>\d+)/$', views.service_detail, name='service_detail'),

    # Doctors
    path('doctors/', views.doctors_list, name='doctors_list'),
    re_path(r'^doctors/(?P<pk>\d+)/$', views.doctor_detail, name='doctor_detail'),

    # Client cabinet
    path('cabinet/', views.cabinet, name='cabinet'),
    path('cabinet/doctor/', views.doctor_cabinet, name='doctor_cabinet'),
    path('cabinet/appointment/new/', views.create_appointment, name='create_appointment'),
    re_path(r'^cabinet/appointment/(?P<pk>\d+)/cancel/$', views.cancel_appointment, name='cancel_appointment'),
    path('cabinet/profile/edit/', views.edit_profile, name='edit_profile'),

    # Admin views
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/clients/', views.manage_clients, name='manage_clients'),
    re_path(r'^admin-panel/clients/(?P<pk>\d+)/$', views.client_detail_admin, name='client_detail_admin'),
    re_path(r'^admin-panel/clients/(?P<pk>\d+)/edit/$', views.client_update, name='client_update'),
    re_path(r'^admin-panel/clients/(?P<pk>\d+)/delete/$', views.client_delete, name='client_delete'),
    path('admin-panel/clients/create/', views.client_create, name='client_create'),
    re_path(r'^admin-panel/doctors/(?P<doctor_pk>\d+)/appointments/$',
            views.appointments_by_doctor, name='appointments_by_doctor'),

    # Stats
    path('stats/', views.stats_page, name='stats'),

    # External APIs
    path('weather/', views.weather_widget, name='weather'),
    path('exchange-rates/', views.exchange_rates, name='exchange_rates'),

    # Bonus: Parallel demo
    path('parallel-demo/', views.parallel_demo, name='parallel_demo'),
]
