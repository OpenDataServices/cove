from django.db import models
import uuid
from django.core.urlresolvers import reverse


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_url = models.URLField(null=True)
    original_file = models.FileField()

    def get_absolute_url(self):
        return reverse('explore', args=(self.pk,))
