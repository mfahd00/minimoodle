from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Course
from django.shortcuts import render, redirect
from django import forms

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description']

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
    
    return render(request, 'courses/create_course.html', {'form': form})
