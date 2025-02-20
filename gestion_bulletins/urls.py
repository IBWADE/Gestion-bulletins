from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('bulletins/', include('bulletins.urls')),  # Incluez vos URLs d'application ici
    path('accounts/', include('django.contrib.auth.urls')),
]


# Serveur de développement : servir les fichiers médias
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)