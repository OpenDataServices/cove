from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect
from django.forms import ModelForm
from datainput.models import SuppliedData
from django.views.generic.edit import CreateView
from django.core.files.base import ContentFile
import requests

class UploadForm(ModelForm):
     class Meta:
         model = SuppliedData
         fields = ['original_file']
         labels = {
            'original_file': _('Upload a file')
         }

class UrlForm(ModelForm):
     class Meta:
         model = SuppliedData
         fields = ['source_url']
         labels = {
            'source_url': _('Supply a URL')
         }

# Create your views here.
input = CreateView.as_view(model=SuppliedData, fields=['original_data'])
def input(request):
    form_classes = {
        'upload_form': UploadForm,
        'url_form': UrlForm,
    }
    forms = {form_name: form_class() for form_name, form_class in form_classes.items()}
    if request.method == 'POST':
        if 'source_url' in request.POST:
            form_name = 'url_form'
        else:
            form_name = 'upload_form'
        form = form_classes[form_name](request.POST, request.FILES)
        forms[form_name] = form
        if form.is_valid():
            data = form.save()
            if form_name == 'url_form':
                r = requests.get(data.source_url)
                # FIXME!!!! - test.json is a bad name, and this loads into memory
                data.original_file.save('test.json', ContentFile(r.content))
            return redirect(data.get_absolute_url())
    return render(request, 'datainput/input.html', {'forms':forms})
