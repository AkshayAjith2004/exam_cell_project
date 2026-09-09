from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from departments.models import Branch, Department
from students.models import Student
from teachers.models import Teacher

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    branches = Branch.objects.select_related('department').all()
    departments = Department.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        photo = request.FILES.get('photo')
        
        # Validations
        if not photo:
            messages.error(request, "Please upload a profile photo.")
            return render(request, 'accounts/signup.html', {'branches': branches, 'departments': departments})
            
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return render(request, 'accounts/signup.html', {'branches': branches, 'departments': departments})
            
        try:
            with transaction.atomic():
                # 1. Create Django User
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # 2. Update UserProfile role and optional photo
                profile = user.profile
                profile.role = role
                if photo:
                    profile.photo = photo
                profile.save()
                
                # 3. Create role-specific records
                if role == 'STUDENT':
                    admission_number = request.POST.get('admission_number')
                    registration_number = request.POST.get('registration_number', '').strip()
                    branch_id = request.POST.get('branch')
                    semester = request.POST.get('semester')
                    phone = request.POST.get('phone')
                    
                    if Student.objects.filter(admission_number=admission_number).exists():
                        raise ValueError(f"Admission number '{admission_number}' already registered.")
                        
                    branch = Branch.objects.get(id=branch_id)
                    Student.objects.create(
                        user=user,
                        admission_number=admission_number,
                        registration_number=registration_number or None,
                        branch=branch,
                        semester=int(semester),
                        phone=phone,
                        photo=photo
                    )
                    
                elif role == 'TEACHER':
                    employee_id = request.POST.get('employee_id')
                    department_id = request.POST.get('department')
                    phone = request.POST.get('phone')
                    
                    if Teacher.objects.filter(employee_id=employee_id).exists():
                        raise ValueError(f"Employee ID '{employee_id}' already registered.")
                        
                    dept = Department.objects.get(id=department_id)
                    Teacher.objects.create(
                        user=user,
                        employee_id=employee_id,
                        department=dept,
                        phone=phone,
                        photo=photo
                    )
                
                messages.success(request, "Account registered successfully! Please sign in using your new credentials.")
                return redirect('login')
                
        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            
    return render(request, 'accounts/signup.html', {
        'branches': branches,
        'departments': departments,
        'semester_choices': range(1, 9)
    })

def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.profile.role not in allowed_roles:
                messages.error(request, "Access denied. Insufficient permissions.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('home')
