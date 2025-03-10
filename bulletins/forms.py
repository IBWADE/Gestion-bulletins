from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import get_object_or_404
from .models import Eleve, Classe, Enseignant, Etablissement, Matiere, Note, CustomUser, Notification, Absence, AnneeScolaire, NiveauScolaire, ChoixMatiere, Paiement, Frais, EmploiDuTemps
from django.forms import SelectDateWidget, ValidationError
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmation du mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password2'])
        if commit:
            user.save()
        return user
    

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = "Rôle"
        self.fields['first_name'].label = "Prénom"
        self.fields['last_name'].label = "Nom"


class NotificationForm(forms.ModelForm):
    utilisateur = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='parent'),  # Filtrer les utilisateurs pour ne montrer que les parents
        required=True,
        label="Destinataire (Parent)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Notification
        fields = ['utilisateur', 'titre', 'message', 'importance']  # Ajout de l'utilisateur dans le formulaire
        labels = {
            'titre': 'Titre de la notification',
            'message': 'Message',
            'importance': 'Importance',
        }
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le titre de la notification'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Rédigez votre message ici...'}),
            'importance': forms.Select(attrs={'class': 'form-control'}),
        }



class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['eleve', 'matiere', 'date', 'motif', 'semestre']  # ✅ Ajout de 'semestre'
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'semestre': forms.Select(attrs={'class': 'form-control'}),  # ✅ Ajout du widget pour 'semestre'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Récupérer l'utilisateur
        super(AbsenceForm, self).__init__(*args, **kwargs)

        # Filtrer les élèves pour un enseignant
        if user and user.role == 'enseignant':
            enseignant = get_object_or_404(Enseignant, user=user)
            self.fields['eleve'].queryset = Eleve.objects.filter(classe__in=enseignant.classes.all())

            # Filtrer les matières enseignées par cet enseignant
            self.fields['matiere'].queryset = Matiere.objects.filter(enseignant=enseignant)
        if 'instance' in kwargs and kwargs['instance']:
            eleve = kwargs['instance'].eleve
            classe = eleve.classe
            etablissement = classe.etablissement

            if "Sixième" in classe.nom or "Cinquième" in classe.nom:
                matieres_filtrees = Matiere.objects.exclude(nom="Physique-Chimie").exclude(nom__startswith="Langue 2")
            elif "Quatrième" in classe.nom:
                if etablissement.choix_pc_langue:
                    matieres_filtrees = Matiere.objects.all()
                else:
                    matieres_filtrees = Matiere.objects.exclude(nom__startswith="Langue 2")
            else:  # Troisième
                matieres_filtrees = Matiere.objects.all()

            self.fields['matiere'].queryset = matieres_filtrees    



class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = ['nom', 'prenom', 'classe', 'parent', 'date_naissance', 'lieu_naissance', 'matricule']
        
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Récupérer l'utilisateur
        super(EleveForm, self).__init__(*args, **kwargs)

        # Restreindre les classes visibles pour un enseignant
        if user and user.role == 'enseignant':
            enseignant = get_object_or_404(Enseignant, user=user)
            self.fields['classe'].queryset = enseignant.classes.all()
        if self.instance and self.instance.classe:
            classe = self.instance.classe
            etablissement = classe.etablissement

            # Déterminer les matières en fonction de la classe
            if "Sixième" in classe.nom or "Cinquième" in classe.nom:
                matieres_filtrees = Matiere.objects.exclude(nom="Physique-Chimie").exclude(nom__startswith="Langue 2")
            elif "Quatrième" in classe.nom:
                if etablissement.choix_pc_langue:
                    matieres_filtrees = Matiere.objects.all()
                else:
                    matieres_filtrees = Matiere.objects.exclude(nom__startswith="Langue 2")
            else:  # Troisième
                matieres_filtrees = Matiere.objects.all()

            # Assurer que l'élève ne choisit que les matières disponibles
            self.fields['classe'].queryset = Classe.objects.filter(etablissement=etablissement)  


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['eleve', 'frais', 'montant_paye', 'date_paiement', 'mode_paiement', 'statut', 'reference', 'mois', 'annee_scolaire']
        exclude = ['annee_scolaire']  # ✅ Exclure annee_scolaire pour éviter l'erreur
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'frais': forms.Select(attrs={'class': 'form-control'}),
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'mois': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.HiddenInput(),  # Champ caché pour l'année scolaire
        }
        labels = {
            'eleve': 'Élève',
            'frais': 'Frais',
            'montant_paye': 'Montant payé',
            'date_paiement': 'Date de paiement',
            'mode_paiement': 'Mode de paiement',
            'statut': 'Statut du paiement',
            'reference': 'Référence (optionnelle)',
            'mois': 'Mois concerné',
        }

    def __init__(self, *args, **kwargs):
        echeance = kwargs.pop('echeance', None)  # Récupérer l'échéance passée en argument
        super().__init__(*args, **kwargs)

        if echeance:
            # Pré-remplir les champs en fonction de l'échéance
            self.fields['eleve'].initial = echeance.eleve
            self.fields['frais'].initial = echeance.frais
            self.fields['montant_paye'].initial = echeance.montant_du
            self.fields['statut'].initial = 'paye'  # Par défaut, le statut est "payé"
            # Déterminer le mois en fonction de la date de l'échéance
            if echeance.date_echeance:
                self.fields['mois'].initial = echeance.date_echeance.month


class PaiementRetroactifForm(forms.ModelForm):
    nombre_mois = forms.IntegerField(
        min_value=1,
        max_value=12,  # Limite à 12 mois pour éviter des erreurs
        label="Nombre de mois à payer",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Paiement
        fields = ['eleve', 'frais', 'montant_paye', 'date_paiement', 'mode_paiement', 'statut', 'reference', 'nombre_mois']
        widgets = {
            'eleve': forms.HiddenInput(),  # Masquer le champ élève (il sera pré-rempli)
            'frais': forms.HiddenInput(),  # Masquer le champ frais (il sera pré-rempli)
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        } 


class FraisForm(forms.ModelForm):
    class Meta:
        model = Frais
        fields = ['type_frais', 'montant', 'classe', 'annee_scolaire', 'description']
        widgets = {
            'type_frais': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'classe': forms.Select(attrs={'class': 'form-control'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'type_frais': 'Type de frais',
            'montant': 'Montant à payer',
            'classe': 'Classe',
            'annee_scolaire': 'Année scolaire',
            'description': 'Description (optionnelle)',
        }                   



class EtablissementForm(forms.ModelForm):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all(),
        empty_label="Sélectionnez une année scolaire",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Etablissement
        fields = ['nom', 'adresse', 'ville', 'pays', 'telephone', 'logo', 'annee_scolaire', 'ia', 'ief', 'choix_matiere_quatrieme']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: +221 XX XXX XX XX'
            }),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: IA de Dakar'}),
            'ief': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: IEF de Pikine'}),
            'choix_matiere_quatrieme': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'niveau', 'etablissement']  # Ajout du champ niveau
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),  # Ajout du widget
            'etablissement': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Récupérer l'utilisateur
        super(ClasseForm, self).__init__(*args, **kwargs)

        # Si un enseignant est rattaché à un établissement spécifique, filtrer
        if user and user.role == 'enseignant':
            enseignant = get_object_or_404(Enseignant, user=user)
            self.fields['etablissement'].queryset = Etablissement.objects.filter(
                id__in=enseignant.classes.values_list('etablissement_id', flat=True)
            )








class NiveauScolaireForm(forms.ModelForm):
    class Meta:
        model = NiveauScolaire
        fields = ['nom', 'ordre', 'matieres_obligatoires', 'matieres_optionnelles']
        widgets = {
            'nom': forms.Select(attrs={'class': 'form-control'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control'}),  # Ajout du widget pour le champ 'ordre'
            'matieres_obligatoires': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
            'matieres_optionnelles': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
        }
        labels = {
            'nom': 'Nom du niveau scolaire',
            'ordre': 'Ordre du niveau scolaire',  # Ajout du label pour le champ 'ordre'
            'matieres_obligatoires': 'Matières obligatoires',
            'matieres_optionnelles': 'Matières optionnelles',
        }
        help_texts = {
            'matieres_obligatoires': "Sélectionnez les matières obligatoires pour ce niveau.",
            'matieres_optionnelles': "Sélectionnez les matières optionnelles que les élèves peuvent choisir.",
        }


class ChoixMatiereForm(forms.Form):
    matieres = forms.ModelMultipleChoiceField(
        queryset=Matiere.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        niveau = kwargs.pop("niveau", None)
        etablissement = kwargs.pop("etablissement", None)
        super().__init__(*args, **kwargs)

        if niveau:
            matieres_optionnelles = Matiere.objects.filter(niveaux_optionnels=niveau)
            appliquer_regle_4e = niveau.nom == "4e" and etablissement and etablissement.choix_matiere_quatrieme

            if appliquer_regle_4e or niveau.nom == "3e":
                pc = Matiere.objects.filter(nom="Science Physique").first()
                langues = Matiere.objects.filter(nom__in=["Espagnol", "Arabe", "Allemand", "Italien"])

                # Si PC est présent ET qu'une langue est aussi disponible, on garde les deux
                if pc in matieres_optionnelles and matieres_optionnelles.intersection(langues).exists():
                    # On ne filtre rien, on garde PC + une langue
                    pass  # 🚀 On laisse tout tel quel !

                print(f"Avant filtrage (4e/3e) : {Matiere.objects.filter(niveaux_optionnels=niveau)}")
                print(f"Après filtrage final ({niveau.nom}) : {matieres_optionnelles}")

            self.fields["matieres"].queryset = matieres_optionnelles






class EnseignantForm(forms.ModelForm):
    matieres = forms.ModelMultipleChoiceField(
        queryset=Matiere.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="Matières enseignées"
    )

    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='enseignant'),  # Filtrer les utilisateurs enseignants
        empty_label="Sélectionnez un utilisateur",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Utilisateur"
    )

    class Meta:
        model = Enseignant
        fields = ['user', 'nom', 'prenom', 'classes', 'matieres']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l’enseignant'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom de l’enseignant'}),
            'classes': forms.SelectMultiple(attrs={'class': 'form-select'}),  # Si classes est un ManyToManyField
        }
        help_texts = {
            'classes': "Sélectionnez les classes enseignées",
        }


class EmploiDuTempsForm(forms.ModelForm):
    class Meta:
        model = EmploiDuTemps
        fields = ['classe', 'enseignant', 'matiere', 'jour', 'heure_debut', 'heure_fin']
        widgets = {
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
        }     

    def clean(self):
        cleaned_data = super().clean()
        enseignant = cleaned_data.get('enseignant')
        classe = cleaned_data.get('classe')
        jour = cleaned_data.get('jour')
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')

        # Vérifier les conflits pour l'enseignant
        conflit_enseignant = EmploiDuTemps.objects.filter(
            enseignant=enseignant,
            jour=jour,
            heure_debut__lt=heure_fin,
            heure_fin__gt=heure_debut,
        ).exclude(pk=self.instance.pk if self.instance else None)  

        if conflit_enseignant.exists():
            raise ValidationError("L'enseignant est déjà occupé à ce créneau horaire.")

        # Vérifier les conflits pour la classe
        conflit_classe = EmploiDuTemps.objects.filter(
            classe=classe,
            jour=jour,
            heure_debut__lt=heure_fin,
            heure_fin__gt=heure_debut,
        ).exclude(pk=self.instance.pk if self.instance else None)  

        if conflit_classe.exists():
            raise ValidationError("La classe a déjà un cours programmé à ce créneau horaire.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'enseignant' in self.data:
            try:
                enseignant_id = int(self.data.get('enseignant'))
                self.fields['matiere'].queryset = Matiere.objects.filter(enseignant__id=enseignant_id)
            except (ValueError, TypeError):
                pass  
        elif self.instance.pk:
            self.fields['matiere'].queryset = self.instance.enseignant.matieres.all()
       




class NoteForm(forms.ModelForm):
    semestre = forms.ChoiceField(
        choices=Note.SEMESTRES,
        widget=forms.HiddenInput()  # Caché mais bien envoyé
    )

    class Meta:
        model = Note
        fields = ['matiere', 'note_devoir', 'note_composition', 'semestre']
        widgets = {
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'note_devoir': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'note_composition': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

    def __init__(self, *args, **kwargs):
        eleve = kwargs.pop('eleve', None)  # Récupérer l'élève pour filtrer ses matières
        super().__init__(*args, **kwargs)

        if eleve:
            classe = eleve.classe
            etablissement = classe.etablissement

            # Appliquer les restrictions selon la classe
            if "Sixième" in classe.nom or "Cinquième" in classe.nom:
                matieres_filtrees = Matiere.objects.exclude(nom="Physique-Chimie").exclude(nom__startswith="Langue 2")
            elif "Quatrième" in classe.nom:
                if etablissement.choix_pc_langue:
                    matieres_filtrees = Matiere.objects.all()
                else:
                    matieres_filtrees = Matiere.objects.exclude(nom__startswith="Langue 2")
            else:  # Troisième
                matieres_filtrees = Matiere.objects.all()

            self.fields['matiere'].queryset = matieres_filtrees




class MatiereForm(forms.ModelForm):
    coefficient = forms.IntegerField(
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={'min': 1, 'class': 'form-control', 'placeholder': 'Coefficient'}),
        label="Coefficient"
    )
    
    class Meta:
        model = Matiere
        fields = '__all__'
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la matière'}),
        }



class NotesEleveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        eleve = kwargs.pop('eleve', None)
        super().__init__(*args, **kwargs)

        if eleve:
            for matiere in Matiere.objects.all():
                self.fields[f'matiere_{matiere.id}'] = forms.ModelChoiceField(
                    queryset=Note.objects.filter(eleve=eleve, matiere=matiere),
                    required=False,
                    widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
                )    


class EnseignantClassesForm(forms.ModelForm):
    classes = forms.ModelMultipleChoiceField(
        queryset=Classe.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Enseignant
        fields = ['classes']
        

class RechercheGlobaleForm(forms.Form):
    TYPE_RECHERCHE_CHOICES = [
        ('eleves_classe', 'Impression Bulletin par élève dans une classe'),
        ('bulletin_eleve', 'Bulletin de notes d\'un élève'),
        ('bulletins_classe', 'Impression globale bulletins de notes dans une classe'),
        ('meilleur_eleve', 'Élève avec la meilleure moyenne dans une classe'),
        ('classes_enseignant', 'Liste des classes d\'un enseignant'),
        ('enseignants_etablissement', 'Enseignants d\'un établissement'),
        ('liste_classes_etablissement', 'Liste des classes d\'un établissement'),
        ('eleves_retard_paiement', 'Élèves en retard de paiement'),
        ('paiements_par_eleve', 'Paiements effectués par un élève'),
        ('paiements_par_periode', 'Paiements effectués sur une période donnée'),
        
    ]

    type_recherche = forms.ChoiceField(
        label="Type de recherche",
        choices=TYPE_RECHERCHE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        label="Classe",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    eleve = forms.ModelChoiceField(
        queryset=Eleve.objects.all(),
        label="Élève",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enseignant = forms.ModelChoiceField(
        queryset=Enseignant.objects.all(),
        label="Enseignant",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    etablissement = forms.ModelChoiceField(
        queryset=Etablissement.objects.all(),
        label="Établissement",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    semestre = forms.ChoiceField(
        label="Semestre",
        choices=[('', 'Tous'), (1, 'Semestre 1'), (2, 'Semestre 2')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_debut = forms.DateField(
        label="Date début",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        label="Date fin",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def clean(self):
        cleaned_data = super().clean()
        type_recherche = cleaned_data.get('type_recherche')
        classe = cleaned_data.get('classe')
        eleve = cleaned_data.get('eleve')
        enseignant = cleaned_data.get('enseignant')
        etablissement = cleaned_data.get('etablissement')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if type_recherche == 'bulletin_eleve' and not eleve:
            self.add_error('eleve', "L'élève est requis pour ce type de recherche.")
        if type_recherche in ['eleves_classe', 'bulletins_classe', 'meilleur_eleve'] and not classe:
            self.add_error('classe', "La classe est requise pour ce type de recherche.")
        if type_recherche == 'classes_enseignant' and not enseignant:
            self.add_error('enseignant', "L'enseignant est requis pour ce type de recherche.")
        if type_recherche in ['enseignants_etablissement', 'liste_classes_etablissement'] and not etablissement:
            self.add_error('etablissement', "L'établissement est requis pour ce type de recherche.")
        if type_recherche == 'paiements_par_periode' and (not date_debut or not date_fin):
            self.add_error('date_debut', "Les dates de début et de fin sont requises pour cette recherche.")
            self.add_error('date_fin', "Les dates de début et de fin sont requises pour cette recherche.")
        

        return cleaned_data


class ArchiverAnneeForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by('-debut', '-fin'),
        empty_label="Sélectionnez une année scolaire",
        widget=forms.Select(attrs={'class': 'form-control', 'required': True})
    )



class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['nom', 'debut', 'fin']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        debut = cleaned_data.get('debut')
        fin = cleaned_data.get('fin')

        if debut and fin and debut >= fin:
            raise forms.ValidationError("La date de début doit être antérieure à la date de fin.")

        return cleaned_data






