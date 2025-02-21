from django.contrib import admin
from .models import Etablissement, Classe, Eleve, Matiere, Enseignant, Note, AnneeScolaire, NiveauScolaire

admin.site.register(Etablissement)
admin.site.register(Classe)
admin.site.register(Eleve)
admin.site.register(Matiere)
admin.site.register(Enseignant)
admin.site.register(Note)

@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'debut', 'fin')

admin.site.register(NiveauScolaire)
    