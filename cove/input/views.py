from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect
from django import forms
from cove.input.models import SuppliedData
from django.core.files.base import ContentFile
import requests


class UploadForm(forms.ModelForm):
    class Meta:
        model = SuppliedData
        fields = ['original_file']
        labels = {
            'original_file': _('Upload a file (.json, .csv, .xlsx)')
        }


class UrlForm(forms.ModelForm):
    class Meta:
        model = SuppliedData
        fields = ['source_url']
        labels = {
            'source_url': _('Supply a URL')
        }


class TextForm(forms.Form):
    paste = forms.CharField(label=_('Paste (JSON only)'), widget=forms.Textarea)


def input(request):
    form_classes = {
        'upload_form': UploadForm,
        'url_form': UrlForm,
        'text_form': TextForm,
    }
    forms = {form_name: form_class() for form_name, form_class in form_classes.items()}

    request_data = None
    if "source_url" in request.GET:
        request_data = request.GET
    if request.POST:
        request_data = request.POST
    if request_data:
        if 'source_url' in request_data:
            form_name = 'url_form'
        elif 'paste' in request_data:
            form_name = 'text_form'
        else:
            form_name = 'upload_form'
        form = form_classes[form_name](request_data, request.FILES)
        forms[form_name] = form
        if form.is_valid():
            if form_name == 'text_form':
                data = SuppliedData()
            else:
                data = form.save(commit=False)
            data.current_app = request.current_app
            data.form_name = form_name
            data.save()
            if form_name == 'url_form':
                try:
                    data.download()
                except requests.ConnectionError as err:
                    return render(request, 'error.html', context={
                        'sub_title': _("Sorry we got a ConnectionError whilst trying to download that file"),
                        'link': 'index',
                        'link_text': _('Try Again'),
                        'msg': _(str(err) + '\n\n Common reasons for this error include supplying a local development url that our servers can\'t access, or misconfigured SSL certificates.')
                    })
                except requests.HTTPError as err:
                    return render(request, 'error.html', context={
                        'sub_title': _("Sorry we got a HTTP Error whilst trying to download that file"),
                        'link': 'index',
                        'link_text': _('Try Again'),
                        'msg': _(str(err) + '\n\n If you can access the file through a browser then the problem may be related to permissions, or you may be blocking certain user agents.')
                    })
            elif form_name == 'text_form':
                data.original_file.save('test.json', ContentFile(form['paste'].value()))
            return redirect(data.get_absolute_url())

    return render(request, 'datainput/input.html', {'forms': forms})
