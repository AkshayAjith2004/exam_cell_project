from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date

from departments.models import Department, Branch, AcademicYear
from classrooms.models import Classroom
from subjects.models import Subject
from students.models import Student
from teachers.models import Teacher
from exams.models import Exam
from timetable.models import Timetable

class Command(BaseCommand):
    help = 'Seeds the database with initial CE Poonjar exam seating data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")

        # 1. Create Superuser (Admin)
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@cep.ac.in',
                'first_name': "System",
                'last_name': "Administrator",
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            admin_user.profile.role = 'ADMIN'
            admin_user.profile.save()
            self.stdout.write("Created Admin superuser: admin / admin123")

        # 2. Create Exam Controller
        ctrl_user, created = User.objects.get_or_create(
            username='controller',
            defaults={
                'email': 'controller@cep.ac.in',
                'first_name': "Exam",
                'last_name': "Controller"
            }
        )
        if created:
            ctrl_user.set_password('ctrl123')
            ctrl_user.save()
            ctrl_user.profile.role = 'EXAM_CONTROLLER'
            ctrl_user.profile.save()
            self.stdout.write("Created Controller user: controller / ctrl123")

        # 3. Create Academic Year
        ay, _ = AcademicYear.objects.get_or_create(
            name="2025-2026",
            defaults={'is_active': True}
        )
        self.stdout.write("Created Academic Year: 2025-2026")

        # 4. Create Departments
        dept_bca, _ = Department.objects.get_or_create(code="BCA", defaults={'name': "Bachelor of Computer Applications"})
        dept_mca, _ = Department.objects.get_or_create(code="MCA", defaults={'name': "Master of Computer Applications"})
        dept_btech, _ = Department.objects.get_or_create(code="BTECH", defaults={'name': "Bachelor of Technology"})
        dept_dip, _ = Department.objects.get_or_create(code="DIPLOMA", defaults={'name': "Diploma in Engineering"})
        self.stdout.write("Created 4 Departments: BCA, MCA, BTECH, DIPLOMA")

        # 5. Create Branches
        branch_bca, _ = Branch.objects.get_or_create(code="BCA", department=dept_bca, defaults={'name': "Computer Applications"})
        branch_mca, _ = Branch.objects.get_or_create(code="MCA", department=dept_mca, defaults={'name': "Computer Applications"})
        branch_cs, _ = Branch.objects.get_or_create(code="CS", department=dept_btech, defaults={'name': "Computer Science & Engineering"})
        branch_ec, _ = Branch.objects.get_or_create(code="EC", department=dept_btech, defaults={'name': "Electronics & Communication"})
        self.stdout.write("Created Branches: BCA, MCA, CS, EC")

        # 6. Create Classrooms
        self.stdout.write("Classrooms registry left empty for manual entries.")

        # 7. Create Teachers
        self.stdout.write("Teachers registry left empty for manual entries (preserving EMP1000).")

        # 8. Create Subjects
        self.stdout.write("Subjects registry left empty for manual entries.")

        self.stdout.write("Database seeding complete. Student registry left empty for manual signups.")

        # 10. Create active Exam Sessions
        exam, _ = Exam.objects.get_or_create(
            code="INT-2026",
            defaults={'name': "Internal Exam 2026", 'academic_year': ay, 'is_active': True}
        )

        self.stdout.write("Database seeding complete. Timetable slots were left empty for manual inputs.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
