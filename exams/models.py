from django.db import models
from departments.models import AcademicYear

class Exam(models.Model):
    name = models.CharField(max_length=150) # e.g. DIPLOMA EXAMINATION APRIL 2026
    code = models.CharField(max_length=50, unique=True) # e.g. 2026-04
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exams')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
