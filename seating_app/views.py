from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from datetime import datetime

from exams.models import Exam
from classrooms.models import Classroom
from timetable.models import Timetable
from students.models import Student
from .models import SeatingArrangement
from .utils import generate_seating
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def generate_seating_view(request):
    exams = Exam.objects.filter(is_active=True)
    classrooms = Classroom.objects.filter(is_available=True).order_by('room_number')
    
    if request.method == 'POST':
        exam_id = request.POST.get('exam')
        exam_date_str = request.POST.get('exam_date')
        session = request.POST.get('session')
        classroom_ids = request.POST.getlist('classrooms')
        strategy = request.POST.get('strategy', 'interleave_branch')
        
        # Parse capacity overrides
        classroom_overrides = {}
        for cid in classroom_ids:
            row_override = request.POST.get(f'rows_{cid}')
            col_override = request.POST.get(f'cols_{cid}')
            if row_override and col_override:
                try:
                    classroom_overrides[str(cid)] = (int(row_override), int(col_override))
                except ValueError:
                    pass
        
        if not exam_id or not exam_date_str or not session or not classroom_ids:
            messages.error(request, "Please fill in all details and select at least one classroom.")
        else:
            try:
                exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
                success, msg, allocated, unallocated = generate_seating(
                    exam_id, exam_date, session, classroom_ids, strategy, classroom_overrides=classroom_overrides
                )
                if success:
                    if unallocated > 0:
                        messages.warning(request, msg)
                    else:
                        messages.success(request, msg)
                    return redirect(f"{'/seating/details/'}?exam_id={exam_id}&date={exam_date_str}&session={session}")
                else:
                    messages.error(request, msg)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                
    return render(request, 'seating/generate.html', {
        'exams': exams,
        'classrooms': classrooms,
        'strategies': [
            ('interleave_branch', 'Interleave Branches (e.g. BCA vs MCA)'),
            ('interleave_sem', 'Interleave Semesters (e.g. Sem 1 vs Sem 2)'),
            ('sequential', 'Sequential (By Subject & Roll Order)')
        ]
    })

@login_required
def seating_details(request):
    exam_id = request.GET.get('exam_id')
    date_str = request.GET.get('date')
    session = request.GET.get('session')
    classroom_id = request.GET.get('classroom_id')
    
    # Format filters
    exams_with_seating = Exam.objects.filter(seating_arrangements__isnull=False).distinct()
    
    # Available slots list
    slots = SeatingArrangement.objects.values(
        'exam__id', 'exam__name', 'timetable__exam_date', 'timetable__session'
    ).annotate(count=Count('id')).order_by('-timetable__exam_date')
    
    selected_exam = None
    exam_date = None
    classrooms = []
    selected_classroom = None
    seating_grid = []
    summary_list = []
    no_allocations = True

    if slots.exists() and (not exam_id or not date_str or not session):
        # Default to latest slot
        latest = slots.first()
        exam_id = latest['exam__id']
        date_str = latest['timetable__exam_date'].strftime('%Y-%m-%d')
        session = latest['timetable__session']

    if exam_id and date_str and session:
        no_allocations = False
        selected_exam = get_object_or_404(Exam, id=exam_id)
        exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get classrooms that have allocations for this slot
        classrooms = Classroom.objects.filter(
            seating_arrangements__exam=selected_exam,
            seating_arrangements__timetable__exam_date=exam_date,
            seating_arrangements__timetable__session=session
        ).distinct().order_by('room_number')
        
        if classroom_id:
            selected_classroom = classrooms.filter(id=classroom_id).first()
        elif classrooms.exists():
            selected_classroom = classrooms.first()
            
        if selected_classroom:
            allocations = SeatingArrangement.objects.filter(
                classroom=selected_classroom,
                exam=selected_exam,
                timetable__exam_date=exam_date,
                timetable__session=session
            ).select_related('student', 'student__user', 'student__branch', 'student__branch__department', 'timetable__subject')
            
            alloc_map = {(a.row_index, a.col_index): a for a in allocations}
            
            for r in range(1, selected_classroom.rows + 1):
                row_data = []
                for c in range(1, selected_classroom.columns + 1):
                    alloc = alloc_map.get((r, c))
                    row_data.append({
                        'row': r,
                        'col': c,
                        'allocation': alloc
                    })
                seating_grid.append(row_data)
                
            summary_list = allocations.order_by('timetable__subject__subject_code', 'student__admission_number')

    return render(request, 'seating/seating_details.html', {
        'slots': slots,
        'exams': exams_with_seating,
        'selected_exam': selected_exam,
        'current_date_str': date_str,
        'current_session': session,
        'classrooms': classrooms,
        'selected_classroom': selected_classroom,
        'seating_grid': seating_grid,
        'summary_list': summary_list,
        'no_allocations': no_allocations
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def edit_seating(request):
    if request.method == 'POST':
        alloc_id = request.POST.get('alloc_id')
        new_row = int(request.POST.get('row'))
        new_col = int(request.POST.get('col'))
        
        alloc = get_object_or_404(SeatingArrangement, id=alloc_id)
        classroom = alloc.classroom
        timetable = alloc.timetable
        exam = alloc.exam
        
        # Out of bounds check
        if new_row > classroom.rows or new_col > classroom.columns or new_row < 1 or new_col < 1:
            messages.error(request, f"Target seat R{new_row} C{new_col} is out of bounds for room {classroom.room_number}.")
        else:
            # Check target occupant
            target_alloc = SeatingArrangement.objects.filter(
                classroom=classroom,
                timetable=timetable,
                row_index=new_row,
                col_index=new_col
            ).first()
            
            try:
                with transaction.atomic():
                    if target_alloc:
                        # Swap seats!
                        target_alloc.row_index = alloc.row_index
                        target_alloc.col_index = alloc.col_index
                        target_alloc.seat_number = f"Row {alloc.row_index}, Col {alloc.col_index}"
                        target_alloc.save()
                        
                    alloc.row_index = new_row
                    alloc.col_index = new_col
                    alloc.seat_number = f"Row {new_row}, Col {new_col}"
                    alloc.save()
                    messages.success(request, f"Seat updated successfully.")
            except Exception as e:
                messages.error(request, f"Error swapping seat: {str(e)}")
                
        date_str = timetable.exam_date.strftime('%Y-%m-%d')
        return redirect(f"{'/seating/details/'}?exam_id={exam.id}&date={date_str}&session={timetable.session}&classroom_id={classroom.id}")
        
    return redirect('seating_details')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def clear_seating(request):
    if request.method == 'POST':
        exam_id = request.POST.get('exam')
        date_str = request.POST.get('date')
        session = request.POST.get('session')
        
        try:
            exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            SeatingArrangement.objects.filter(
                exam_id=exam_id,
                timetable__exam_date=exam_date,
                timetable__session=session
            ).delete()
            messages.success(request, f"Seating arrangements for the selected slot cleared.")
        except Exception as e:
            messages.error(request, f"Error clearing seating: {str(e)}")
            
    return redirect('seating_details')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def clear_all_seating(request):
    if request.method == 'POST':
        SeatingArrangement.objects.all().delete()
        messages.success(request, "All seating arrangements cleared successfully.")
    return redirect('seating_details')
