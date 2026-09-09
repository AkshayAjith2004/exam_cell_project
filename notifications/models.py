from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_authored')

    def __str__(self):
        return f"{self.title} (by {self.author.username} on {self.created_at.strftime('%Y-%m-%d')})"
