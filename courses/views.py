from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponseForbidden
from django import forms
from .models import Course, Lesson, Enrollment
from .forms import CourseForm, LessonForm

# -----------------------------
# STUDENT / GENERAL VIEWS
# -----------------------------

def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    enrolled = False
    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'enrolled': enrolled,
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('course_detail', course_id=course.id)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login new user
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

@login_required
def dashboard(request):
    enrollments = request.user.enrollments.select_related('course')
    return render(request, 'auth/dashboard.html', {'enrollments': enrollments})

# -----------------------------
# INSTRUCTOR VIEWS
# -----------------------------

@login_required
def create_course(request):
    # Only instructors allowed
    if not request.user.profile.is_instructor:
        return HttpResponseForbidden("You are not an instructor.")

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user  # assign current user
            course.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()

    return render(request, 'courses/create_course.html', {'form': form})

@login_required
def create_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Only the course creator can add lessons
    if course.created_by != request.user:
        return HttpResponseForbidden("You cannot add lessons to this course.")

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = LessonForm()

    return render(request, 'courses/create_lesson.html', {'form': form, 'course': course})
