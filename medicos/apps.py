from django.apps import AppConfig



class MilenioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicos'

    def ready(self):
        # Importa os signals para garantir que estão registrados
        import medicos.signals_financeiro
