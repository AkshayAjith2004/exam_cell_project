from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile
from departments.models import AcademicYear, Department, Branch

class AcademicYearManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Admin user
        self.admin_user = User.objects.create_user(username="admin_user", password="password123")
        profile_a = UserProfile.objects.get(user=self.admin_user)
        profile_a.role = 'ADMIN'
        profile_a.save()
        
        # Student user (unauthorized for admin actions)
        self.student_user = User.objects.create_user(username="student_user", password="password123")
        profile_s = UserProfile.objects.get(user=self.student_user)
        profile_s.role = 'STUDENT'
        profile_s.save()
        
        # Initial academic years
        self.ay1 = AcademicYear.objects.create(name="2024-2025", is_active=True)
        self.ay2 = AcademicYear.objects.create(name="2025-2026", is_active=False)

    def test_model_activation_and_deactivation(self):
        # Initial state: ay1 is active, ay2 is inactive
        self.assertTrue(self.ay1.is_active)
        self.assertFalse(self.ay2.is_active)
        
        # Activate ay2 - both should now be active
        self.ay2.is_active = True
        self.ay2.save()
        
        self.ay1.refresh_from_db()
        self.ay2.refresh_from_db()
        self.assertTrue(self.ay1.is_active)
        self.assertTrue(self.ay2.is_active)
        
        # Deactivate ay2
        self.ay2.is_active = False
        self.ay2.save()
        
        self.ay2.refresh_from_db()
        self.assertFalse(self.ay2.is_active)

    def test_academic_year_activate_view(self):
        self.client.login(username="admin_user", password="password123")
        
        # Post activate action for ay2
        response = self.client.post(reverse('academic_year_toggle', kwargs={'pk': self.ay2.id}), {
            'status_action': 'activate',
            'next': reverse('dashboard')
        })
        self.assertRedirects(response, reverse('dashboard'))
        
        self.ay1.refresh_from_db()
        self.ay2.refresh_from_db()
        # Both ay1 and ay2 should now be active!
        self.assertTrue(self.ay1.is_active)
        self.assertTrue(self.ay2.is_active)

    def test_academic_year_deactivate_view(self):
        self.client.login(username="admin_user", password="password123")
        
        # Post deactivate action for ay1
        response = self.client.post(reverse('academic_year_toggle', kwargs={'pk': self.ay1.id}), {
            'status_action': 'deactivate',
            'next': reverse('dashboard')
        })
        self.assertRedirects(response, reverse('dashboard'))
        
        self.ay1.refresh_from_db()
        self.assertFalse(self.ay1.is_active)

    def test_academic_year_add_from_dashboard(self):
        self.client.login(username="admin_user", password="password123")
        
        response = self.client.post(reverse('academic_year_add'), {
            'name': '2026-2027',
            'is_active': 'on',
            'next': reverse('dashboard')
        })
        self.assertRedirects(response, reverse('dashboard'))
        
        new_ay = AcademicYear.objects.get(name="2026-2027")
        self.assertTrue(new_ay.is_active)
        
        # Previous active should still remain active!
        self.ay1.refresh_from_db()
        self.assertTrue(self.ay1.is_active)

    def test_dashboard_renders_academic_years_and_controls(self):
        self.client.login(username="admin_user", password="password123")
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('academic_years', response.context)
        self.assertIn('active_academic_year', response.context)
        self.assertEqual(response.context['active_academic_year'], self.ay1)
        
        # Check that Activate and Deactivate buttons and Academic Calendar Years header are present in HTML
        content = response.content.decode('utf-8')
        self.assertIn("Academic Calendar Years", content)
        self.assertIn("Deactivate", content)
        self.assertIn("Activate", content)

    def test_unauthorized_user_blocked(self):
        self.client.login(username="student_user", password="password123")
        
        response = self.client.post(reverse('academic_year_toggle', kwargs={'pk': self.ay2.id}), {
            'status_action': 'activate'
        })
        # Should redirect to dashboard with access denied message
        self.assertRedirects(response, reverse('dashboard'))
        
        # ay2 should still be inactive
        self.ay2.refresh_from_db()
        self.assertFalse(self.ay2.is_active)
