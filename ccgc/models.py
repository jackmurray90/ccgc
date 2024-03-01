from django.contrib.auth.models import User
from django.db import models


class CsvFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="csv_files")
    file = models.FileField()
    filename = models.CharField(max_length=500)
