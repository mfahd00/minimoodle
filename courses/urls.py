from django.contrib import admin
from django.urls import path, include
from courses import views as course_views

urlpatterns = [
    path('', course_views.home, name='home'),
    path('courses/', course_views.course_list, name='course_list'),
    path('courses/<int:course_id>/', course_views.course_detail, name='course_detail'),
    path('courses/create/', course_views.create_course, name='create_course'),
    path('courses/<int:course_id>/edit/', course_views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', course_views.delete_course, name='delete_course'),
    path('courses/<int:course_id>/add_lesson/', course_views.create_lesson, name='create_lesson'),
    path('courses/<int:course_id>/enroll/', course_views.enroll_course, name='enroll_course'),
    path('register/', course_views.register, name='register'),
    path('login/', course_views.login_view, name='login'),
    path('logout/', course_views.logout_view, name='logout'),
    path('dashboard/', course_views.dashboard, name='dashboard'),
]
