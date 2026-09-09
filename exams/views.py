from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from departments.models import AcademicYear
from .models import Exam
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def exam_list(request):
    exams = Exam.objects.select_related('academic_year').all()
    
    code_filter = request.GET.get('code_filter', '').strip()
    name_filter = request.GET.get('name_filter', '').strip()
    
    if code_filter:
        exams = exams.filter(code__icontains=code_filter)
    if name_filter:
        exams = exams.filter(name__icontains=name_filter)
        
    exams = exams.order_by('-code')
    academic_years = AcademicYear.objects.all().order_by('-name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        academic_year_id = request.POST.get('academic_year')
        is_active = request.POST.get('is_active') == 'on'
        
        if Exam.objects.filter(code=code).exists():
            messages.error(request, f"Exam with code '{code}' already exists.")
        else:
            try:
                ay = AcademicYear.objects.get(id=academic_year_id)
                Exam.objects.create(
                    name=name,
                    code=code,
                    academic_year=ay,
                    is_active=is_active
                )
                messages.success(request, f"Exam session '{name}' created successfully.")
            except Exception as e:
                messages.error(request, f"Error saving exam session: {str(e)}")
                
        return redirect('exam_list')
        
    return render(request, 'exams/exam_list.html', {
        'exams': exams,
        'academic_years': academic_years,
        'code_filter': code_filter,
        'name_filter': name_filter
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def exam_edit(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    academic_years = AcademicYear.objects.all().order_by('-name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        academic_year_id = request.POST.get('academic_year')
        is_active = request.POST.get('is_active') == 'on'
        
        if Exam.objects.filter(code=code).exclude(id=exam.id).exists():
            messages.error(request, f"Exam with code '{code}' already exists.")
        else:
            try:
                ay = AcademicYear.objects.get(id=academic_year_id)
                exam.name = name
                exam.code = code
                exam.academic_year = ay
                exam.is_active = is_active
                exam.save()
                messages.success(request, f"Exam session '{name}' updated successfully.")
                return redirect('exam_list')
            except Exception as e:
                messages.error(request, f"Error updating exam: {str(e)}")
                
    return render(request, 'exams/exam_edit.html', {
        'exam': exam,
        'academic_years': academic_years
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    name = exam.name
    exam.delete()
    messages.success(request, f"Exam session '{name}' deleted successfully.")
    return redirect('exam_list')

