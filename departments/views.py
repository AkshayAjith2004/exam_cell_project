from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Department, Branch, AcademicYear
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def department_list(request):
    departments = Department.objects.all().order_by('code')
    academic_years = AcademicYear.objects.all().order_by('-name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_department':
            name = request.POST.get('name')
            code = request.POST.get('code').upper()
            
            if Department.objects.filter(code=code).exists():
                messages.error(request, f"Department code '{code}' already exists.")
            else:
                Department.objects.create(name=name, code=code)
                messages.success(request, f"Department '{name}' added successfully.")
                
        elif action == 'add_academic_year':
            name = request.POST.get('name')
            is_active = request.POST.get('is_active') == 'on'
            
            if AcademicYear.objects.filter(name=name).exists():
                messages.error(request, f"Academic year '{name}' already exists.")
            else:
                AcademicYear.objects.create(name=name, is_active=is_active)
                messages.success(request, f"Academic year '{name}' added successfully.")
                
        return redirect('department_list')

    return render(request, 'departments/department_list.html', {
        'departments': departments,
        'academic_years': academic_years,
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def academic_year_toggle(request, pk):
    ay = get_object_or_404(AcademicYear, pk=pk)
    status_action = request.POST.get('status_action') or request.GET.get('status_action')
    
    if status_action == 'activate':
        ay.is_active = True
        ay.save()
        messages.success(request, f"Academic Calendar Year '{ay.name}' has been activated.")
    elif status_action == 'deactivate':
        ay.is_active = False
        ay.save()
        messages.success(request, f"Academic Calendar Year '{ay.name}' has been deactivated.")
    else:
        ay.is_active = not ay.is_active
        ay.save()
        status_text = "activated" if ay.is_active else "deactivated"
        messages.success(request, f"Academic Calendar Year '{ay.name}' has been {status_text}.")
        
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('dashboard')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def academic_year_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, "Academic year name cannot be empty.")
        elif AcademicYear.objects.filter(name=name).exists():
            messages.error(request, f"Academic year '{name}' already exists.")
        else:
            AcademicYear.objects.create(name=name, is_active=is_active)
            messages.success(request, f"Academic year '{name}' added successfully.")
            
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('dashboard')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def academic_year_delete(request, pk):
    ay = get_object_or_404(AcademicYear, pk=pk)
    name = ay.name
    ay.delete()
    messages.success(request, f"Academic year '{name}' deleted successfully.")
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('dashboard')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def branch_list(request):
    branches = Branch.objects.select_related('department').all().order_by('department__code', 'code')
    departments = Department.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code').upper()
        department_id = request.POST.get('department')
        
        try:
            dept = Department.objects.get(id=department_id)
            if Branch.objects.filter(code=code, department=dept).exists():
                messages.error(request, f"Branch code '{code}' already exists in department '{dept.code}'.")
            else:
                Branch.objects.create(name=name, code=code, department=dept)
                messages.success(request, f"Branch '{name}' added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding branch: {str(e)}")
            
        return redirect('branch_list')

    return render(request, 'departments/branch_list.html', {
        'branches': branches,
        'departments': departments,
    })
