import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_bulletins.settings')

application = get_wsgi_application()

# Exécuter la migration via le script
import migrate
