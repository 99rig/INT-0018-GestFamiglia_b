"""
Database Router per gestire database multipli.
L'app 'updates' usa un database SQLite separato che può essere committato.
Tutte le altre app usano PostgreSQL.
"""


class UpdatesDBRouter:
    """
    Router che dirige tutte le operazioni del modello AppVersion
    e dell'app updates verso il database SQLite dedicato
    """

    def db_for_read(self, model, **hints):
        """Suggerisce il database da usare per la lettura"""
        if model._meta.app_label == 'updates':
            return 'updates_db'
        return None

    def db_for_write(self, model, **hints):
        """Suggerisce il database da usare per la scrittura"""
        if model._meta.app_label == 'updates':
            return 'updates_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permette relazioni solo se i modelli sono nello stesso database.
        Updates app non dovrebbe avere relazioni con altre app.
        """
        db_set = {'default', 'updates_db'}
        if obj1._meta.app_label == 'updates' or obj2._meta.app_label == 'updates':
            # Non permettere relazioni tra updates e altre app
            return obj1._meta.app_label == obj2._meta.app_label
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determina se permettere la migrazione di un modello su un database
        """
        if app_label == 'updates':
            # updates app migra solo su updates_db
            return db == 'updates_db'
        elif db == 'updates_db':
            # Solo updates app può migrare su updates_db
            return False
        return None