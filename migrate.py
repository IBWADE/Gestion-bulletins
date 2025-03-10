import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_bulletins.settings')
django.setup()

from django.core.management import call_command

try:
    call_command("migrate")
    print("✅ Migrations appliquées avec succès !")
except Exception as e:
    print(f"❌ Erreur lors de la migration : {e}")
