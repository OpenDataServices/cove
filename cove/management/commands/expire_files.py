from django.core.management.base import BaseCommand
from cove.input.models import SuppliedData
from django.utils import timezone
from datetime import timedelta
import shutil


class Command(BaseCommand):
    help = 'Delete files that are older than 7 days'

    def handle(self, *args, **options):
        old_data = SuppliedData.objects.filter(created__lt=timezone.now() - timedelta(days=7))
        for supplied_data in old_data:
            try:
                shutil.rmtree(supplied_data.upload_dir())
            except FileNotFoundError:
                continue
