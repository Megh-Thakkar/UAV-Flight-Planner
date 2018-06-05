from __future__ import unicode_literals

from django.db import models

# Create your models here.

class KMLFile(models.Model):
    file_path = models.FileField(upload_to='files/', null=True)
    name = models.CharField(max_length=20)
    csv_file = models.FileField(upload_to='csv/', null=True)
    zone_no = models.IntegerField(default=0)
    zone_name = models.CharField(max_length=2, null=True)
    def __unicode__(self):
        return self.name

