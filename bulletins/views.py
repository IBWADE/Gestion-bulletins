from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from .models import (Eleve, Note, Etablissement, Classe, Enseignant, Matiere, CustomUser, Absence, Notification, 
                     Archive, AnneeScolaire, ChoixMatiere, NiveauScolaire, Paiement, Frais, Paiement, Echeance, EmploiDuTemps,
                       NoteArchive, ArchivePaiement, ArchiveNote, PaiementRestauré, ArchiveFrais, FraisRestauré)
from django.views import View
from django.shortcuts import render, redirect
from .forms import EleveForm, EtablissementForm, ClasseForm, EnseignantForm, MatiereForm, NoteForm, NotesEleveForm, EnseignantClassesForm, RechercheGlobaleForm, NotificationForm, AbsenceForm, ArchiverAnneeForm, AnneeScolaireForm, NiveauScolaireForm, PaiementForm
from django.db.models import Sum, FloatField, ExpressionWrapper, Case, When, Window, F, Count, Max, Value, OuterRef, Subquery, ProtectedError
from django.db.models.functions import Rank, Coalesce, Cast, Round
from django.utils import timezone  # Import nécessaire
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import IntegerField
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserForm, ChoixMatiereForm, FraisForm, PaiementRetroactifForm, EmploiDuTempsForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg
import logging
from django.utils.timezone import now
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from datetime import datetime
from datetime import timedelta
from .utils import generer_echeances_pour_eleve  # Importer la fonction
from dateutil.relativedelta import relativedelta
from datetime import date
from django.db import transaction




logger = logging.getLogger(__name__)




# Décorateur pour vérifier si l'utilisateur est administrateur
# Fonction pour vérifier si l'utilisateur est administrateur
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

# Fonction pour vérifier si l'utilisateur est enseignant
def is_enseignant(user):
    return user.is_authenticated and user.role == 'enseignant'

# Fonction pour vérifier si l'utilisateur est parent
def is_parent(user):
    return user.is_authenticated and user.role == 'parent'

# Fonction pour vérifier admin et enseignant
def is_admin_or_enseignant(user):
    return user.is_authenticated and (user.role == 'admin' or user.role == 'enseignant')

# Fonction pour vérifier admin et enseignant
def is_admin_or_parent(user):
    return user.is_authenticated and (user.role == 'admin' or user.role == 'parent')

# Fonction pour vérifier admin et enseignant
def is_admin_or_enseignant_or_parent(user):
    return user.is_authenticated and (user.role == 'admin' or user.role == 'parent' or user.role == 'enseignant')




@login_required
@user_passes_test(is_admin, login_url='login')
def creer_utilisateur(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_utilisateurs')  # Rediriger vers la liste des utilisateurs
    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'bulletins/creer_utilisateur.html', context)



@login_required
@user_passes_test(is_admin, login_url='login')
def liste_utilisateurs(request):
    query = request.GET.get('q', '')
    utilisateurs = CustomUser.objects.all()
    if query:
        utilisateurs = utilisateurs.filter(Q(prenom__icontains=query) | Q(nom__icontains=query))
    # Pagination (par exemple, 10 classes par page)
    paginator = Paginator(utilisateurs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bulletins/liste_utilisateurs.html', {'utilisateurs': page_obj})



@login_required
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Rediriger vers la page demandée avant la connexion (si 'next' est présent)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                # Sinon, rediriger vers la page d'accueil selon le rôle
                if user.role == 'admin' or user.is_superuser:
                    return redirect('accueil_admin')
                elif user.role == 'enseignant':
                    return redirect('accueil_enseignant')
                elif user.role == 'parent':
                    return redirect('accueil_parent')
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
    }
    return render(request, 'bulletins/login.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@user_passes_test(is_admin, login_url='login')
def creer_compte(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')  # Seul l'administrateur peut accéder à cette page

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Le compte a été créé avec succès.")
            return redirect('creer_compte')
        else:
            messages.error(request, "Veuillez corriger les erreurs suivantes.")
    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'bulletins/creer_compte.html', context)



@login_required
def profile_user(request, user_id):
    utilisateur = get_object_or_404(CustomUser, id=user_id)
    context = {
        'utilisateur': utilisateur,
    }
    return render(request, 'bulletins/profile_user.html', context)


@login_required
def modifier_user(request, user_id):
    utilisateur = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            return redirect('liste_utilisateurs')
    else:
        form = CustomUserForm(instance=utilisateur)

    context = {
        'form': form,
        'utilisateur': utilisateur,
    }
    return render(request, 'bulletins/modifier_user.html', context)


@receiver(post_save, sender=Absence)
def creer_notification_absence(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            utilisateur=instance.eleve.parent,
            titre="Absence enregistrée",
            message=f"Votre enfant {instance.eleve.prenom} {instance.eleve.nom} a manqué le cours de {instance.matiere.nom} le {instance.date}."
        )


@receiver(post_save, sender=Note)
def creer_notification_bulletin(sender, instance, created, **kwargs):
    if created:
        # Vérifier si l'élève a un parent
        if instance.eleve.parent:
            Notification.objects.create(
                utilisateur=instance.eleve.parent,
                titre="Nouvelle note ajoutée",
                message=f"Une nouvelle note a été ajoutée pour {instance.eleve.prenom} {instance.eleve.nom} en {instance.matiere.nom}."
            )
        else:
            # Gérer le cas où l'élève n'a pas de parent (par exemple, afficher un message dans les logs ou ignorer la création)
            print(f"Aucun parent trouvé pour l'élève {instance.eleve.prenom} {instance.eleve.nom}. Notification non envoyée.")
     


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def saisie_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.date = now()  # Ajouter la date actuelle
            notification.save()
            return redirect('liste_notifications')
    else:
        form = NotificationForm()

    return render(request, 'bulletins/saisie_notification.html', {'form': form})
 


@login_required
def liste_notifications(request):
    filtre = request.GET.get('filtre', '')

    if request.user.role == 'admin':  
        # L'administrateur voit toutes les notifications
        notifications = Notification.objects.all()
    elif request.user.role == 'enseignant':  
        # Récupérer les élèves de l'enseignant
        eleves_de_enseignant = Eleve.objects.filter(classe__enseignants__user=request.user)

        # Récupérer les parents de ces élèves
        parents = CustomUser.objects.filter(enfants__in=eleves_de_enseignant).distinct()

        # Sélectionner les notifications adressées aux parents de ses élèves
        notifications = Notification.objects.filter(utilisateur__in=parents)
    elif request.user.role == 'parent':  
        # Le parent voit uniquement ses propres notifications
        notifications = Notification.objects.filter(utilisateur=request.user)
    else:
        notifications = Notification.objects.none()

    # Appliquer les filtres
    if filtre == "non_lues":
        notifications = notifications.filter(lue=False)
    elif filtre == "lues":
        notifications = notifications.filter(lue=True)
    elif filtre == "importantes":
        notifications = notifications.filter(importance='importance')

    notifications = notifications.order_by('-date')

       # Pagination (10 notifications par page)
    paginator = Paginator(notifications, 10)  # Ajuste le nombre selon ton besoin
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'notifications': notifications,
        'filtre': filtre,
        "page_obj": page_obj,
    }
    return render(request, 'bulletins/liste_notifications.html', context)





@login_required
def marquer_comme_lue(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)

    # Vérifier si l'utilisateur est bien le destinataire de la notification
    if request.user.role == 'parent' and notification.utilisateur == request.user:
        notification.lue = True
        notification.save()
        return redirect('accueil_parent')  # Redirection vers l'accueil du parent
    elif request.user.role == 'admin' or request.user.role == 'enseignant':
        notification.lue = True
        notification.save()
        return redirect('liste_notifications')  # Admins et enseignants restent sur la liste

    return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cette notification.")





@login_required
def marquer_toutes_comme_lues(request):
    if request.user.is_parent():  # Vérifier si l'utilisateur est un parent
        Notification.objects.filter(utilisateur=request.user, lue=False).update(lue=True)
        return redirect('accueil_parent')  # Rediriger vers l'accueil parent
    
    elif request.user.is_admin() or request.user.is_enseignant():
        Notification.objects.filter(utilisateur=request.user, lue=False).update(lue=True)
        return redirect('liste_notifications')  # Rediriger vers la liste des notifications

    return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier ces notifications.")


@login_required
@user_passes_test(is_admin, login_url='login')
def vider_notifications(request):
    filtre = request.POST.get('filtre', '')

    notifications = Notification.objects.all()

    # Appliquer le filtre avant suppression
    if filtre == "non_lues":
        notifications = notifications.filter(lue=False)
    elif filtre == "lues":
        notifications = notifications.filter(lue=True)
    elif filtre == "importantes":
        notifications = notifications.filter(importance="importance")  # Correction ici

    notifications.delete()
    return redirect('liste_notifications')




@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def saisie_absence(request):
    if request.method == 'POST':
        form = AbsenceForm(request.POST, user=request.user)
        if form.is_valid():
            absence = form.save(commit=False)

            # Déterminer automatiquement le semestre si ce n'est pas choisi
            if not absence.semestre:
                absence.semestre = 1 if timezone.now().month <= 6 else 2  # ✅ Semestre 1 : Jan-Juin, Semestre 2 : Juil-Déc

            absence.save()
            messages.success(request, "L'absence a été enregistrée avec succès.")
            return redirect('liste_absences')
    else:
        form = AbsenceForm(user=request.user)

    context = {'form': form, 'title': 'Saisir une absence'}
    return render(request, 'bulletins/saisie_absence.html', context)






@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def liste_absences(request):
    # Filtrer les absences selon le rôle de l'utilisateur
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        absences = Absence.objects.filter(eleve__classe__in=enseignant.classes.all()).order_by('-date')
    else:  # Admin
        absences = Absence.objects.all().order_by('-date')

    context = {
        'absences': absences,
        'title': 'Liste des absences',
    }
    return render(request, 'bulletins/liste_absences.html', context)




@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def detail_absence(request, absence_id):
    absence = get_object_or_404(Absence, id=absence_id)

    # Vérification d'accès pour les enseignants
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        if absence.eleve.classe not in enseignant.classes.all():
            messages.error(request, "Vous n'avez pas accès à cette absence.")
            return redirect('liste_absences')

    context = {
        'absence': absence,
        'title': 'Détails de l’absence',
    }
    return render(request, 'bulletins/detail_absence.html', context)



@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def modifier_absence(request, absence_id):
    absence = get_object_or_404(Absence, id=absence_id)

    # Vérification d'accès pour les enseignants
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        if absence.eleve.classe not in enseignant.classes.all():
            messages.error(request, "Vous n'avez pas accès à cette absence.")
            return redirect('liste_absences')

    if request.method == 'POST':
        form = AbsenceForm(request.POST, instance=absence)
        if form.is_valid():
            form.save()
            messages.success(request, "L'absence a été modifiée avec succès.")
            return redirect('liste_absences')
    else:
        form = AbsenceForm(instance=absence)

    context = {
        'form': form,
        'absence': absence,
        'title': 'Modifier une absence',
    }
    return render(request, 'bulletins/modifier_absence.html', context)



@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def supprimer_absence(request, absence_id):
    absence = get_object_or_404(Absence, id=absence_id)

    # Vérification d'accès pour les enseignants
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        if absence.eleve.classe not in enseignant.classes.all():
            messages.error(request, "Vous n'avez pas accès à cette absence.")
            return redirect('liste_absences')

    if request.method == 'POST':
        absence.delete()
        messages.success(request, "L'absence a été supprimée avec succès.")
        return redirect('liste_absences')

    context = {
        'absence': absence,
        'title': 'Supprimer une absence',
    }
    return render(request, 'bulletins/confirmation_suppression.html', context)



@login_required
@user_passes_test(is_parent, login_url='login')
def accueil_parent(request):
    # Récupérer les enfants du parent connecté
    enfants = Eleve.objects.filter(parent=request.user)    

    enfants_data = []

    for enfant in enfants:
        # Récupérer l'année scolaire
        annee_scolaire = enfant.classe.etablissement.annee_scolaire if enfant.classe and enfant.classe.etablissement else "Non définie"
        # Calculer la moyenne générale pour chaque semestre
        notes_s1 = Note.objects.filter(eleve=enfant, semestre=1).annotate(
            points_matiere=Coalesce(
                ExpressionWrapper(
                    ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                    output_field=FloatField()
                ),
                Value(0.0),
                output_field=FloatField()
            )
        )
        notes_s2 = Note.objects.filter(eleve=enfant, semestre=2).annotate(
            points_matiere=Coalesce(
                ExpressionWrapper(
                    ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                    output_field=FloatField()
                ),
                Value(0.0),
                output_field=FloatField()
            )
        )

        total_points_s1 = sum(note.points_matiere for note in notes_s1)
        total_coefficients_s1 = sum(note.matiere.coefficient for note in notes_s1)
        moyenne_generale_s1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0

        total_points_s2 = sum(note.points_matiere for note in notes_s2)
        total_coefficients_s2 = sum(note.matiere.coefficient for note in notes_s2)
        moyenne_generale_s2 = total_points_s2 / total_coefficients_s2 if total_coefficients_s2 > 0 else 0

        moyenne_annuelle = (moyenne_generale_s1 + moyenne_generale_s2) / 2 if moyenne_generale_s1 > 0 and moyenne_generale_s2 > 0 else 0

        # Calcul des rangs dans la classe
        if enfant.classe:
            # Classement global (basé sur la moyenne annuelle)
            classement_general = (
                Eleve.objects.filter(classe=enfant.classe)
                .annotate(
                    total_points=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                                output_field=FloatField()
                            ),
                            filter=Q(note__semestre__in=[1, 2])
                        ),
                        Value(0.0),
                        output_field=FloatField()
                    ),
                    total_coefficients=Coalesce(
                        Sum('note__matiere__coefficient', filter=Q(note__semestre__in=[1, 2])),
                        Value(1.0),
                        output_field=FloatField()
                    ),
                    moyenne_annuelle=Case(
                        When(total_coefficients=0, then=Value(0.0)),
                        default=ExpressionWrapper(F('total_points') / F('total_coefficients'), output_field=FloatField()),
                        output_field=FloatField()
                    )
                )
                .order_by('-moyenne_annuelle')
            )

            # Classement Semestre 1
            classement_s1 = (
                Eleve.objects.filter(classe=enfant.classe)
                .annotate(
                    total_points_s1=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                                output_field=FloatField()
                            ),
                            filter=Q(note__semestre=1)
                        ),
                        Value(0.0),
                        output_field=FloatField()
                    ),
                    total_coefficients_s1=Coalesce(
                        Sum('note__matiere__coefficient', filter=Q(note__semestre=1)),
                        Value(1.0),
                        output_field=FloatField()
                    ),
                    moyenne_s1=Case(
                        When(total_coefficients_s1=0, then=Value(0.0)),
                        default=ExpressionWrapper(F('total_points_s1') / F('total_coefficients_s1'), output_field=FloatField()),
                        output_field=FloatField()
                    )
                )
                .order_by('-moyenne_s1')
            )

            # Classement Semestre 2
            classement_s2 = (
                Eleve.objects.filter(classe=enfant.classe)
                .annotate(
                    total_points_s2=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                                output_field=FloatField()
                            ),
                            filter=Q(note__semestre=2)
                        ),
                        Value(0.0),
                        output_field=FloatField()
                    ),
                    total_coefficients_s2=Coalesce(
                        Sum('note__matiere__coefficient', filter=Q(note__semestre=2)),
                        Value(1.0),
                        output_field=FloatField()
                    ),
                    moyenne_s2=Case(
                        When(total_coefficients_s2=0, then=Value(0.0)),
                        default=ExpressionWrapper(F('total_points_s2') / F('total_coefficients_s2'), output_field=FloatField()),
                        output_field=FloatField()
                    )
                )
                .order_by('-moyenne_s2')
            )

            # Trouver les rangs de l'élève
            rang_general = next((i + 1 for i, e in enumerate(classement_general) if e.id == enfant.id), None)
            rang_s1 = next((i + 1 for i, e in enumerate(classement_s1) if e.id == enfant.id), None)
            rang_s2 = next((i + 1 for i, e in enumerate(classement_s2) if e.id == enfant.id), None)
        else:
            rang_general = None
            rang_s1 = None
            rang_s2 = None

        enfants_data.append({
            'enfant': enfant,
            'classe': enfant.classe.nom if enfant.classe else "Non défini",
            'etablissement': enfant.classe.etablissement.nom if enfant.classe and enfant.classe.etablissement else "Non défini",
            'moyenne_s1': moyenne_generale_s1,
            'moyenne_s2': moyenne_generale_s2,
            'moyenne_annuelle': moyenne_annuelle,
            'rang_general': rang_general,
            'rang_s1': rang_s1,
            'rang_s2': rang_s2,
            'annee_scolaire': annee_scolaire,
        })

    # Récupérer les notifications du parent connecté
    notifications = Notification.objects.filter(utilisateur=request.user).order_by('-date')[:5]  # Limiter à 5 notifications récentes

    context = {
        'enfants_data': enfants_data,
        'notifications': notifications,  # Ajouter les notifications au contexte
    }

    return render(request, 'bulletins/accueil_parent.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def accueil_admin(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    context = {}
    return render(request, 'bulletins/accueil_admin.html', context)



@login_required
@user_passes_test(is_enseignant, login_url='login')
def accueil_enseignant(request):
    if not request.user.is_authenticated or request.user.role != 'enseignant':
        return redirect('login')

    context = {}
    return render(request, 'bulletins/accueil_enseignant.html', context)




@login_required
def accueil(request):
    return render(request, 'bulletins/accueil.html')

class CreateViewMixin:
    template_name = None
    form_class = None
    success_url = None

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})


class EleveCreateView(CreateViewMixin, View):
    template_name = 'bulletins/saisie_eleve.html'
    form_class = EleveForm
    success_url = 'liste_eleves'





@login_required
@user_passes_test(is_parent, login_url='login')
def details_enfant(request, eleve_id):
    # Récupérer l'enfant ou renvoyer une erreur 404 si non trouvé
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe else "Non défini"
    

    # Vérifier si l'utilisateur connecté est bien le parent de cet élève
    if request.user.role != 'parent' or eleve.parent != request.user:
        messages.error(request, "Vous n'avez pas accès aux informations de cet élève.")
        return redirect('accueil_parent')

    # Filtrer les notes selon l'élève avec annotation correcte
    notes = Note.objects.filter(eleve=eleve).annotate(
        moyenne_calculee=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_matiere=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    # Préparer les données pour chaque semestre
    notes_semestre_1 = notes.filter(semestre=1)
    notes_semestre_2 = notes.filter(semestre=2)

    # Calcul des totaux pour chaque semestre
    total_points_s1 = sum(note.points_matiere for note in notes_semestre_1)
    total_coefficients_s1 = sum(note.matiere.coefficient for note in notes_semestre_1)
    moyenne_generale_s1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0

    total_points_s2 = sum(note.points_matiere for note in notes_semestre_2)
    total_coefficients_s2 = sum(note.matiere.coefficient for note in notes_semestre_2)
    moyenne_generale_s2 = total_points_s2 / total_coefficients_s2 if total_coefficients_s2 > 0 else 0

    # Calcul de la moyenne annuelle
    moyenne_annuelle = (moyenne_generale_s1 + moyenne_generale_s2) / 2 if moyenne_generale_s1 > 0 and moyenne_generale_s2 > 0 else 0

    # Calcul des rangs dans la classe
    if eleve.classe:
        # Classement global (basé sur la moyenne annuelle)
        classement_general = (
            Eleve.objects.filter(classe=eleve.classe)
            .annotate(
                total_points=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                            output_field=FloatField()
                        ),
                        filter=Q(note__semestre__in=[1, 2])
                    ),
                    Value(0.0),
                    output_field=FloatField()
                ),
                total_coefficients=Coalesce(
                    Sum('note__matiere__coefficient', filter=Q(note__semestre__in=[1, 2])),
                    Value(1.0),
                    output_field=FloatField()
                ),
                moyenne_annuelle=Case(
                    When(total_coefficients=0, then=Value(0.0)),
                    default=ExpressionWrapper(F('total_points') / F('total_coefficients'), output_field=FloatField()),
                    output_field=FloatField()
                )
            )
            .order_by('-moyenne_annuelle')
        )

        # Classement Semestre 1
        classement_s1 = (
            Eleve.objects.filter(classe=eleve.classe)
            .annotate(
                total_points_s1=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                            output_field=FloatField()
                        ),
                        filter=Q(note__semestre=1)
                    ),
                    Value(0.0),
                    output_field=FloatField()
                ),
                total_coefficients_s1=Coalesce(
                    Sum('note__matiere__coefficient', filter=Q(note__semestre=1)),
                    Value(1.0),
                    output_field=FloatField()
                ),
                moyenne_s1=Case(
                    When(total_coefficients_s1=0, then=Value(0.0)),
                    default=ExpressionWrapper(F('total_points_s1') / F('total_coefficients_s1'), output_field=FloatField()),
                    output_field=FloatField()
                )
            )
            .order_by('-moyenne_s1')
        )

        # Classement Semestre 2
        classement_s2 = (
            Eleve.objects.filter(classe=eleve.classe)
            .annotate(
                total_points_s2=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                            output_field=FloatField()
                        ),
                        filter=Q(note__semestre=2)
                    ),
                    Value(0.0),
                    output_field=FloatField()
                ),
                total_coefficients_s2=Coalesce(
                    Sum('note__matiere__coefficient', filter=Q(note__semestre=2)),
                    Value(1.0),
                    output_field=FloatField()
                ),
                moyenne_s2=Case(
                    When(total_coefficients_s2=0, then=Value(0.0)),
                    default=ExpressionWrapper(F('total_points_s2') / F('total_coefficients_s2'), output_field=FloatField()),
                    output_field=FloatField()
                )
            )
            .order_by('-moyenne_s2')
        )

        # Trouver les rangs de l'élève
        rang_general = next((i + 1 for i, e in enumerate(classement_general) if e.id == eleve.id), None)
        rang_s1 = next((i + 1 for i, e in enumerate(classement_s1) if e.id == eleve.id), None)
        rang_s2 = next((i + 1 for i, e in enumerate(classement_s2) if e.id == eleve.id), None)
    else:
        rang_general = None
        rang_s1 = None
        rang_s2 = None

    context = {
        'eleve': eleve,
        'notes_semestre_1': notes_semestre_1,
        'notes_semestre_2': notes_semestre_2,
        'total_points_s1': total_points_s1,  # Ajout explicite dans le contexte
        'total_coefficients_s1': total_coefficients_s1,
        'moyenne_generale_s1': moyenne_generale_s1,
        'total_points_s2': total_points_s2,  # Ajout explicite dans le contexte
        'total_coefficients_s2': total_coefficients_s2,
        'moyenne_generale_s2': moyenne_generale_s2,
        'moyenne_annuelle': moyenne_annuelle,
        'rang_s1': rang_s1,
        'rang_s2': rang_s2,
        'rang_general': rang_general,
        'annee_scolaire': annee_scolaire,
    }


    return render(request, 'bulletins/details_enfant.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_eleve(request):
    if request.method == 'POST':
        form = EleveForm(request.POST)
        if form.is_valid():
            eleve = form.save(commit=False)
            if request.user.role == 'parent':  # Assure-toi que l'utilisateur est un parent
                eleve.parent = request.user

            # Vérifier que l'élève a une classe attribuée
            if not eleve.classe:
                messages.error(request, "L'élève doit être affecté à une classe.")
                return render(request, 'bulletins/saisie_eleve.html', {'form': form})

            eleve.save()

            try:
                # Générer les échéances pour l'élève
                from .utils import generer_echeances_pour_eleve
                generer_echeances_pour_eleve(eleve)
                messages.success(request, "Élève enregistré avec succès et échéances générées.")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la génération des échéances : {str(e)}")

            return redirect('liste_eleves')
    else:
        form = EleveForm()

    return render(request, 'bulletins/saisie_eleve.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_eleves(request):
    query = request.GET.get('q', '')

    # Vérifier le rôle de l'utilisateur
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        eleves = Eleve.objects.filter(classe__in=enseignant.classes.all())
    else:  # Admin peut voir tous les élèves
        eleves = Eleve.objects.all()

    if query:
        eleves = eleves.filter(Q(prenom__icontains=query) | Q(nom__icontains=query))

    # Pagination
    paginator = Paginator(eleves, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bulletins/liste_eleves.html', {'eleves': page_obj})

@login_required
@user_passes_test(is_admin, login_url='login')
def liste_eleves_bis(request):
    query = request.GET.get('q', '')
    
    # Vérifier le rôle de l'utilisateur
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        eleves = Eleve.objects.filter(classe__in=enseignant.classes.all())
    else:  # Admin peut voir tous les élèves
        eleves = Eleve.objects.all()

    # Filtrer par recherche sur le nom ou prénom
    if query:
        eleves = eleves.filter(Q(prenom__icontains=query) | Q(nom__icontains=query))

    # Trier les élèves avant la pagination (par exemple, par nom et prénom)
    eleves = eleves.order_by('nom', 'prenom')

    # Pagination
    paginator = Paginator(eleves, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer l'année scolaire en cours à partir de l'établissement de l'élève
    annee_scolaire = None
    if page_obj:
        eleve = page_obj.object_list.first()  # Prendre le premier élève pour récupérer son année scolaire
        if eleve.classe and eleve.classe.etablissement:
            annee_scolaire = eleve.classe.etablissement.annee_scolaire.nom  # Accéder à l'année scolaire via l'établissement

    context = {
        'eleves': page_obj,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/liste_eleves_bis.html', context)





@login_required
@user_passes_test(is_admin, login_url='login')
def liste_eleves_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)
    context = {
        'classe': classe,
        'eleves': eleves,
    }
    return render(request, 'bulletins/liste_eleves_classe.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def liste_eleves_classe_vis(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)

    eleves_avec_moyenne = []
    for eleve in eleves:
        notes = eleve.note_set.annotate(
            moyenne_matiere=(F('note_devoir') + F('note_composition')) / 2.0
        )

        # Calcul du total des points (pondération par coefficient)
        total_points = notes.aggregate(
            total=Coalesce(Sum(F('moyenne_matiere') * F('matiere__coefficient'), output_field=FloatField()), 0.0)
        )['total']

        # Calcul du total des coefficients
        total_coefficients = notes.aggregate(
            total=Coalesce(Sum(F('matiere__coefficient'), output_field=FloatField()), 0.0)
        )['total']

        # Calcul de la moyenne générale
        moyenne_generale = (total_points / total_coefficients) if total_coefficients > 0 else 0.0

        # Ajout des valeurs à l'élève
        eleve.moyenne_generale = moyenne_generale
        eleves_avec_moyenne.append(eleve)

    # Trier les élèves par moyenne générale (du plus haut au plus bas)
    eleves_avec_moyenne.sort(key=lambda x: x.moyenne_generale, reverse=True)

    # Attribution du rang
    for index, eleve in enumerate(eleves_avec_moyenne, start=1):
        eleve.rang = index


    context = {
        'classe': classe,
        'eleves': eleves,
    }
    return render(request, 'bulletins/liste_eleves_classe_vis.html', context)
    

@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_etablissement(request):
    if request.method == 'POST':
        # Si le formulaire est soumis
        form = EtablissementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Enregistrer l'établissement dans la base de données
            return redirect('liste_etablissements')  # Rediriger vers la liste des établissements
    else:
        # Si c'est une requête GET, afficher un formulaire vide
        form = EtablissementForm()
    
    # Afficher le formulaire dans le template
    return render(request, 'bulletins/saisie_etablissement.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_etablissements(request):
    etablissements = Etablissement.objects.all()
    return render(request, 'bulletins/liste_etablissements.html', {'etablissements': etablissements})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_classes(request):
    query = request.GET.get('q', '')

    # Filtrer selon le rôle de l'utilisateur
    if request.user.role == 'enseignant':
        enseignant = get_object_or_404(Enseignant, user=request.user)
        classes = Classe.objects.filter(id__in=enseignant.classes.all())
    else:  # Admin voit toutes les classes
        classes = Classe.objects.all()

    if query:
        classes = classes.filter(Q(nom__icontains=query) | Q(etablissement__nom__icontains=query))

    # Pagination
    paginator = Paginator(classes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bulletins/liste_classes.html', {'classes': page_obj})




@login_required
@user_passes_test(is_enseignant, login_url='login')
def liste_classes_enseignant(request):
    # Récupérer l'enseignant associé à l'utilisateur connecté
    try:
        enseignant = Enseignant.objects.get(user=request.user)  # Utilisez le champ 'user'
    except Enseignant.DoesNotExist:
        messages.error(request, "Aucun enseignant n'est associé à cet utilisateur.")
        return redirect('accueil')

    # Récupérer les classes attribuées à cet enseignant
    classes = enseignant.classes.all()

    context = {
        'enseignant': enseignant,
        'classes': classes,
    }
    return render(request, 'bulletins/liste_classes_enseignant.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='login')
def liste_eleves_classe_enseignant(request, classe_id):
    # Vérifier si l'utilisateur est un enseignant
    try:
        enseignant = Enseignant.objects.get(user=request.user)
    except Enseignant.DoesNotExist:
        messages.error(request, "Vous n'êtes pas un enseignant valide.")
        return redirect('accueil')

    # Récupérer la classe correspondante
    classe = get_object_or_404(Classe, id=classe_id, enseignants=enseignant)

    # Vérifier si l'enseignant a accès à cette classe
    if classe not in enseignant.classes.all():
        messages.error(request, "Vous n'avez pas accès à cette classe.")
        return redirect('liste_classes_enseignant')

    # Récupérer les élèves de la classe
    eleves = Eleve.objects.filter(classe=classe)

    context = {
        'enseignant': enseignant,
        'classe': classe,
        'eleves': eleves,
    }
    return render(request, 'bulletins/liste_eleves_classe_enseignant.html', context)



def generer_appreciation(moyenne):
    """Retourne une appréciation basée sur la moyenne."""
    if moyenne >= 16:
        return "Excellent 🌟"
    elif moyenne >= 14:
        return "Très Bien ✅"
    elif moyenne >= 12:
        return "Bien 👍"
    elif moyenne >= 10:
        return "Assez Bien 🙂"
    elif moyenne >= 9:
        return "Passable ⚠️"
    elif moyenne >= 8:
        return "Insuffisant ❌"
    else:
        return "Faible ❗"

@login_required
@user_passes_test(is_enseignant, login_url='login')
def details_notes_eleve_enseignant(request, eleve_id, semestre):
    # Récupérer l'élève
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    moyennes_par_matiere = []
    total_points_general = 0
    total_coefficients = 0

    # Vérifier si l'enseignant a accès à cette classe
    enseignant = get_object_or_404(Enseignant, user=request.user)
    if eleve.classe not in enseignant.classes.all():
        messages.error(request, "Vous n'avez pas accès aux informations de cet élève.")
        return redirect('accueil_enseignant')

    # Filtrer les notes selon le semestre avec annotation correcte
    notes = Note.objects.filter(eleve=eleve, semestre=semestre).annotate(
        moyenne_calcul=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_calcul=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )    
    

    # Préparer les données pour le contexte
    for note in notes:
        appreciation = generer_appreciation(note.moyenne_calcul)
        moyennes_par_matiere.append({
            'note_id': note.id,
            'matiere': note.matiere,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': note.moyenne_calcul,
            'points_matiere': note.points_calcul,
            'semestre': semestre,
            'appreciation': appreciation,  # Ajout de l'appréciation            
        })
        total_points_general += note.points_calcul
        total_coefficients += note.matiere.coefficient

    # Calcul de la moyenne générale (None si pas de notes)
    moyenne_generale = total_points_general / total_coefficients if total_coefficients > 0 else None

    # Calcul du classement pour ce semestre
    eleves_classe = Eleve.objects.filter(classe=eleve.classe)
    classement = eleves_classe.annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=semestre)  # Filtrer uniquement sur le semestre
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coeffs=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=semestre)),
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne=Case(
            When(total_coeffs=0, then=Value(None)),  # Mettre None au lieu de 0
            default=ExpressionWrapper(F('total_points') / F('total_coeffs'), output_field=FloatField()),
            output_field=FloatField()
        )
    ).order_by('-moyenne')

    # Déterminer le rang de l'élève
    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    context = {
        'eleve': eleve,
        'moyennes_par_matiere': moyennes_par_matiere,
        'total_points_general': total_points_general,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'total_eleves': eleves_classe.count(),
        'semestre': semestre,
        'enseignant': enseignant,  # ✅ Ajouté pour que le template puisse l'utiliser
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/details_notes_eleve_enseignant.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='login')
def saisie_note_enseignant(request, eleve_id, semestre):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"


    # Vérifier si l'utilisateur est un administrateur
    if request.user.is_superuser:
        # Un administrateur peut saisir toutes les matières
        matieres_autorisees = Matiere.objects.all()
    else:
        # Sinon, c'est un enseignant, on vérifie son accès
        enseignant = get_object_or_404(Enseignant, user=request.user)

        # Vérifier si l'enseignant peut accéder à cet élève
        if not enseignant.classes.filter(id=eleve.classe.id).exists():
            messages.error(request, "Vous n'avez pas accès aux informations de cet élève.")
            return redirect('accueil_enseignant')

        # Filtrer uniquement les matières enseignées par cet enseignant
        matieres_autorisees = enseignant.matieres.all()

    # Exclure les matières déjà notées
    notes_existantes = Note.objects.filter(eleve=eleve, semestre=semestre).values_list('matiere_id', flat=True)
    matieres_restantes = matieres_autorisees.exclude(id__in=notes_existantes)

    matiere_selectionnee = None  # Initialisation

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)

            # Vérifier que l'enseignant ne tente pas de saisir une matière qu'il n'enseigne pas
            if not request.user.is_superuser and note.matiere not in matieres_autorisees:
                messages.error(request, "Vous ne pouvez pas saisir des notes pour une matière que vous n'enseignez pas.")
                return redirect('saisie_note_enseignant', eleve_id=eleve.id, semestre=semestre)

            note.eleve = eleve
            note.semestre = semestre
            note.save()
            return redirect('saisie_note_enseignant', eleve_id=eleve.id, semestre=semestre)
    else:
        if matieres_restantes.exists():
            matiere_selectionnee = matieres_restantes.first()
            form = NoteForm(initial={'eleve': eleve, 'matiere': matiere_selectionnee, 'semestre': semestre})
        else:
            messages.info(request, "Toutes les notes ont déjà été saisies pour cet élève.")
            return redirect('details_notes_eleve_enseignant', eleve_id=eleve.id, semestre=semestre)

    context = {
        'eleve': eleve,
        'form': form,
        'matieres_restantes': matieres_restantes,
        'semestre': semestre,
        'matiere_selectionnee': matiere_selectionnee,  # Ajout de la matière sélectionnée
        'annee_scolaire': annee_scolaire,
    }    
    return render(request, 'bulletins/saisie_notes_eleve_ens.html', context)


    

@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_classe(request):
    if request.method == 'POST':
        # Si le formulaire est soumis
        form = ClasseForm(request.POST)
        if form.is_valid():
            form.save()  # Enregistrer la classe dans la base de données
            return redirect('liste_classes')  # Rediriger vers la liste des classes
    else:
        # Si c'est une requête GET, afficher un formulaire vide
        form = ClasseForm()
    
    # Afficher le formulaire dans le template
    return render(request, 'bulletins/saisie_classe.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')   
def detail_classes_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    classes = enseignant.classes.all()  # Récupérer les classes enseignées par cet enseignant
    return render(request, 'bulletins/detail_classes_enseignant.html', {'enseignant': enseignant, 'classes': classes})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_classes_etablissement(request, etablissement_id):
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    classes = Classe.objects.filter(etablissement=etablissement)
    return render(request, 'bulletins/liste_classes_etablissement.html', {'etablissement': etablissement, 'classes': classes})


@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_enseignant(request):
    if request.method == 'POST':
        form = EnseignantForm(request.POST)
        if form.is_valid():
            enseignant = form.save(commit=False)  # Ne pas enregistrer immédiatement
            user = form.cleaned_data.get('user')  # Récupérer l'utilisateur depuis le formulaire
            if user and user.role == 'enseignant':  # Vérifier que l'utilisateur existe et a le rôle 'enseignant'
                enseignant.user = user
                enseignant.save()
                form.save_m2m()  # Enregistrer les relations ManyToMany
                messages.success(request, "L'enseignant a été créé avec succès.")
                return redirect('liste_enseignants')
            else:
                messages.error(request, "Veuillez sélectionner un utilisateur valide avec le rôle 'enseignant'.")
    else:
        form = EnseignantForm()

    context = {
        'form': form,
        'title': 'Créer un enseignant',
    }
    return render(request, 'bulletins/saisie_enseignant.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def liste_enseignants(request):
    query = request.GET.get('q', '')
    enseignants = Enseignant.objects.all()

    if query:
        enseignants = enseignants.filter(Q(nom__icontains=query) | Q(prenom__icontains=query))

    # Pagination (par exemple, 10 classes par page)
    paginator = Paginator(enseignants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bulletins/liste_enseignants.html', {'enseignants': page_obj})



@login_required
@user_passes_test(is_admin, login_url='login')
def liste_classes_etablissement_popup(request, etablissement_id):
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    classes = Classe.objects.filter(etablissement=etablissement)

    # Préparer le contexte pour le template popup
    context = {
        'etablissement': etablissement,
        'classes': classes,
    }
    return render(request, 'bulletins/liste_classes_etablissement_popup.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def liste_eleves_classe_popup(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)

    context = {
        'classe': classe,
        'eleves': eleves,
    }
    return render(request, 'bulletins/popup_liste_eleves_classe.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def eleve(request, eleve_id):
    # Récupérer l'élève ou renvoyer une erreur 404 si non trouvé
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    
    # Récupérer toutes les notes de l'élève
    notes = Note.objects.filter(eleve=eleve)
    
    # Calculer la moyenne générale (si la méthode existe dans le modèle Eleve)
    moyenne_generale = eleve.moyenne_generale()
    
    # Calculer le rang de l'élève (si vous avez implémenté cette fonctionnalité)
    # Par exemple, en utilisant une méthode dans le modèle Eleve
    rang = eleve.calculer_rang()
    
    # Préparer le contexte pour le template
    context = {
        'eleve': eleve,
        'notes': notes,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'annee_scolaire': annee_scolaire,
    }    
    # Rendre le template avec le contexte
    return render(request, 'bulletins/bulletin_eleve.html', context)



def moyenne_generale(self):
    notes = Note.objects.filter(eleve=self)
    total = sum(note.note * note.matiere.coefficient for note in notes)
    coefficients = sum(note.matiere.coefficient for note in notes)
    return total / coefficients if coefficients > 0 else 0



@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_matiere(request):
    if request.method == 'POST':
        # Si le formulaire est soumis
        form = MatiereForm(request.POST)
        if form.is_valid():
            form.save()  # Enregistrer l'élève dans la base de données
            return redirect('liste_matieres')  # Rediriger vers la liste des élèves
    else:
        # Si c'est une requête GET, afficher un formulaire vide
        form = MatiereForm()
    
    # Afficher le formulaire dans le template
    return render(request, 'bulletins/saisie_matieres.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_matieres(request):
    matieres = Matiere.objects.all()
    return render(request, 'bulletins/liste_matieres.html', {'matieres': matieres})


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def saisie_note(request):
    if request.method == 'POST':
        # Si le formulaire est soumis
        form = NoteForm(request.POST)
        if form.is_valid():
            form.save()  # Enregistrer la note dans la base de données
            return redirect('liste_notes')  # Rediriger vers la liste des notes
    else:
        # Si c'est une requête GET, afficher un formulaire vide
        form = NoteForm()
    
    # Afficher le formulaire dans le template
    return render(request, 'bulletins/saisie_note.html', {'form': form})



@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def saisie_notes_eleve(request, eleve_id, semestre):
    eleve = get_object_or_404(Eleve, id=eleve_id)

    # Vérifier si l'élève a une classe
    if not eleve.classe:
        messages.warning(request, "Cet élève n'est pas encore affecté à une classe.")
        return redirect('liste_eleves')  # Remplace 'liste_eleves' par une page appropriée

    classe = eleve.classe
    etablissement = classe.etablissement
    annee_scolaire = etablissement.annee_scolaire if classe else None

    # Récupération des matières obligatoires
    matieres_obligatoires = Matiere.objects.filter(niveaux_obligatoires=classe.niveau)

    # Par défaut, aucun matière optionnelle
    matieres_optionnelles = Matiere.objects.none()

    # Si l'élève est en 4e ou 3e, récupérer uniquement ses matières optionnelles choisies
    if classe.niveau.nom in ["4e", "3e"]:
        matieres_optionnelles = Matiere.objects.filter(
            id__in=ChoixMatiere.objects.filter(eleve=eleve).values_list("matiere_id", flat=True)
        )

    # Union des matières obligatoires et des matières optionnelles sélectionnées par l'élève
    matieres_autorisees = matieres_obligatoires | matieres_optionnelles

    # Si l'utilisateur est un enseignant, filtrer les matières qu'il enseigne
    if not request.user.is_superuser:
        enseignant = get_object_or_404(Enseignant, user=request.user)

        # Vérifier que l'enseignant a accès à la classe de l'élève
        if not enseignant.classes.filter(id=classe.id).exists():
            messages.error(request, "Vous n'avez pas accès aux informations de cet élève.")
            return redirect('accueil_enseignant')

        # Filtrer uniquement les matières enseignées par l'enseignant
        matieres_autorisees = matieres_autorisees.filter(
            id__in=enseignant.matieres.values_list('id', flat=True)
        )

    # Exclure les matières déjà notées pour ce semestre
    notes_existantes = Note.objects.filter(eleve=eleve, semestre=semestre).values_list('matiere_id', flat=True)
    matieres_restantes = matieres_autorisees.exclude(id__in=notes_existantes)

    matiere_selectionnee = None

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)

            if not request.user.is_superuser and note.matiere not in matieres_autorisees:
                messages.error(request, "Vous ne pouvez pas saisir des notes pour une matière que vous n'enseignez pas.")
                return redirect('saisie_notes_eleve', eleve_id=eleve.id, semestre=semestre)

            note.eleve = eleve
            note.semestre = semestre
            note.save()
           # messages.success(request, "Note enregistrée avec succès.")
            return redirect('saisie_notes_eleve', eleve_id=eleve.id, semestre=semestre)

    else:
        if matieres_restantes.exists():
            matiere_selectionnee = matieres_restantes.first()
            form = NoteForm(initial={'eleve': eleve, 'matiere': matiere_selectionnee, 'semestre': semestre})
        else:
            messages.info(request, "Toutes les notes ont déjà été saisies pour cet élève.")
            return redirect('details_notes_eleve', eleve_id=eleve.id, semestre=semestre)

    context = {
        'eleve': eleve,
        'form': form,
        'matieres_restantes': matieres_restantes,
        'semestre': semestre,
        'matiere_selectionnee': matiere_selectionnee,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/saisie_notes_eleve.html', context)





@login_required
def details_notes_eleve(request, eleve_id, semestre):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe else None  # ✅ Récupération via l'établissement
    moyennes_par_matiere = []
    total_points_general = 0
    total_coefficients = 0

    # Récupérer toutes les notes de l'élève pour ce semestre
    notes = Note.objects.filter(eleve=eleve, semestre=semestre)

    # Préparer les données pour le contexte
    for note in notes:
        moyenne_matiere = (note.note_devoir + note.note_composition) / 2.0
        points_matiere = moyenne_matiere * note.matiere.coefficient
        appreciation = generer_appreciation(moyenne_matiere)

        # Récupérer toutes les moyennes des élèves de la classe pour cette matière
        moyennes_classe = [
            (n.eleve.id, (n.note_devoir + n.note_composition) / 2.0)
            for n in Note.objects.filter(
                eleve__classe=eleve.classe,
                semestre=semestre,
                matiere=note.matiere
            ).order_by('-note_devoir', '-note_composition')
        ]

        # Trier et déterminer le rang
        moyennes_classe.sort(key=lambda x: x[1], reverse=True)
        rang_matiere = next((i + 1 for i, (eid, _) in enumerate(moyennes_classe) if eid == eleve.id), None)

        moyennes_par_matiere.append({
            'note_id': note.id,
            'matiere': note.matiere.nom,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': moyenne_matiere,
            'points_matiere': points_matiere,
            'rang_matiere': rang_matiere,  # ✅ Ajout du rang par matière
            'semestre': semestre,
            'appreciation': appreciation,  # Ajout de l'appréciation
        })

        total_points_general += points_matiere
        total_coefficients += note.matiere.coefficient

    # Calcul de la moyenne générale
    moyenne_generale = total_points_general / total_coefficients if total_coefficients > 0 else None

    # Calcul du classement général
    eleves_classe = Eleve.objects.filter(classe=eleve.classe)
    classement = eleves_classe.annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=semestre)
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coeffs=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=semestre)),
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne=Case(
            When(total_coeffs=0, then=Value(None)),
            default=ExpressionWrapper(F('total_points') / F('total_coeffs'), output_field=FloatField()),
            output_field=FloatField()
        )
    ).order_by('-moyenne')

    # Déterminer le rang général de l'élève
    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    context = {
        'eleve': eleve,
        'moyennes_par_matiere': moyennes_par_matiere,
        'total_points_general': total_points_general,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'total_eleves': eleves_classe.count(),
        'semestre': semestre,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/details_notes_eleve.html', context)


def details_notes_eleve_restaurer(request, eleve_id, semestre, annee_scolaire):
    # Déterminer l'année scolaire actuelle si non spécifiée
    if annee_scolaire is None or annee_scolaire == "None":
        annee_scolaire = "2024-2025"  # Remplacez par une méthode dynamique si nécessaire

    eleve = get_object_or_404(Eleve, id=eleve_id)
    total_eleves = Eleve.objects.count()  # Nombre total d'élèves dans la base

    moyennes_par_matiere = []
    total_points_general = 0
    total_coefficients = 0

    # ✅ Récupérer les notes archivées de l'élève pour l'année et le semestre spécifiés
    notes = NoteArchive.objects.filter(eleve=eleve, semestre=semestre, annee_scolaire=annee_scolaire)

    # ✅ Préparation des rangs par matière
    rangs_par_matiere = {}
    
    for note in notes:
        moyenne_matiere = (note.note_devoir + note.note_composition) / 2.0
        points_matiere = moyenne_matiere * note.matiere.coefficient

        # ✅ Calculer l’appréciation pour chaque matière
        if moyenne_matiere >= 16:
            appreciation_matiere = "Excellent"
        elif moyenne_matiere >= 14:
            appreciation_matiere = "Très Bien"
        elif moyenne_matiere >= 12:
            appreciation_matiere = "Bien"
        elif moyenne_matiere >= 10:
            appreciation_matiere = "Assez Bien"
        else:
            appreciation_matiere = "Insuffisant"

        moyennes_par_matiere.append({
            'matiere': note.matiere.nom,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': moyenne_matiere,
            'points_matiere': points_matiere,
            'appreciation': appreciation_matiere,
            'semestre': semestre,
        })

        total_points_general += points_matiere
        total_coefficients += note.matiere.coefficient

    # ✅ Calcul de la moyenne générale restaurée
    moyenne_generale = total_points_general / total_coefficients if total_coefficients > 0 else None

    # ✅ Calcul du rang général et du rang par matière
    rang_general = None

    if notes.exists():
        # 📌 1. Calcul des moyennes générales pour le classement
        classement_general = NoteArchive.objects.filter(semestre=semestre, annee_scolaire=annee_scolaire)

        moyennes_generales = {}
        
        for note in classement_general:
            if note.eleve not in moyennes_generales:
                moyennes_generales[note.eleve] = {'total_points': 0, 'total_coefficients': 0}
            moyenne_matiere = (note.note_devoir + note.note_composition) / 2.0
            moyennes_generales[note.eleve]['total_points'] += moyenne_matiere * note.matiere.coefficient
            moyennes_generales[note.eleve]['total_coefficients'] += note.matiere.coefficient

        # 📌 2. Calcul de la moyenne générale par élève
        moyennes_generales = {
            eleve: data['total_points'] / data['total_coefficients'] if data['total_coefficients'] > 0 else 0
            for eleve, data in moyennes_generales.items()
        }

        # 📌 3. Classement des élèves selon leur moyenne générale
        classement_eleve = sorted(moyennes_generales.items(), key=lambda x: x[1], reverse=True)
        
        # 📌 4. Attribution du rang général
        rang_general = [eleve[0] for eleve in classement_eleve].index(eleve) + 1

        # 📌 5. Calcul des rangs par matière
        for matiere in notes.values_list('matiere', flat=True).distinct():
            notes_matiere = NoteArchive.objects.filter(matiere=matiere, semestre=semestre, annee_scolaire=annee_scolaire)
            
            moyennes_par_eleve = {
                note.eleve: (note.note_devoir + note.note_composition) / 2.0
                for note in notes_matiere
            }

            classement_matiere = sorted(moyennes_par_eleve.items(), key=lambda x: x[1], reverse=True)
            
            rangs_par_matiere[matiere] = {eleve: idx + 1 for idx, (eleve, _) in enumerate(classement_matiere)}

    # ✅ Appréciation générale
    appreciation_generale = None
    if moyenne_generale is not None:
        if moyenne_generale >= 16:
            appreciation_generale = "Excellent 🌟"
        elif moyenne_generale >= 14:
            appreciation_generale = "Très Bien ✅"
        elif moyenne_generale >= 12:
            appreciation_generale = "Bien 👍"
        elif moyenne_generale >= 10:
            appreciation_generale = "Passable 🙂"
        elif moyenne_generale >= 9:
            appreciation_generale = "Insuffisant ⚠️"    
        else:
            appreciation_generale = "Faible ❗"
    else:
        appreciation_generale = "Pas de notes restaurées"


       
    # ✅ Ajout du rang par matière dans les moyennes
    for item in moyennes_par_matiere:
        matiere_id = Matiere.objects.get(nom=item['matiere']).id
        item['rang_matiere'] = rangs_par_matiere.get(matiere_id, {}).get(eleve, "Non classé")

    context = {
        'eleve': eleve,
        'moyennes_par_matiere': moyennes_par_matiere,
        'total_points_general': total_points_general,
        'moyenne_generale': moyenne_generale,
        'semestre': semestre,
        'annee_scolaire': annee_scolaire,
        'rang_general': rang_general,
        'appreciation_generale': appreciation_generale,
        'total_eleves': total_eleves,
    }
    return render(request, 'bulletins/details_notes_eleve_restaurer.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def details_notes_eleve_classe(request, eleve_id, semestre):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe else None  # ✅ Récupération via l'établissement
    moyennes_par_matiere = []
    total_points_general = 0
    total_coefficients = 0

    # Filtrer les notes selon le semestre avec annotation correcte
    notes = Note.objects.filter(eleve=eleve, semestre=semestre).annotate(
        moyenne_calcul=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_calcul=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    # Préparer les données pour le contexte
    for note in notes:
        moyennes_par_matiere.append({
            'note_id': note.id,
            'matiere': note.matiere.nom,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': note.moyenne_calcul,
            'points_matiere': note.points_calcul,
            'semestre': semestre,
        })
        total_points_general += note.points_calcul
        total_coefficients += note.matiere.coefficient

    # Calcul de la moyenne générale (None si pas de notes)
    moyenne_generale = total_points_general / total_coefficients if total_coefficients > 0 else None

    # Calcul du classement pour ce semestre
    eleves_classe = Eleve.objects.filter(classe=eleve.classe)
    classement = eleves_classe.annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=semestre)  # Filtrer uniquement sur le semestre
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coeffs=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=semestre)),
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne=Case(
            When(total_coeffs=0, then=Value(None)),  # Mettre None au lieu de 0
            default=ExpressionWrapper(F('total_points') / F('total_coeffs'), output_field=FloatField()),
            output_field=FloatField()
        )
    ).order_by('-moyenne')

    # Déterminer le rang de l'élève
    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    context = {
        'eleve': eleve,
        'moyennes_par_matiere': moyennes_par_matiere,
        'total_points_general': total_points_general,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'total_eleves': eleves_classe.count(),
        'semestre': semestre,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/details_notes_eleve_classe.html', context)



@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def modifier_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()  # Enregistrer les modifications
            # Rediriger vers les détails du semestre concerné
            return redirect('details_notes_eleve', eleve_id=note.eleve.id, semestre=note.semestre)
    else:
        form = NoteForm(instance=note)
        annee_scolaire = note.eleve.classe.etablissement.annee_scolaire if note.eleve.classe else "Non définie"


    context = {
        'form': form,
        'note': note,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/modifier_note.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def modifier_note_ens(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()  # Enregistrer les modifications
            # Rediriger vers les détails du semestre concerné
            return redirect('details_notes_eleve_enseignant', eleve_id=note.eleve.id, semestre=note.semestre)
    else:
        form = NoteForm(instance=note)
        annee_scolaire = note.eleve.classe.etablissement.annee_scolaire if note.eleve.classe else "Non définie"

    context = {
        'form': form,
        'note': note,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/modifier_note_ens.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def impression_bulletins_classe1(request, classe_id, semestre):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)
    total_eleve = eleves.count()
    
    bulletins = []
    moyennes_classes = {}
    nombre_absences = 0
    
    ordre_matieres = [
        "Rédaction", "Orthographe", "Texte suivi de questions", "Mathématiques",
        "Science Physique", "Anglais", "Arabe", "Espagnol", "Histoire/Géographie", "Education civique",
        "Sc. De Vie et de la terre", "Economie familiale", "Ed. Physique et Sportive"
    ]
    # ✅ Initialisation d'annee_scolaire pour éviter l'erreur si eleves est vide
    annee_scolaire = "Non définie"
    
    for eleve in eleves:
        annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

        # Récupérer les matières suivies par l'élève
        matieres_suivies = Matiere.objects.filter(
            Q(niveaux_obligatoires=classe.niveau) |  
            Q(id__in=ChoixMatiere.objects.filter(eleve=eleve).values_list('matiere_id', flat=True))
        ).distinct()

        
        notes = Note.objects.filter(eleve=eleve, semestre=semestre, matiere__in=matieres_suivies).annotate(
            moyenne_calculee=ExpressionWrapper(
                (F('note_devoir') + F('note_composition')) / 2.0,
                output_field=FloatField()
            ),
            points_matiere=ExpressionWrapper(
                ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                output_field=FloatField()
            )
        )

        total_points = sum(note.points_matiere for note in notes)
        total_coefficients = sum(note.matiere.coefficient for note in notes)
        moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0

        moyennes_classes[eleve.id] = moyenne_generale

        rangs_par_matiere = {}
        appreciations_par_matiere = {}

        for note in notes:
            classement_matiere = Note.objects.filter(
                matiere=note.matiere, semestre=semestre, eleve__classe=classe
            ).annotate(
                moyenne=ExpressionWrapper(
                    (F('note_devoir') + F('note_composition')) / 2.0,
                    output_field=FloatField()
                )
            ).order_by('-moyenne')

            rang_matiere = next((i + 1 for i, n in enumerate(classement_matiere) if n.eleve.id == eleve.id), None)
            rangs_par_matiere[note.matiere.nom] = rang_matiere
            appreciations_par_matiere[note.matiere.nom] = generer_appreciation(note.moyenne_calculee)
        
        absences = Absence.objects.filter(eleve=eleve, semestre=semestre)
        nombre_absences = absences.count()

        notes_par_matiere = [
            {
                'matiere': matiere,
                'coefficient': next((note.matiere.coefficient for note in notes if note.matiere.nom == matiere), None),
                'note_devoir': next((note.note_devoir for note in notes if note.matiere.nom == matiere), None),
                'note_composition': next((note.note_composition for note in notes if note.matiere.nom == matiere), None),
                'moyenne_matiere': next((note.moyenne_calculee for note in notes if note.matiere.nom == matiere), None),
                'points_matiere': next((note.points_matiere for note in notes if note.matiere.nom == matiere), None),
                'rang_matiere': rangs_par_matiere.get(matiere, None),
                'appreciation': appreciations_par_matiere.get(matiere, ""),
            }
            for matiere in ordre_matieres if matiere in matieres_suivies.values_list('nom', flat=True)
        ]

        bulletins.append({
            'eleve': eleve,
            'notes_par_matiere': notes_par_matiere,
            'total_points': total_points,
            'moyenne_generale': moyenne_generale,
            'total_coefficients': total_coefficients,
            'nombre_absences': nombre_absences,
        })

    # ✅ Classement général des élèves par moyenne générale
    classement_general = sorted(moyennes_classes.items(), key=lambda x: x[1], reverse=True)
    rang = {eleve_id: i + 1 for i, (eleve_id, _) in enumerate(classement_general)}

    # ✅ Ajout du rang général dans les bulletins
    for bulletin in bulletins:
        bulletin['rang'] = rang.get(bulletin['eleve'].id, None)

    moyenne_classe = sum(moyennes_classes.values()) / len(moyennes_classes) if moyennes_classes else 0
    meilleure_moyenne = max(moyennes_classes.values(), default=0)

    context = {
        'classe': classe,
        'bulletins': bulletins,
        'moyenne_classe': moyenne_classe,
        'meilleure_moyenne': meilleure_moyenne,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,
        'total_eleve': total_eleve,
    }

    return render(request, 'bulletins/impression_bulletins_classe1.html', context)




@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def impression_bulletins_classe2(request, classe_id, semestre):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)
    total_eleves = eleves.count()
    
    bulletins = []
    moyennes_classes = []
    moyennes_annuelles = {}
    moyennes_semestrielles = {}
    nombre_absences = 0

    ordre_matieres = [
        "Rédaction", "Orthographe", "Texte suivi de questions", "Mathématiques",
        "Science Physique", "Anglais", "Arabe", "Espagnol", "Histoire/Géographie", "Education civique",
        "Sc. De Vie et de la terre", "Economie familiale", "Ed. Physique et Sportive"
    ]
    # ✅ Initialisation d'annee_scolaire pour éviter l'erreur si eleves est vide
    annee_scolaire = "Non définie"

    for eleve in eleves:
        annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

        # Récupérer les matières suivies par l'élève
        matieres_suivies = Matiere.objects.filter(
            Q(niveaux_obligatoires=classe.niveau) |  
            Q(id__in=ChoixMatiere.objects.filter(eleve=eleve).values_list('matiere_id', flat=True))
        ).distinct()


        # Moyenne du semestre actuel
        notes = Note.objects.filter(eleve=eleve, semestre=semestre, matiere__in=matieres_suivies).annotate(
            moyenne_calculee=ExpressionWrapper(
                (F('note_devoir') + F('note_composition')) / 2.0,
                output_field=FloatField()
            ),
            points_matiere=ExpressionWrapper(
                ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                output_field=FloatField()
            )
        )

        total_points = sum(note.points_matiere for note in notes)
        total_coefficients = sum(note.matiere.coefficient for note in notes)

        if total_coefficients > 0:
            moyenne_generale = total_points / total_coefficients
            moyennes_classes.append(moyenne_generale)
            moyennes_semestrielles[eleve.id] = moyenne_generale
        else:
           # print(f"⚠️ Aucune note pour {eleve.nom} en Semestre {semestre}, il est ignoré du classement.")
            moyenne_generale = 0  # Éviter les erreurs de division par zéro

        # Moyenne du semestre 1
        notes_semestre_1 = Note.objects.filter(eleve=eleve, semestre=1).annotate(
            moyenne_calculee=ExpressionWrapper(
                (F('note_devoir') + F('note_composition')) / 2.0,
                output_field=FloatField()
            ),
            points_matiere=ExpressionWrapper(
                ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                output_field=FloatField()
            )
        )

        total_points_s1 = sum(note.points_matiere for note in notes_semestre_1)
        total_coefficients_s1 = sum(note.matiere.coefficient for note in notes_semestre_1)
        moyenne_semestre_1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0

        # Moyenne annuelle
        moyenne_annuelle = (moyenne_semestre_1 + moyenne_generale) / 2
        moyennes_annuelles[eleve.id] = moyenne_annuelle
        passe_classe = "Oui" if moyenne_annuelle >= 10 else "Non"

        # Classement par matière
        rangs_par_matiere = {}
        appreciations_par_matiere = {}

        for note in notes:
            classement_matiere = Note.objects.filter(
                matiere=note.matiere, 
                semestre=semestre, 
                eleve__classe=classe
            ).annotate(
                moyenne=ExpressionWrapper(
                    (F('note_devoir') + F('note_composition')) / 2.0,
                    output_field=FloatField()
                )
            ).order_by('-moyenne')

            rang_matiere = next((i + 1 for i, n in enumerate(classement_matiere) if n.eleve.id == eleve.id), None)
            rangs_par_matiere[note.matiere.nom] = rang_matiere
            appreciations_par_matiere[note.matiere.nom] = generer_appreciation(note.moyenne_calculee)

        # Nombre total d'absences
        absences = Absence.objects.filter(eleve=eleve, semestre=1)  # Filtrer seulement le semestre 1
        nombre_absences = absences.count()

        # Organiser les notes selon l'ordre fixé
        matieres_suivies_noms = set(matieres_suivies.values_list('nom', flat=True))

        notes_par_matiere = [
            {
                'matiere': matiere,
                'coefficient': next((note.matiere.coefficient for note in notes if note.matiere.nom == matiere), None),
                'note_devoir': next((note.note_devoir for note in notes if note.matiere.nom == matiere), None),
                'note_composition': next((note.note_composition for note in notes if note.matiere.nom == matiere), None),
                'moyenne_matiere': next((note.moyenne_calculee for note in notes if note.matiere.nom == matiere), None),
                'points_matiere': next((note.points_matiere for note in notes if note.matiere.nom == matiere), None),
                'rang_matiere': rangs_par_matiere.get(matiere, None),
                'appreciation': appreciations_par_matiere.get(matiere, ""),
            }
            for matiere in ordre_matieres if matiere in matieres_suivies_noms  # Utilisation de l'ensemble
        ]


        bulletins.append({
            'eleve': eleve,
            'notes_par_matiere': notes_par_matiere,
            'total_points': total_points,
            'moyenne_semestre_1': moyenne_semestre_1,
            'moyenne_generale': moyenne_generale,
            'moyenne_annuelle': moyenne_annuelle,
            'total_coefficients': total_coefficients,
            'nombre_absences': nombre_absences,
            'passe_classe': passe_classe,            
        })

    # Classement semestriel (Semestre 2) - Exclure les élèves sans notes
    classement_semestriel = sorted(
        [(eleve_id, moyenne) for eleve_id, moyenne in moyennes_semestrielles.items() if moyenne > 0],
        key=lambda x: x[1], 
        reverse=True
    )
    rangs_semestriels = {eleve_id: i + 1 for i, (eleve_id, _) in enumerate(classement_semestriel)}

    # Classement annuel
    classement_annuel = sorted(moyennes_annuelles.items(), key=lambda x: x[1], reverse=True)
    rangs_annuels = {eleve_id: i + 1 for i, (eleve_id, _) in enumerate(classement_annuel)}

    # Mise à jour des bulletins avec le rang du semestre 2 et le rang annuel
    for bulletin in bulletins:
        bulletin['rang_semestriel'] = rangs_semestriels.get(bulletin['eleve'].id, None)
        bulletin['rangs_annuels'] = rangs_annuels.get(bulletin['eleve'].id, None)

    # Moyenne et meilleure moyenne de la classe
    moyenne_classe = sum(moyennes_classes) / len(moyennes_classes) if moyennes_classes else 0
    meilleure_moyenne = max(moyennes_classes, default=0)

    context = {
        'classe': classe,
        'bulletins': bulletins,
        'moyenne_classe': moyenne_classe,
        'meilleure_moyenne': meilleure_moyenne,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,
        'rangs_annuels': rangs_annuels,
        'rangs_semestriels': rangs_semestriels,
        'total_eleves': total_eleves,
    }

    return render(request, 'bulletins/impression_bulletins_classe2.html', context)





@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_classes_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    
    if request.method == 'POST':
        form = EnseignantClassesForm(request.POST, instance=enseignant)
        if form.is_valid():
            form.save()
            return redirect('liste_enseignants')  # Rediriger vers la liste des enseignants
    else:
        form = EnseignantClassesForm(instance=enseignant)
    
    context = {
        'enseignant': enseignant,
        'form': form,
    }
    return render(request, 'bulletins/saisie_classes_enseignant.html', context)



@login_required
def recherche_globale(request):
    resultats = {}
    type_recherche = None

    if request.method == 'POST':
        form = RechercheGlobaleForm(request.POST)
        if form.is_valid():
            type_recherche = form.cleaned_data['type_recherche']
            classe = form.cleaned_data.get('classe')
            eleve = form.cleaned_data.get('eleve')
            enseignant = form.cleaned_data.get('enseignant')
            etablissement = form.cleaned_data.get('etablissement')
            semestre = form.cleaned_data.get('semestre')

          # 🔹 Recherche des élèves d'une classe
            if type_recherche == 'eleves_classe' and classe and semestre:
                eleves = Eleve.objects.filter(classe=classe, note__semestre=semestre).annotate(
                    total_points=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                                output_field=FloatField()
                            ),
                            output_field=FloatField()
                        ),
                        Value(0.0),
                        output_field=FloatField()
                    ),
                    total_coefficients=Coalesce(
                        Sum('note__matiere__coefficient', output_field=FloatField()),
                        Value(1.0),
                        output_field=FloatField()
                    ),
                    moyenne_generale=ExpressionWrapper(
                        F('total_points') / F('total_coefficients'),
                        output_field=FloatField()
                    )
                ).annotate(
                    rang=Window(
                        expression=Rank(),
                        order_by=F('moyenne_generale').desc()
                    )
                ).order_by('-moyenne_generale')

                resultats = {'eleves': eleves, 'classe': classe, 'semestre': semestre}


           # 🔹 Meilleur élève d'une classe avec prise en compte du semestre
            elif type_recherche == 'meilleur_eleve' and classe and form.cleaned_data.get('semestre'):
                semestre = form.cleaned_data['semestre']

                meilleur = Eleve.objects.filter(classe=classe, note__semestre=semestre).annotate(
                    moyenne=ExpressionWrapper(
                        Coalesce(
                            Sum(
                                ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                                output_field=FloatField()
                            ),
                            Value(0.0),
                            output_field=FloatField()
                        ) / Coalesce(Sum('note__matiere__coefficient', output_field=FloatField()), Value(1.0)),
                        output_field=FloatField()
                    )
                ).order_by('-moyenne').first()

                resultats = {'meilleur_eleve': meilleur, 'classe': classe, 'semestre': semestre}


            # 🔹 Liste des bulletins d'une classe avec prise en compte du semestre
            elif type_recherche == 'bulletins_classe' and classe and form.cleaned_data.get('semestre'):
                semestre = form.cleaned_data['semestre']
                resultats = {'bulletins_classe': classe, 'semestre': semestre}
    

            # 🔹 Bulletin d'un élève
            elif type_recherche == 'bulletin_eleve' and form.cleaned_data.get('eleve') and form.cleaned_data.get('semestre'):
                eleve = form.cleaned_data['eleve']
                semestre = form.cleaned_data['semestre']
                resultats = {'eleve': eleve, 'classe': eleve.classe, 'semestre': semestre}

            # 🔹 Classes d'un enseignant
            elif type_recherche == 'classes_enseignant' and enseignant:
                classes = enseignant.classes.all()
                resultats = {'classes': classes, 'enseignant': enseignant}

           # 🔹 Enseignants d'un établissement
            elif type_recherche == 'enseignants_etablissement' and etablissement:
                enseignants = Enseignant.objects.filter(classes__etablissement=etablissement).distinct().prefetch_related('matieres')
                resultats = {'enseignants': enseignants, 'etablissement': etablissement}


            # 🔹 Liste des classes d'un établissement
            elif type_recherche == 'liste_classes_etablissement' and etablissement:
                classes = Classe.objects.filter(etablissement=etablissement)
                resultats = {'classes_etablissement': classes, 'etablissement': etablissement}
            # 🔹 Élèves en retard de paiement
            elif type_recherche == 'eleves_retard_paiement':
                eleves = Eleve.objects.filter(
                    echeances__statut='impaye',
                    echeances__date_echeance__lt=date.today()  # Seulement les échéances en retard
                ).distinct()
                resultats = {'eleves_retard': eleves}

            # 🔹 Paiements effectués par un élève
            elif type_recherche == 'paiements_par_eleve' and eleve:
                paiements = Paiement.objects.filter(eleve=eleve)
                resultats = {'paiements': paiements, 'eleve': eleve}

            # 🔹 Paiements effectués sur une période donnée
            elif type_recherche == 'paiements_par_periode':
                date_debut = form.cleaned_data.get('date_debut')
                date_fin = form.cleaned_data.get('date_fin')

                if date_debut and date_fin:
                    paiements = Paiement.objects.filter(date_paiement__range=[date_debut, date_fin])
                    resultats = {'paiements_periode': paiements, 'date_debut': date_debut, 'date_fin': date_fin}
    

    else:
        form = RechercheGlobaleForm()

    return render(request, 'bulletins/recherche_globale.html', {
        'form': form,
        'type_recherche': type_recherche,
        'resultats': resultats
    })



@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_etablissement(request, etablissement_id):
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    if request.method == 'POST':
        form = EtablissementForm(request.POST, request.FILES, instance=etablissement)
        if form.is_valid():
            form.save()
            return redirect('liste_etablissements')
    else:
        form = EtablissementForm(instance=etablissement)
    return render(request, 'bulletins/saisie_etablissement.html', {'form': form, 'title': 'Modifier un établissement'})



@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_etablissement(request, etablissement_id):
    etablissement = get_object_or_404(Etablissement, id=etablissement_id)
    if request.method == 'POST':
        etablissement.delete()
        return redirect('liste_etablissements')
    return render(request, 'bulletins/confirmation_suppression.html', {'objet': etablissement, 'type': 'Établissement'})



@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    if request.method == 'POST':
        form = EnseignantForm(request.POST, request.FILES, instance=enseignant)
        if form.is_valid():
            form.save()
            return redirect('liste_enseignants')
    else:
        form = EnseignantForm(instance=enseignant)
    return render(request, 'bulletins/saisie_enseignant.html', {'form': form, 'title': 'Modifier un enseignant'})



@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    if request.method == 'POST':
        enseignant.delete()
        return redirect('liste_enseignants')
    return render(request, 'bulletins/confirmation_suppression.html', {'objet': enseignant, 'type': 'Enseignant'})



@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    if request.method == 'POST':
        form = ClasseForm(request.POST, request.FILES, instance=classe)
        if form.is_valid():
            form.save()
            return redirect('liste_classes')
    else:
        form = ClasseForm(instance=classe)
    return render(request, 'bulletins/saisie_classe.html', {'form': form, 'title': 'Modifier une classe'})



@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    if request.method == 'POST':
        classe.delete()
        return redirect('liste_classes')
    return render(request, 'bulletins/confirmation_suppression.html', {'objet': classe, 'type': 'Classes'})





@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    if request.method == 'POST':
        form = EleveForm(request.POST, request.FILES, instance=eleve)
        if form.is_valid():
            form.save()
            return redirect('liste_eleves')
    else:
        form = EleveForm(instance=eleve)
    return render(request, 'bulletins/saisie_eleve.html', {'form': form, 'title': 'Modifier un eleve'})



@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    if request.method == 'POST':
        eleve.delete()
        return redirect('liste_eleves')
    return render(request, 'bulletins/confirmation_suppression.html', {'objet': eleve, 'type': 'Eleve'})




@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_matiere(request, matiere_id):
    matiere = get_object_or_404(Matiere, id=matiere_id)
    if request.method == 'POST':
        form = MatiereForm(request.POST, request.FILES, instance=matiere)
        if form.is_valid():
            form.save()
            return redirect('liste_matieres')
    else:
        form = MatiereForm(instance=matiere)
    return render(request, 'bulletins/saisie_matieres.html', {'form': form, 'title': 'Modifier une matiere'})



@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_matiere(request, matiere_id):
    matiere = get_object_or_404(Eleve, id=matiere_id)
    if request.method == 'POST':
        matiere.delete()
        return redirect('liste_matieres')
    return render(request, 'bulletins/confirmation_suppression.html', {'objet': matiere, 'type': 'Matiere'})



@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def calcul_passage_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    eleves = Eleve.objects.filter(classe=classe)


    resultats = []
    for eleve in eleves:
        annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"
        # Calcul de la moyenne générale pour chaque semestre
        moyennes_semestres = {}
        for semestre in [1, 2]:
            notes = Note.objects.filter(eleve=eleve, semestre=semestre).annotate(
                points_matiere=ExpressionWrapper(
                    ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                    output_field=FloatField()
                )
            )
            total_points = sum(note.points_matiere for note in notes)
            total_coefficients = sum(note.matiere.coefficient for note in notes)
            moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0
            moyennes_semestres[semestre] = moyenne_generale

        # Calcul de la moyenne annuelle
        moyenne_annuelle = sum(moyennes_semestres.values()) / len(moyennes_semestres) if moyennes_semestres else 0

        # Déterminer si l'élève passe en classe supérieure
        seuil_passage = 10  # Seuil pour passer en classe supérieure
        passe_classe = moyenne_annuelle >= seuil_passage

        resultats.append({
            'eleve': eleve,
            'moyenne_semestre_1': moyennes_semestres.get(1, 0),
            'moyenne_semestre_2': moyennes_semestres.get(2, 0),
            'moyenne_annuelle': moyenne_annuelle,
            'passe_classe': passe_classe,            
        })

    context = {
        'classe': classe,
        'resultats': resultats,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/calcul_passage_classe.html', context)



def generer_appreciation(moyenne):
    """Retourne une appréciation basée sur la moyenne."""
    if moyenne >= 16:
        return "Excellent 🌟"
    elif moyenne >= 14:
        return "Très Bien ✅"
    elif moyenne >= 12:
        return "Bien 👍"
    elif moyenne >= 10:
        return "Assez Bien 🙂"
    elif moyenne >= 9:
        return "Passable ⚠️"
    elif moyenne >= 8:
        return "Insuffisant ❌"
    else:
        return "Faible ❗"

@login_required
@user_passes_test(is_admin, login_url='login')
def bulletin_semestre_1(request, eleve_id):
    # Récupérer l'élève et vérifier sa classe
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    classe = eleve.classe
    etablissement = classe.etablissement if classe else None
    total_eleves = Eleve.objects.filter(classe=classe).count() if classe else 1
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    # Ordre d'affichage des matières
    ordre_matieres = [
        "Rédaction", "Orthographe", "Texte suivi de questions", "Mathématiques",
        "Science Physique", "Anglais", "Arabe", "Espagnol", "Histoire/Géographie", "Education civique",
        "Sc. De Vie et de la terre", "Economie familiale", "Ed. Physique et Sportive"
    ]

    # Récupérer les notes de l'élève pour le semestre 1
    notes = Note.objects.filter(eleve=eleve, semestre=1).select_related('matiere')

    # Initialisation des variables
    total_points = 0
    total_coefficients = 0
    notes_avec_rangs = []

    for note in notes:
        moyenne_matiere = (note.note_devoir + note.note_composition) / 2.0
        points_matiere = moyenne_matiere * note.matiere.coefficient

        # Récupérer le rang de l'élève pour cette matière
        moyennes_classe = Note.objects.filter(
            eleve__classe=classe,
            matiere=note.matiere
        ).annotate(
            moyenne=ExpressionWrapper((F('note_devoir') + F('note_composition')) / 2.0, output_field=FloatField())
        ).order_by('-moyenne')

        rang_matiere = next((i + 1 for i, n in enumerate(moyennes_classe) if n.eleve.id == eleve.id), None)

        # Génération de l'appréciation dynamique
        appreciation = generer_appreciation(moyenne_matiere)

        notes_avec_rangs.append({
            'matiere': note.matiere.nom,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': moyenne_matiere,
            'points_matiere': points_matiere,
            'appreciation': appreciation,  # Ajout de l'appréciation ici
            'rang_matiere': rang_matiere,
        })

        total_points += points_matiere
        total_coefficients += note.matiere.coefficient

    # Trier les matières selon l'ordre prédéfini
    notes_avec_rangs.sort(key=lambda note: ordre_matieres.index(note['matiere']) if note['matiere'] in ordre_matieres else len(ordre_matieres))

    # Calcul de la moyenne générale
    moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0.0

    # Classement général des élèves
    classement = Eleve.objects.filter(classe=classe).annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=1),
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=1), output_field=FloatField()),
            Value(1.0)
        ),
        moyenne=ExpressionWrapper(F('total_points') / F('total_coefficients'), output_field=FloatField())
    ).filter(moyenne__gt=0).order_by('-moyenne')

    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    moyenne_classe = (
        classement.aggregate(moyenne_classe=Coalesce(Sum('moyenne') / total_eleves, Value(0.0)))['moyenne_classe']
        if total_eleves > 0 else 0.0
    )

    meilleure_moyenne = classement.first().moyenne if classement.exists() else 0.0

    # Gestion des absences
    absences = Absence.objects.filter(eleve=eleve, semestre=1)
    total_absences = absences.count()
    absences = Absence.objects.filter(eleve=eleve, semestre=1)  # Filtrer seulement le semestre 1      

    today = timezone.now()

    context = {
        'eleve': eleve,
        'notes': notes_avec_rangs,
        'total_points': total_points,
        'total_coefficients': total_coefficients,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'moyenne_classe': moyenne_classe,
        'meilleure_moyenne': meilleure_moyenne,
        'today': today,
        'annee_scolaire': annee_scolaire,
        'total_eleves': total_eleves,
        'date_naissance': eleve.date_naissance,
        'lieu_naissance': eleve.lieu_naissance,
        'etablissement_nom': etablissement.nom if etablissement else "Non défini",
        'etablissement_adresse': etablissement.adresse if etablissement else "Non définie",
        'etablissement_telephone': etablissement.telephone if etablissement else "Non défini",
        'total_absences': total_absences,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/bulletin_semestre_1.html', context)



@login_required
@user_passes_test(is_admin, login_url='login')
def bulletin_semestre_2(request, eleve_id):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    classe = eleve.classe
    etablissement = classe.etablissement if classe else None
    total_eleves = Eleve.objects.filter(classe=classe).count() if classe else 1
    annee_scolaire = etablissement.annee_scolaire if etablissement else "Non définie"

    # Ordre d'affichage des matières
    ordre_matieres = [
        "Rédaction", "Orthographe", "Texte suivi de questions", "Mathématiques",
        "Science Physique", "Anglais", "Arabe", "Espagnol", "Histoire/Géographie", "Education civique",
        "Sc. De Vie et de la terre", "Economie familiale", "Ed. Physique et Sportive"
    ]

    # Récupérer les notes de l'élève pour le semestre 2
    notes = Note.objects.filter(eleve=eleve, semestre=2).select_related('matiere')

    # Initialisation des variables
    total_points = 0
    total_coefficients = 0
    notes_avec_rangs = []

    for note in notes:
        moyenne_matiere = (note.note_devoir + note.note_composition) / 2.0
        points_matiere = moyenne_matiere * note.matiere.coefficient

        # Récupérer le rang de l'élève pour cette matière
        moyennes_classe = Note.objects.filter(
            eleve__classe=classe,
            matiere=note.matiere,
            semestre=2
        ).annotate(
            moyenne=ExpressionWrapper((F('note_devoir') + F('note_composition')) / 2.0, output_field=FloatField())
        ).order_by('-moyenne')

        rang_matiere = next((i + 1 for i, n in enumerate(moyennes_classe) if n.eleve.id == eleve.id), None)

        # Génération de l'appréciation dynamique
        appreciation = generer_appreciation(moyenne_matiere)

        notes_avec_rangs.append({
            'matiere': note.matiere.nom,
            'coefficient': note.matiere.coefficient,
            'note_devoir': note.note_devoir,
            'note_composition': note.note_composition,
            'moyenne_matiere': moyenne_matiere,
            'points_matiere': points_matiere,
            'appreciation': appreciation,  # Ajout de l'appréciation ici
            'rang_matiere': rang_matiere,
        })

        total_points += points_matiere
        total_coefficients += note.matiere.coefficient

    # Trier les matières selon l'ordre prédéfini
    notes_avec_rangs.sort(key=lambda note: ordre_matieres.index(note['matiere']) if note['matiere'] in ordre_matieres else len(ordre_matieres))

    # Calcul de la moyenne générale semestre 2
    moyenne_generale_s2 = total_points / total_coefficients if total_coefficients > 0 else 0.0

    # Récupérer la moyenne du semestre 1
    moyenne_generale_s1 = eleve.moyenne_generale_semestre(1)

    # Calcul de la moyenne annuelle
    moyenne_annuelle = (moyenne_generale_s1 + moyenne_generale_s2) / 2 if moyenne_generale_s1 > 0 and moyenne_generale_s2 > 0 else 0.0

    # Seuil de passage
    seuil_passage = 10
    passe_classe = moyenne_annuelle >= seuil_passage

    # Classement général des élèves pour le semestre 2
    classement_s2 = Eleve.objects.filter(classe=classe).annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=2),
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=2), output_field=FloatField()),
            Value(1.0)
        ),
        moyenne=ExpressionWrapper(F('total_points') / F('total_coefficients'), output_field=FloatField())
    ).filter(moyenne__gt=0).order_by('-moyenne')

    rang_semestre_2 = next((i + 1 for i, e in enumerate(classement_s2) if e.id == eleve.id), None)

    # Classement annuel
    classement_annuel = Eleve.objects.filter(classe=eleve.classe).annotate(
    total_points_s1=Coalesce(
        Sum(
            ExpressionWrapper(
                ((Cast(F('note__note_devoir'), FloatField()) + Cast(F('note__note_composition'), FloatField())) / 2.0) 
                * Cast(F('note__matiere__coefficient'), FloatField()),
                output_field=FloatField()
            ),
            filter=Q(note__semestre=1),
            output_field=FloatField()
        ),
        Value(0.0),
        output_field=FloatField()
    ),
    total_points_s2=Coalesce(
        Sum(
            ExpressionWrapper(
                ((Cast(F('note__note_devoir'), FloatField()) + Cast(F('note__note_composition'), FloatField())) / 2.0) 
                * Cast(F('note__matiere__coefficient'), FloatField()),
                output_field=FloatField()
            ),
            filter=Q(note__semestre=2),
            output_field=FloatField()
        ),
        Value(0.0),
        output_field=FloatField()
    ),
    total_coefficients_s1=Coalesce(Sum(Cast(F('note__matiere__coefficient'), FloatField()), filter=Q(note__semestre=1)), Value(1.0)),
    total_coefficients_s2=Coalesce(Sum(Cast(F('note__matiere__coefficient'), FloatField()), filter=Q(note__semestre=2)), Value(1.0)),

    moyenne_s1=ExpressionWrapper(F('total_points_s1') / F('total_coefficients_s1'), output_field=FloatField()),
    moyenne_s2=ExpressionWrapper(F('total_points_s2') / F('total_coefficients_s2'), output_field=FloatField()),

    moyenne_annuelle=ExpressionWrapper((F('moyenne_s1') + F('moyenne_s2')) / 2.0, output_field=FloatField())
).order_by('-moyenne_annuelle')

    rang_annuel = next((i + 1 for i, e in enumerate(classement_annuel) if e.id == eleve.id), None)

    # Gestion des absences
    absences = Absence.objects.filter(eleve=eleve, semestre=2)
    total_absences = absences.count()

    today = timezone.now()

    context = {
        'eleve': eleve,
        'notes': notes_avec_rangs,
        'total_points': total_points,
        'total_coefficients': total_coefficients,
        'moyenne_generale_s2': moyenne_generale_s2,
        'moyenne_generale_s1': moyenne_generale_s1,
        'moyenne_annuelle': moyenne_annuelle,
        'passe_classe': passe_classe,
        'rang_semestre_2': rang_semestre_2,
        'rang_annuel': rang_annuel,
        'total_eleves': total_eleves,
        'annee_scolaire': annee_scolaire,
        'total_absences': total_absences,
        'today': today,
    }
    return render(request, 'bulletins/bulletin_semestre_2.html', context)


@login_required
def statistiques_globales(request):
    # Statistiques globales
    total_etablissements = Etablissement.objects.count()
    total_classes = Classe.objects.count()
    total_eleves = Eleve.objects.count()
    total_enseignants = Enseignant.objects.count()
    total_matieres = Matiere.objects.count()

    # --- Moyenne générale par établissement ---
    moyennes_etablissements = (
        Etablissement.objects.annotate(
            total_points=Coalesce(
                Sum(
                    ExpressionWrapper(
                        ((F('classe__eleve__note__note_devoir') + F('classe__eleve__note__note_composition')) / Value(2.0)) 
                        * F('classe__eleve__note__matiere__coefficient'),
                        output_field=FloatField()
                    ),
                    filter=Q(classe__eleve__note__semestre__in=[1, 2])
                ),
                Value(0.0),
                output_field=FloatField()
            ),
            total_coefficients=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('classe__eleve__note__matiere__coefficient'),
                        output_field=FloatField()
                    ),
                    filter=Q(classe__eleve__note__semestre__in=[1, 2])
                ),
                Value(1.0),
                output_field=FloatField()
            ),
            moyenne_generale=ExpressionWrapper(
                F('total_points') / F('total_coefficients'),
                output_field=FloatField()
            )
        ).order_by('-moyenne_generale')
    )

    # --- Classement des établissements ---
    classement_etablissements = [
        {'nom': etab.nom, 'moyenne_generale': etab.moyenne_generale}
        for etab in moyennes_etablissements
    ]

    # --- Taux de réussite global ---
    eleves_avec_moyenne = Eleve.objects.annotate(
        total_points=Coalesce(
            Sum(
                ((F('note__note_devoir') + F('note__note_composition')) / Value(2.0)) * F('note__matiere__coefficient'),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum(
                F('note__matiere__coefficient'),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(1.0),  # Pour éviter la division par zéro
            output_field=FloatField()
        ),
        moyenne_annuelle=ExpressionWrapper(
            F('total_points') / Coalesce(F('total_coefficients'), Value(1.0)),
            output_field=FloatField()
        )
    )

    # Nombre d'élèves ayant une moyenne annuelle >= 10
    eleves_reussis = eleves_avec_moyenne.filter(moyenne_annuelle__gte=10).count()

    # Calcul du taux de réussite global
    taux_reussite = (eleves_reussis / total_eleves) * 100 if total_eleves > 0 else 0

    # --- Taux de réussite par classe ---
    classes = Classe.objects.all()  # Assure-toi que les classes existent bien
    taux_reussite_globale = []
    couleurs_reussite = []

    for classe in classes:
        total_eleves_classe = Eleve.objects.filter(classe=classe).count()
        eleves_reussis_classe = eleves_avec_moyenne.filter(classe=classe, moyenne_annuelle__gte=10).count()
        
        taux_classe = (eleves_reussis_classe / total_eleves_classe) * 100 if total_eleves_classe > 0 else 0
        taux_reussite_globale.append(taux_classe)

        # Attribution des couleurs en fonction du taux de réussite
        if taux_classe >= 75:
            couleurs_reussite.append("#4CAF50")  # Vert pour un bon taux de réussite
        elif 50 <= taux_classe < 75:
            couleurs_reussite.append("#FFC107")  # Jaune pour un taux moyen
        else:
            couleurs_reussite.append("#F44336")  # Rouge pour un faible taux de réussite


      
    # --- Moyenne générale par classe ---
        moyennes_classes = (
    Classe.objects.annotate(
        total_points=Coalesce(
            Sum(
                ((F('eleve__note__note_devoir') + F('eleve__note__note_composition')) / 2.0) * F('eleve__note__matiere__coefficient'),
                filter=Q(eleve__note__semestre__in=[1, 2]),  # Sélectionne les semestres 1 et 2
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum(
                F('eleve__note__matiere__coefficient'),
                filter=Q(eleve__note__semestre__in=[1, 2]),  # Sélectionne les semestres 1 et 2
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        moyenne_generale=Case(
            When(total_coefficients__gt=0, then=F('total_points') / F('total_coefficients')),
            default=Value(0.0),
            output_field=FloatField()
        )
    )
    .filter(total_coefficients__gt=0)  # Exclure les classes sans notes
    .annotate(moyenne_arrondie=Round('moyenne_generale', 2))  # Arrondir à 2 décimales
    .order_by('-moyenne_generale')
)

    # --- Premiers de chaque classe ---
    premiers_par_classe = []
    for classe in Classe.objects.all():
        premier = (
            Eleve.objects.filter(classe=classe)
            .annotate(
                total_points=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            ((F('note__note_devoir') + F('note__note_composition')) / Value(2.0)) 
                            * F('note__matiere__coefficient'),
                            output_field=FloatField()
                        ),
                        filter=Q(note__semestre__in=[1, 2])
                    ),
                    Value(0.0),
                    output_field=FloatField()
                ),
                total_coefficients=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F('note__matiere__coefficient'),
                            output_field=FloatField()
                        ),
                        filter=Q(note__semestre__in=[1, 2])
                    ),
                    Value(0.0),
                    output_field=FloatField()
                ),
                moyenne_annuelle=Case(
                    When(total_coefficients__gt=0, then=F('total_points') / F('total_coefficients')),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
            .filter(total_coefficients__gt=0)  # Exclut les élèves sans moyenne
            .order_by('-moyenne_annuelle')
            .first()
        )
        if premier:
            premiers_par_classe.append({
                'classe': classe.nom,
                'etablissement': classe.etablissement.nom if classe.etablissement else "Non défini",
                'premier': premier,
                'moyenne_annuelle': premier.moyenne_annuelle
            })
            eleves_notes = Eleve.objects.annotate(
    nb_notes=Count('note'),
    total_points=Sum(
        ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
        filter=Q(note__semestre__in=[1, 2]),
        output_field=FloatField()
    ),
    total_coefficients=Sum(
        F('note__matiere__coefficient'),
        filter=Q(note__semestre__in=[1, 2]),
        output_field=FloatField()
    )
)

      
    # --- Trois meilleurs élèves de l'établissement ---
    meilleurs_eleves_etablissement = (
    Eleve.objects.annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / Value(2.0)) 
                    * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne_annuelle=ExpressionWrapper(
            F('total_points') / F('total_coefficients'),
            output_field=FloatField()
        )
    )
    .order_by('-moyenne_annuelle')[:3]  # Garde les 3 meilleurs
)
    
    # --- Trois mauvais élèves de l'établissement ---
    mauvais_eleves_etablissement = (
    Eleve.objects.annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / Value(2.0)) 
                    * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre__in=[1, 2])
            ),
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne_annuelle=ExpressionWrapper(
            F('total_points') / F('total_coefficients'),
            output_field=FloatField()
        )
    )
    .order_by('moyenne_annuelle')[:3]  # Garde les 3 derniers
)
    
    taux_echec = 100 - taux_reussite  # Calcul du taux d'échec
      

    context = {
        'total_etablissements': total_etablissements,
        'total_classes': total_classes,
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_matieres': total_matieres,
        'moyennes_etablissements': moyennes_etablissements,
        'classement_etablissements': classement_etablissements,        
        'taux_reussite': taux_reussite,
        'taux_echec':taux_echec,
        'moyennes_classes': moyennes_classes,
        'premiers_par_classe': premiers_par_classe,
        'meilleurs_eleves_etablissement': meilleurs_eleves_etablissement,
        'mauvais_eleves_etablissement':mauvais_eleves_etablissement,               
        "taux_reussite_globale": taux_reussite_globale,
        "couleurs_reussite": couleurs_reussite,
        "classes": classes
    }
    return render(request, 'bulletins/statistiques_globales.html', context)


def determiner_mention(moyenne):
    if moyenne >= 16:
        return "Très Bien"
    elif moyenne >= 14:
        return "Bien"
    elif moyenne >= 12:
        return "Assez Bien"
    elif moyenne >= 10:
        return "Passable"
    else:
        return "Insuffisant"


def calculer_rang_semestre(classe, semestre, annee_scolaire):
    """
    Calcule le rang de chaque élève dans une classe pour un semestre donné.
    """
    eleves = Eleve.objects.filter(classe=classe)
    rangs = []

    for eleve in eleves:
        # Filtrer les notes par semestre et année scolaire via la classe et l'établissement
        notes = Note.objects.filter(
            eleve=eleve,
            semestre=semestre,
            eleve__classe__etablissement__annee_scolaire=annee_scolaire
        ).annotate(
            points_matiere=ExpressionWrapper(
                ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                output_field=FloatField()
            )
        )
        total_points = sum(note.points_matiere for note in notes)
        rangs.append({'eleve': eleve, 'total_points': total_points})

    # Trier les élèves par total_points décroissant
    rangs.sort(key=lambda x: x['total_points'], reverse=True)

    # Attribuer les rangs
    for index, rang in enumerate(rangs):
        rang['rang'] = index + 1

    return rangs


def calculer_rang_annuel(classe, annee_scolaire):
    """
    Calcule le rang annuel de chaque élève dans une classe.
    """
    eleves = Eleve.objects.filter(classe=classe)
    rangs = []

    for eleve in eleves:
        # Calculer la moyenne annuelle en utilisant la méthode de l'élève
        moyenne_annuelle = eleve.moyenne_annuelle()
        rangs.append({'eleve': eleve, 'moyenne_annuelle': moyenne_annuelle})

    # Trier les élèves par moyenne_annuelle décroissante
    rangs.sort(key=lambda x: x['moyenne_annuelle'], reverse=True)

    # Attribuer les rangs
    for index, rang in enumerate(rangs):
        rang['rang'] = index + 1

    return rangs


@login_required
@user_passes_test(is_admin, login_url='login')
def archiver_annee(request):
    if request.method == 'POST':
        form = ArchiverAnneeForm(request.POST)
        if form.is_valid():
            annee_scolaire_actuelle = form.cleaned_data['annee_scolaire']

            try:
                # Vérifications des notes et des coefficients
                if Note.objects.filter(matiere__isnull=True).exists():
                    messages.error(request, "Certaines notes n'ont pas de matière associée. Corrigez avant d'archiver.")
                    return redirect('archiver_annee')

                if Matiere.objects.filter(Q(coefficient__isnull=True) | Q(coefficient__lte=0)).exists():
                    messages.error(request, "Certaines matières ont un coefficient invalide. Corrigez avant d'archiver.")
                    return redirect('archiver_annee')

                # Vérification si l'année est déjà archivée
                if Archive.objects.filter(annee_scolaire=annee_scolaire_actuelle.nom).exists():
                    messages.error(request, "L'année scolaire est déjà archivée.")
                    return redirect('archiver_annee')

                # Récupération des élèves ayant des notes pour l'année scolaire actuelle
                eleves = Eleve.objects.filter(
                    classe__etablissement__annee_scolaire=annee_scolaire_actuelle
                ).distinct()

                # Archiver les notes et les absences
                for eleve in eleves:
                    # Calcul des notes par semestre
                    notes_semestre_1 = Note.objects.filter(eleve=eleve, semestre=1).annotate(
                        moyenne_matiere=ExpressionWrapper(
                            (F('note_devoir') + F('note_composition')) / 2.0,
                            output_field=FloatField()
                        ),
                        points_matiere=ExpressionWrapper(
                            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                            output_field=FloatField()
                        )
                    ).values(
                        'matiere__id', 'matiere__nom', 'matiere__coefficient',
                        'note_devoir', 'note_composition', 'moyenne_matiere', 'points_matiere'
                    )

                    notes_semestre_2 = Note.objects.filter(eleve=eleve, semestre=2).annotate(
                        moyenne_matiere=ExpressionWrapper(
                            (F('note_devoir') + F('note_composition')) / 2.0,
                            output_field=FloatField()
                        ),
                        points_matiere=ExpressionWrapper(
                            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
                            output_field=FloatField()
                        )
                    ).values(
                        'matiere__id', 'matiere__nom', 'matiere__coefficient',
                        'note_devoir', 'note_composition', 'moyenne_matiere', 'points_matiere'
                    )

                    # Calcul des moyennes
                    total_points_s1 = sum(note['points_matiere'] for note in notes_semestre_1)
                    total_coefficients_s1 = sum(note['matiere__coefficient'] for note in notes_semestre_1)
                    moyenne_generale_s1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0

                    total_points_s2 = sum(note['points_matiere'] for note in notes_semestre_2)
                    total_coefficients_s2 = sum(note['matiere__coefficient'] for note in notes_semestre_2)
                    moyenne_generale_s2 = total_points_s2 / total_coefficients_s2 if total_coefficients_s2 > 0 else 0

                    moyenne_annuelle = (moyenne_generale_s1 + moyenne_generale_s2) / 2 if moyenne_generale_s1 and moyenne_generale_s2 else max(moyenne_generale_s1, moyenne_generale_s2, 0)

                    # Déterminer si l'élève passe en classe supérieure
                    passe_classe = moyenne_annuelle >= 10

                    # Archiver les absences
                    absences = [{'date': absence.date.isoformat(), 'motif': absence.motif} for absence in Absence.objects.filter(eleve=eleve)]

                    # Calculer les rangs
                    rangs_semestre_1 = calculer_rang_semestre(eleve.classe, 1, annee_scolaire_actuelle)
                    rangs_semestre_2 = calculer_rang_semestre(eleve.classe, 2, annee_scolaire_actuelle)
                    rangs_annuel = calculer_rang_annuel(eleve.classe, annee_scolaire_actuelle)

                    # Trouver le rang de l'élève
                    rang_s1 = next((r['rang'] for r in rangs_semestre_1 if r['eleve'] == eleve), None)
                    rang_s2 = next((r['rang'] for r in rangs_semestre_2 if r['eleve'] == eleve), None)
                    rang_annuel = next((r['rang'] for r in rangs_annuel if r['eleve'] == eleve), None)

                    # Créer l'archive pour l'élève
                    Archive.objects.create(
                        annee_scolaire=annee_scolaire_actuelle.nom,
                        eleve=eleve,
                        classe=eleve.classe.nom if eleve.classe else None,
                        etablissement=eleve.classe.etablissement if eleve.classe and eleve.classe.etablissement else None,
                        notes={'semestre_1': list(notes_semestre_1), 'semestre_2': list(notes_semestre_2)},
                        absences=absences,
                        moyenne_annuelle=moyenne_annuelle,
                        passe_classe=passe_classe,
                        total_points_semestre_1=total_points_s1,
                        total_points_semestre_2=total_points_s2,
                        mention_semestre_1=determiner_mention(moyenne_generale_s1),
                        mention_semestre_2=determiner_mention(moyenne_generale_s2),
                        mention_annuelle=determiner_mention(moyenne_annuelle),
                        rang_semestre_1=rang_s1,
                        rang_semestre_2=rang_s2,
                        rang_annuel=rang_annuel
                    )

                # Archiver les paiements
                # Archiver les paiements
                paiements_a_archiver = Paiement.objects.filter(annee_scolaire=annee_scolaire_actuelle)
                for paiement in paiements_a_archiver:
                    eleve = paiement.eleve  # Récupérer l'élève associé au paiement
                    
                    # Créer l'archive pour le paiement
                    ArchivePaiement.objects.create(
                        annee_scolaire=annee_scolaire_actuelle.nom,
                        eleve_id=paiement.eleve.id,  # ID de l'élève
                        eleve_nom=eleve.nom,  # Nom de l'élève
                        eleve_prenom=eleve.prenom,  # Prénom de l'élève
                        frais=paiement.frais.get_type_frais_display(),
                        montant_paye=paiement.montant_paye,
                        date_paiement=paiement.date_paiement,
                        mode_paiement=paiement.mode_paiement,
                        statut=paiement.statut,
                        reference=paiement.reference,
                        date_archivage=timezone.now()
                    )


                    # Archiver les frais
                    frais_a_archiver = Frais.objects.filter(annee_scolaire=annee_scolaire_actuelle)
                    for frais in frais_a_archiver:
                        # Créer l'archive pour le frais
                        ArchiveFrais.objects.create(
                            annee_scolaire=annee_scolaire_actuelle.nom,
                            type_frais=frais.get_type_frais_display(),
                            montant=frais.montant,
                            classe=frais.classe.nom if frais.classe else None,
                            description=frais.description,
                            date_archivage=timezone.now()
                        )


                # Supprimer les emplois du temps de l'année en cours
                emplois_du_temps_a_supprimer = EmploiDuTemps.objects.filter(classe__etablissement__annee_scolaire=annee_scolaire_actuelle)
                emplois_du_temps_a_supprimer.delete()

                # Supprimer les autres données de l'année en cours
                Note.objects.filter(eleve__classe__etablissement__annee_scolaire=annee_scolaire_actuelle).delete()
                Absence.objects.filter(eleve__classe__etablissement__annee_scolaire=annee_scolaire_actuelle).delete()
                paiements_a_archiver.delete()
                # Supprimer les notifications de l'année en cours
                notifications_a_supprimer = Notification.objects.filter(
                    date__year=annee_scolaire_actuelle.debut.year
                )
                notifications_a_supprimer.delete()

                # Récupérer la nouvelle année scolaire
                nouvelle_annee_scolaire = AnneeScolaire.objects.filter(
                    debut__gt=annee_scolaire_actuelle.fin
                ).first()

                if not nouvelle_annee_scolaire:
                    messages.error(request, "Aucune nouvelle année scolaire n'a été trouvée.")
                    return redirect('archiver_annee')

                # Supprimer les échéances existantes pour la nouvelle année scolaire
                for eleve in eleves:
                    Echeance.objects.filter(
                        eleve=eleve,
                        date_echeance__gte=nouvelle_annee_scolaire.debut,
                        date_echeance__lte=nouvelle_annee_scolaire.fin
                    ).delete()

                # Régénérer les échéances pour la nouvelle année scolaire
                from .utils import generer_echeances_pour_eleve
                for eleve in eleves:
                    generer_echeances_pour_eleve(eleve)

                messages.success(request, f"L'année scolaire {annee_scolaire_actuelle.nom} a été archivée avec succès. Les échéances ont été régénérées pour la nouvelle année scolaire.")
                return redirect('liste_archives')

            except Exception as e:
                messages.error(request, f"Erreur lors de l'archivage : {e}")
                return redirect('accueil_admin')

    else:
        form = ArchiverAnneeForm()

    return render(request, 'bulletins/archiver_annee.html', {'form': form, 'title': 'Archiver une Année Scolaire'})


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_archives(request):
    # Récupérer toutes les archives
    archives = Archive.objects.all().order_by('-annee_scolaire')  # Trier par année scolaire décroissante    
    archives_paiements = ArchivePaiement.objects.all().order_by('-annee_scolaire')
    archives_frais = ArchiveFrais.objects.all().order_by('-annee_scolaire')

    # Récupérer tous les élèves pour utiliser les prénoms et noms dans le template
    eleves = {eleve.id: eleve for eleve in Eleve.objects.all()}

    context = {
        'archives': archives,       
        'archives_paiements': archives_paiements,       
        'eleves': eleves,  # Passer les élèves au contexte
        'title': 'Liste des Archives',
        'archives_frais': archives_frais,
    }
    return render(request, 'bulletins/liste_archives.html', context)



@login_required
@user_passes_test(is_admin, login_url='login')
def detail_archive(request, archive_id):
    archive = get_object_or_404(Archive, id=archive_id)

    # Récupérer les archives des frais, paiements et emplois du temps pour cette année scolaire    
    archives_paiements = ArchivePaiement.objects.filter(annee_scolaire=archive.annee_scolaire)
    

    # Vérifier si l'archive contient des notes
    notes_semestre_1 = archive.notes.get('semestre_1', []) if isinstance(archive.notes, dict) else []
    notes_semestre_2 = archive.notes.get('semestre_2', []) if isinstance(archive.notes, dict) else []

    # Vérifier que les notes ont bien les clés attendues
    for note in notes_semestre_1 + notes_semestre_2:
        if not all(k in note for k in ['matiere__nom', 'moyenne_matiere', 'points_matiere']):
            print(f"⚠️ Erreur de structure dans les notes : {note}")  # Debug console

    # Sécuriser l'accès aux clés et éviter les KeyError
    total_points_s1 = sum(note.get('points_matiere', 0) for note in notes_semestre_1) if notes_semestre_1 else 0
    total_coefficients_s1 = sum(Matiere.objects.filter(nom=note.get('matiere__nom')).values_list('coefficient', flat=True).first() or 0 for note in notes_semestre_1) if notes_semestre_1 else 0
    moyenne_generale_s1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0

    total_points_s2 = sum(note.get('points_matiere', 0) for note in notes_semestre_2) if notes_semestre_2 else 0
    total_coefficients_s2 = sum(Matiere.objects.filter(nom=note.get('matiere__nom')).values_list('coefficient', flat=True).first() or 0 for note in notes_semestre_2) if notes_semestre_2 else 0
    moyenne_generale_s2 = total_points_s2 / total_coefficients_s2 if total_coefficients_s2 > 0 else 0

    context = {
        'archive': archive,
        'notes_semestre_1': notes_semestre_1,
        'notes_semestre_2': notes_semestre_2,
        'moyenne_generale_s1': moyenne_generale_s1,
        'moyenne_generale_s2': moyenne_generale_s2,
        'mention_semestre_1': archive.mention_semestre_1,
        'mention_semestre_2': archive.mention_semestre_2,
        'mention_annuelle': archive.mention_annuelle,
        'rang_semestre_1': archive.rang_semestre_1,  # Ajout Rang S1
        'rang_semestre_2': archive.rang_semestre_2,  # Ajout Rang S2
        'rang_annuel': archive.rang_annuel,          # Ajout Rang Annuel       
        'archives_paiements': archives_paiements,       
        'title': 'Détail de l’Archive',
    }

    return render(request, 'bulletins/detail_archive.html', context)




@login_required
@user_passes_test(is_admin, login_url='login')
def restaurer_archive(request, archive_id):
    try:
        archive = Archive.objects.get(id=archive_id)

        if request.method == "POST":
            # Exécuter la restauration seulement si le formulaire est soumis
            annee_scolaire_restaurée = archive.annee_scolaire
            annee_scolaire_actuelle = f"{timezone.now().year}-{timezone.now().year + 1}"

            if annee_scolaire_restaurée == annee_scolaire_actuelle:
                messages.error(request, "L'archive appartient déjà à l'année scolaire en cours.")
                return redirect('liste_archives')

            eleve = archive.eleve
            if not eleve:
                messages.error(request, "L'élève de cette archive n'existe plus.")
                return redirect('liste_archives')

            # Déboguer les types de données avant de restaurer
            print(f"Archive notes: {archive.notes}")
            print(f"Archive absences: {archive.absences}")

            with transaction.atomic():
                # Restaurer les notes dans NoteArchive
                for semestre, notes in archive.notes.items():
                    for note in notes:
                        # Déboguer le contenu de 'note'
                        print(f"Restaurer note: {note}")

                        if isinstance(note, dict):  # Vérifier que 'note' est bien un dictionnaire
                            matiere = Matiere.objects.get(nom=note.get('matiere__nom'))
                            # Sauvegarder les données dans NoteArchive
                            NoteArchive.objects.create(
                                eleve=eleve,
                                matiere=matiere,
                                semestre=1 if semestre == 'semestre_1' else 2,
                                note_devoir=note.get('note_devoir'),
                                note_composition=note.get('note_composition'),
                                annee_scolaire=archive.annee_scolaire  # Ajouter l'année scolaire
                            )
                        else:
                            # Si 'note' n'est pas un dictionnaire, afficher une erreur
                            print("Erreur : 'note' n'est pas un dictionnaire.")
                            messages.error(request, "Erreur de format dans les notes.")
                            return redirect('liste_archives')

                # Restaurer les absences
                for absence in archive.absences:
                    if isinstance(absence, dict):  # Vérifier que 'absence' est un dictionnaire
                        Absence.objects.create(
                            eleve=eleve,
                            date=timezone.datetime.fromisoformat(absence['date']),
                            motif=absence['motif']
                        )
                    else:
                        print("Erreur : 'absence' n'est pas un dictionnaire.")
                        messages.error(request, "Erreur de format dans les absences.")
                        return redirect('liste_archives')
                    

                # Restaurer la moyenne annuelle
                eleve.moyenne_annuelle = archive.moyenne_annuelle
                eleve.save()

                # Gestion du passage de classe
                if archive.passe_classe:
                    classe_actuelle = eleve.classe
                    if classe_actuelle and classe_actuelle.niveau:
                        niveau_suivant = NiveauScolaire.objects.filter(ordre=classe_actuelle.niveau.ordre + 1).first()
                        if niveau_suivant:
                            nouvelle_classe = Classe.objects.filter(niveau=niveau_suivant, etablissement=classe_actuelle.etablissement).first()
                            eleve.classe = nouvelle_classe if nouvelle_classe else None
                        else:
                            eleve.classe = None
                    else:
                        eleve.classe = None
                    eleve.save()

            messages.success(request, f"L'archive de l'année scolaire {archive.annee_scolaire} a été restaurée avec succès.")
            return redirect('liste_archives')

        # Si c'est une requête GET, afficher la page de confirmation
        return render(request, 'bulletins/restaurer_annee_scolaire.html', {'archive': archive})

    except Archive.DoesNotExist:
        messages.error(request, "L'archive que vous essayez de restaurer n'existe pas.")
        return redirect('liste_archives')
    except Exception as e:
        messages.error(request, f"Erreur lors de la restauration de l'archive : {e}")
        return redirect('liste_archives')
    
    
def restaurer_paiement(request, paiement_id):
    try:
        # Récupérer l'archive du paiement
        paiement_archive = ArchivePaiement.objects.get(id=paiement_id)

        if request.method == "POST":
            annee_scolaire_actuelle = f"{timezone.now().year}-{timezone.now().year + 1}"

            # Vérifier si l'archive appartient à l'année scolaire en cours
            if paiement_archive.annee_scolaire == annee_scolaire_actuelle:
                messages.error(request, "Le paiement appartient déjà à l'année scolaire en cours.")
                return redirect('liste_archives')

            # Récupérer l'élève associé au paiement
            try:
                eleve = Eleve.objects.get(id=paiement_archive.eleve_id)
            except Eleve.DoesNotExist:
                messages.error(request, "L'élève associé à ce paiement n'existe plus.")
                return redirect('liste_archives')

            # Vérifier si l'élève est associé à une classe
            if not eleve.classe:
                messages.error(request, "L'élève n'est pas associé à une classe.")
                return redirect('liste_archives')

            # Récupérer l'objet AnneeScolaire
            try:
                annee_scolaire_obj = AnneeScolaire.objects.get(nom=paiement_archive.annee_scolaire)
            except AnneeScolaire.DoesNotExist:
                messages.error(request, f"L'année scolaire {paiement_archive.annee_scolaire} n'existe pas.")
                return redirect('liste_archives')

            # Vérifier si les frais sont restaurés ou s'il faut les créer
            frais_restauré, created = FraisRestauré.objects.get_or_create(
                type_frais=paiement_archive.frais.strip(),  # Supprimer les espaces supplémentaires
                annee_scolaire=paiement_archive.annee_scolaire,
                classe=eleve.classe,
                defaults={
                    'montant': paiement_archive.montant_paye,  # Montant par défaut
                    'description': f"{paiement_archive.frais} pour {eleve.classe}",
                    'date_archivage': timezone.now(),
                }
            )

            if created:
                messages.info(request, f"Les frais restaurés '{paiement_archive.frais}' ont été créés pour l'année scolaire {paiement_archive.annee_scolaire} et la classe {eleve.classe}.")

            # Vérifier si un paiement a déjà été restauré pour cet élève et cette année scolaire
            paiement_existant = PaiementRestauré.objects.filter(
                eleve=eleve,
                annee_scolaire=annee_scolaire_obj,
                frais=frais_restauré
            ).exists()

            if paiement_existant:
                messages.error(request, "Le paiement a déjà été restauré pour cet élève.")
                return redirect('liste_archives')

            print(f"Création du paiement restauré pour {eleve.prenom} {eleve.nom} avec {frais_restauré.type_frais} pour {annee_scolaire_obj.nom}")

            with transaction.atomic():
                # Création du paiement restauré
                PaiementRestauré.objects.create(
                    eleve=eleve,
                    frais=frais_restauré,
                    montant_paye=paiement_archive.montant_paye,
                    date_paiement=paiement_archive.date_paiement,
                    mode_paiement=paiement_archive.mode_paiement,
                    statut=paiement_archive.statut,
                    reference=paiement_archive.reference,
                    mois=None,  # Par défaut, aucun mois n'est spécifié
                    est_anticipation=False,
                    est_retroactif=False,
                    nombre_mois=1,
                    annee_scolaire=annee_scolaire_obj  # Utilisation de l'objet AnneeScolaire
                )

                messages.success(request, f"Le paiement pour l'élève {eleve.prenom} {eleve.nom} a été restauré avec succès.")
                return redirect('liste_archives')

        # Si la requête n'est pas POST, afficher le formulaire avec les détails du paiement archive
        return render(request, 'bulletins/restaurer_paiement.html', {'paiement': paiement_archive})

    except ArchivePaiement.DoesNotExist:
        messages.error(request, "Le paiement que vous essayez de restaurer n'existe pas.")
        return redirect('liste_archives')
    except Exception as e:
        messages.error(request, f"Erreur lors de la restauration du paiement : {str(e)}")
        return redirect('liste_archives')


    
@login_required
@user_passes_test(is_admin, login_url='login')
def restaurer_archive_liste(request):
    archives = Archive.objects.all()  # Récupère toutes les archives
    archives_paiements = ArchivePaiement.objects.all()
    context = {
        'archives': archives,
        'archives_paiements': archives_paiements,
    }
    return render(request, 'bulletins/restaurer_archive_liste.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def details_payement_rest(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    paiements = PaiementRestauré.objects.filter(eleve=eleve).order_by('-date_paiement')

    # Calcul du total payé
    total_paye = sum(paiement.montant_paye for paiement in paiements)

    return render(request, 'bulletins/detail_paiements_eleve.html', {
        'eleve': eleve,
        'paiements': paiements,
        'total_paye': total_paye  # Passer le total au template
    })



@login_required
@user_passes_test(is_admin, login_url='login')
def saisie_annee_scolaire(request):
    if request.method == 'POST':
        form = AnneeScolaireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "L'année scolaire a été ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de la saisie de l'année scolaire. Veuillez vérifier les informations.")
        return redirect('liste_annees_scolaires')
    else:
        form = AnneeScolaireForm()

    context = {
        'form': form,
        'title': 'Ajouter une année scolaire',
    }
    return render(request, 'bulletins/saisie_annee_scolaire.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_annees_scolaires(request):
    annees_list = AnneeScolaire.objects.all().order_by('-debut')
    paginator = Paginator(annees_list, 10)  # 10 années par page
    page_number = request.GET.get('page')
    annees = paginator.get_page(page_number)

    context = {
        'annees': annees,
        'title': 'Liste des années scolaires',
    }
    return render(request, 'bulletins/liste_annees_scolaires.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_annee_scolaire(request, annee_id):
    annee = get_object_or_404(AnneeScolaire, id=annee_id)
    if request.method == 'POST':
        form = AnneeScolaireForm(request.POST, instance=annee)
        if form.is_valid():
            form.save()
            messages.success(request, "L'année scolaire a été ajoutée avec succès.")
        else:
            messages.error(request, "Erreur lors de la saisie de l'année scolaire. Veuillez vérifier les informations.")
        return redirect('liste_annees_scolaires')
    else:
        form = AnneeScolaireForm(instance=annee)

    context = {
        'form': form,
        'annee': annee,
        'title': 'Modifier une année scolaire',
    }
    return render(request, 'bulletins/modifier_annee_scolaire.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_annee_scolaire(request, annee_id):
    annee = get_object_or_404(AnneeScolaire, id=annee_id)
    if request.method == 'POST':
        try:
            annee.delete()
            messages.success(request, "L'année scolaire a été supprimée avec succès.")
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cette année scolaire car elle est liée à d'autres enregistrements.")
        return redirect('liste_annees_scolaires')

    context = {
        'objet': annee,
        'type': 'Année Scolaire',
    }
    return render(request, 'bulletins/confirmation_suppression.html', context)



# @user_passes_test(is_admin, login_url='login')
@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def choisir_matieres_optionnelles(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    # Vérifier si l'élève a une classe
    if not eleve.classe:
        messages.warning(request, "Cet élève n'est pas encore affecté à une classe.")
        return redirect('liste_eleves')  # Remplace 'liste_eleves' par une page appropriée
    niveau = eleve.classe.niveau
    etablissement = eleve.classe.etablissement

    # Récupérer toutes les matières optionnelles pour ce niveau
    matieres_optionnelles = Matiere.objects.filter(niveaux_optionnels=niveau)

    # Appliquer la règle spécifique de la 4e pour choisir entre Physique-Chimie et une langue étrangère
    if niveau.nom == "4e" and etablissement.choix_matiere_quatrieme:
        pc = Matiere.objects.filter(nom="Science Physique").first()
        langues = Matiere.objects.filter(nom__in=["Espagnol", "Arabe", "Allemand", "Italien"])

        # Si Physique-Chimie est présente, exclure les langues de la sélection
        if pc in matieres_optionnelles:
            matieres_optionnelles = matieres_optionnelles.exclude(id__in=langues.values_list("id", flat=True))

    # Vérifier les choix existants de l'élève
    choix_existant = ChoixMatiere.objects.filter(eleve=eleve)
    matieres_existes_ids = [c.matiere.id for c in choix_existant]

    if request.method == 'POST':
        form = ChoixMatiereForm(request.POST, niveau=niveau, etablissement=etablissement)
        if form.is_valid():
            choix_matieres = form.cleaned_data['matieres']

            # Validation des règles concernant Physique-Chimie et les langues
            if "Physique-Chimie" in [m.nom for m in choix_matieres] and \
               set([m.nom for m in choix_matieres]) & {"Espagnol", "Arabe", "Allemand", "Italien"}:
                messages.error(request, "Vous devez choisir entre Physique-Chimie et une seule langue.")
                return redirect("choisir_matieres_optionnelles", eleve_id=eleve.id)

            # Supprimer les anciens choix et enregistrer les nouveaux
            choix_existant.delete()
            for matiere in choix_matieres:
                ChoixMatiere.objects.create(eleve=eleve, matiere=matiere)
            messages.success(request, "Vos choix ont été enregistrés avec succès.")
            return redirect("profil_eleve", eleve_id=eleve.id)
    else:
        # Initialiser le formulaire avec les matières déjà choisies
        form = ChoixMatiereForm(initial={"matieres": matieres_existes_ids}, niveau=niveau, etablissement=etablissement)

    context = {
        "form": form,
        "eleve": eleve,
        "matieres_optionnelles": matieres_optionnelles,  # Afficher toutes les matières optionnelles disponibles
    }
    return render(request, "bulletins/choisir_matieres.html", context)


@login_required
@user_passes_test(is_admin, login_url='login')
def profil_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    return render(request, "bulletins/profil_eleve.html", {"eleve": eleve})


@login_required
@user_passes_test(is_admin, login_url='login')
def ajouter_niveau(request):
    if request.method == "POST":
        form = NiveauScolaireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Niveau scolaire ajouté avec succès !")
            return redirect("liste_niveaux")  # Assure-toi d’avoir cette URL
    else:
        form = NiveauScolaireForm()

    return render(request, "bulletins/ajouter_niveau.html", {"form": form})

@login_required
@user_passes_test(is_admin, login_url='login')
def liste_niveaux(request):
    niveaux = NiveauScolaire.objects.all()
    return render(request, 'bulletins/liste_niveaux.html', {'niveaux': niveaux, 'title': 'Liste des niveaux scolaires'})


@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_niveau(request, niveau_id):
    niveau = get_object_or_404(NiveauScolaire, id=niveau_id)

    if request.method == "POST":
        form = NiveauScolaireForm(request.POST, instance=niveau)
        if form.is_valid():
            form.save()
            messages.success(request, "Le niveau a été mis à jour avec succès.")
            return redirect('liste_niveaux')
    else:
        form = NiveauScolaireForm(instance=niveau)

    return render(request, 'bulletins/modifier_niveau.html', {'form': form, 'niveau': niveau, 'title': 'Modifier un niveau scolaire'})


@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_niveau(request, niveau_id):
    niveau = get_object_or_404(NiveauScolaire, id=niveau_id)

    if request.method == "POST":
        niveau.delete()
        messages.success(request, "Le niveau a été supprimé avec succès.")
        return redirect('liste_niveaux')

    return render(request, 'bulletins/supprimer_niveau.html', {'niveau': niveau, 'title': 'Supprimer un niveau'})




@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def impression_bulletin_eleve(request, eleve_id, semestre):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    # Filtrer les notes du semestre spécifié
    notes = Note.objects.filter(eleve=eleve, semestre=semestre).annotate(
        moyenne_calculee=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_matiere=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    # Calcul des totaux
    total_points = sum(note.points_matiere for note in notes)
    total_coefficients = sum(note.matiere.coefficient for note in notes)
    moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0

    # Classement de l'élève dans sa classe pour le semestre
    classement = Eleve.objects.filter(classe=eleve.classe).annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(Sum('note__matiere__coefficient', output_field=FloatField()), Value(1.0)),
        moyenne=ExpressionWrapper(
            F('total_points') / F('total_coefficients'),
            output_field=FloatField()
        )
    ).order_by('-moyenne')

    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    context = {
        'eleve': eleve,
        'notes': notes,
        'total_points': total_points,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,  # Ajout du semestre dans le contexte
    }

    return render(request, 'bulletins/impression_bulletin_eleve.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def bulletin_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    # Calcul des notes pour chaque semestre
    notes_semestre_1 = Note.objects.filter(eleve=eleve, semestre=1).annotate(
        moyenne_calcules=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_calcules=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    notes_semestre_2 = Note.objects.filter(eleve=eleve, semestre=2).annotate(
        moyenne_calcules=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_calcules=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    # Calcul des totaux pour chaque semestre
    total_points_s1 = sum(note.points_calcules for note in notes_semestre_1)
    total_coefficients_s1 = sum(note.matiere.coefficient for note in notes_semestre_1)
    moyenne_generale_s1 = total_points_s1 / total_coefficients_s1 if total_coefficients_s1 > 0 else 0.0

    total_points_s2 = sum(note.points_calcules for note in notes_semestre_2)
    total_coefficients_s2 = sum(note.matiere.coefficient for note in notes_semestre_2)
    moyenne_generale_s2 = total_points_s2 / total_coefficients_s2 if total_coefficients_s2 > 0 else 0.0

    # Calcul de la moyenne annuelle
    moyenne_annuelle = (moyenne_generale_s1 + moyenne_generale_s2) / 2 if moyenne_generale_s1 > 0 and moyenne_generale_s2 > 0 else 0.0

    # Déterminer si l'élève passe en classe supérieure
    seuil_passage = 10  # Seuil configurable
    passe_classe = moyenne_annuelle >= seuil_passage

    # Classement de l'élève dans sa classe (basé sur la moyenne annuelle)
    classement = Eleve.objects.filter(classe=eleve.classe).annotate(
        total_points_s1=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=1)  # Utilisation de Q ici
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients_s1=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=1)),  # Utilisation de Q ici
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne_s1=Case(
            When(total_coefficients_s1=0, then=Value(0.0)),
            default=ExpressionWrapper(
                F('total_points_s1') / F('total_coefficients_s1'),
                output_field=FloatField()
            ),
            output_field=FloatField()
        ),
        total_points_s2=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                filter=Q(note__semestre=2)  # Utilisation de Q ici
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients_s2=Coalesce(
            Sum('note__matiere__coefficient', filter=Q(note__semestre=2)),  # Utilisation de Q ici
            Value(1.0),
            output_field=FloatField()
        ),
        moyenne_s2=Case(
            When(total_coefficients_s2=0, then=Value(0.0)),
            default=ExpressionWrapper(
                F('total_points_s2') / F('total_coefficients_s2'),
                output_field=FloatField()
            ),
            output_field=FloatField()
        ),
        moyenne_annuelle=ExpressionWrapper(
            (F('moyenne_s1') + F('moyenne_s2')) / 2.0,
            output_field=FloatField()
        )
    ).order_by('-moyenne_annuelle')

    # Trouver le rang de l'élève
    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    context = {
        'eleve': eleve,
        'notes_semestre_1': notes_semestre_1,
        'notes_semestre_2': notes_semestre_2,
        'moyenne_generale_s1': moyenne_generale_s1,
        'moyenne_generale_s2': moyenne_generale_s2,
        'moyenne_annuelle': moyenne_annuelle,
        'passe_classe': passe_classe,
        'rang': rang,
        'annee_scolaire': annee_scolaire,
    }
    return render(request, 'bulletins/bulletin_eleve.html', context)


@login_required
@user_passes_test(is_admin_or_enseignant, login_url='login')
def bulletin_eleve_m2(request, eleve_id, semestre):
    # Récupérer l'élève
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    annee_scolaire = eleve.classe.etablissement.annee_scolaire if eleve.classe and eleve.classe.etablissement else "Non définie"

    # Filtrer les notes du semestre spécifié
    notes = Note.objects.filter(eleve=eleve, semestre=semestre).annotate(
        moyenne_calcules=ExpressionWrapper(
            (F('note_devoir') + F('note_composition')) / 2.0,
            output_field=FloatField()
        ),
        points_calcules=ExpressionWrapper(
            ((F('note_devoir') + F('note_composition')) / 2.0) * F('matiere__coefficient'),
            output_field=FloatField()
        )
    )

    # Calcul des totaux
    total_points = sum(note.points_calcules for note in notes)
    total_coefficients = sum(note.matiere.coefficient for note in notes)
    moyenne_generale = total_points / total_coefficients if total_coefficients > 0 else 0.0

    # Classement de l'élève dans sa classe pour le semestre
    classement = Eleve.objects.filter(classe=eleve.classe).annotate(
        total_points=Coalesce(
            Sum(
                ExpressionWrapper(
                    ((F('note__note_devoir') + F('note__note_composition')) / 2.0) * F('note__matiere__coefficient'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            ),
            Value(0.0),
            output_field=FloatField()
        ),
        total_coefficients=Coalesce(Sum('note__matiere__coefficient', output_field=FloatField()), Value(1.0)),
        moyenne=ExpressionWrapper(
            F('total_points') / F('total_coefficients'),
            output_field=FloatField()
        )
    ).order_by('-moyenne')

    # Trouver le rang de l'élève
    rang = next((i + 1 for i, e in enumerate(classement) if e.id == eleve.id), None)

    # Définir la date actuelle
    today = timezone.now()

    # Préparer le contexte
    context = {
        'eleve': eleve,
        'notes': notes,
        'total_points': total_points,
        'total_coefficients': total_coefficients,
        'moyenne_generale': moyenne_generale,
        'rang': rang,
        'today': today,
        'annee_scolaire': annee_scolaire,
        'semestre': semestre,  # Ajout du semestre dans le contexte
    }

    return render(request, 'bulletins/bulletin_eleve_m2.html', context)



# Vues pour les frais
@login_required
@user_passes_test(is_admin, login_url='login')
def liste_frais(request):
    frais_list = Frais.objects.all()
    return render(request, 'bulletins/liste_frais.html', {'frais_list': frais_list})


@login_required
@user_passes_test(is_admin, login_url='login')
def ajouter_frais(request):
    if request.method == 'POST':
        form = FraisForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_frais')
    else:
        form = FraisForm()
    return render(request, 'bulletins/form_frais.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
def modifier_frais(request, frais_id):
    frais = get_object_or_404(Frais, id=frais_id)
    if request.method == 'POST':
        form = FraisForm(request.POST, instance=frais)
        if form.is_valid():
            form.save()
            return redirect('liste_frais')
    else:
        form = FraisForm(instance=frais)
    return render(request, 'bulletins/form_frais.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
def supprimer_frais(request, frais_id):
    frais = get_object_or_404(Frais, id=frais_id)
    frais.delete()
    return redirect('liste_frais')

# Vues pour les paiements
def liste_paiements(request):
    paiement_list = Paiement.objects.all()
    return render(request, 'bulletins/liste_paiements.html', {'paiement_list': paiement_list})


@login_required
@user_passes_test(is_admin, login_url='login')
def enregistrer_paiement(request, eleve_id=None, frais_id=None):
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_paiements')
    else:
        initial = {}
        if eleve_id and frais_id:
            eleve = get_object_or_404(Eleve, id=eleve_id)
            frais = get_object_or_404(Frais, id=frais_id)
            initial = {'eleve': eleve, 'frais': frais}
        form = PaiementForm(initial=initial)
    return render(request, 'bulletins/enregistrer_paiement.html', {'form': form})

# Vues pour les échéances
def echeances_impayees(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    
    # Récupérer toutes les échéances de l'élève
    echeances = Echeance.objects.filter(eleve=eleve)
    
    # Calculer le solde restant (somme des échéances impayées)
    solde_restant = sum(echeance.montant_du for echeance in echeances if echeance.statut == 'impaye')
    
    return render(request, 'bulletins/echeances_impayees.html', {
        'eleve': eleve,
        'echeances': echeances,  # Toutes les échéances
        'solde_restant': solde_restant,  # Solde restant
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_eleves_par_classe(request):
    classe_id = request.GET.get('classe')
    search_query = request.GET.get('search')

    classes = Classe.objects.all()
    eleves = Eleve.objects.all()

    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    if search_query:
        eleves = eleves.filter(nom__icontains=search_query) | eleves.filter(prenom__icontains=search_query)

    # Calculer le mois actuel et le mois précédent
    mois_actuel = datetime.now().month
    mois_precedent = mois_actuel - 1 if mois_actuel > 1 else 12  # Gérer le passage de janvier à décembre
    mois_suivant = mois_actuel  # Le mois suivant est le mois actuel

    # Ajouter les mois payés et manquants pour chaque élève
    for eleve in eleves:
        # Récupérer les mois déjà payés pour cet élève
        eleve.mois_payes = list(Paiement.objects.filter(eleve=eleve, frais__type_frais='mensualite').values_list('mois', flat=True))
        # Calculer les mois manquants (mois passés non payés)
        eleve.mois_manquants = [mois for mois in range(1, mois_actuel) if mois not in eleve.mois_payes]

    return render(request, 'bulletins/liste_eleves_par_classe.html', {
        'classes': classes,
        'eleves': eleves,
        'selected_classe': int(classe_id) if classe_id else None,
        'search_query': search_query,
        'mois_precedent': mois_precedent,  # Passer le mois précédent au template
        'mois_suivant': mois_suivant,  # Passer le mois suivant au template
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def liste_eleves_par_classe_rest(request):
    classe_id = request.GET.get('classe')
    search_query = request.GET.get('search')

    classes = Classe.objects.all()
    eleves = Eleve.objects.all()

    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    if search_query:
        eleves = eleves.filter(nom__icontains=search_query) | eleves.filter(prenom__icontains=search_query)

    # Calculer le mois actuel et le mois précédent
    mois_actuel = datetime.now().month
    mois_precedent = mois_actuel - 1 if mois_actuel > 1 else 12  # Gérer le passage de janvier à décembre
    mois_suivant = mois_actuel  # Le mois suivant est le mois actuel

    # Ajouter les mois payés et manquants pour chaque élève
    for eleve in eleves:
        # Récupérer les mois déjà payés pour cet élève
        eleve.mois_payes = list(Paiement.objects.filter(eleve=eleve, frais__type_frais='mensualite').values_list('mois', flat=True))
        # Calculer les mois manquants (mois passés non payés)
        eleve.mois_manquants = [mois for mois in range(1, mois_actuel) if mois not in eleve.mois_payes]

    return render(request, 'bulletins/liste_eleves_par_classe_rest.html', {
        'classes': classes,
        'eleves': eleves,
        'selected_classe': int(classe_id) if classe_id else None,
        'search_query': search_query,
        'mois_precedent': mois_precedent,  # Passer le mois précédent au template
        'mois_suivant': mois_suivant,  # Passer le mois suivant au template
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def paiement_inscription(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    frais_inscription = Frais.objects.filter(type_frais='inscription', classe=eleve.classe).first()

    # Vérifier si un paiement d'inscription existe déjà
    paiement_existant = Paiement.objects.filter(eleve=eleve, frais=frais_inscription).first()
    if paiement_existant:
        messages.info(request, "Le paiement de l'inscription a déjà été effectué.")
        return redirect('details_paiement', paiement_id=paiement_existant.id)

    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.eleve = eleve
            paiement.frais = frais_inscription
            paiement.annee_scolaire = frais_inscription.annee_scolaire  # Définir l'année scolaire
            paiement.statut = 'paye'
            paiement.save()
            messages.success(request, "Paiement de l'inscription enregistré avec succès.")
            return redirect('details_paiement', paiement_id=paiement.id)
    else:
        # Initialiser le formulaire avec l'année scolaire
        form = PaiementForm(initial={
            'eleve': eleve,
            'frais': frais_inscription,
            'annee_scolaire': frais_inscription.annee_scolaire,  # Ajouter l'année scolaire
            'statut': 'paye'
        })

    return render(request, 'bulletins/paiement_form.html', {'form': form, 'eleve': eleve, 'type_paiement': 'inscription'})


@login_required
@user_passes_test(is_admin, login_url='login')
def paiement_mensuel(request, eleve_id, mois):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    frais_mensuel = Frais.objects.filter(type_frais='mensualite', classe=eleve.classe).first()

    # Récupérer l'année scolaire actuelle de la classe de l'élève
    annee_scolaire = eleve.classe.etablissement.annee_scolaire
    annee_actuelle = datetime.now().year  # Définir l'année actuelle

    # Vérifier si un paiement mensuel existe déjà pour ce mois et cette année scolaire
    paiement_existant = Paiement.objects.filter(
        eleve=eleve,
        frais=frais_mensuel,
        mois=mois,
        annee_scolaire=annee_scolaire
    ).first()

    if paiement_existant:
        messages.info(request, f"Le paiement pour le mois {paiement_existant.get_mois_display()} de l'année scolaire {paiement_existant.annee_scolaire.nom} a déjà été effectué.")
        return redirect('details_paiement', paiement_id=paiement_existant.id)

    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.eleve = eleve
            paiement.frais = frais_mensuel
            paiement.mois = mois
            paiement.annee_scolaire = annee_scolaire
            paiement.save()

            # Mettre à jour le statut de l'échéance correspondante
            echeance = Echeance.objects.filter(
                eleve=eleve,
                frais=frais_mensuel,
                date_echeance__month=mois,
                date_echeance__year=annee_actuelle
            ).first()
            if echeance:
                echeance.statut = 'paye'
                echeance.save()

            messages.success(request, f"Paiement pour le mois {paiement.get_mois_display()} de l'année scolaire {paiement.annee_scolaire.nom} enregistré avec succès.")
            return redirect('details_paiement', paiement_id=paiement.id)
    else:
        form = PaiementForm(initial={'eleve': eleve, 'frais': frais_mensuel, 'mois': mois, 'annee_scolaire': annee_scolaire})

    return render(request, 'bulletins/paiement_form.html', {
        'form': form,
        'eleve': eleve,
        'type_paiement': 'mensuel',
        'mois': mois,
        'annee_scolaire': annee_scolaire
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def details_paiement(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    return render(request, 'bulletins/details_paiement.html', {'paiement': paiement})




@login_required
@user_passes_test(is_admin, login_url='login')
def paiement_retroactif(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    frais_mensuel = Frais.objects.filter(type_frais='mensualite', classe=eleve.classe).first()

    if not frais_mensuel:
        messages.error(request, "Aucun frais mensuel n'est configuré pour cette classe.")
        return redirect('liste_eleves_par_classe')

    # Récupérer l'année scolaire en cours
    annee_scolaire = AnneeScolaire.get_annee_scolaire_en_cours()
    if not annee_scolaire:
        messages.error(request, "Aucune année scolaire n'est configurée pour la période en cours.")
        return redirect('liste_eleves_par_classe')

    # Vérifier si un paiement rétroactif existe déjà pour cet élève
    paiement_existant = Paiement.objects.filter(
        eleve=eleve,
        frais=frais_mensuel,
        est_retroactif=True,
        statut='paye',  # Ne considérer que les paiements effectués
        annee_scolaire=annee_scolaire  # Filtrer par année scolaire
    ).first()

    # Si un paiement rétroactif existe déjà, rediriger vers les détails
    if paiement_existant:
        messages.info(request, "Un paiement rétroactif existe déjà pour cet élève.")
        return redirect('details_paiement_retro', paiement_id=paiement_existant.id)

    if request.method == 'POST':
        form = PaiementRetroactifForm(request.POST)
        if form.is_valid():
            nombre_mois = form.cleaned_data['nombre_mois']
            mois_actuel = datetime.now().month

            # Calculer les mois concernés par le paiement rétroactif
            mois_debut = mois_actuel - nombre_mois + 1
            mois_fin = mois_actuel

            # Calculer le montant total pour tous les mois
            montant_total = frais_mensuel.montant * nombre_mois

            # Créer un seul paiement pour tous les mois concernés
            paiement = Paiement.objects.create(
                eleve=eleve,
                frais=frais_mensuel,
                montant_paye=montant_total,
                date_paiement=timezone.now(),
                mode_paiement=form.cleaned_data['mode_paiement'],
                statut='paye',
                reference=form.cleaned_data['reference'],
                mois=mois_fin,  # Enregistrer le dernier mois concerné
                est_retroactif=True,
                nombre_mois=nombre_mois,
                annee_scolaire=annee_scolaire  # Associer l'année scolaire en cours
            )

            messages.success(request, f"Paiement rétroactif pour {nombre_mois} mois enregistré avec succès.")
            return redirect('details_paiement_retro', paiement_id=paiement.id)
    else:
        form = PaiementRetroactifForm(initial={'eleve': eleve, 'frais': frais_mensuel})

    return render(request, 'bulletins/paiement_retroactif_form.html', {'form': form, 'eleve': eleve})




@login_required
@user_passes_test(is_admin, login_url='login')
def details_paiement_retro(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    return render(request, 'bulletins/details_paiement_retro.html', {'paiement': paiement})



@login_required
@user_passes_test(is_admin, login_url='login')
def liste_paiements_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)
    paiements = eleve.paiements.filter(statut='paye').order_by('-date_paiement')  # Récupérer les paiements payés

    # Pagination
    paginator = Paginator(paiements, 10)  # Afficher 10 paiements par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bulletins/liste_paiements_eleve.html', {'eleve': eleve, 'paiements': paiements, 'page_obj': page_obj,
        'solde_restant': eleve.solde_restant()})



@login_required
@user_passes_test(is_admin, login_url='login')
def imprimer_recu(request, paiement_id):
    paiement = get_object_or_404(Paiement, id=paiement_id)
    etablissement = paiement.eleve.classe.etablissement if paiement.eleve.classe else None
    return render(request, 'bulletins/recu_paiement.html', {
        'paiement': paiement,
        'etablissement': etablissement,
        'date_du_jour': date.today(),
    })



@login_required
@user_passes_test(is_admin, login_url='login')
def paiement_echeance(request, echeance_id):
    echeance = get_object_or_404(Echeance, id=echeance_id)

    # ✅ Récupérer l'année scolaire depuis le frais lié
    annee_scolaire_actuelle = echeance.frais.annee_scolaire  

      
    if request.method == 'POST':
        form = PaiementForm(request.POST, echeance=echeance)  # Passer l'échéance au formulaire
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.eleve = echeance.eleve
            paiement.frais = echeance.frais
            paiement.annee_scolaire = annee_scolaire_actuelle  # ✅ Utilisation de l'année scolaire du frais
            paiement.save()

            # Mettre à jour le statut de l'échéance
            if paiement.montant_paye >= echeance.montant_du:
                echeance.statut = 'paye'
                echeance.save()
                messages.success(request, "L'échéance a été payée avec succès.")
            else:
                messages.warning(request, "Le montant payé est inférieur au montant dû. L'échéance reste partiellement payée.")
            
            return redirect('echeances_impayees_eleve', eleve_id=echeance.eleve.id)
    else:
        form = PaiementForm(echeance=echeance)  # Passer l'échéance au formulaire

    return render(request, 'bulletins/paiement_echeance_form.html', {'form': form, 'echeance': echeance})



@login_required
@user_passes_test(is_admin, login_url='login')
def echeances_impayees_eleve(request, eleve_id):
    eleve = get_object_or_404(Eleve, id=eleve_id)

    # Récupérer l'année scolaire en cours
    annee_scolaire_en_cours = AnneeScolaire.get_annee_scolaire_en_cours()
    
    if not annee_scolaire_en_cours:
        return render(request, 'bulletins/echeances_impayees_eleve.html', {
            'eleve': eleve,
            'echeances_impayees': [],
            'erreur': "Aucune année scolaire en cours.",
            'solde_restant': eleve.solde_restant()
        })

    # Récupérer les échéances impayées
    echeances_impayees = eleve.echeances.filter(
        statut='impaye',
        frais__annee_scolaire=annee_scolaire_en_cours
    ).order_by('date_echeance')

    # Calcul du total impayé (échéances existantes)
    total_impaye = echeances_impayees.aggregate(total=Sum('montant_du'))['total'] or Decimal('0.00')

    return render(request, 'bulletins/echeances_impayees_eleve.html', {
        'eleve': eleve,
        'echeances_impayees': echeances_impayees,
        'total_impaye': total_impaye,
        'solde_restant': eleve.solde_restant(),  # ✅ Appel direct au solde
        'annee_scolaire': annee_scolaire_en_cours,
    })



@login_required
@user_passes_test(is_admin, login_url='login')
def facture_echeance(request, echeance_id):
    echeance = get_object_or_404(Echeance, id=echeance_id)
    etablissement = Etablissement.objects.first()  # À ajuster selon ton setup
    return render(request, 'bulletins/facture_echeance.html', {
        'echeance': echeance,
        'etablissement': etablissement,
        'date_du_jour': date.today(),
    })


def emploi_du_temps_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    emploi_du_temps = EmploiDuTemps.objects.filter(classe=classe).order_by('jour', 'heure_debut')
    
    return render(request, 'bulletins/emploi_du_temps_classe.html', {
        'classe': classe,
        'emploi_du_temps': emploi_du_temps,
    })



def emploi_du_temps_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    emploi_du_temps = EmploiDuTemps.objects.filter(enseignant=enseignant).order_by('jour', 'heure_debut')
    
    return render(request, 'bulletins/emploi_du_temps_enseignant.html', {
        'enseignant': enseignant,
        'emploi_du_temps': emploi_du_temps,
    })


def ajouter_creneau(request):
    if request.method == 'POST':
        form = EmploiDuTempsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_emploi_du_temps')  # Rediriger vers la liste des créneaux
    else:
        form = EmploiDuTempsForm()
    
    return render(request, 'bulletins/creneau_form.html', {
        'form': form,
        'titre': 'Ajouter un créneau',
    })


def get_matieres_par_enseignant(request):
    enseignant_id = request.GET.get('enseignant_id')
    if enseignant_id:
        try:
            enseignant = Enseignant.objects.get(id=enseignant_id)
            matieres = enseignant.matieres.all()
            matieres_data = [{'id': matiere.id, 'nom': matiere.nom} for matiere in matieres]
            return JsonResponse({'matieres': matieres_data})
        except Enseignant.DoesNotExist:
            return JsonResponse({'matieres': []})
    return JsonResponse({'matieres': []})


def modifier_creneau(request, creneau_id):
    creneau = get_object_or_404(EmploiDuTemps, id=creneau_id)
    if request.method == 'POST':
        form = EmploiDuTempsForm(request.POST, instance=creneau)
        if form.is_valid():
            form.save()
            return redirect('liste_emploi_du_temps')  # Rediriger vers la liste des créneaux
    else:
        form = EmploiDuTempsForm(instance=creneau)
    
    return render(request, 'bulletins/creneau_form.html', {
        'form': form,
        'titre': 'Modifier un créneau',
    })


def liste_classes_emp(request):
    classes = Classe.objects.all()
    return render(request, 'bulletins/liste_classes_emp.html', {
        'classes': classes,
    })


def liste_enseignants_emp(request):
    enseignants = Enseignant.objects.all()
    return render(request, 'bulletins/liste_enseignants_emp.html', {
        'enseignants': enseignants,
    })


def liste_emploi_du_temps(request):
    classe_id = request.GET.get('classe')  # Récupérer l'ID de la classe sélectionnée
    creneaux_list = EmploiDuTemps.objects.all().order_by('jour', 'heure_debut')

    if classe_id:
        creneaux_list = creneaux_list.filter(classe_id=classe_id)

    paginator = Paginator(creneaux_list, 10)  # 10 éléments par page
    page_number = request.GET.get('page')
    creneaux = paginator.get_page(page_number)

    classes = Classe.objects.all()  # Récupérer toutes les classes pour le filtre

    return render(request, 'bulletins/liste_emploi_du_temps.html', {
        'creneaux': creneaux,
        'classes': classes,
        'selected_classe': classe_id,  # Passer la classe sélectionnée pour l'affichage
    })


def etat_impression_classe(request, classe_id):
    classe = get_object_or_404(Classe, id=classe_id)
    emploi_du_temps = EmploiDuTemps.objects.filter(classe=classe).order_by('jour', 'heure_debut')
    
    # Organiser les créneaux par jour
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    emploi_par_jour = {jour: [] for jour in jours}
    
    for creneau in emploi_du_temps:
        emploi_par_jour[creneau.jour].append(creneau)
    
    return render(request, 'bulletins/etat_impression_classe.html', {
        'classe': classe,
        'emploi_par_jour': emploi_par_jour,
    })


def etat_impression_enseignant(request, enseignant_id):
    enseignant = get_object_or_404(Enseignant, id=enseignant_id)
    emploi_du_temps = EmploiDuTemps.objects.filter(enseignant=enseignant).order_by('jour', 'heure_debut')
    
    # Organiser les créneaux par jour
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    emploi_par_jour = {jour: [] for jour in jours}
    
    for creneau in emploi_du_temps:
        emploi_par_jour[creneau.jour].append(creneau)

    # Récupérer l'année scolaire en cours et les informations de l'établissement
    annee_scolaire = AnneeScolaire.get_annee_scolaire_en_cours()
    etablissement = Etablissement.objects.first()  # Assurez-vous d'adapter la méthode de récupération

    return render(request, 'bulletins/etat_impression_enseignant.html', {
        'enseignant': enseignant,
        'emploi_par_jour': emploi_par_jour,
        'annee_scolaire': annee_scolaire,
        'etablissement': etablissement,
    })
