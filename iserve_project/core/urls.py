from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.student_services, name='student_services'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('staff-registrations/approve/<int:registration_id>/', views.approve_staff_registration, name='approve_staff_registration'),
    path('staff-registrations/reject/<int:registration_id>/', views.reject_staff_registration, name='reject_staff_registration'),
    path('appointments/new/', views.create_appointment, name='create_appointment'),
    path('appointments/<int:appointment_id>/update/', views.update_appointment, name='update_appointment'),
]