from django.shortcuts import render
from django import forms
from datainput.models import SuppliedData
from django.views.generic.edit import CreateView

# Create your views here.
input = CreateView.as_view(model=SuppliedData, fields=['original_data'])
