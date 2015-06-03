from django.db import models
import uuid
from django.core.urlresolvers import reverse
import os
from django.conf import settings


def upload_to(instance, filename=''):
    return os.path.join(str(instance.pk), filename)


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_url = models.URLField(null=True)
    original_file = models.FileField(upload_to=upload_to)
    current_app = models.CharField(max_length=20)

    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True, null=True)
    
    form_name = models.CharField(
        max_length=20,
        choices=[
            ('upload_form', 'File upload'),
            ('url_form', 'Downloaded from URL'),
            ('text_form', 'Pasted into textarea'),
        ],
        null=True
    )

    def get_absolute_url(self):
        return reverse('cove:explore', args=(self.pk,), current_app=self.current_app)

    def upload_dir(self):
        return os.path.join(settings.MEDIA_ROOT, upload_to(self))

    def upload_url(self):
        return os.path.join(settings.MEDIA_URL, upload_to(self))
