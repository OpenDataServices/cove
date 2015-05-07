from django.conf import settings


class CoveConfigByNamespaceMiddleware():
    def get_cove_config(self, request):
        namespace = request.resolver_match.namespace
        request.current_app = namespace
        by_namespace = settings.COVE_CONFIG_BY_NAMESPACE
        return {key: by_namespace[key][namespace] if namespace in by_namespace[key] else by_namespace[key]['default'] for key in by_namespace}

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.cove_config = self.get_cove_config(request)
