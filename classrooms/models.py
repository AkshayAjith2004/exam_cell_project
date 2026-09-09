from django.db import models

class Classroom(models.Model):
    room_number = models.CharField(max_length=50, unique=True)
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=50)
    rows = models.PositiveIntegerField(help_text="Number of rows in seat grid")
    columns = models.PositiveIntegerField(help_text="Number of columns in seat grid")
    capacity = models.PositiveIntegerField(editable=False)
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.capacity = self.rows * self.columns
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.room_number} - {self.building} (Cap: {self.capacity})"
