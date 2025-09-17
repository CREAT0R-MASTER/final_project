import threading
from django.conf import settings

_thread_locals = threading.local()

def get_current_db():
    return getattr(_thread_locals, 'TENANT_DB', 'default')


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw_db = request.headers.get('X-TENANT-DB', 'default')
        db = f"tenant_{raw_db}" if raw_db != 'default' and not raw_db.startswith('tenant_') else raw_db

        _thread_locals.TENANT_DB = db

        if db != 'default' and db not in settings.DATABASES:
            default_db = settings.DATABASES['default']
            settings.DATABASES[db] = {
                'ENGINE': default_db['ENGINE'],
                'NAME': db,
                'USER': default_db['USER'],
                'PASSWORD': default_db['PASSWORD'],
                'HOST': default_db.get('HOST', 'localhost'),
                'PORT': default_db.get('PORT', '3306'),
                'ATOMIC_REQUESTS': default_db.get('ATOMIC_REQUESTS', False),
                'AUTOCOMMIT': default_db.get('AUTOCOMMIT', True),
                'TIME_ZONE': default_db.get('TIME_ZONE', None),
                'CONN_MAX_AGE': default_db.get('CONN_MAX_AGE', 0),
                'CONN_HEALTH_CHECKS': default_db.get('CONN_HEALTH_CHECKS', False),
                'OPTIONS': default_db.get('OPTIONS', {}),
            }

        return self.get_response(request)
