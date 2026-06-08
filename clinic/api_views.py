from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Service, Doctor, Appointment, Client, ServiceCategory


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'category', 'category_name', 'price', 'duration_minutes', 'description']


class DoctorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    specializations = serializers.StringRelatedField(many=True)

    class Meta:
        model = Doctor
        fields = ['id', 'full_name', 'category', 'department', 'specializations',
                  'experience_years', 'phone', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name()


class AppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    services_list = ServiceSerializer(source='services', many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'client', 'client_name', 'doctor', 'doctor_name',
                  'appointment_date', 'status', 'services_list', 'total_cost', 'notes']

    def get_total_cost(self, obj):
        return obj.total_cost()


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True).select_related('category')
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        cat = self.request.query_params.get('category')
        if cat:
            qs = qs.filter(category__id=cat)
        return qs


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Doctor.objects.filter(is_active=True).select_related('category', 'department')
    serializer_class = DoctorSerializer
    permission_classes = [permissions.AllowAny]


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Appointment.objects.all().select_related('client', 'doctor')
        if hasattr(user, 'doctor'):
            return Appointment.objects.filter(doctor=user.doctor).select_related('client', 'doctor')
        try:
            client = Client.objects.get(user=user)
            return Appointment.objects.filter(client=client).select_related('client', 'doctor')
        except Client.DoesNotExist:
            return Appointment.objects.none()
