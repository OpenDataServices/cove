from django.db import models
from cove.input.models import SuppliedData


class Dataset(models.Model):
    supplied_data = models.OneToOneField(SuppliedData)
    name = models.CharField(unique=True, max_length=50)
    deleted = models.BooleanField(default=False)


class ProcessRun(models.Model):
    dataset = models.ForeignKey(Dataset)
    process = models.CharField(
        max_length=20
    )
    datetime = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=True)
