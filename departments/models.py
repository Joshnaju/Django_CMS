from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        db_table = 'department'

    def __str__(self):
        return self.name