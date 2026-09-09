from django.db import models
from exams.models import Exam
from subjects.models import Subject

class Timetable(models.Model):
    SESSION_CHOICES = [
        ('Morning', 'Morning (09:30 AM - 12:30 PM)'),
        ('Afternoon', 'Afternoon (02:00 PM - 05:00 PM)'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')
    exam_date = models.DateField()
    session = models.CharField(max_length=20, choices=SESSION_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    attachment = models.FileField(upload_to='timetables/', null=True, blank=True)

    class Meta:
        unique_together = ('exam', 'subject', 'exam_date', 'session')

    def __str__(self):
        return f"{self.exam.code} - {self.subject.subject_code} ({self.exam_date} {self.session})"
