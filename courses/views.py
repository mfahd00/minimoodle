from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count
from .models import Course, Lesson, Enrollment, Profile, Category, Assignment, Submission
from .forms import CourseForm, LessonForm, CustomUserCreationForm, AssignmentForm, SubmissionForm
from django.contrib.auth.models import User

def register_student(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.is_instructor = False
            user.profile.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register_student.html', {'form': form, 'page_title': 'Student Registration'})


def register_instructor(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.is_instructor = True
            user.profile.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register_instructor.html', {'form': form, 'page_title': 'Instructor Registration'})

def choose_registration(request):
    return render(request, 'auth/choose_registration.html', {
        'page_title': 'Register'
    })

def login_student(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.profile.is_instructor:
                login(request, user)
                return redirect('dashboard')
            else:
                error = "⚠️ You are not a student. Use the instructor tab."
        else:
            error = "Invalid username or password."
    return render(request, 'auth/login.html', {'student_error': error, 'show_tab': 'student'})


def login_instructor(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.profile.is_instructor:
                login(request, user)
                return redirect('dashboard')
            else:
                error = "⚠️ You are not an instructor. Use the student tab."
        else:
            error = "Invalid username or password."
    return render(request, 'auth/login.html', {'instructor_error': error, 'show_tab': 'instructor'})





@login_required
def logout_view(request):
    logout(request)
    return redirect('login_student')

def home(request):
    latest_courses = Course.objects.all()[:5]
    return render(request, 'index.html', {'latest_courses': latest_courses})


def course_list(request):
    sort_by = request.GET.get('sort', 'popular')
    courses = Course.objects.annotate(num_students=Count('enrollment')).all()

    if sort_by == 'popular':
        courses = courses.order_by('-num_students')
    elif sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'oldest':
        courses = courses.order_by('created_at')

    categories = Category.objects.all()
    paginator = Paginator(courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'courses/course_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'show_sidebar': True,
        'full_page_center': False,
    })


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

@login_required
def dashboard(request):
    if request.user.profile.is_instructor:
        courses = Course.objects.filter(created_by=request.user)
        return render(request, 'auth/dashboard.html', {
            'is_instructor': True,
            'courses': courses
        })
    else:
        enrollments = request.user.enrollments.select_related('course').distinct()
        for enrollment in enrollments:
            total = enrollment.course.lessons.count()
            completed = enrollment.completed_lessons.count()
            enrollment.progress = int((completed / total) * 100) if total > 0 else 0
        return render(request, 'auth/dashboard.html', {
            'is_instructor': False,
            'enrollments': enrollments
        })

@login_required
def create_course(request):
    if not request.user.profile.is_instructor:
        return HttpResponseForbidden("You are not an instructor.")
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form, 'page_title': 'Create Course'})


@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.created_by:
        return HttpResponseForbidden("Not allowed.")
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/create_course.html', {'form': form, 'page_title': 'Edit Course'})


@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.created_by:
        return HttpResponseForbidden("Not allowed.")
    course.delete()
    return redirect('course_list')


@login_required
def create_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.created_by != request.user:
        return HttpResponseForbidden("Not allowed.")
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = LessonForm()
    return render(request, 'courses/create_lesson.html', {'form': form, 'course': course, 'page_title': 'Add Lesson'})


def courses_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    courses = Course.objects.filter(category=category)
    categories = Category.objects.all()

    paginator = Paginator(courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'courses/course_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category,
        'show_sidebar': True,
        'full_page_center': False,
    })

from django.shortcuts import render

def login_page(request):
    return render(request, 'auth/login.html')


@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not request.user.profile.is_instructor or course.created_by != request.user:
        return HttpResponseForbidden("Only the instructor of this course can create assignments.")
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.created_by = request.user
            assignment.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = AssignmentForm()

    return render(request, 'assignments/create_assignment.html', {
        'form': form,
        'course': course,
        'page_title': 'Create Assignment'
    })


@login_required
def assignment_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = course.assignments.all()
    return render(request, 'assignments/assignment_list.html', {
        'course': course,
        'assignments': assignments,
    })


def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            messages.success(request, "✅ Assignment submitted successfully!")
            return redirect('course_detail', course_id=assignment.course.id)
        else:
            messages.error(request, "❌ Submission failed. Please check the form and try again.")
    else:
        form = SubmissionForm()

    return render(request, 'assignments/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
def view_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if not request.user.profile.is_instructor or assignment.created_by != request.user:
        return HttpResponseForbidden("Only the instructor can view submissions.")
    
    submissions = assignment.submissions.all()
    return render(request, 'assignments/view_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })

