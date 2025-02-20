"""
WSGI config for gestion_bulletins project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_bulletins.settings')

application = get_wsgi_application()

# Exécuter les migrations automatiquement au démarrage
try:
    call_command("migrate")
except Exception as e:
    print(f"Erreur lors de la migration : {e}")

# Création automatique du superutilisateur (exécute une seule fois)
User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "wibrahima@gmail.com", "P@lfren1er")
    print("Superutilisateur créé avec succès !")    
