from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from departments.models import Department
from .models import Teacher
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def teacher_list(request):
    teachers = Teacher.objects.select_related('user', 'department').all().order_by('employee_id')
    departments = Department.objects.all()
    
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'departments': departments,
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def teacher_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        phone = request.POST.get('phone')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        elif Teacher.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f"Employee ID '{employee_id}' already exists.")
        else:
            try:
                # 1. Create Django User
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # 2. Set profile role
                profile = user.profile
                profile.role = 'TEACHER'
                profile.save()
                
                # 3. Create Teacher profile
                dept = Department.objects.get(id=department_id)
                Teacher.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department=dept,
                    phone=phone
                )
                messages.success(request, f"Teacher '{first_name} {last_name}' registered successfully.")
            except Exception as e:
                messages.error(request, f"Error registering teacher: {str(e)}")
                
    return redirect('teacher_list')
