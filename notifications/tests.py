from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import UserProfile
from notifications.models import Notification

class NotificationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Exam Controller user
        self.controller_user = User.objects.create_user(username='controller1', password='password123')
        self.controller_profile, _ = UserProfile.objects.get_or_create(user=self.controller_user, defaults={'role': 'EXAM_CONTROLLER'})
        self.controller_profile.role = 'EXAM_CONTROLLER'
        self.controller_profile.save()
        
        # Create Student user
        self.student_user = User.objects.create_user(username='student1', password='password123')
        self.student_profile, _ = UserProfile.objects.get_or_create(user=self.student_user, defaults={'role': 'STUDENT'})
        self.student_profile.role = 'STUDENT'
        self.student_profile.save()
        
        # Create Notice
        self.notice = Notification.objects.create(
            title="Exam Schedule Release",
            message="Final exam schedule has been published.",
            author=self.controller_user
        )

    def test_exam_controller_can_delete_notice(self):
        self.client.login(username='controller1', password='password123')
        response = self.client.post(f'/notifications/{self.notice.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notification.objects.filter(id=self.notice.id).exists())

    def test_student_cannot_delete_notice(self):
        self.client.login(username='student1', password='password123')
        response = self.client.post(f'/notifications/{self.notice.id}/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(id=self.notice.id).exists())
