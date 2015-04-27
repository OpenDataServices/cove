from django.db import models
import uuid
from django.core.urlresolvers import reverse

def make_uuid():
    return str(uuid.uuid4())

class UUIDModel(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, default=make_uuid, editable=False)

    class Meta:
        abstract = True

class SuppliedData(UUIDModel):
    original_data = models.FileField()

    def get_absolute_url(self):
        return reverse('explore', args=(self.pk,))
