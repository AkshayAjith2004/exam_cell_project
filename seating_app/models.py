from django.db import models
from students.models import Student
from exams.models import Exam
from timetable.models import Timetable
from classrooms.models import Classroom

class SeatingArrangement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='seating_arrangements')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='seating_arrangements')
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='seating_arrangements')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='seating_arrangements')
    row_index = models.PositiveIntegerField()
    col_index = models.PositiveIntegerField()
    seat_number = models.CharField(max_length=50)

    class Meta:
        unique_together = [
            ('classroom', 'timetable', 'row_index', 'col_index'),
            ('student', 'timetable'), # student can only sit once per timetabled exam
        ]

    def __str__(self):
        return f"{self.student.admission_number} - {self.classroom.room_number} (Seat: R{self.row_index}C{self.col_index})"
