from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required ,user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from .models import Course, Lesson, Enrollment, Profile, Category, Assignment, Submission, Announcement
from .forms import CourseForm, LessonForm, StudentRegistrationForm, AssignmentForm, SubmissionForm, AnnouncementForm, InstructorRegistrationForm

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'auth/register_student.html', {'form': form, 'page_title': 'Student Registration'})

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


def register_instructor(request):
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.is_instructor = True
            user.profile.is_approved = False
            user.profile.save()
            return render(request, 'auth/pending_approval.html', {
                'page_title': 'Pending Approval'
            })
        else:
            print("❌ Form errors:", form.errors)
    else:
        form = InstructorRegistrationForm()     

    return render(request, 'auth/register_instructor.html', {
        'form': form,
        'page_title': 'Instructor Registration'
    })




def login_instructor(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.profile.is_instructor:
                if not user.profile.is_approved:
                    error = "⏳ Your instructor account is awaiting moderator approval."
                else:
                    login(request, user)
                    return redirect('dashboard')
            else:
                error = "⚠️ You are not an instructor. Use the student tab."
        else:
            error = "Invalid username or password."
    return render(request, 'auth/login.html', {'instructor_error': error, 'show_tab': 'instructor'})

def login_moderator(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'profile') and user.profile.is_moderator:
                login(request, user)
                return redirect('dashboard')  
            else:
                error = "⚠️ You are not authorized as a moderator."
        else:
            error = "Invalid username or password."
    
    return render(request, 'auth/login.html', {'moderator_error': error, 'show_tab': 'moderator'})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login_student')

def home(request):
    latest_courses = Course.objects.all()[:5]
    return render(request, 'index.html', {'latest_courses': latest_courses})



def course_list(request):
    sort_by = request.GET.get('sort', 'popular')
    category_id = request.GET.get('category')

    courses = Course.objects.annotate(num_students=Count('enrollment')).all()

    if category_id:
        courses = courses.filter(category_id=category_id)

    if sort_by == 'popular':
        courses = courses.order_by('-num_students')
    elif sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'oldest':
        courses = courses.order_by('created_at')

    paginator = Paginator(courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

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
    submissions = {}

    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

        for assignment in course.assignments.all():
            submissions[assignment.id] = Submission.objects.filter(
                assignment=assignment, student=request.user
            ).exists()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'enrolled': enrolled,
        'submissions': submissions,
    })

def choose_registration(request):
    return render(request, 'auth/choose_registration.html', {
        'page_title': 'Register'
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('course_detail', course_id=course.id)


from django.db.models import Q


@login_required


def dashboard(request):
    user = request.user
    latest_announcement = Announcement.objects.order_by('-created_at').first()

    # Moderator dashboard first
    if hasattr(user, "profile") and user.profile.is_moderator:
        context = {
            'is_moderator': True,
            'pending_instructors_count': Profile.objects.filter(is_instructor=True, is_approved=False).count(),
            'total_instructors': Profile.objects.filter(is_instructor=True).count(),
            'latest_announcement': latest_announcement,
        }
        return render(request, 'auth/dashboard.html', context)

    # Instructor pending approval check
    if user.profile.is_instructor and not user.profile.is_approved:
        return render(request, 'auth/pending_approval.html')

    # Instructor dashboard
    if user.profile.is_instructor:
        courses = Course.objects.filter(created_by=user)
        enrollments = Enrollment.objects.filter(course__in=courses).select_related('student')
        students = list({enrollment.student for enrollment in enrollments})
        return render(request, 'auth/dashboard.html', {
            'is_instructor': True,
            'courses': courses,
            'students': students,
            'latest_announcement': latest_announcement,
        })

    # Student dashboard
    enrollments = user.enrollments.select_related('course').distinct()
    for enrollment in enrollments:
        total = enrollment.course.lessons.count()
        completed = enrollment.completed_lessons.count()
        enrollment.progress = int((completed / total) * 100) if total > 0 else 0

    now = timezone.now()
    pending_assignments = Assignment.objects.filter(
        course__in=[en.course for en in enrollments],
        due_date__gte=now
    ).filter(
        Q(submissions__isnull=True) | ~Q(submissions__student=user)
    ).distinct()

    pending_count = pending_assignments.count()
    remaining_classes = sum(
        en.course.lessons.count() - en.completed_lessons.count()
        for en in enrollments
    )

    return render(request, 'auth/dashboard.html', {
        'is_instructor': False,
        'enrollments': enrollments,
        'pending_assignments': pending_assignments,
        'pending_count': pending_count,
        'remaining_classes': remaining_classes,
        'latest_announcement': latest_announcement,
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

@login_required
def student_assignments(request):
    if request.user.profile.is_instructor:
        return HttpResponseForbidden("Instructors cannot access student assignments.")

    enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course', flat=True)
    assignments = Assignment.objects.filter(course__in=enrolled_courses).order_by('-due_date')
    submitted_ids = Submission.objects.filter(student=request.user).values_list('assignment_id', flat=True)
    pending_assignments = assignments.exclude(id__in=submitted_ids)
    submitted_assignments = assignments.filter(id__in=submitted_ids)

    return render(request, 'assignments/student_assignments.html', {
        'pending_assignments': pending_assignments,
        'submitted_assignments': submitted_assignments,
        'page_title': 'My Assignments',
    })

@login_required
def pending_classes(request):
    if request.user.profile.is_instructor:
        return HttpResponseForbidden("Instructors cannot access pending classes.")

    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    pending_lessons = []

    for enrollment in enrollments:
        completed = enrollment.completed_lessons.values_list('id', flat=True)
        lessons_left = enrollment.course.lessons.exclude(id__in=completed)
        for lesson in lessons_left:
            pending_lessons.append({
                'course': enrollment.course,
                'lesson': lesson,
            })

    return render(request, 'courses/pending_classes.html', {
        'pending_lessons': pending_lessons,
        'page_title': 'Pending Classes',
    })

@login_required
def announcement_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    announcements = course.announcements.all()
    return render(request, 'announcements/announcement_list.html', {
        'course': course,
        'announcements': announcements,
    })

def create_announcement(request):
    if not request.user.profile.is_instructor:
        return redirect('global_announcement_list')

    courses = Course.objects.filter(created_by=request.user)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            course_id = request.POST.get('course_id')
            if course_id:
                announcement.course = get_object_or_404(Course, id=course_id)
            announcement.created_by = request.user
            announcement.save()
            return redirect('global_announcement_list')
    else:
        form = AnnouncementForm()

    return render(request, 'announcements/announcement_form.html', {
        'form': form,
        'courses': courses,
    })

@login_required
def global_announcement_list(request):
    announcements = Announcement.objects.all().order_by('-created_at')

    if request.user.profile.is_instructor and request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('content')
        course_id = request.POST.get('course_id')

        if title and message and course_id:
            course = Course.objects.get(id=course_id)
            Announcement.objects.create(
                course=course,
                title=title,
                message=message,
                created_by=request.user
            )
            return redirect('global_announcement_list')

    courses = Course.objects.filter(created_by=request.user) if request.user.profile.is_instructor else None
    return render(request, 'announcements/announcement_list.html', {'announcements': announcements, 'courses': courses})

def is_moderator(user):
    return hasattr(user, 'profile') and user.profile.is_moderator

@login_required
@user_passes_test(is_moderator)
def pending_instructors(request):
    pending_instructors = Profile.objects.filter(is_instructor=True, is_approved=False)
    return render(request, 'auth/pending_instructors.html', {'pending_instructors': pending_instructors})


@login_required
@user_passes_test(is_moderator)
def approve_instructor(request, user_id):
    instructor = get_object_or_404(User, id=user_id, profile__is_instructor=True)
    instructor.profile.is_approved = True
    instructor.profile.save()
    return redirect('pending_instructors')

@login_required
def all_instructors(request):
    if not request.user.profile.is_moderator:
        return render(request, 'error.html', {'message': 'Unauthorized access.'})
    instructors = User.objects.filter(profile__is_instructor=True)
    return render(request, 'moderator/all_instructors.html', {'instructors': instructors})

@login_required
def moderator_stats(request):
    total_instructors = Profile.objects.filter(is_instructor=True).count()
    total_students = Profile.objects.filter(is_instructor=False, is_moderator=False).count()
    total_courses = Course.objects.count()

    context = {
        'total_instructors': total_instructors,
        'total_students': total_students,
        'total_courses': total_courses,
    }
    return render(request, 'moderator/moderator_stats.html', context)