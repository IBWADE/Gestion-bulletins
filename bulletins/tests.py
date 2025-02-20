from django.test import TestCase
from .models import Eleve, Matiere, Note, Classe, Etablissement

class EleveModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Création des objets liés
        etablissement= Etablissement.objects.create(nom="Saint Joseph")
        classe = Classe.objects.create(nom="6ème A", etablissement=etablissement)
        matiere = Matiere.objects.create(nom="Maths", coefficient=2)
        eleve = Eleve.objects.create(nom="Doe", prenom="John", classe=classe)
        Note.objects.create(
            eleve=eleve, 
            matiere=matiere, 
            note_devoir=15, 
            note_composition=18
        )

    def test_calcul_rang(self):
        eleve = Eleve.objects.get(nom="Doe")
        self.assertEqual(eleve.calculer_rang(), 1)