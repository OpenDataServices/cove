from django.db import models

class SuppliedData(models.Model):
    original_data = models.FileField()

    def get_absolute_url(self):
        return '/fixme'
