from django.contrib import admin
from .models import Etablissement, Classe, Eleve, Matiere, Enseignant, Note, AnneeScolaire, NiveauScolaire, Echeance, NoteArchive, PaiementRestauré, FraisRestauré

admin.site.register(Etablissement)
admin.site.register(Classe)
admin.site.register(Eleve)
admin.site.register(Matiere)
admin.site.register(Enseignant)
admin.site.register(Note)
admin.site.register(NoteArchive)
admin.site.register(PaiementRestauré)
admin.site.register(FraisRestauré)



@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'debut', 'fin')

admin.site.register(NiveauScolaire)
admin.site.register(Echeance)
    