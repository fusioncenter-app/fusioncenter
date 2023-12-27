# apps.py

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plans'

    def ready(self):
        import plans.signals
