from __future__ import unicode_literals

from django.db import models

# Create your models here.

class KMLFile(models.Model):
    file_path = models.FileField(upload_to='files/', null=True)
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name

