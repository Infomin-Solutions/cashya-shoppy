from root.models import SiteSetting
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        if SiteSetting.objects.count() == 0:
            SiteSetting.objects.create()
            self.stdout.write(
                self.style.SUCCESS('SiteSetting created Successfully')
            )
        else:
            SiteSetting.objects.create()
            self.stdout.write(
                self.style.SUCCESS('SiteSetting already exists')
            )
