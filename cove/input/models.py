from django.db import models
import uuid
from django.core.urlresolvers import reverse
import os
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from cove.input import get_google_doc
import rfc6266  # (content-disposition header parser)

CONTENT_TYPE_MAP = {
    'application/json': 'json',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'text/csv': 'csv'
}


def upload_to(instance, filename=''):
    return os.path.join(str(instance.pk), filename)


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_url = models.URLField(null=True, max_length=2000)
    original_file = models.FileField(upload_to=upload_to)
    current_app = models.CharField(max_length=20)

    created = models.DateTimeField(auto_now_add=True, null=True)
    modified = models.DateTimeField(auto_now=True, null=True)
    rendered = models.BooleanField(default=False)

    # Last schema version applied to the stored data
    schema_version = models.CharField(max_length=10, default='')
    # Schema version in uploaded/linked file
    data_schema_version = models.CharField(max_length=10, default='')

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
        return reverse('explore', args=(self.pk,), current_app=self.current_app)

    def upload_dir(self):
        return os.path.join(settings.MEDIA_ROOT, upload_to(self))

    def upload_url(self):
        return os.path.join(settings.MEDIA_URL, upload_to(self))

    def is_google_doc(self):
        return self.source_url.startswith('https://docs.google.com/')

    def download(self):
        if self.source_url:
            if self.is_google_doc():
                get_google_doc(self)
            else:
                r = requests.get(self.source_url, headers={'User-Agent': 'Cove (cove.opendataservice.coop)'})
                r.raise_for_status()
                content_type = r.headers.get('content-type', '').split(';')[0].lower()
                file_extension = CONTENT_TYPE_MAP.get(content_type)

                if not file_extension:
                    possible_extension = rfc6266.parse_requests_response(r).filename_unsafe.split('.')[-1]
                    if possible_extension in CONTENT_TYPE_MAP.values():
                        file_extension = possible_extension

                file_name = r.url.split('/')[-1].split('?')[0][:100]
                if file_name == '':
                    file_name = 'file'
                if file_extension:
                    if not file_name.endswith(file_extension):
                        file_name = file_name + '.' + file_extension
                self.original_file.save(
                    file_name,
                    ContentFile(r.content))
        else:
            raise ValueError('No source_url specified.')

    def __repr__(self):
        return "<SuppliedData source_url={} original_file.name={}>".format(
            repr(self.source_url),
            repr(self.original_file.name))
