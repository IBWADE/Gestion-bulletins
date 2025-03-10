from django.urls import path
from . import views
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.contrib.auth import views as auth_views



schema_view = get_schema_view(
    openapi.Info(
        title="API Gestion Scolaire",
        default_version='v1',
        description="API pour la gestion des bulletins scolaires",
    ),
    public=True,
)

urlpatterns = [
    # Page d'accueil
    path('', views.accueil, name='accueil'),

    # Authentification
    path('login/', views.login_view, name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Pages d'accueil selon le rôle
    path('accueil-admin/', views.accueil_admin, name='accueil_admin'),
    path('accueil-enseignant/', views.accueil_enseignant, name='accueil_enseignant'),
    path('accueil-parent/', views.accueil_parent, name='accueil_parent'),
    path('details-enfant/<int:eleve_id>/', views.details_enfant, name='detail_enfant'),

    # Gestion des utilisateurs
    path('creer-compte/', views.creer_compte, name='creer_compte'),
    path('creer-utilisateur/', views.creer_utilisateur, name='creer_utilisateur'),
    path('liste_utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('profile-user/<int:user_id>/', views.profile_user, name='profile_user'),
    path('modifier-user/<int:user_id>/', views.modifier_user, name='modifier_user'),

    # Documentation API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # Notification
    path('saisie-notification/', views.saisie_notification, name='saisie_notification'),
    path('liste-notifications/', views.liste_notifications, name='liste_notifications'),

    # Absence
    path('saisie-absence/', views.saisie_absence, name='saisie_absence'),
    path('liste-absences/', views.liste_absences, name='liste_absences'),
    path('absence/<int:absence_id>/details/', views.detail_absence, name='detail_absence'),
    path('absence/<int:absence_id>/modifier/', views.modifier_absence, name='modifier_absence'),
    path('absence/<int:absence_id>/supprimer/', views.supprimer_absence, name='supprimer_absence'),

    # Gestion des élèves     
    path('bulletin/<int:eleve_id>/', views.bulletin_eleve, name='bulletin_eleve'),
    path('bulletin-m2/<int:eleve_id>/<int:semestre>/', views.bulletin_eleve_m2, name='bulletin_eleve_m2'),
    path('eleve/<int:eleve_id>/', views.eleve, name='eleve'),
    path('saisie-eleve/', views.saisie_eleve, name='saisie_eleve'),
    path('liste-eleves/', views.liste_eleves, name='liste_eleves'),
    path("profil-eleve/<int:eleve_id>/", views.profil_eleve, name="profil_eleve"),  # Vérifie bien cette ligne !
    path('modifier-eleve/<int:eleve_id>/', views.modifier_eleve, name='modifier_eleve'),
    path('supprimer-eleve/<int:eleve_id>/', views.supprimer_eleve, name='supprimer_eleve'),

     # URLs pour les frais
    path('liste-frais/', views.liste_frais, name='liste_frais'),
    path('ajout-frais/', views.ajouter_frais, name='ajouter_frais'),
    path('modifier-frais/<int:frais_id>/', views.modifier_frais, name='modifier_frais'),
    path('supprimer-frais/<int:frais_id>/', views.supprimer_frais, name='supprimer_frais'),

    # URLs pour les paiements
    path('paiements/', views.liste_paiements, name='liste_paiements'),
    path('paiements/enregistrer/', views.enregistrer_paiement, name='enregistrer_paiement'),
    path('paiements/enregistrer/<int:eleve_id>/<int:frais_id>/', views.enregistrer_paiement, name='enregistrer_paiement_eleve'),
    path('liste-eleves-par-classe/', views.liste_eleves_par_classe, name='liste_eleves_par_classe'),
    path('paiement/inscription/<int:eleve_id>/', views.paiement_inscription, name='paiement_inscription'),
    path('paiement/mensuel/<int:eleve_id>/', views.paiement_mensuel, name='paiement_mensuel'),
    path('paiement/mensuel/<int:eleve_id>/<int:mois>/', views.paiement_mensuel, name='paiement_mensuel_mois'),
    path('paiement/details/<int:paiement_id>/', views.details_paiement, name='details_paiement'),
    path('paiement/retroactif/<int:eleve_id>/', views.paiement_retroactif, name='paiement_retroactif'),
    path('detail-paiement-retro/details/<int:paiement_id>/', views.details_paiement_retro, name='details_paiement_retro'),
    path('eleve/<int:eleve_id>/paiements/', views.liste_paiements_eleve, name='liste_paiements_eleve'),
    path('paiement/<int:paiement_id>/recu/', views.imprimer_recu, name='imprimer_recu'),
    path('eleve/<int:eleve_id>/echeances-impayees/', views.echeances_impayees_eleve, name='echeances_impayees_eleve'),
    path('echeance/<int:echeance_id>/payer/', views.paiement_echeance, name='paiement_echeance'),
    path('facture/<int:echeance_id>/', views.facture_echeance, name='facture_echeance'),

    # URLs pour les échéances
    path('eleves/<int:eleve_id>/echeances/', views.echeances_impayees, name='echeances_impayees'),

    

    # Gestion des établissements
    path('saisie-etablissement/', views.saisie_etablissement, name='saisie_etablissement'),
    path('liste-etablissements/', views.liste_etablissements, name='liste_etablissements'),
    path('etablissements/modifier/<int:etablissement_id>/', views.modifier_etablissement, name='modifier_etablissement'),
    path('etablissements/supprimer/<int:etablissement_id>/', views.supprimer_etablissement, name='supprimer_etablissement'),

    # Gestion des classes
    path('liste-classes/', views.liste_classes, name='liste_classes'),
    path('saisie-classe/', views.saisie_classe, name='saisie_classe'),
    path('modifier-classe/<int:classe_id>/', views.modifier_classe, name='modifier_classe'),
    path('supprimer-classe/<int:classe_id>/', views.supprimer_classe, name='supprimer_classe'),
    path('liste-classes-etablissement/<int:etablissement_id>/', views.liste_classes_etablissement, name='liste_classes_etablissement'),
    path('liste-eleves-classe/<int:classe_id>/', views.liste_eleves_classe, name='liste_eleves_classe'),
    path('liste-eleves-classe-vis/<int:classe_id>/', views.liste_eleves_classe_vis, name='liste_eleves_classe_vis'),
    path('liste-classes-etablissement-popup/<int:etablissement_id>/', views.liste_classes_etablissement_popup, name='liste_classes_etablissement_popup'),
    
    # Gestion des enseignants
    path('saisie-enseignant/', views.saisie_enseignant, name='saisie_enseignant'),
    path('liste-enseignants/', views.liste_enseignants, name='liste_enseignants'),
    path('modifier-enseignant/<int:enseignant_id>/', views.modifier_enseignant, name='modifier_enseignant'),
    path('supprimer-enseignant/<int:enseignant_id>/', views.supprimer_enseignant, name='supprimer_enseignant'),
    path('saisie-classes-enseignant/<int:enseignant_id>/', views.saisie_classes_enseignant, name='saisie_classes_enseignant'),
    path('detail-classes-enseignant/<int:enseignant_id>/', views.detail_classes_enseignant, name='detail_classes_enseignant'),
    path('liste-classe-ens/', views.liste_classes_enseignant, name='liste_classes_enseignant'),
    path('liste-eleves-classe-enseignant/<int:classe_id>/eleves/', views.liste_eleves_classe_enseignant, name='liste_eleves_classe_enseignant'),
    path('details-notes-eleve-ens/<int:eleve_id>/details/<int:semestre>/', views.details_notes_eleve_enseignant, name='details_notes_eleve_enseignant'),
    path('saisie-note-enseignant/<int:eleve_id>/notes/saisie/<int:semestre>/', views.saisie_note_enseignant, name='saisie_note_enseignant'),
    path('modifier-note-ens/<int:note_id>/', views.modifier_note_ens, name='modifier_note_ens'),

    # Gestion des matières
    path('saisie-matieres/', views.saisie_matiere, name='saisie_matiere'),
    path('liste-matieres/', views.liste_matieres, name='liste_matieres'),
    path('modifier-matiere/<int:matiere_id>/', views.modifier_matiere, name='modifier_matiere'),
    path('supprimer-matiere/<int:matiere_id>/', views.supprimer_matiere, name='supprimer_matiere'),
    path('eleve/<int:eleve_id>/choix-matieres/', views.choisir_matieres_optionnelles, name='choisir_matieres'),

    # Gestion emploi du temps
    path('liste-classes-emp/', views.liste_classes_emp, name='liste_classes_emp'),
    path('liste-enseignants-emp/', views.liste_enseignants_emp, name='liste_enseignants_emp'),
    path('emploi-du-temps/classe/<int:classe_id>/', views.emploi_du_temps_classe, name='emploi_du_temps_classe'),
    path('emploi-du-temps/enseignant/<int:enseignant_id>/', views.emploi_du_temps_enseignant, name='emploi_du_temps_enseignant'),
    path('ajouter-creneau/', views.ajouter_creneau, name='ajouter_creneau'),
    path('modifier-creneau/<int:creneau_id>/', views.modifier_creneau, name='modifier_creneau'),
    path('liste-emploi-du-temps/', views.liste_emploi_du_temps, name='liste_emploi_du_temps'),
    path('etat-impression/classe/<int:classe_id>/', views.etat_impression_classe, name='etat_impression_classe'),
    path('etat-impression/enseignant/<int:enseignant_id>/', views.etat_impression_enseignant, name='etat_impression_enseignant'),
    path('get_matieres_par_enseignant/', views.get_matieres_par_enseignant, name='get_matieres_par_enseignant'),

    # Gestion des notes
    path('saisie-notes-eleve/<int:eleve_id>/notes/saisie/<int:semestre>/', views.saisie_notes_eleve, name='saisie_notes_eleve'),
    path('details-notes-eleve/<int:eleve_id>/notes/saisie/<int:semestre>/', views.details_notes_eleve, name='details_notes_eleve'),
    path('details-notes-eleve-classe/<int:eleve_id>/notes/saisie/<int:semestre>/', views.details_notes_eleve_classe, name='details_notes_eleve_classe'),
    path('impression-bulletin/<int:eleve_id>/<int:semestre>/', views.impression_bulletin_eleve, name='impression_bulletin_eleve'),
    path('impression-bulletins-classe1/<int:classe_id>/<int:semestre>/', views.impression_bulletins_classe1, name='impression_bulletins_classe1'),
    path('impression-bulletins-classe2/<int:classe_id>/<int:semestre>/', views.impression_bulletins_classe2, name='impression_bulletins_classe2'),
    path('recherche-globale/', views.recherche_globale, name='recherche_globale'),
    path('calcul-passage-classe/<int:classe_id>/', views.calcul_passage_classe, name='calcul_passage_classe'),
    path('bulletin/semestre-1/<int:eleve_id>/', views.bulletin_semestre_1, name='bulletin_semestre_1'),
    path('bulletin/semestre-2/<int:eleve_id>/', views.bulletin_semestre_2, name='bulletin_semestre_2'),
    path('modifier-note/<int:note_id>/', views.modifier_note, name='modifier_note'),

    # Gestion des statistiques
    path('statistiques-globales/', views.statistiques_globales, name='statistiques_globales'),

    # Archivage
    path('archiver-annee/', views.archiver_annee, name='archiver_annee'),
    path('liste-archives/', views.liste_archives, name='liste_archives'),
    path('detail-archive/<int:archive_id>/', views.detail_archive, name='detail_archive'),

    # Restaurer
    path('restaurer-annee-scolaire/<int:archive_id>', views.restaurer_archive, name='restaurer_archive'),
    path('liste-restaurer-archive/', views.restaurer_archive_liste, name='restaurer_archive_liste'),
    path('details-notes-eleve-rest/<int:eleve_id>/notes/saisie/<int:semestre>/<str:annee_scolaire>/', views.details_notes_eleve_restaurer, name='details_notes_eleve_rest'),
    path('liste-eleves-bis/', views.liste_eleves_bis, name='liste_eleves_bis'),
    path('restaurer-paiement/<int:paiement_id>/', views.restaurer_paiement, name='restaurer_paiement'),
    path('liste-eleves-par-classe-rest/', views.liste_eleves_par_classe_rest, name='liste_eleves_par_classe_rest'),
    path('detail-eleve-paiement-rest/<int:eleve_id>/paiements/', views.details_payement_rest, name='details_payement_rest'),


    # Annee
    path('archiver-annee/', views.archiver_annee, name='archiver_annee'),
    path('saisie-annee-scolaire/', views.saisie_annee_scolaire, name='saisie_annee_scolaire'),
    path('liste-annees-scolaires/', views.liste_annees_scolaires, name='liste_annees_scolaires'),
    path('modifier-annee-scolaire/<int:annee_id>/', views.modifier_annee_scolaire, name='modifier_annee_scolaire'),
    path('supprimer-annee-scolaire/<int:annee_id>/', views.supprimer_annee_scolaire, name='supprimer_annee_scolaire'),

    # Ajouter un niveau scolaire
    path('niveaux/ajouter/', views.ajouter_niveau, name='ajouter_niveau'),    
    path('liste-niveaux/', views.liste_niveaux, name='liste_niveaux'),    
    path('modifier-niveaux/<int:niveau_id>/modifier/', views.modifier_niveau, name='modifier_niveau'),    
    path('supprimer-niveaux/<int:niveau_id>/supprimer/', views.supprimer_niveau, name='supprimer_niveau'),

    # Ajouter une matiere optionnelle
    path('eleve/<int:eleve_id>/choix-matieres/', views.choisir_matieres_optionnelles, name='choisir_matieres_optionnelles'),

    # Marquer comme lue
    path('notifications/lue/<int:notification_id>/', views.marquer_comme_lue, name='marquer_comme_lue'),
    path('notifications/lire_toutes/', views.marquer_toutes_comme_lues, name='marquer_toutes_comme_lues'),
    path('vider-notifications/', views.vider_notifications, name='vider_notifications'),
  
]






