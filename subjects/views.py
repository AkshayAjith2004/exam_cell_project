from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from departments.models import Department, Branch
from teachers.models import Teacher
from .models import Subject
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def subject_list(request):
    subjects = Subject.objects.select_related('department', 'branch', 'faculty', 'faculty__user').all().order_by('subject_code')
    departments = Department.objects.all()
    branches = Branch.objects.select_related('department').all()
    teachers = Teacher.objects.select_related('user').all()
    
    if request.method == 'POST' and request.user.profile.role in ['ADMIN', 'EXAM_CONTROLLER', 'TEACHER']:
        subject_code = request.POST.get('subject_code', '').upper().strip()
        subject_name = request.POST.get('subject_name', '').strip()
        department_id = request.POST.get('department')
        branch_id = request.POST.get('branch')
        semester = int(request.POST.get('semester'))

        branch = None
        if branch_id:
            try:
                branch = Branch.objects.get(id=branch_id)
                dept = branch.department
            except Branch.DoesNotExist:
                dept = Department.objects.get(id=department_id) if department_id else None
        else:
            dept = Department.objects.get(id=department_id) if department_id else None
        
        if Subject.objects.filter(subject_code=subject_code).exists():
            messages.error(request, f"Subject with code '{subject_code}' already exists.")
        elif not dept:
            messages.error(request, "Please select a valid Department or Branch.")
        else:
            try:
                Subject.objects.create(
                    subject_code=subject_code,
                    subject_name=subject_name,
                    department=dept,
                    branch=branch,
                    semester=semester
                )
                branch_label = f" ({branch.code})" if branch else ""
                messages.success(request, f"Subject '{subject_name}'{branch_label} registered successfully.")
            except Exception as e:
                messages.error(request, f"Error registering subject: {str(e)}")
                
        return redirect('subject_list')

    return render(request, 'subjects/subject_list.html', {
        'subjects': subjects,
        'departments': departments,
        'branches': branches,
        'teachers': teachers,
        'semester_choices': range(1, 9)
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject_code = request.POST.get('subject_code', '').upper().strip()
        subject_name = request.POST.get('subject_name', '').strip()
        department_id = request.POST.get('department')
        branch_id = request.POST.get('branch')
        semester = int(request.POST.get('semester'))
        
        if Subject.objects.filter(subject_code=subject_code).exclude(pk=pk).exists():
            messages.error(request, f"Subject code '{subject_code}' is already used by another subject.")
        else:
            branch = None
            if branch_id:
                try:
                    branch = Branch.objects.get(id=branch_id)
                    dept = branch.department
                except Branch.DoesNotExist:
                    dept = Department.objects.get(id=department_id) if department_id else subject.department
            else:
                dept = Department.objects.get(id=department_id) if department_id else subject.department

            subject.subject_code = subject_code
            subject.subject_name = subject_name
            subject.department = dept
            subject.branch = branch
            subject.semester = semester
            subject.save()
            messages.success(request, f"Subject '{subject_name}' updated successfully.")
    return redirect('subject_list')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def assign_faculty(request, subject_id):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=subject_id)
        faculty_id = request.POST.get('faculty')
        try:
            if faculty_id:
                faculty = Teacher.objects.get(id=faculty_id)
                subject.faculty = faculty
            else:
                subject.faculty = None
            subject.save()
            messages.success(request, f"Faculty assigned successfully to subject '{subject.subject_name}'.")
        except Exception as e:
            messages.error(request, f"Error assigning faculty: {str(e)}")
    return redirect('subject_list')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    name = subject.subject_name
    subject.delete()
    messages.success(request, f"Subject '{name}' deleted successfully.")
    return redirect('subject_list')


