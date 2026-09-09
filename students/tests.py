import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from departments.models import Department, Branch
from students.models import Student

class StudentFilterAndUploadTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Computer Science', code='CS')
        self.branch = Branch.objects.create(name='Computer Science', code='CS', department=self.dept)

        # Admin user for authentication
        self.admin_user = User.objects.create_superuser(username='admin', password='password', email='admin@test.com')
        UserProfile.objects.filter(user=self.admin_user).update(role='ADMIN')
        self.client.login(username='admin', password='password')

        # Create sample S3 and S4 students
        u1 = User.objects.create_user(username='stu_s3_1', first_name='ABHISHEK KRISHNAN S S')
        self.s3_student = Student.objects.create(
            user=u1,
            admission_number='CS_S3_A_R1',
            registration_number='REG_S3_001',
            branch=self.branch,
            semester=3,
            batch='A',
            phone='1234567890'
        )

        u2 = User.objects.create_user(username='stu_s4_1', first_name='ABIN VARGHESE')
        self.s4_student = Student.objects.create(
            user=u2,
            admission_number='CS_S4_A_R1',
            registration_number='REG_S4_001',
            branch=self.branch,
            semester=4,
            batch='A',
            phone='1234567890'
        )
        u3 = User.objects.create_user(username='stu_s5_1', first_name='ADITHYA P K')
        self.s5_student = Student.objects.create(
            user=u3,
            admission_number='CS_S5_A_R1',
            registration_number='REG_S5_001',
            branch=self.branch,
            semester=5,
            batch='A',
            phone='1234567890'
        )

    def test_semester_filter(self):
        # Filter sem=3
        res = self.client.get(reverse('student_list'), {'sem': '3'})
        self.assertEqual(res.status_code, 200)
        students = list(res.context['page_obj'])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].semester, 3)

        # Filter sem=4
        res_s4 = self.client.get(reverse('student_list'), {'sem': '4'})
        self.assertEqual(res_s4.status_code, 200)
        students_s4 = list(res_s4.context['page_obj'])
        self.assertEqual(len(students_s4), 1)
        self.assertEqual(students_s4[0].semester, 4)

        # Filter sem=5
        res_s5 = self.client.get(reverse('student_list'), {'sem': '5'})
        self.assertEqual(res_s5.status_code, 200)
        students_s5 = list(res_s5.context['page_obj'])
        self.assertEqual(len(students_s5), 1)
        self.assertEqual(students_s5[0].semester, 5)

    def test_search_query_s3_and_s4(self):
        # Search 'S3'
        res = self.client.get(reverse('student_list'), {'q': 'S3'})
        self.assertEqual(res.status_code, 200)
        students = list(res.context['page_obj'])
        self.assertTrue(any(s.semester == 3 for s in students))

        # Search 's4'
        res_s4 = self.client.get(reverse('student_list'), {'q': 's4'})
        self.assertEqual(res_s4.status_code, 200)
        students_s4 = list(res_s4.context['page_obj'])
        self.assertTrue(any(s.semester == 4 for s in students_s4))

    def test_2_column_csv_upload(self):
        # Test uploading 2-column CSV (Roll No, Name) as per user's screenshot format
        csv_data = "Roll No,Name\n1,ADITHYAN T PRAVEEN\n2,ADITHYAN K P\n"
        csv_file = io.BytesIO(csv_data.encode('utf-8'))
        csv_file.name = 's3_students.csv'

        response = self.client.post(reverse('student_bulk_upload'), {
            'excel_file': csv_file,
            'default_branch': self.branch.id,
            'default_semester': 3,
            'batch': 'A'
        })
        self.assertEqual(response.status_code, 302)

        # Verify students were created with sem 3
        stu1 = Student.objects.filter(user__first_name='ADITHYAN T PRAVEEN').first()
        self.assertIsNotNone(stu1)
        self.assertEqual(stu1.semester, 3)
        self.assertEqual(stu1.branch, self.branch)

        stu2 = Student.objects.filter(user__first_name='ADITHYAN K P').first()
        self.assertIsNotNone(stu2)
        self.assertEqual(stu2.semester, 3)

    def test_edit_student_admission_number(self):
        # Update admission number of s3_student
        res = self.client.post(reverse('student_edit', args=[self.s3_student.pk]), {
            'first_name': self.s3_student.user.first_name,
            'last_name': 'UPDATED',
            'email': 'updated@test.com',
            'phone': '9999999999',
            'admission_number': 'NEW_ADM_123',
            'registration_number': 'REG_NEW_123',
            'branch': self.branch.id,
            'semester': 3,
            'batch': 'A'
        })
        self.assertEqual(res.status_code, 302)
        self.s3_student.refresh_from_db()
        self.assertEqual(self.s3_student.admission_number, 'NEW_ADM_123')

    def test_multi_batch_upload_in_single_file(self):
        # CSV with Batch A (Roll 1..15) and Batch B (Roll 1..10)
        batch_a_rows = "\n".join([f"{i},STUDENT_A_{i}" for i in range(1, 16)])
        batch_b_rows = "\n".join([f"{i},STUDENT_B_{i}" for i in range(1, 11)])
        csv_data = f"Roll No,Name\n{batch_a_rows}\nBATCH B\nRoll No,Name\n{batch_b_rows}\n"
        csv_file = io.BytesIO(csv_data.encode('utf-8'))
        csv_file.name = 's3_both_batches.csv'

        res = self.client.post(reverse('student_bulk_upload'), {
            'excel_file': csv_file,
            'default_branch': self.branch.id,
            'default_semester': 3,
            'batch': 'AUTO'
        })
        self.assertEqual(res.status_code, 302)

        stu_a = Student.objects.filter(user__first_name='STUDENT_A_1').first()
        self.assertIsNotNone(stu_a)
        self.assertEqual(stu_a.batch, 'A')

        stu_b = Student.objects.filter(user__first_name='STUDENT_B_1').first()
        self.assertIsNotNone(stu_b)
        self.assertEqual(stu_b.batch, 'B')

    def test_optional_no_batch_upload(self):
        # Test uploading CSV without specifying batch (No Batch / NONE)
        csv_data = "Roll No,Name\n1,TEST NO BATCH STU 1\n2,TEST NO BATCH STU 2\n"
        csv_file = io.BytesIO(csv_data.encode('utf-8'))
        csv_file.name = 'no_batch_students.csv'

        res = self.client.post(reverse('student_bulk_upload'), {
            'excel_file': csv_file,
            'default_branch': self.branch.id,
            'default_semester': 3,
            'batch': 'NONE'
        })
        self.assertEqual(res.status_code, 302)

        stu = Student.objects.filter(user__first_name='TEST NO BATCH STU 1').first()
        self.assertIsNotNone(stu)
        self.assertIsNone(stu.batch)
        self.assertEqual(stu.semester, 3)




