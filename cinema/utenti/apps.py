from django.apps import AppConfig

class UtentiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utenti'

#Per usare "signals" per "ProfiloUtente"
    def ready(self):
        import utenti.signals

