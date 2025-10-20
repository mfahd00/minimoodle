from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from courses import views as course_views
from django.contrib.auth import views as auth_views

def home(request):
    from courses.models import Course
    latest_courses = Course.objects.all()[:6]
    return render(request, 'index.html', {'latest_courses': latest_courses})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('courses/', include('courses.urls')),

    # Registration URLs
    path('register/', course_views.choose_registration, name='register'),
    path('register/student/', course_views.register_student, name='register_student'),
    path('register/instructor/', course_views.register_instructor, name='register_instructor'),

    # Login/Logout
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', course_views.dashboard, name='dashboard'),
]
