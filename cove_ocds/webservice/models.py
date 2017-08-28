from django.db import models
from cove.input.models import SuppliedData

class WebServiceModel(SuppliedData):
    def get_raw_url(self):
        ## super() is a reference to the SuppliedData class
        return reverse('explore_raw', args=(super().pk,), current_app=super().current_app)