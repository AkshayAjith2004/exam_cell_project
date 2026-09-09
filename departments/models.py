from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True) # e.g. BCA, MCA, BTECH

    def __str__(self):
        return f"{self.name} ({self.code})"

class Branch(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20) # e.g. CS, EC, General
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='branches')

    class Meta:
        unique_together = ('code', 'department')

    def __str__(self):
        return f"{self.department.code} - {self.name} ({self.code})"

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g. 2025-2026
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"
