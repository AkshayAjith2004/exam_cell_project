from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EXAM_CONTROLLER', 'Exam Controller'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    photo = models.ImageField(upload_to='profiles/photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        try:
            # Bypass custom property to call save on the db object
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)

# Safe User.profile getter property
@property
def get_user_profile(self):
    try:
        return UserProfile.objects.get(user=self)
    except UserProfile.DoesNotExist:
        role = 'ADMIN' if self.is_superuser or self.is_staff else 'STUDENT'
        return UserProfile.objects.create(user=self, role=role)

User.profile = get_user_profile
