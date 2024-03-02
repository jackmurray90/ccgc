from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models
import os


class CsvFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="csv_files")
    file = models.FileField()
    filename = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField()

@receiver(models.signals.post_delete, sender=CsvFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
