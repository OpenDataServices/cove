from django.db import models
import uuid
from django.core.urlresolvers import reverse


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_url = models.URLField(null=True)
    original_file = models.FileField()
    current_app = models.CharField(max_length=20)

    def get_absolute_url(self):
        return reverse('cove:explore', args=(self.pk,), current_app=self.current_app)
