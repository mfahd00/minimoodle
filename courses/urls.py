from django.contrib import admin
from django.urls import path, include
from courses import views as course_views
from . import views


urlpatterns = [
    path('', course_views.home, name='home'),
    path('courses/', course_views.course_list, name='course_list'),
    path('courses/<int:course_id>/', course_views.course_detail, name='course_detail'),
    path('courses/create/', course_views.create_course, name='create_course'),
    path('courses/<int:course_id>/edit/', course_views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', course_views.delete_course, name='delete_course'),
    path('courses/<int:course_id>/add_lesson/', course_views.create_lesson, name='create_lesson'),
    path('courses/<int:course_id>/enroll/', course_views.enroll_course, name='enroll_course'),
    path('register/', views.choose_registration, name='register'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/instructor/', views.register_instructor, name='register_instructor'),
    path('login/', views.login_page, name='login'),
    path('login/student/', views.login_student, name='login_student'),
    path('login/instructor/', views.login_instructor, name='login_instructor'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('courses/category/<int:category_id>/', views.courses_by_category, name='courses_by_category'),
    path('courses/<int:course_id>/assignments/', views.assignment_list, name='assignment_list'),
    path('courses/<int:course_id>/assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignments/<int:assignment_id>/submissions/', views.view_submissions, name='view_submissions'),
    path('assignments/', views.student_assignments, name='student_assignments'),
    path('pending-classes/', views.pending_classes, name='pending_classes'),

]