from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Window, F, Sum, FloatField, ExpressionWrapper, Avg
from django.db.models.functions import Rank
from decimal import Decimal
from django.conf import settings
from django.core.validators import FileExtensionValidator, RegexValidator
from django.utils.timezone import now
from django.templatetags.static import static
from django.utils import timezone

# Modele CustomUser
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='parent')

    # Ajouter des related_name personnalisés pour éviter les conflits
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name="custom_user_set",
        related_query_name="custom_user"
    )


class Absence(models.Model):
    SEMESTRES = (
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    )

    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, related_name='absences')
    matiere = models.ForeignKey('Matiere', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=now)
    motif = models.CharField(max_length=255, null=True, blank=True)
    semestre = models.PositiveIntegerField(choices=SEMESTRES, default=1, verbose_name="Semestre")  # ✅ Ajout du semestre

    def __str__(self):
        return f"{self.eleve} - {self.date} - {self.get_semestre_display()}"

    
    
# Modele Notification
class Notification(models.Model):
    utilisateur = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=100)
    message = models.TextField()
    date = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"   
    

# Annee scolaire
class AnneeScolaire(models.Model):
    nom = models.CharField(max_length=9, unique=True)  # Format : "2023-2024"
    debut = models.DateField()
    fin = models.DateField()

    def __str__(self):
        return self.nom   


# Niveau Scolaire    
#Ajouter un modèle NiveauScolaire
#Ce modèle permettra de définir les règles pour chaque niveau (sixième, cinquième, etc.).
class NiveauScolaire(models.Model):
    NOM_NIVEAUX = [
        ('6e', 'Sixième'),
        ('5e', 'Cinquième'),
        ('4e', 'Quatrième'),
        ('3e', 'Troisième'),
    ]

    nom = models.CharField(max_length=10, choices=NOM_NIVEAUX, unique=True)
    ordre = models.IntegerField(default=1, unique=True)   # Ajout du champ ordre

    matieres_obligatoires = models.ManyToManyField('Matiere', related_name="niveaux_obligatoires")
    matieres_optionnelles = models.ManyToManyField('Matiere', related_name="niveaux_optionnels", blank=True)

    def __str__(self):
        return self.get_nom_display()
    





# Modèle Etablissement
class Etablissement(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=200)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    telephone = models.CharField(
        max_length=20,
        default="+2210000000",
        validators=[RegexValidator(regex=r'^\+?\d{9,15}$', message="Entrez un numéro valide.")],
        help_text="Format recommandé : +221XXXXXXXXX"
    )
    logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    annee_scolaire = models.ForeignKey(
        AnneeScolaire,
        on_delete=models.CASCADE,
        related_name="etablissements",
        null=True,
        blank=True
    )
    choix_matiere_quatrieme = models.BooleanField(
        default=False,
        help_text="Si activé, les élèves de 4ème choisiront entre PC et une langue, comme en 3ème."
    )

    # Ajout des champs IA et IEF
    ia = models.CharField(max_length=100, verbose_name="Inspection Académique", blank=True, null=True)
    ief = models.CharField(max_length=100, verbose_name="Inspection de l'Éducation et de la Formation", blank=True, null=True)

    def __str__(self):
        return f"{self.nom} ({self.annee_scolaire})"



    
    
# Modele Classe
#Associer un NiveauScolaire aux Classe
#Ajout d'un champ dans le modèle Classe
class Classe(models.Model):
    nom = models.CharField(max_length=100)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE)
    niveau = models.ForeignKey(NiveauScolaire, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.niveau})"
    

    
    
# Modele Eleve
class Eleve(models.Model):
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enfants',
        limit_choices_to={'role': 'parent'},
        null=True, blank=True
    )
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    classe = models.ForeignKey('Classe', on_delete=models.SET_NULL, null=True, blank=True)     
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=255, null=True, blank=True, verbose_name="Lieu de naissance")
    matricule = models.CharField(max_length=50, null=True, blank=True, unique=True, verbose_name="Matricule")

    class Meta:
        indexes = [
            models.Index(fields=['classe', 'nom']),
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def moyenne_generale(self):
        notes = Note.objects.filter(eleve=self)
        total = sum(note.points_matiere for note in notes)
        coefficients = sum(note.matiere.coefficient for note in notes)
        
        if coefficients == 0:
            return Decimal('0.00')
        
        moyenne = Decimal(total) / Decimal(coefficients)
        return moyenne.quantize(Decimal('0.00'))    
    
    def moyenne_generale_semestre(self, semestre):
        # Récupérer les notes de l'élève pour le semestre spécifié
        notes = Note.objects.filter(eleve=self, semestre=semestre).annotate(
            points_matiere=ExpressionWrapper(
                ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                output_field=models.FloatField()
            )
        )
        total_points = sum(note.points_matiere for note in notes)
        total_coefficients = sum(note.matiere.coefficient for note in notes)
        return total_points / total_coefficients if total_coefficients > 0 else 0

    def moyenne_annuelle(self):
        # Calculer la moyenne annuelle en combinant les deux semestres
        moyenne_s1 = self.moyenne_generale_semestre(1)
        moyenne_s2 = self.moyenne_generale_semestre(2)
        return (moyenne_s1 + moyenne_s2) / 2 if moyenne_s1 > 0 and moyenne_s2 > 0 else 0

    def passe_classe(self):
        # Déterminer si l'élève passe en classe supérieure
        seuil_passage = 10  # Seuil configurable
        return self.moyenne_annuelle() >= seuil_passage

    def calculer_rang(self):
        from .models import Note  # Import circulaire à gérer
        return Eleve.objects.filter(classe=self.classe).annotate(
            total_points=Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                )
            )
        ).annotate(
            rang=Window(
                expression=Rank(),
                order_by=F('total_points').desc()
            )
        ).get(id=self.id).rang
    
    @property
    def niveau(self):
        return self.classe.niveau if self.classe else None
   

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    
# Modele Matiere
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    coefficient = models.IntegerField()

    def __str__(self):
        return self.nom
    

# Modele Choix Matiere
# Ajouter un modèle pour stocker les matières choisies par les élèves en 4e et 3e
class ChoixMatiere(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="choix_matieres")
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('eleve', 'matiere')  # Empêche un élève de choisir deux fois la même matière

    def __str__(self):
        return f"{self.eleve} a choisi {self.matiere}"


    
    
# Modele Enseignant
class Enseignant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE) 
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    matieres = models.ManyToManyField(Matiere)
    classes = models.ManyToManyField('Classe', related_name='enseignants', blank=True)  # Ajoutez cette ligne    

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    

# Modele Note
class Note(models.Model):
    SEMESTRES = (
        (1, 'Semestre 1'),
        (2, 'Semestre 2'),
    )
    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE)
    matiere = models.ForeignKey('Matiere', on_delete=models.CASCADE)
    note_devoir = models.FloatField(default=0, verbose_name="Note des devoirs")
    note_composition = models.FloatField(default=0, verbose_name="Note des compositions")
    semestre = models.PositiveIntegerField(choices=SEMESTRES, default=1, verbose_name="Semestre")
    date = models.DateField(auto_now_add=True)
    _points_matiere = None  # Variable interne pour stocker une valeur forcée
    

    @property
    def moyenne_matiere(self):  # ✅ Reste une property
        return (self.note_devoir + self.note_composition) / 2

    @property
    def points_matiere(self):
        return self.moyenne_matiere * self.matiere.coefficient

    @points_matiere.setter
    def points_matiere(self, value):
        self._points_matiere = value  # Permet d'affecter manuellement une valeur

    def reset_points_matiere(self):
        """Réinitialise points_matiere pour revenir au calcul automatique"""
        self._points_matiere = None
        
    def clean(self):
        errors = {}
        if not self.matiere:
            errors['matiere'] = "Une matière doit être associée à cette note."
        if not (0 <= self.note_devoir <= 20):
            errors['note_devoir'] = "La note doit être entre 0 et 20."
        if not (0 <= self.note_composition <= 20):
            errors['note_composition'] = "La note doit être entre 0 et 20."

        if errors:
            raise ValidationError(errors)
            
    def __str__(self):
        return f"{self.eleve} - {self.matiere} - Semestre {self.semestre} : Devoirs={self.note_devoir}, Compo={self.note_composition}"
    

# Modele Archive
class Archive(models.Model):
    annee_scolaire = models.CharField(max_length=9)  # Format : "2023-2024"
    eleve = models.ForeignKey('Eleve', on_delete=models.SET_NULL, null=True, blank=True)
    classe = models.CharField(max_length=100, blank=True, null=True)
    etablissement = models.CharField(max_length=100, blank=True, null=True)
    notes = models.JSONField(blank=True, null=True)
    absences = models.JSONField(blank=True, null=True)
    moyenne_annuelle = models.FloatField(default=0.0)
    passe_classe = models.BooleanField(default=False)
    date_archivage = models.DateTimeField(default=timezone.now)  # Date d'archivage

    # ✅ Ajout des nouveaux champs demandés
    total_points_semestre_1 = models.FloatField(default=0)
    total_points_semestre_2 = models.FloatField(default=0)
    mention_semestre_1 = models.CharField(max_length=20, null=True, blank=True)
    mention_semestre_2 = models.CharField(max_length=20, null=True, blank=True)
    mention_annuelle = models.CharField(max_length=20, null=True, blank=True)
    rang_semestre_1 = models.IntegerField(null=True, blank=True)
    rang_semestre_2 = models.IntegerField(null=True, blank=True)
    rang_annuel = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.eleve} - {self.annee_scolaire}"


    

