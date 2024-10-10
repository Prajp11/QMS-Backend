# Create your models here.
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    received_date = models.DateTimeField(auto_now_add=True)
    quality_status = models.CharField(max_length=50)
    rejected_reason = models.TextField(null=True, blank=True)

    def _str_(self):  # Fixed method name
        return self.name

