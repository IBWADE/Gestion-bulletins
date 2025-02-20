"""
WSGI config for gestion_bulletins project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_bulletins.settings')

application = get_wsgi_application()

# Exécuter les migrations automatiquement au démarrage
try:
    call_command("migrate")
except Exception as e:
    print(f"Erreur lors de la migration : {e}")
