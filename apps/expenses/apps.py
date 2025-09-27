from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.expenses'
    verbose_name = 'Spese'

    def ready(self):
        import apps.expenses.signals
