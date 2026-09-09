from django.db import transaction
from departments.models import Branch
from classrooms.models import Classroom
from timetable.models import Timetable
from students.models import Student
from exams.models import Exam
from .models import SeatingArrangement
import collections

def interleave_lists(lists):
    """
    Round-robin interleaves a list of lists.
    E.g. [[A1, A2, A3], [B1, B2], [C1]] -> [A1, B1, C1, A2, B2, A3]
    """
    result = []
    active_lists = [list(l) for l in lists if l]
    while active_lists:
        next_active = []
        for l in active_lists:
            if l:
                result.append(l.pop(0))
                if l:
                    next_active.append(l)
        active_lists = next_active
    return result

def generate_seating(exam_id, exam_date, session, classroom_ids, strategy='interleave_branch', classroom_overrides=None):
    """
    Generates seating arrangements for a given exam date, session, and selected classrooms.
    Returns: (success, message, allocated_count, unallocated_count)
    """
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return False, "Selected examination does not exist.", 0, 0

    # 1. Fetch timetables for this exam on this date/session
    timetables = Timetable.objects.filter(exam=exam, exam_date=exam_date, session=session).select_related('subject', 'subject__department')
    if not timetables.exists():
        return False, f"No exam timetable scheduled on {exam_date} ({session}) for this exam.", 0, 0

    # 2. Fetch active/available classrooms
    classrooms = list(Classroom.objects.filter(id__in=classroom_ids, is_available=True).order_by('room_number'))
    if not classrooms:
        return False, "No available classrooms selected.", 0, 0

    # Apply capacity overrides
    if classroom_overrides:
        for classroom in classrooms:
            cid_str = str(classroom.id)
            if cid_str in classroom_overrides:
                r, c = classroom_overrides[cid_str]
                classroom.rows = r
                classroom.columns = c
                classroom.capacity = r * c

    # 3. Find students writing these exams
    student_exams = []
    for slot in timetables:
        # Get students matching the branch (if set) or department, and semester of the timetabled subject
        if slot.subject.branch:
            students = Student.objects.filter(
                branch=slot.subject.branch,
                semester=slot.subject.semester
            ).select_related('user', 'branch', 'branch__department').order_by('admission_number')
        else:
            students = Student.objects.filter(
                branch__department=slot.subject.department,
                semester=slot.subject.semester
            ).select_related('user', 'branch', 'branch__department').order_by('admission_number')
        
        for student in students:
            student_exams.append((student, slot))

    if not student_exams:
        return False, "No students registered for the scheduled exams in this slot.", 0, 0

    # 4. Group & Interleave based on Strategy
    if strategy == 'interleave_branch':
        # Group by Branch + Semester (e.g. CS-Semester 6, EC-Semester 6, BCA-Semester 4)
        groups = collections.defaultdict(list)
        for student, slot in student_exams:
            key = (student.branch.id, student.semester)
            groups[key].append((student, slot))
        allocation_queue = interleave_lists(groups.values())

    elif strategy == 'interleave_sem':
        # Group by Semester only
        groups = collections.defaultdict(list)
        for student, slot in student_exams:
            key = student.semester
            groups[key].append((student, slot))
        allocation_queue = interleave_lists(groups.values())

    else: # sequential
        # Sort sequentially by subject code and student roll/admission number
        allocation_queue = sorted(student_exams, key=lambda x: (x[1].subject.subject_code, x[0].admission_number))

    # 5. Allocate to rooms inside database transaction
    allocated_count = 0
    unallocated_count = 0
    allocations_to_create = []

    total_seats_available = sum(c.capacity for c in classrooms)

    with transaction.atomic():
        # Clear existing seating arrangements for these timetabled slots
        SeatingArrangement.objects.filter(timetable__in=timetables).delete()

        queue_idx = 0
        for classroom in classrooms:
            R = classroom.rows
            C = classroom.columns

            # Fill row-by-row, column-by-column
            for r in range(1, R + 1):
                for c in range(1, C + 1):
                    if queue_idx < len(allocation_queue):
                        student, slot = allocation_queue[queue_idx]
                        
                        arr = SeatingArrangement(
                            student=student,
                            exam=exam,
                            timetable=slot,
                            classroom=classroom,
                            row_index=r,
                            col_index=c,
                            seat_number=f"Row {r}, Col {c}"
                        )
                        allocations_to_create.append(arr)
                        queue_idx += 1
                        allocated_count += 1
                    else:
                        break
                if queue_idx >= len(allocation_queue):
                    break
            if queue_idx >= len(allocation_queue):
                break

        # Bulk create for efficiency
        SeatingArrangement.objects.bulk_create(allocations_to_create)
        
        # Calculate remaining
        if queue_idx < len(allocation_queue):
            unallocated_count = len(allocation_queue) - queue_idx

    if unallocated_count > 0:
        msg = f"Allocation completed with warnings. Seated {allocated_count} students. {unallocated_count} students could not be seated due to insufficient capacity (Selected rooms capacity: {total_seats_available})."
        return True, msg, allocated_count, unallocated_count
    else:
        msg = f"Success! All {allocated_count} students allocated successfully to {len(classrooms)} classrooms."
        return True, msg, allocated_count, 0
