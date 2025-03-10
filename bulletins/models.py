import json
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
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, timedelta, datetime
from .utils import generer_echeances_pour_eleve  # Importer la fonction
from dateutil.relativedelta import relativedelta




# Modele CustomUser
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='parent')

    # Ajouter des méthodes pour vérifier le rôle facilement
    def is_admin(self):
        return self.role == 'admin'

    def is_enseignant(self):
        return self.role == 'enseignant'

    def is_parent(self):
        return self.role == 'parent'

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


# modele Absence
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
    IMPORTANCE_CHOICES = [
        ('faible', 'Faible'),
        ('normale', 'Normale'),
        ('importance', 'Importance'),
    ]

    utilisateur = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=100)
    message = models.TextField()
    date = models.DateTimeField(default=now)
    importance = models.CharField(max_length=10, choices=IMPORTANCE_CHOICES, default='normale')
    lue = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username} ({self.importance})"

    

# modele Annee scolaire
class AnneeScolaire(models.Model):
    nom = models.CharField(max_length=9, unique=True)  # Format : "2023-2024"
    debut = models.DateField()
    fin = models.DateField()

    def clean(self):
     if self.fin <= self.debut:
        raise ValidationError("La date de fin doit être après la date de début.")
     
    @classmethod
    def get_annee_scolaire_en_cours(cls):
        aujourdhui = timezone.now().date()
        return cls.objects.filter(debut__lte=aujourdhui, fin__gte=aujourdhui).first() 


    def __str__(self):
        return self.nom   


# Niveau Scolaire    
#Ajouter un modèle NiveauScolaire
#Ce modèle permettra de définir les règles pour chaque niveau (sixième, cinquième, etc.).
class NiveauScolaire(models.Model):
    NOM_NIVEAUX = [
        ('6e', '6ᵉ (Sixième)'),  
        ('5e', '5ᵉ (Cinquième)'),
        ('4e', '4ᵉ (Quatrième)'),
        ('3e', '3ᵉ (Troisième)'),
        ('2nde', '2ⁿᵈᵉ (Seconde)'),  # "nde" en exposant
        ('1ere', '1ʳᵉ (Première)'),  # "re" en exposant
        ('Tle', 'Tᵉʳᵐ (Terminale)')  # Abréviation Terminale
    ]

    nom = models.CharField(max_length=10, choices=NOM_NIVEAUX, unique=True)
    ordre = models.IntegerField(null=True, blank=True)  # Ordre des niveaux

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
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    classe = models.ForeignKey('Classe', on_delete=models.SET_NULL, null=True, blank=True)     
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default='M')
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
    
    def solde_restant(self):
        """Calcule le montant total restant à payer par l'élève en incluant toutes les mensualités dues."""

        # Récupérer l'année scolaire en cours
        annee_scolaire_en_cours = self.classe.etablissement.annee_scolaire

        if not annee_scolaire_en_cours:
            return Decimal('0.00')

        # ✅ 1. Calcul des frais de scolarité (inscription, autres frais)
        total_frais_scolarite = self.classe.frais.filter(
            type_frais__in=['inscription', 'autre'],
            annee_scolaire=annee_scolaire_en_cours
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0.00')

        # ✅ 2. Calcul des mensualités dues
        frais_mensuels = self.classe.frais.filter(
            type_frais='mensualite',
            annee_scolaire=annee_scolaire_en_cours
        ).first()

        montant_mensualite = frais_mensuels.montant if frais_mensuels else Decimal('0.00')

        date_debut_mensualites = (annee_scolaire_en_cours.debut + relativedelta(months=1)).replace(day=5)  
        date_actuelle = date.today()

        mensualites_dues = []
        date_mensualite = date_debut_mensualites

        while date_mensualite < annee_scolaire_en_cours.fin.replace(day=5):  # Aller jusqu'à juin inclus

            mensualites_dues.append(date_mensualite)
            date_mensualite += relativedelta(months=1)

        total_mensualites_dues = len(mensualites_dues) * montant_mensualite

        # ✅ 3. Total des paiements effectués
        total_paye = self.paiements.aggregate(
            total=Sum('montant_paye')
        )['total'] or Decimal('0.00')

        # ✅ 4. Calcul final du solde restant
        solde_total = (total_frais_scolarite + total_mensualites_dues) - total_paye      

        return solde_total


    def echeances_impayees(self):
        """Retourne les échéances impayées de l'élève."""
        return self.echeances.filter(statut='impaye')
    
    def a_un_paiement_retroactif(self):
        """
        Vérifie si l'élève a déjà un paiement rétroactif payé.
        """
        return self.paiements.filter(est_retroactif=True, statut='paye').exists()

    def get_paiement_retroactif(self):
        """
        Retourne le premier paiement rétroactif payé de l'élève.
        """
        return self.paiements.filter(est_retroactif=True, statut='paye').first()
    
    def a_paiements_en_retard(self):
        return self.paiements.filter(date_echeance__lt=now(), statut='impaye').exists()
   

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
  
    
# Modele Frais
class Frais(models.Model):
    TYPE_FRAIS_CHOICES = [
        ('inscription', 'Frais d\'inscription'),
        ('mensualite', 'Mensualité'),
        ('autre', 'Autre frais'),
    ]

    type_frais = models.CharField(max_length=20, choices=TYPE_FRAIS_CHOICES, default='mensualite')
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant à payer")
    classe = models.ForeignKey('Classe', on_delete=models.CASCADE, related_name='frais', null=True, blank=True)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE, related_name='frais')
    description = models.TextField(blank=True, null=True, help_text="Description du frais (optionnel)")

    class Meta:
        unique_together = ('type_frais', 'annee_scolaire', 'classe')

    def est_paye_par(self, eleve):
        """Vérifie si l'élève a payé ce frais."""
        total_paye = self.paiements.filter(eleve=eleve).aggregate(
            total=models.Sum('montant_paye')
        )['total'] or Decimal('0.00')

        return total_paye >= self.montant

    def __str__(self):
        return f"{self.get_type_frais_display()} - {self.montant} FCFA ({self.classe})"
    
    
# Modele Paiement
class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile', 'Mobile Money'),
    ]

    STATUT_PAIEMENT_CHOICES = [
        ('paye', 'Payé'),
        ('partiel', 'Partiel'),
        ('impaye', 'Impayé'),
    ]

    MOIS_CHOICES = [
        (1, 'Janvier'),
        (2, 'Février'),
        (3, 'Mars'),
        (4, 'Avril'),
        (5, 'Mai'),
        (6, 'Juin'),
        (7, 'Juillet'),
        (8, 'Août'),
        (9, 'Septembre'),
        (10, 'Octobre'),
        (11, 'Novembre'),
        (12, 'Décembre'),
    ]

    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, related_name='paiements')
    frais = models.ForeignKey('Frais', on_delete=models.CASCADE, related_name='paiements')
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    date_paiement = models.DateField(default=timezone.now, verbose_name="Date de paiement")
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes')
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='paye')
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Référence du paiement (ex: numéro de chèque)")
    mois = models.IntegerField(choices=MOIS_CHOICES, blank=True, null=True, help_text="Mois concerné (pour les paiements mensuels)")
    est_anticipation = models.BooleanField(default=False, verbose_name="Paiement anticipé")
    est_retroactif = models.BooleanField(default=False, verbose_name="Paiement rétroactif")
    nombre_mois = models.PositiveIntegerField(default=1, verbose_name="Nombre de mois concernés")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='paiements')

    def __str__(self):
        return f"{self.eleve} - {self.frais} - {self.montant_paye} FCFA"

# Modele echeance
class Echeance(models.Model):
    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, related_name='echeances')
    frais = models.ForeignKey('Frais', on_delete=models.CASCADE, related_name='echeances')
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    montant_du = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant dû")
    statut = models.CharField(max_length=20, choices=Paiement.STATUT_PAIEMENT_CHOICES, default='impaye')

    def __str__(self):
        return f"{self.eleve} - {self.frais} - {self.date_echeance}"
    

# Signal pour détecter les changements de classe
@receiver(post_save, sender=Eleve)
def mettre_a_jour_echeances(sender, instance, **kwargs):
    if instance.pk:  # Vérifie que l'élève existe déjà dans la base de données
        try:
            ancien_eleve = Eleve.objects.get(pk=instance.pk)
            if ancien_eleve.classe != instance.classe:  # Vérifie si la classe a changé
                # Supprimer les échéances existantes
                instance.echeances.all().delete()

                # Régénérer les échéances pour la nouvelle classe (si elle existe)
                if instance.classe:
                    from .utils import generer_echeances_pour_eleve
                    generer_echeances_pour_eleve(instance)
        except Eleve.DoesNotExist:
            pass   
    
    
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
    

# Modele Emploi du temps
class EmploiDuTemps(models.Model):
    classe = models.ForeignKey('Classe', on_delete=models.CASCADE)
    enseignant = models.ForeignKey('Enseignant', on_delete=models.CASCADE)
    matiere = models.ForeignKey('Matiere', on_delete=models.CASCADE)   
    jour = models.CharField(max_length=10, choices=[
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        ('Vendredi', 'Vendredi'),
        ('Samedi', 'Samedi'),
    ])
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def __str__(self):
        return f"{self.classe} - {self.matiere} - {self.jour} {self.heure_debut}-{self.heure_fin}"
    

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
    
def validate_json(value):
    try:
        json.loads(value)  # Vérifie si c'est un JSON valide
    except ValueError:
        raise ValidationError("Données JSON invalides.")    
    


class Archive(models.Model):
    annee_scolaire = models.CharField(max_length=9)  # Format : "2023-2024"
    eleve = models.ForeignKey('Eleve', on_delete=models.SET_NULL, null=True, blank=True)
    classe = models.CharField(max_length=100, blank=True, null=True)
    etablissement = models.ForeignKey('Etablissement', on_delete=models.CASCADE)
    notes = models.JSONField(blank=True, null=True, validators=[validate_json])
    absences = models.JSONField(blank=True, null=True, validators=[validate_json])
    moyenne_annuelle = models.FloatField(default=0.0)
    passe_classe = models.BooleanField(default=False)
    date_archivage = models.DateTimeField(default=timezone.now)  # Date d'archivage
    motif_archivage = models.CharField(
        max_length=50,
        choices=[
            ('fin_annee', 'Fin d’année scolaire'),
            ('depart', 'Départ de l’établissement'),
            ('redoublement', 'Redoublement'),
        ],
        default='fin_annee'
    )

    # ✅ Ajout des nouveaux champs demandés
    total_points_semestre_1 = models.FloatField(default=0)
    total_points_semestre_2 = models.FloatField(default=0)
    
    MENTION_CHOICES = [
        ('Bien', 'Bien'),
        ('Assez bien', 'Assez bien'),
        ('Passable', 'Passable'),
        ('Très bien', 'Très bien'),
        ('Excellent', 'Excellent'),
    ]
    
    mention_semestre_1 = models.CharField(max_length=20, null=True, blank=True, choices=MENTION_CHOICES)
    mention_semestre_2 = models.CharField(max_length=20, null=True, blank=True, choices=MENTION_CHOICES)
    mention_annuelle = models.CharField(max_length=20, null=True, blank=True, choices=MENTION_CHOICES)
    rang_semestre_1 = models.IntegerField(null=True, blank=True)
    rang_semestre_2 = models.IntegerField(null=True, blank=True)
    rang_annuel = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('eleve', 'annee_scolaire')

    def __str__(self):
        return f"{self.eleve} - {self.annee_scolaire}"
    


class NoteArchive(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    semestre = models.IntegerField(choices=[(1, "Semestre 1"), (2, "Semestre 2")])
    note_devoir = models.FloatField()
    note_composition = models.FloatField()
    annee_scolaire = models.CharField(max_length=9)

    def __str__(self):
        return f"{self.eleve.prenom} {self.eleve.nom} - {self.matiere.nom} ({self.annee_scolaire})"
    

class ArchivePaiement(models.Model):
    annee_scolaire = models.CharField(max_length=9)  # Format : "2023-2024"
    eleve_id = models.IntegerField()  # ID de l'élève
    eleve_nom = models.CharField(max_length=100)  # Nom de l'élève
    eleve_prenom = models.CharField(max_length=100)  # Prénom de l'élève
    frais = models.CharField(max_length=200)  # Type de frais
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    mode_paiement = models.CharField(max_length=20, choices=Paiement.MODE_PAIEMENT_CHOICES)
    statut = models.CharField(max_length=20, choices=Paiement.STATUT_PAIEMENT_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)
    date_archivage = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.eleve_nom} {self.eleve_prenom} - {self.frais} - {self.montant_paye} FCFA"

    

class ArchiveNote(models.Model):
    annee_scolaire = models.CharField(max_length=9)  # Format : "2023-2024"
    eleve = models.CharField(max_length=200)  # Nom de l'élève
    matiere = models.CharField(max_length=100)  # Nom de la matière
    note_devoir = models.FloatField()
    note_composition = models.FloatField()
    moyenne_matiere = models.FloatField()
    points_matiere = models.FloatField()
    semestre = models.PositiveIntegerField()
    date_archivage = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.eleve} - {self.matiere} - {self.annee_scolaire}"
    
class FraisRestauré(models.Model):
    annee_scolaire = models.CharField(max_length=20)
    type_frais = models.CharField(max_length=20, choices=Frais.TYPE_FRAIS_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    classe = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    date_archivage = models.DateTimeField()

    def __str__(self):
        return f"{self.type_frais} - {self.montant} FCFA ({self.classe})"       
    

class PaiementRestauré(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile', 'Mobile Money'),
    ]

    STATUT_PAIEMENT_CHOICES = [
        ('paye', 'Payé'),
        ('partiel', 'Partiel'),
        ('impaye', 'Impayé'),
    ]

    MOIS_CHOICES = [
        (1, 'Janvier'),
        (2, 'Février'),
        (3, 'Mars'),
        (4, 'Avril'),
        (5, 'Mai'),
        (6, 'Juin'),
        (7, 'Juillet'),
        (8, 'Août'),
        (9, 'Septembre'),
        (10, 'Octobre'),
        (11, 'Novembre'),
        (12, 'Décembre'),
    ]

    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, related_name='paiements_restaures')
    frais = models.ForeignKey('FraisRestauré', on_delete=models.CASCADE, related_name='paiements_restaures')
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    date_paiement = models.DateField(default=timezone.now, verbose_name="Date de paiement")
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes')
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='paye')
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Référence du paiement (ex: numéro de chèque)")
    mois = models.IntegerField(choices=MOIS_CHOICES, blank=True, null=True, help_text="Mois concerné (pour les paiements mensuels)")
    est_anticipation = models.BooleanField(default=False, verbose_name="Paiement anticipé")
    est_retroactif = models.BooleanField(default=False, verbose_name="Paiement rétroactif")
    nombre_mois = models.PositiveIntegerField(default=1, verbose_name="Nombre de mois concernés")
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE, related_name='paiements_restaures')  # Utiliser ForeignKey

    def __str__(self):
        return f"{self.eleve} - {self.frais} - {self.montant_paye} FCFA"
    

class ArchiveFrais(models.Model):
    annee_scolaire = models.CharField(max_length=20)
    type_frais = models.CharField(max_length=20, choices=Frais.TYPE_FRAIS_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    classe = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    date_archivage = models.DateTimeField()

    def __str__(self):
        return f"{self.type_frais} - {self.montant} FCFA ({self.classe})"
    

 
    











    

