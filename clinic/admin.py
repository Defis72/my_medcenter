from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CompanyInfo, CompanyHistory, Article, GlossaryTerm, Contact,
    Vacancy, Review, PromoCode, Specialization, Department,
    DoctorCategory, Doctor, ServiceCategory, Service, Client,
    Diagnosis, ClientDiagnosis, Schedule, Appointment, Sale
)


class CompanyHistoryInline(admin.TabularInline):
    model = CompanyHistory
    extra = 1


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyHistoryInline]
    list_display = ['name', 'phone', 'email', 'updated_at']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_published', 'published_at']
    list_filter = ['is_published']
    search_fields = ['title', 'content']
    list_editable = ['is_published']


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ['question', 'added_at']
    search_fields = ['question', 'answer']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'phone', 'email', 'order']
    list_editable = ['order']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'salary_from', 'salary_to', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['is_active']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved']
    list_editable = ['is_approved']
    search_fields = ['author_name', 'text']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
    list_filter = ['is_active']
    list_editable = ['is_active']


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'floor']


@admin.register(DoctorCategory)
class DoctorCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    inlines = [ScheduleInline]
    list_display = ['get_full_name', 'category', 'department', 'phone', 'is_active']
    list_filter = ['category', 'department', 'is_active', 'specializations']
    search_fields = ['first_name', 'last_name', 'email']
    list_editable = ['is_active']
    filter_horizontal = ['specializations']

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name']
    list_editable = ['price', 'is_active']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'phone', 'email', 'date_of_birth', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_filter = ['created_at']

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'ФИО'


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']


class ClientDiagnosisInline(admin.TabularInline):
    model = ClientDiagnosis
    extra = 0


@admin.register(ClientDiagnosis)
class ClientDiagnosisAdmin(admin.ModelAdmin):
    list_display = ['client', 'diagnosis', 'doctor', 'date_set']
    list_filter = ['doctor', 'diagnosis']
    search_fields = ['client__last_name', 'diagnosis__name']


class SaleInline(admin.StackedInline):
    model = Sale
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    inlines = [SaleInline]
    list_display = ['client', 'doctor', 'appointment_date', 'status', 'get_cost']
    list_filter = ['status', 'doctor', 'appointment_date']
    search_fields = ['client__last_name', 'doctor__last_name']
    list_editable = ['status']
    filter_horizontal = ['services']
    date_hierarchy = 'appointment_date'

    def get_cost(self, obj):
        return f'{obj.total_cost()} руб.'
    get_cost.short_description = 'Стоимость'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'total_amount', 'discount', 'final_amount', 'payment_method', 'paid_at']
    list_filter = ['payment_method', 'paid_at']
    date_hierarchy = 'paid_at'
