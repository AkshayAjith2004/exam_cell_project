from django.db import models
from departments.models import Department, Branch

class Subject(models.Model):
    subject_code = models.CharField(max_length=50, unique=True)
    subject_name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    semester = models.PositiveIntegerField()
    faculty = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subjects')

    def __str__(self):
        branch_str = f" [{self.branch.code}]" if self.branch else ""
        return f"{self.subject_code} - {self.subject_name}{branch_str}"

