import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fundoo_notes_app.settings')

application = get_asgi_application()
