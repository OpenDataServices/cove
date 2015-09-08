from django.db import models
from cove.input.models import SuppliedData

PROCESS_CHOICES = [
    ('fetch', 'Fetch'),
    ('convert', 'Convert'),
    ('staging', 'Pushed to staging'),
    ('live', 'Pushed to live'),
]


class Dataset(models.Model):
    supplied_data = models.OneToOneField(SuppliedData)

    def name(self):
        return self.supplied_data.original_file.name

    def most_recent_process_by_type(self):
        return {type_: Process.objects.filter(type=type_).order_by('-datetime').first() for type_, type_name in PROCESS_CHOICES}


class Process(models.Model):
    dataset = models.ForeignKey(Dataset)
    type = models.CharField(
        max_length=20,
        choices=PROCESS_CHOICES
    )
    datetime = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)
