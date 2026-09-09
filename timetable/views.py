from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from exams.models import Exam
from subjects.models import Subject
from departments.models import Department, Branch
from .models import Timetable
from accounts.views import role_required
from datetime import date

@login_required
@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER', 'STUDENT'])
def timetable_list(request):
    from django.db.models import Q
    entries = Timetable.objects.select_related('exam', 'subject', 'subject__department', 'subject__branch').all().order_by('exam_date', 'start_time')
    
    student_obj = None
    if request.user.profile.role == 'STUDENT':
        try:
            student_obj = request.user.student_profile
            entries = entries.filter(
                Q(subject__branch=student_obj.branch) | Q(subject__branch__isnull=True, subject__department=student_obj.branch.department),
                subject__semester=student_obj.semester
            )
        except Exception:
            entries = entries.none()
    else:
        # Semester filter option for admins/teachers
        selected_sem = request.GET.get('sem', '').strip()
        if selected_sem and selected_sem.isdigit():
            entries = entries.filter(subject__semester=int(selected_sem))

        # Branch / Department filter option for admins/teachers
        selected_branch = request.GET.get('branch', '').strip()
        if selected_branch and selected_branch.isdigit():
            entries = entries.filter(subject__branch_id=int(selected_branch))

        selected_dept = request.GET.get('dept', '').strip()
        if selected_dept and selected_dept.isdigit():
            entries = entries.filter(subject__department_id=int(selected_dept))

    exams = Exam.objects.filter(is_active=True)
    subjects = Subject.objects.all().select_related('department', 'branch').order_by('semester', 'subject_code')
    departments = Department.objects.all().order_by('code')
    branches = Branch.objects.select_related('department').all().order_by('department__code', 'code')
    
    if request.method == 'POST' and request.user.profile.role in ['ADMIN', 'EXAM_CONTROLLER']:
        exam_id = request.POST.get('exam')
        semester_val = request.POST.get('semester')
        branch_id = request.POST.get('branch')
        department_id = request.POST.get('department')
        attachment = request.FILES.get('attachment')
        
        try:
            exam = Exam.objects.get(id=exam_id)
            sem_num = int(semester_val) if (semester_val and semester_val.isdigit()) else 1
            
            branch = None
            dept = None
            if branch_id:
                branch = Branch.objects.filter(id=branch_id).first()
                if branch:
                    dept = branch.department
            elif department_id:
                dept = Department.objects.filter(id=department_id).first()

            # Find subject matching semester and branch/dept
            subject_qs = Subject.objects.filter(semester=sem_num)
            if branch:
                subject = subject_qs.filter(branch=branch).first()
            elif dept:
                subject = subject_qs.filter(department=dept).first()
            else:
                subject = subject_qs.first()

            if not subject:
                if not dept:
                    dept = Department.objects.first()
                
                b_code = branch.code if branch else (dept.code if dept else 'GEN')
                b_name = f"{dept.code} - {branch.name}" if (branch and dept) else (dept.name if dept else 'General')
                
                code = f"{b_code}-S{sem_num}-TT"
                name = f"{b_name} Semester {sem_num} Timetable"
                
                if Subject.objects.filter(subject_code=code).exists():
                    code = f"{b_code}-S{sem_num}-TT-{Subject.objects.count()+1}"
                    
                subject = Subject.objects.create(
                    subject_code=code,
                    subject_name=name,
                    department=dept,
                    branch=branch,
                    semester=sem_num
                )

            # Check if entry already exists for this exam and subject
            existing_entry = Timetable.objects.filter(exam=exam, subject=subject).first()
            if existing_entry:
                if attachment:
                    existing_entry.attachment = attachment
                existing_entry.save()
                target_label = f"{dept.code} ({branch.code})" if branch else (dept.code if dept else "")
                messages.success(request, f"Updated timetable for '{exam.name}' - {target_label} Semester {sem_num} successfully.")
            else:
                Timetable.objects.create(
                    exam=exam,
                    subject=subject,
                    exam_date=date.today(),
                    session='Morning',
                    start_time='09:30',
                    end_time='12:30',
                    attachment=attachment
                )
                target_label = f"{dept.code} ({branch.code})" if branch else (dept.code if dept else "")
                messages.success(request, f"Scheduled timetable for '{exam.name}' - {target_label} Semester {sem_num} successfully.")
        except Exception as e:
            messages.error(request, f"Error scheduling exam timetable: {str(e)}")
            
        return redirect('timetable_list')
        
    return render(request, 'timetable/timetable_list.html', {
        'entries': entries,
        'exams': exams,
        'subjects': subjects,
        'departments': departments,
        'branches': branches,
        'semester_choices': range(1, 9),
        'selected_sem': selected_sem if not student_obj else '',
        'selected_branch': selected_branch if not student_obj else '',
        'selected_dept': selected_dept if not student_obj else '',
        'student': student_obj,
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def timetable_delete(request, pk):
    entry = get_object_or_404(Timetable, pk=pk)
    subject_name = entry.subject.subject_name
    entry.delete()
    messages.success(request, f"Scheduled exam slot for '{subject_name}' deleted successfully.")
    return redirect('timetable_list')



