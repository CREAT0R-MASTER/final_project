# core/db_router.py

from core.middleware import get_current_db

class TenantRouter:
    def db_for_read(self, model, **hints):
        return get_current_db()

    def db_for_write(self, model, **hints):
        return get_current_db()

    def allow_relation(self, obj1, obj2, **hints):
        db = get_current_db()
        return db == obj1._state.db == obj2._state.db

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default' or db.startswith("tenant_")
