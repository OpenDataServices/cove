from django.conf import settings


class CoveConfigCurrentApp():
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.current_app = settings.COVE_CONFIG['app_name']
