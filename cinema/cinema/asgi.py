import os
from django.core.asgi import get_asgi_application
from .routing import application as channels_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema.settings')

django_asgi_app = get_asgi_application()

application = channels_application
