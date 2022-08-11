from django.apps import AppConfig
import Jobs.updater

class SharedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Shared'

    def ready(self) -> None:
        Jobs.updater.start()
        return super().ready()
