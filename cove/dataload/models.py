from django.db import models
from cove.input.models import SuppliedData


class Dataset(models.Model):
    supplied_data = models.OneToOneField(SuppliedData)

    def name(self):
        return self.supplied_data.original_file.name


class ProcessRun(models.Model):
    dataset = models.ForeignKey(Dataset)
    process = models.CharField(
        max_length=20
    )
    datetime = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)
