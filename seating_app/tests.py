from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date

from departments.models import Department, Branch, AcademicYear
from classrooms.models import Classroom
from subjects.models import Subject
from students.models import Student
from teachers.models import Teacher
from exams.models import Exam
from timetable.models import Timetable
from seating_app.models import SeatingArrangement
from seating_app.utils import generate_seating, interleave_lists

class SeatingAlgorithmTest(TestCase):
    
    def setUp(self):
        # 1. Create Academic Year and Departments
        self.ay = AcademicYear.objects.create(name="2026-AY", is_active=True)
        self.dept_cs = Department.objects.create(name="Computer Science", code="CS")
        
        # 2. Create Branches
        self.branch_bca = Branch.objects.create(name="BCA", code="BCA", department=self.dept_cs)
        self.branch_mca = Branch.objects.create(name="MCA", code="MCA", department=self.dept_cs)
        
        # 3. Create Classrooms
        self.room1 = Classroom.objects.create(
            room_number="101", building="Block A", floor="1st Floor", rows=4, columns=4
        ) # Capacity = 16
        
        # 4. Create Teacher (Faculty)
        self.teacher_user = User.objects.create_user(username="prof_john", password="password123")
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, employee_id="EMP001", department=self.dept_cs, phone="9988776655"
        )
        
        # 5. Create Subjects
        self.sub_bca = Subject.objects.create(
            subject_code="BCA401", subject_name="Java Programming",
            department=self.dept_cs, semester=4, faculty=self.teacher
        )
        self.sub_mca = Subject.objects.create(
            subject_code="MCA201", subject_name="Data Structures",
            department=self.dept_cs, semester=2, faculty=self.teacher
        )
        
        # 6. Create Students (5 BCA and 4 MCA)
        self.bca_students = []
        for i in range(1, 6):
            user = User.objects.create_user(username=f"bca_std_{i}", password="password123")
            user.profile.role = 'STUDENT'
            user.profile.save()
            std = Student.objects.create(
                user=user, admission_number=f"26BCA00{i}", branch=self.branch_bca, semester=4, phone="123"
            )
            self.bca_students.append(std)
            
        self.mca_students = []
        for i in range(1, 5):
            user = User.objects.create_user(username=f"mca_std_{i}", password="password123")
            user.profile.role = 'STUDENT'
            user.profile.save()
            std = Student.objects.create(
                user=user, admission_number=f"26MCA00{i}", branch=self.branch_mca, semester=2, phone="456"
            )
            self.mca_students.append(std)

        # 7. Create Exam & Timetables
        self.exam = Exam.objects.create(name="Diploma Semester Exams", code="DIP-2026", academic_year=self.ay, is_active=True)
        
        self.today = date.today()
        self.slot1 = Timetable.objects.create(
            exam=self.exam, subject=self.sub_bca, exam_date=self.today, session="Morning", start_time="09:30", end_time="12:30"
        )
        self.slot2 = Timetable.objects.create(
            exam=self.exam, subject=self.sub_mca, exam_date=self.today, session="Morning", start_time="09:30", end_time="12:30"
        )

    def test_interleave_utility(self):
        # Round-robin interleaving test
        lists = [
            ['A1', 'A2', 'A3'],
            ['B1', 'B2'],
            ['C1']
        ]
        result = interleave_lists(lists)
        self.assertEqual(result, ['A1', 'B1', 'C1', 'A2', 'B2', 'A3'])

    def test_generate_seating_success(self):
        # Generate seating arrangement
        success, msg, allocated, unallocated = generate_seating(
            exam_id=self.exam.id,
            exam_date=self.today,
            session="Morning",
            classroom_ids=[self.room1.id],
            strategy='interleave_branch'
        )
        
        self.assertTrue(success)
        self.assertEqual(allocated, 9) # 5 BCA + 4 MCA = 9 students
        self.assertEqual(unallocated, 0)
        
        # Verify SeatingArrangement database records
        allocations = SeatingArrangement.objects.filter(exam=self.exam, classroom=self.room1).order_by('row_index', 'col_index')
        self.assertEqual(allocations.count(), 9)
        
        # Verify that adjacent seats are interleaved
        # Room is 4x4. The first row should contain: BCA, MCA, BCA, MCA
        row_1_seats = allocations.filter(row_index=1).order_by('col_index')
        self.assertEqual(row_1_seats.count(), 4)
        
        self.assertEqual(row_1_seats[0].student.branch.code, "BCA")
        self.assertEqual(row_1_seats[1].student.branch.code, "MCA")
        self.assertEqual(row_1_seats[2].student.branch.code, "BCA")
        self.assertEqual(row_1_seats[3].student.branch.code, "MCA")
