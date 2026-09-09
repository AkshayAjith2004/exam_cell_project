from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Classroom
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def classroom_list(request):
    classrooms = Classroom.objects.all().order_by('room_number')
    
    if request.method == 'POST':
        room_number = request.POST.get('room_number')
        building = request.POST.get('building')
        floor = request.POST.get('floor')
        rows = int(request.POST.get('rows'))
        columns = int(request.POST.get('columns'))
        is_available = request.POST.get('is_available') == 'on'
        
        if Classroom.objects.filter(room_number=room_number).exists():
            messages.error(request, f"Classroom '{room_number}' already exists.")
        else:
            Classroom.objects.create(
                room_number=room_number,
                building=building,
                floor=floor,
                rows=rows,
                columns=columns,
                is_available=is_available
            )
            messages.success(request, f"Classroom '{room_number}' registered successfully.")
            return redirect('classroom_list')
            
    from exams.models import Exam
    exams = Exam.objects.filter(is_active=True)
    return render(request, 'classrooms/classroom_list.html', {
        'classrooms': classrooms,
        'exams': exams
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def classroom_toggle(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    classroom.is_available = not classroom.is_available
    classroom.save()
    messages.success(request, f"Classroom '{classroom.room_number}' availability status updated.")
    return redirect('classroom_list')
