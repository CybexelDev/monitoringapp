from django.apps import AppConfig


class MonitoringappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoringapp"

    def ready(self):
        from . import notification_signals
        from . import master_admin_notification_signals