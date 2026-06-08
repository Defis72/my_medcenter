from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clinic.api_views import ServiceViewSet, DoctorViewSet, AppointmentViewSet

router = DefaultRouter()
router.register('services', ServiceViewSet)
router.register('doctors', DoctorViewSet)
router.register('appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
