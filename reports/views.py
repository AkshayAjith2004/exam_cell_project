from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime

from exams.models import Exam
from classrooms.models import Classroom
from seating_app.models import SeatingArrangement
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def print_report(request, report_type):
    exam_id = request.GET.get('exam_id')
    date_str = request.GET.get('date')
    session = request.GET.get('session')
    classroom_id = request.GET.get('classroom_id')
    
    if report_type == 'timetable':
        from timetable.models import Timetable
        if exam_id:
            exam = get_object_or_404(Exam, id=exam_id)
            entries = Timetable.objects.filter(exam=exam).select_related('exam', 'subject', 'subject__department').order_by('exam_date', 'start_time')
        else:
            exam = Exam.objects.filter(is_active=True).first()
            entries = Timetable.objects.select_related('exam', 'subject', 'subject__department').all().order_by('exam_date', 'start_time')
            
        context = {
            'report_type': report_type,
            'exam': exam,
            'entries': entries,
            'print_date': datetime.now().strftime('%d-%b-%Y %I:%M %p')
        }
        return render(request, 'reports/print_layout.html', context)

    if not exam_id or not date_str or not session:
        messages.error(request, "Exam, Date, and Session are required to generate reports.")
        return redirect('seating_details')
        
    exam = get_object_or_404(Exam, id=exam_id)
    exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    context = {
        'report_type': report_type,
        'exam': exam,
        'exam_date': exam_date,
        'session': session,
        'print_date': datetime.now().strftime('%d-%b-%Y %I:%M %p')
    }
    
    if report_type == 'hall_chart':
        # Grid diagram for a specific room
        classroom = get_object_or_404(Classroom, id=classroom_id)
        allocations = SeatingArrangement.objects.filter(
            classroom=classroom,
            exam=exam,
            timetable__exam_date=exam_date,
            timetable__session=session
        ).select_related('student', 'student__user', 'student__branch', 'student__branch__department', 'timetable__subject').order_by('row_index', 'col_index')
        
        # Build 2D grid
        alloc_map = {(a.row_index, a.col_index): a for a in allocations}
        seating_grid = []
        for r in range(1, classroom.rows + 1):
            row_data = []
            for c in range(1, classroom.columns + 1):
                row_data.append(alloc_map.get((r, c)))
            seating_grid.append(row_data)
            
        context.update({
            'classroom': classroom,
            'allocations': allocations,
            'seating_grid': seating_grid,
        })
        
    elif report_type == 'desk_slips':
        # Slips for a room
        classroom = get_object_or_404(Classroom, id=classroom_id)
        allocations = SeatingArrangement.objects.filter(
            classroom=classroom,
            exam=exam,
            timetable__exam_date=exam_date,
            timetable__session=session
        ).select_related('student', 'student__user', 'student__branch', 'timetable__subject').order_by('row_index', 'col_index')
        
        context.update({
            'classroom': classroom,
            'allocations': allocations,
        })
        
    elif report_type == 'notice_board':
        # Master list of all students sorted by branch, semester, and roll
        allocations = SeatingArrangement.objects.filter(
            exam=exam,
            timetable__exam_date=exam_date,
            timetable__session=session
        ).select_related('student', 'student__user', 'student__branch', 'classroom', 'timetable__subject').order_by('timetable__subject__subject_code', 'student__admission_number')
        
        context.update({
            'allocations': allocations,
        })
        
    elif report_type == 'branch_wise':
        # Summary of which branches are in which classrooms
        allocations = SeatingArrangement.objects.filter(
            exam=exam,
            timetable__exam_date=exam_date,
            timetable__session=session
        ).select_related('student__branch', 'classroom').order_by('student__branch__code', 'classroom__room_number')
        
        # Group by Branch + Semester -> list of rooms & student counts in each room
        branch_mapping = {}
        for a in allocations:
            key = f"{a.student.branch.code} - Sem {a.student.semester}"
            if key not in branch_mapping:
                branch_mapping[key] = {}
            room = a.classroom.room_number
            branch_mapping[key][room] = branch_mapping[key].get(room, 0) + 1
            
        summary_list = []
        for key, rooms in branch_mapping.items():
            rooms_str = ", ".join([f"{room} ({count} candidates)" for room, count in rooms.items()])
            total_candidates = sum(rooms.values())
            summary_list.append({
                'class_name': key,
                'rooms': rooms_str,
                'total': total_candidates
            })
            
        context.update({
            'summary_list': summary_list
        })
        
    else:
        messages.error(request, "Invalid report type.")
        return redirect('seating_details')
        
    return render(request, 'reports/print_layout.html', context)
